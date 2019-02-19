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