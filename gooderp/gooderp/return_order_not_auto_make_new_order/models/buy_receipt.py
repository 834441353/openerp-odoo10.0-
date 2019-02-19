# -*- coding: utf-8 -*-

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import datetime
from odoo.tools import float_compare, float_is_zero

class BuyReceipt(models.Model):
    _inherit = ['buy.receipt']

    @api.one
    def buy_receipt_done(self):
        '''审核采购入库单/退货单，更新本单的付款状态/退款状态，并生成结算单和付款单'''
        # 报错
        self._wrong_receipt_done()
        # 调用wh.move中审核方法，更新审核人和审核状态
        self.buy_move_id.approve_order()

        # 将收货/退货数量写入订单行
        self._line_qty_write()

        # 创建入库的会计凭证
        voucher = self.create_voucher()

        # 入库单/退货单 生成结算单
        invoice_id = self._receipt_make_invoice()
        self.write({
            'voucher_id': voucher and voucher.id,
            'invoice_id': invoice_id and invoice_id.id,# 为保证审批流程顺畅，否则，未审批就可审核
            'state': 'done',  # 为保证审批流程顺畅，否则，未审批就可审核
        })
        # 采购费用产生结算单
        self._buy_amount_to_invoice()
        # 生成付款单
        if self.payment:
            flag = not self.is_return and 1 or -1
            amount = flag * self.amount
            this_reconcile = flag * self.payment
            self._make_payment(invoice_id, amount, this_reconcile)
        # 生成分拆单 FIXME:无法跳转到新生成的分单
        if self.order_id and not self.modifying:
            # 如果已退货也已退款，不生成新的分单,改成如果是退货，不生成新的分单
            #if self.is_return and self.payment:
            if self.is_return:
                return True
            return self.order_id.buy_generate_receipt()

    @api.multi
    def buy_return_to_return(self):
        '''销售退货单转化为销售发货单'''
        buy_order_draft = self.search([
            ('is_return', '=', False),
            ('order_id', '=', self.order_id.id),
            ('state', '=', 'draft')
        ])

        if buy_order_draft:
            raise UserError(u'采购退货单存在草稿状态的采购入库单！')
        # for record in self:
        if self.order_id and not self.modifying:
            # 如果已退货也已退款，不生成新的分单
            if self.is_return and self.payment:
                return True
            return self.order_id.buy_generate_receipt()