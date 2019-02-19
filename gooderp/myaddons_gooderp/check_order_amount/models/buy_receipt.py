# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo import fields, models, api, tools


class BuyReceipt(models.Model):
    _inherit = 'buy.receipt'

    @api.one
    def _wrong_receipt_done(self):
        '''审核时不合法的给出报错
        :return:
        '''
        res = super(BuyReceipt, self)._wrong_receipt_done()

        total = 0
        if self.line_in_ids:
            # 入库时优惠前总金额
            total = sum(line.subtotal for line in self.line_in_ids)
        elif self.line_out_ids:
            # 退货时优惠前总金额
            total = sum(line.subtotal for line in self.line_out_ids)
        amount = total - self.discount_amount + self.delivery_fee
        decimal_amount = self.env.ref('core.decimal_amount')
        if float_compare(self.amount, amount, precision_digits=decimal_amount.digits) != 0:
                    raise UserError(u'采购单据的合计金额 %s 不等于明细行的合计金额 %s'
                                    % (self.amount, amount))
        return res