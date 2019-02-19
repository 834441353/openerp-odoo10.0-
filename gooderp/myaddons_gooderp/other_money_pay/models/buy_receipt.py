# -*- coding: utf-8 -*-

from odoo import fields, models, api

class BuyReceipt(models.Model):
    _inherit = "buy.receipt"

    def _receipt_make_invoice(self):
        '''入库单/退货单 生成结算单'''
        if not self.is_return:
            if not self.invoice_by_receipt:
                return False
            amount = self.amount
            tax_amount = sum(line.tax_amount for line in self.line_in_ids)
        else:
            amount = -self.amount
            tax_amount = - sum(line.tax_amount for line in self.line_out_ids)
        categ = self.env.ref('money.core_category_purchase')
        # if not float_is_zero(amount, 2):
        #取消限制0金额的单据不产生结算单
        invoice_id = self.env['money.invoice'].create(
            self._get_invoice_vals(
                self.partner_id, categ, self.date, amount, tax_amount)
        )
        return invoice_id