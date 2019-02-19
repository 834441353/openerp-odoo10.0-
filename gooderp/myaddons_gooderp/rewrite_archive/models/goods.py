# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class Goods(models.Model):
    _inherit = 'goods'

    current_qty = fields.Float(u'当前数量', store=True)

    @api.multi
    def write(self, vals):
        # 业务伙伴应收/应付余额不为0时，不允许归档
        if vals.get('active') == False:
            if self.current_qty != 0:
                raise UserError(u'商品%s库存数量为%s，库存数量不为０时不能取消商品'%(self.name,self.current_qty))
        return super(Goods, self).write(vals)