# -*- coding: utf-8 -*-

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp
import datetime
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

class SellDelivery(models.Model):
    _inherit = 'sell.delivery'

    @api.multi
    def sell_delivery_done(self):
        '''审核销售发货单/退货单，更新本单的收款状态/退款状态，并生成结算单和收款单'''
        for record in self:
            record._wrong_delivery_done()
            # 库存不足 生成零的
            if self.env.user.company_id.is_enable_negative_stock:
                result_vals = self.env['wh.move'].create_zero_wh_in(
                    record, record._name)
                if result_vals:
                    return result_vals
            # 调用wh.move中审核方法，更新审核人和审核状态
            record.sell_move_id.approve_order()
            # 将发货/退货数量写入销货订单行
            if record.order_id:
                record._line_qty_write()
            voucher = False
            # 创建出库的会计凭证，生成盘盈的入库单的不产生出库凭证
            if not self.env.user.company_id.endmonth_generation_cost:
                voucher = record.create_voucher()
            # 发货单/退货单 生成结算单
            invoice_id = record._delivery_make_invoice()
            record.write({
                'voucher_id': voucher and voucher.id,
                'invoice_id': invoice_id and invoice_id.id,# 为保证审批流程顺畅，否则，未审批就可审核
                'state': 'done',    # 为保证审批流程顺畅，否则，未审批就可审核
            })
            # 销售费用产生结算单
            record._sell_amount_to_invoice()
            # 生成收款单，并审核
            if record.receipt:
                flag = not record.is_return and 1 or -1
                amount = flag * (record.amount + record.partner_cost)
                this_reconcile = flag * record.receipt
                money_order = record._make_money_order(
                    invoice_id, amount, this_reconcile)
                money_order.money_order_done()
                self.money_order_id = money_order.id

            # 先收款后发货订单自动核销
            self.auto_reconcile_sell_order()

            #退货单不自动生成分拆单，出货单自动创建新的分拆单
            # 生成分拆单 FIXME:无法跳转到新生成的分单
            if record.order_id and not record.modifying:
                # 如果已退货也已退款，不生成新的分单，修改成如果是退货，不生成新的分单
                #if record.is_return and record.receipt:
                if record.is_return:
                    return True
                return record.order_id.sell_generate_delivery()

    @api.multi
    def sell_return_to_return(self):
        '''销售退货单转化为销售发货单'''
        sell_order_draft = self.search([
            ('is_return', '=', False),
            ('order_id', '=', self.order_id.id),
            ('state', '=', 'draft')
        ])

        if sell_order_draft:
            raise UserError(u'销售退货单存在草稿状态的发货单！')
        for record in self:
            if record.order_id and not record.modifying:
                # 如果已退货也已退款，不生成新的分单
                if record.is_return and record.receipt:
                    return True
                return record.order_id.sell_generate_delivery()