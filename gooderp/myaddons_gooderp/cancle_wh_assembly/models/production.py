# coding: utf-8

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class WhAssembly(models.Model):
    _inherit = 'wh.assembly'

    @api.multi
    def cancel_approved_feeding(self):
        ''' 撤销发料 '''
        for order in self:
            if order.state == 'draft':
                raise UserError(u'单据%s未发料，不需要取消发料'%(self.name))
            if order.state == 'done':
                raise UserError(u'单据%s已经验收入库，不允许取消发料，请先取消入库'%(self.name))
            line_out_cost = 0

            for line_out in order.line_out_ids:
                line_out_cost += line_out.cost
                if line_out.state == 'done':
                    line_out.action_draft()
            # 删除出库凭证
            out_voucher, order.out_voucher_id = order.out_voucher_id, False
            if out_voucher.state == 'done':
                out_voucher.voucher_draft()
            out_voucher.unlink()

            order.approve_uid = False
            order.approve_date = False
            order.state = 'draft'
            return