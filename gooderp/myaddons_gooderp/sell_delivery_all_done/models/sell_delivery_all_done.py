# coding: utf-8

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class sell_delivery_all_done(models.TransientModel):
    """
        批量审核
    """
    _name = 'sell.delivery.all.done'

    type = fields.Selection([('approve', u'审核'), ('check', u'检查')], u'类型',
                            default=lambda self: self.env.context.get('type'))

    @api.multi
    def sell_delivery_all_done(self):
        draft_ids = self.env['sell.delivery'].browse(self.env.context.get('active_ids'))
        if self.type == 'approve':
            for draft_id in draft_ids:
                if draft_id.state != 'draft':
                    raise UserError(_('只能批量审核草稿状态的单据.'))
                draft_id.sell_delivery_done()
        return True

