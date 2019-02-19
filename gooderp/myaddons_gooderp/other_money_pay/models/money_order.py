# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_is_zero
from odoo import fields, models, api, tools


class MoneyInvoice(models.Model):
    _inherit = 'money.invoice'

    @api.multi
    def money_invoice_done(self):
        """
        结算单审核方法
        判断审核的时候，是否生成凭证
        :return:
        """
        for inv in self:
            #结算单的已核销金额等于0
            inv.reconciled = 0.0
            #结算单的未核销金额等于合计
            inv.to_reconcile = inv.amount
            inv.state = 'done'
            if not inv.date_due:
                inv.date_due = fields.Date.context_today(self)
            if inv.category_id.type == 'income':
                inv.partner_id.receivable += inv.amount
            if inv.category_id.type == 'expense':
                inv.partner_id.payable += inv.amount

        vals = {}
        # 初始化单的话，先找是否有初始化凭证，没有则新建一个
        for invoice in self:
            #如果发票是初始化单
            if invoice.is_init:
                vouch_obj = self.env['voucher'].search(
                    [('is_init', '=', True)])
                if not vouch_obj:
                    vouch_obj = self.env['voucher'].create(
                        {'date': invoice.date,
                         'is_init': True,
                         'ref': '%s,%s' % (self._name, self.id)})
                invoice.write({'voucher_id': vouch_obj.id})
            else:
                #判断单据是否为其他收支单，如果是，则不生成凭证取结算单生成的凭证
                #如果不是其他收支单
                if not invoice.category_id == self.env.ref('other_money_pay.categ_other_get') and not invoice.category_id == self.env.ref('other_money_pay.categ_other_pay'):
                    #判断结算单的金额为0创建凭证
                    if not float_is_zero(inv.amount, 2):
                        vouch_obj = self.env['voucher'].create({'date': invoice.date, 'ref': '%s,%s' % (self._name, self.id)})
                        invoice.write({'voucher_id':vouch_obj.id})
                #如果是其他收支单生成的结算单
                else:
                    #查找其他收支单生成的凭证，结算单的凭证为其他收支单的凭证
                    vouch_obj = self.env['other.money.order'].search([('name', '=', self.name)])
            if not invoice.category_id.account_id:
                raise UserError(u'请配置%s的会计科目' % (invoice.category_id.name))
            partner_cat = invoice.category_id.type == 'income' and invoice.partner_id.c_category_id or invoice.partner_id.s_category_id
            partner_account_id = partner_cat.account_id.id
            if not partner_account_id:
                raise UserError(u'请配置%s的会计科目' % (partner_cat.name))
            # 排除 其他收入单，其他支出单
            if not invoice.category_id == self.env.ref('other_money_pay.categ_other_get') and not invoice.category_id == self.env.ref('other_money_pay.categ_other_pay'):
                #单据的金额为0的时候不执行
                if not float_is_zero(inv.amount, 2):
                    #结算单类型属于收入
                    if invoice.category_id.type == 'income':
                        vals.update({'vouch_obj_id': vouch_obj.id, 'partner_credit': invoice.partner_id.id, 'name': invoice.name, 'string': invoice.note or '',
                                     'amount': invoice.amount, 'credit_account_id': invoice.category_id.account_id.id, 'partner_debit': invoice.partner_id.id,
                                     'debit_account_id': partner_account_id, 'sell_tax_amount': invoice.tax_amount or 0,
                                     'credit_auxiliary_id': invoice.auxiliary_id.id, 'currency_id': invoice.currency_id.id or '',
                                     'rate_silent': self.env['res.currency'].get_rate_silent(self.date, invoice.currency_id.id) or 0,
                                     })
                    #结算单的类型为支出
                    else:
                        vals.update({'vouch_obj_id': vouch_obj.id, 'name': invoice.name, 'string': invoice.note or '',
                                     'amount': invoice.amount, 'credit_account_id': partner_account_id,
                                     'debit_account_id': invoice.category_id.account_id.id, 'partner_debit': invoice.partner_id.id,
                                     'partner_credit': invoice.partner_id.id, 'buy_tax_amount': invoice.tax_amount or 0,
                                     'debit_auxiliary_id': invoice.auxiliary_id.id, 'currency_id': invoice.currency_id.id or '',
                                     'rate_silent': self.env['res.currency'].get_rate_silent(self.date, invoice.currency_id.id) or 0,
                                     })
                    if invoice.is_init:
                        vals.update({'init_obj': 'money_invoice', })
                    invoice.create_voucher_line(vals)
            # 删除初始非需要的凭证明细行,不审核凭证
            if invoice.is_init:
                vouch_line_ids = self.env['voucher.line'].search([
                    ('account_id', '=', invoice.category_id.account_id.id),
                    ('init_obj', '=', 'money_invoice')])
                for vouch_line_id in vouch_line_ids:
                    vouch_line_id.unlink()
        return



