# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'partner'

    @api.multi
    def write(self, vals):
        # 业务伙伴应收/应付余额不为0时，不允许归档
        if vals.get('active') == False:
            if self.receivable != 0:
                raise UserError(u'客户%s应收余额为%s，该余额不为0，不能取消业务伙伴'%(self.name,self.receivable))
            if self.payable != 0:
                raise UserError(u'供应商%s应付余额为%s，该余额不为0，不能取消业务伙伴'%(self.name,self.receivable))
        return super(Partner, self).write(vals)