# -*- coding: utf-8 -*-

from openerp import models, _, fields, api
import xlrd, base64
from openerp.osv import osv
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_is_zero
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

class partner_statement(models.Model):
    """
        业务伙伴对账单
    """
    _name = 'partner.statement'
    _inherit = ['mail.thread']
    _description = u"业务伙伴对账单"
    _order = 'date desc, id desc'

    partner_id = fields.Many2one('partner',u'业务伙伴', readonly=True, ondelete='restrict')
    is_customer = fields.Boolean(u'客户')
    is_supplier = fields.Boolean(u'供应商')
    c_category_id = fields.Many2one('core.category', u'客户类别',
                                    ondelete='restrict',
                                    domain=[('type', '=', 'customer')],
                                    context={'type': 'customer'})
    s_category_id = fields.Many2one('core.category', u'供应商类别',
                                    ondelete='restrict',
                                    domain=[('type', '=', 'supplier')],
                                    context={'type': 'supplier'})
    c_balance = fields.Float(u'系统应收金额', readonly=True,
                             digits=dp.get_precision('Amount'))
    s_balance = fields.Float(u'系统应付余额', readonly=True,
                             digits=dp.get_precision('Amount'))
    new_c_balance = fields.Float(u'对账应收余额',
                                 digits=dp.get_precision('Amount'))
    new_s_balance = fields.Float(u'对账应付余额',
                                 digits=dp.get_precision('Amount'))
    image = fields.Binary(u'聊天记录截图')
    file = fields.Binary(u'附件')
    file_name = fields.Char(u'附件名字')
    note= fields.Text(u'备注')
    date = fields.Date(u'日期', readonly=True)
    done_date = fields.Date(u'完成日期', readonly=True)
    state = fields.Selection([('draft',u'未核对'),('doing',u'部分核对'),('done',u'已完成')],u'状态',
                              track_visibility='onchange', default='draft', readonly=True)

    # 定时任务
    @api.model
    def auto_get_statement(self):
        partner_ids = self.env['partner'].search([('active','=',True)])
        for partner_id in partner_ids:
            value = {}
            value['partner_id'] = partner_id.id
            value['new_c_balance'] = partner_id.receivable
            value['new_s_balance'] = partner_id.payable
            value['date'] = fields.date.today()
            value['s_category_id'] = partner_id.s_category_id.id
            value['c_category_id'] = partner_id.c_category_id.id
            if partner_id.c_category_id:
                value['is_customer'] = True
            if partner_id.s_category_id:
                value['is_supplier'] = True
            self.create(value)

    @api.multi
    def write(self, vals):
        super(partner_statement, self).write(vals)
        if vals.get('state') == 'done':
            if not self.image:
                raise osv.except_osv(_(u'警告'),_(u'请先录入聊谈记录截图！'))
            if not self.file:
                raise osv.except_osv(_(u'警告'),_(u'请先上传附件！'))
        state = ''
        #如果该业务伙伴是双重身份，那么只对完客户或者只对完供应商就是部分核对
        #如果修改了对账金额
        if vals.get('new_c_balance') or vals.get('new_s_balance'):
            if self.new_c_balance:
                if self.new_c_balance == self.c_balance and self.new_s_balance != self.s_balance:
                    state = 'doing'
                if self.new_c_balance == self.c_balance and self.new_s_balance == self.s_balance:
                    state = 'done'
        super(partner_statement, self).write({'state':state,})
        return True

    # 重新对账
    @api.multi
    def btn_doing(self):
        return self.write({'state':'doing'})