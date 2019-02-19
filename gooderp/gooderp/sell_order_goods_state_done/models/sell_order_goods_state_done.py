# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class SellOrderReceivable(models.Model):
    _inherit = 'sell.order'

    @api.one
    @api.depends('line_ids.quantity', 'line_ids.quantity_out', 'delivery_ids')
    def _get_sell_goods_state(self):
        '''返回发货状态'''
        if all(line.quantity_out == 0 for line in self.line_ids):
            self.goods_state = u'未出库'
        elif any(line.quantity > line.quantity_out for line in self.line_ids):
            self.goods_state = u'部分出库'
        elif any(line.quantity > line.quantity_out for line in self.line_ids):
            for  delivery_ids in self.delivery_ids:
                if delivery_ids.states !== draft:
                    self.goods_state = u'部分完成'
        else:
            self.goods_state = u'全部出库'