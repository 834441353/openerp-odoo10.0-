# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class SellOrderReceivable(models.Model):
    _inherit = 'sell.order'

    receivable = fields.Float(related='partner_id.receivable', string=u'应收金额',
                              digits=dp.get_precision('Amount'), help=u'客户当前的欠款金额')