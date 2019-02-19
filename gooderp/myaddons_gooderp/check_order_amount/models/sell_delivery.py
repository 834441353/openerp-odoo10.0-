# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo import fields, models, api, tools


class SellDelivery(models.Model):
    _inherit = 'sell.delivery'

    @api.one
    def _wrong_delivery_done(self):
        '''审核时不合法的给出报错
        :return:
        '''
        res = super(SellDelivery, self)._wrong_delivery_done()
        total = 0
        if self.line_out_ids:
            # 发货时优惠前总金
            total = sum(line.subtotal for line in self.line_out_ids)
        elif self.line_in_ids:
            # 退货时优惠前总金额
            total = sum(line.subtotal for line in self.line_in_ids)
        amount = total - self.discount_amount
        decimal_amount = self.env.ref('core.decimal_amount')
        if float_compare(self.amount, amount, precision_digits=decimal_amount.digits) != 0:
                    raise UserError(u'销售单据的合计金额 %s 不等于明细行的合计金额 %s'
                                    % (self.amount, amount))
        return res