class MoneyInvoice(models.Model):
    _inherit = 'bank.statements.report'

    def init(self):
        # union money_order, other_money_order, money_transfer_order
        cr = self._cr
        tools.drop_view_if_exists(cr, 'bank_statements_report')
        cr.execute("""
            CREATE or REPLACE VIEW bank_statements_report AS (
            SELECT  ROW_NUMBER() OVER(ORDER BY bank_id,date) AS id,
                    bank_id,
                    date,
                    name,
                    get,
                    pay,
                    balance,
                    partner_id,
                    note
            FROM
                (
                SELECT mol.bank_id,
                        mo.date,
                        mo.name,
                        (CASE WHEN mo.type = 'get' THEN mol.amount ELSE 0 END) AS get,
                        (CASE WHEN mo.type = 'pay' THEN mol.amount ELSE 0 END) AS pay,
                        0 AS balance,
                        mo.partner_id,
                        mo.note
                FROM money_order_line AS mol
                LEFT JOIN money_order AS mo ON mol.money_id = mo.id
                WHERE mo.state = 'done'
                UNION ALL

                SELECT  omo.bank_id,
                        omo.date,
                        omo.name,
                        (CASE WHEN omo.type = 'other_get' THEN
                         (CASE WHEN ba.currency_id IS NULL THEN omo.total_amount ELSE omo.currency_amount END)
                         ELSE 0 END) AS get,
                        (CASE WHEN omo.type = 'other_pay' THEN
                         (CASE WHEN ba.currency_id IS NULL THEN omo.total_amount ELSE omo.currency_amount END)
                         ELSE 0 END) AS pay,
                        0 AS balance,
                        omo.partner_id,
                        omo.note AS note
                FROM other_money_order AS omo
                LEFT JOIN bank_account AS ba ON ba.id = omo.bank_id
                LEFT JOIN res_currency AS rc ON rc.id = ba.currency_id
                WHERE omo.state = 'done' AND omo.partner_id IS NULL
                UNION ALL
                SELECT  mtol.out_bank_id AS bank_id,
                        mto.date,
                        mto.name,
                        0 AS get,
                        (CASE WHEN ba.currency_id IS NULL THEN mtol.amount ELSE mtol.currency_amount END) AS pay,
                        0 AS balance,
                        NULL AS partner_id,
                        mto.note
                FROM money_transfer_order_line AS mtol
                LEFT JOIN money_transfer_order AS mto ON mtol.transfer_id = mto.id
                LEFT JOIN bank_account AS ba ON ba.id = mtol.out_bank_id
                LEFT JOIN res_currency AS rc ON rc.id = ba.currency_id
                WHERE mto.state = 'done'
                UNION ALL
                SELECT  mtol.in_bank_id AS bank_id,
                        mto.date,
                        mto.name,
                        mtol.amount AS get,
                        0 AS pay,
                        0 AS balance,
                        NULL AS partner_id,
                        mto.note
                FROM money_transfer_order_line AS mtol
                LEFT JOIN money_transfer_order AS mto ON mtol.transfer_id = mto.id
                WHERE mto.state = 'done'
                ) AS bs)
        """)