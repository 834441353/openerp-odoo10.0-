# -*- coding: utf-8 -*-

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import datetime
from odoo.tools import float_compare, float_is_zero

# 字段只读状态
READONLY_STATES = {
    'done': [('readonly', True)],
}
ISODATEFORMAT = '%Y-%m-%d'


class BuyReceipt(models.Model):
    _inherit = "buy.receipt"

    def _receipt_make_invoice(self):
        '''入库单/退货单 生成结算单'''
        invoice_id = False
        if not self.is_return:
            if not self.invoice_by_receipt:
                return False
            amount = self.amount
            tax_amount = sum(line.tax_amount for line in self.line_in_ids)
        else:
            amount = -self.amount
            tax_amount = - sum(line.tax_amount for line in self.line_out_ids)
        categ = self.env.ref('money.core_category_purchase')
        if not float_is_zero(amount, 2):
            invoice_id = self.env['money.invoice'].create(
                self._get_invoice_vals(
                    self.partner_id, categ, self.date, amount, tax_amount)
            )
        #零金额生成结算单
        else:
            invoice_id = self.env['money.invoice'].create(
                self._get_zero_invoice_vals(
                    self.partner_id, categ, self.date, amount, tax_amount)
            )
        return invoice_id

    def _get_zero_invoice_vals(self, partner_id, category_id, date, amount, tax_amount):
        '''返回创建 money_invoice 时所需数据'''
        return {
            'move_id': self.buy_move_id.id,
            'name': self.name,
            'partner_id': partner_id.id,
            'category_id': category_id.id,
            'date': date,
            'amount': amount,
            'reconciled': 0,
            'to_reconcile': amount,
            'tax_amount': tax_amount,
            'date_due': self.date_due,
            'state': 'draft',
            'currency_id': self.currency_id.id,
            'note': self.note,
        }

