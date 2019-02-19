# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_is_zero
from odoo import fields, models, api, tools


class OtherMoneyOrder(models.Model):
    _inherit = 'sell.delivery'

    def _delivery_make_invoice(self):
        '''发货单/退货单 生成结算单'''
        if not self.is_return:
            amount = self.amount + self.partner_cost
            tax_amount = sum(line.tax_amount for line in self.line_out_ids)
        else:
            amount = -(self.amount + self.partner_cost)
            tax_amount = - sum(line.tax_amount for line in self.line_in_ids)
        category = self.env.ref('money.core_category_sale')
        invoice_id = False
        if not float_is_zero(amount, 2):
            invoice_id = self.env['money.invoice'].create(
                self._get_invoice_vals(
                    self.partner_id, category, self.date, amount, tax_amount)
            )
        #添加调价 如果单据的金额是0的情况下生成0金额结算单（生成结算单不生成凭证）
        else:
            invoice_id = self.env['money.invoice'].create(
                self._get_zero_invoice_vals(
                    self.partner_id, category, self.date, amount, tax_amount)
            )
        return invoice_id


    def _get_zero_invoice_vals(self, partner_id, category_id, date, amount, tax_amount):
        '''返回创建 money_invoice 时所需数据'''
        return {
            'move_id': self.sell_move_id.id,
            'name': self.name,
            'partner_id': partner_id.id,
            'category_id': category_id.id,
            'date': date,
            'amount': amount,
            'reconciled': 0,
            'to_reconcile': amount,
            'tax_amount': tax_amount,
            'date_due': self.date_due,
            'state': 'done',
            'currency_id': self.currency_id.id,
            'note': self.note,
        }

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
                'invoice_id': invoice_id and invoice_id.id,
                'state': 'done',  # 为保证审批流程顺畅，否则，未审批就可审核
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

            # 先收款后发货订单自动核销
            self.auto_reconcile_sell_order()

            # 生成分拆单 FIXME:无法跳转到新生成的分单
            if record.order_id and not record.modifying:
                return record.order_id.sell_generate_delivery()