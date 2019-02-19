# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import fields, models, api, tools


class SellDelivery(models.Model):
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

        invoice_id = self.env['money.invoice'].create(
            self._get_invoice_vals(
                self.partner_id, category, self.date, amount, tax_amount)
        )
        return invoice_id
