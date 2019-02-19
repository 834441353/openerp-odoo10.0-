# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_is_zero
from odoo import fields, models, api, tools


class OtherMoneyOrder(models.Model):
    _inherit = 'other.money.order'
    _order = 'date desc, id desc'


    # 字段只读状态
    READONLY_STATES = {
        'done': [('readonly', True)],
    }

    ISODATEFORMAT = '%Y-%m-%d'

    @api.one
    #@api.depends('type', 'invoice_id.reconciled', 'invoice_id.amount')
    def _get_other_money_state(self):
        '''返回收款状态        判断发票的已核销金额'''
        if self.type == 'other_get':
            if not self.partner_id:
                self.get_state = u'全部收款'
            else:
                if self.invoice_id.reconciled == 0:
                    self.get_state = u'未收款'
                elif self.invoice_id.reconciled < self.invoice_id.amount:
                    self.get_state = u'部分收款'
                elif self.invoice_id.reconciled == self.invoice_id.amount:
                    self.get_state = u'全部收款'
        # 返回退款状态
        if self.type == 'other_pay':
            if not self.partner_id:
                self.pay_state = u'全部付款'
            else:
                if self.invoice_id.reconciled == 0:
                    self.pay_state = u'未付款'
                elif abs(self.invoice_id.reconciled) < abs(self.invoice_id.amount):
                    self.pay_state = u'部分付款'
                elif self.invoice_id.reconciled == self.invoice_id.amount:
                    self.pay_state = u'全部付款'

    #继承修改的字段
    bank_id = fields.Many2one('bank.account', string=u'结算账户',
                          #银行账户非必填
                          required=False,
                          ondelete='restrict',
                          readonly=True,states={
                              'draft': [('readonly', False)]},
                          help=u'本次其他收支的结算账户')
    total_amount = fields.Float(string=u'成交金额',
                                compute='_compute_total_amount',
                                store=True, readonly=True,
                                digits=dp.get_precision('Amount'),
                                help=u'本次其他收支的总金额')
    state = fields.Selection(track_visibility='onchange')

    #新增加的字段
    currency_id = fields.Many2one('res.currency', u'外币币别', readonly=True,
                                  help=u'外币币别')
    invoice_id = fields.Many2one('money.invoice', u'发票号',
                                 copy=False, ondelete='set null',
                                 help=u'产生的发票号')
    discount_amount = fields.Float(u'优惠金额', states=READONLY_STATES,
                                   digits=dp.get_precision('Amount'),
                                   help=u'整单优惠金额，可由优惠率自动计算得出，也可手动输入')
    receipt = fields.Float(u'本次收款', states=READONLY_STATES,
                           digits=dp.get_precision('Amount'),
                           help=u'本次收款金额')
    payment = fields.Float(u'本次付款', states=READONLY_STATES,
                       digits=dp.get_precision('Amount'),
                       help=u'本次付款金额')
    get_state = fields.Char(u'收款状态', compute=_get_other_money_state,
                              default=u'未收款',
                              help=u"其他收入单的收款状态", index=True, copy=False)
    pay_state = fields.Char(u'付款状态', compute=_get_other_money_state,
                               default=u'未退款',
                               help=u"其他支出单的付款状态", index=True, copy=False)
    voucher_id = fields.Many2one('voucher', u'会计凭证', readonly=True,
                                 help=u'审核时产生的会计凭证')
    ref = fields.Char(u'说明')
    date_due = fields.Date(u'到期日期', copy=False,
                           default=lambda self: fields.Date.context_today(
                               self),
                           help=u'其他收支单的截止日期')
    user_id = fields.Many2one(
        'res.users',
        u'经办人',
        ondelete='restrict',
        states=READONLY_STATES,
        default=lambda self: self.env.user,
        help=u'单据经办人',
    )

    @api.onchange('date')
    def onchange_date(self):
        if self._context.get('type') == 'other_pay':
            return {'domain': {'partner_id': [('c_category_id', '!=', False)]}}
        else:
            return {'domain': {'partner_id': [('s_category_id', '!=', False)]}}

    @api.one
    @api.depends('line_ids.amount', 'line_ids.tax_amount', 'discount_amount')
    # 计算应付金额/应收金额
    def _compute_total_amount(self):
        self.total_amount = sum((line.amount + line.tax_amount - self.discount_amount)
                                for line in self.line_ids)


    @api.multi
    #'''审核时不合法的给出报错'''
    def other_money_done(self):
        self.ensure_one()
        if self.state == 'done':
            raise UserError(u'请不要重复审核！')
        if not self.line_ids:
            raise UserError(u'请输入其他收支明细行')
        if not self.partner_id:
            decimal_amount = self.env.ref('core.decimal_amount')
            if float_compare(self.receipt + self.payment, self.total_amount, precision_digits=decimal_amount.digits) != 0:
                raise UserError(u'费用单据，本次收付款金额必须等于成交金额')

        for line in self.line_ids:
            if line.price_taxed < 0:
                raise UserError(u' %s 的单价不能小于0！' % line.category_id.name)
            if self.receipt + self.payment > 0:
                if not self.bank_id:
                    raise UserError(u'本次收款金额大于0，请选择结算账户')
                if not self.bank_id.account_id:
                    raise UserError(u'请配置%s的会计科目' % (self.bank_id.name))

        #创建凭证并生成结算单，同时审核非初始化凭证
        vouch_obj = self.create_voucher()
        #如果有业务伙伴，创建结算单
        if self.partner_id:
            invoice_id = self._make_other_invoice(vouch_obj)
            self.write({
                'voucher_id': vouch_obj.id,
                'invoice_id': invoice_id and invoice_id.id,
                'state': 'done',    # 为保证审批流程顺畅，否则，未审批就可审核
            })
        else:
            self.write({
                'voucher_id': vouch_obj.id,
                'state': 'done',    # 为保证审批流程顺畅，否则，未审批就可审核
            })

        #如果本次收支款不为0则创建收付款单
        if self.partner_id:
            if self.receipt + self.payment != 0:
                if self.payment != 0:
                    amount = -self.total_amount
                    this_reconcile = -self.payment
                    self._make_other_receipt(invoice_id, amount, this_reconcile)
                if self.receipt != 0:
                    amount = -self.total_amount
                    this_reconcile = -self.receipt
                    self._make_other_payment(invoice_id, amount, this_reconcile)
                    # 根据单据类型更新账户余额
        else:
            if self.type == 'other_pay':
                decimal_amount = self.env.ref('core.decimal_amount')
                if float_compare(self.bank_id.balance, self.total_amount, decimal_amount.digits) == -1:
                    raise UserError(u'账户余额不足。\n账户余额:%s 本次支出金额:%s' %
                                    (self.bank_id.balance, self.total_amount))
                self.bank_id.balance -= self.total_amount
            else:
                self.bank_id.balance += self.total_amount


    def _make_other_invoice(self, vouch_obj):
        '''
       其他收支单生成结算单money_invoice
        '''
        invoice_id = False
        #区分其他收支单的类型
        amount = -self.total_amount
        tax_amount = -sum(line.tax_amount for line in self.line_ids)
        if self.type == 'other_get':
            category = self.env.ref('other_money_pay.categ_other_get')
        else:
            category = self.env.ref('other_money_pay.categ_other_pay')
        invoice_id = self.env['money.invoice'].create(
            self._get_invoice_vals(
                self.partner_id, category, self.date, amount, tax_amount, vouch_obj))
        return invoice_id

    def _get_invoice_vals(self, partner_id, category_id, date, amount, tax_amount, vouch_obj):
        '''返回创建 结算单money_invoice 时所需数据'''
        return {
            'name': self.name,
            'partner_id': partner_id.id,
            'category_id': category_id.id,
            'date': date,
            'amount': amount,
            'reconciled': 0,
            'to_reconcile': amount,
            'tax_amount': tax_amount,
            'date_due': self.date_due,
            'state': 'draft',
            'currency_id': self.currency_id.id,
            'note': self.note,
            'voucher_id': vouch_obj.id,
        }

    @api.one
    #'''由其它支出单成付款单'''
    def _make_other_payment(self, invoice_id, amount, receipt):
        categ = self.env.ref('other_money_pay.categ_other_pay')
        money_lines = [
            {'bank_id': self.bank_id.id, 'amount': receipt}]
        source_lines = [{'name': invoice_id.id,
                         'category_id': categ.id,
                         'date': invoice_id.date,
                         'amount': amount,
                         'reconciled': 0.0,
                         'to_reconcile': amount,
                         'this_reconcile': receipt}]
        rec = self.with_context(type='pay')
        money_order = rec.env['money.order'].create({
            'partner_id': self.partner_id.id,
            'bank_name': self.partner_id.bank_name,
            'bank_num': self.partner_id.bank_num,
            'date': fields.Date.context_today(self),
            'line_ids':
                [(0, 0, line) for line in money_lines],
            'source_ids':
                [(0, 0, line) for line in source_lines],
            'amount': amount,
            'reconciled': receipt,
            'to_reconcile': amount,
            'state': 'draft',
            'origin_name': self.name,
            'note': self.note,
            'buy_id': False,
        })
        return money_order

    @api.one
    #'''由其它支出单成收款单'''
    def _make_other_receipt(self, invoice_id, amount, this_reconcile):
        categ = self.env.ref('other_money_pay.categ_other_get')
        money_lines = [{
            'bank_id': self.bank_id.id,
            'amount': amount,
        }]
        source_lines = [{
            'name': invoice_id and invoice_id.id,
            'category_id': categ.id,
            'date': invoice_id and invoice_id.date,
            'amount': amount,
            'reconciled': 0.0,
            'to_reconcile': amount,
            'this_reconcile': this_reconcile,
        }]
        rec = self.with_context(type='get')
        money_order = rec.env['money.order'].create({
            'partner_id': self.partner_id.id,
            'date': self.date,
            'line_ids': [(0, 0, line) for line in money_lines],
            'source_ids': [(0, 0, line) for line in source_lines],
            'amount': amount,
            'reconciled': this_reconcile,
            'to_reconcile': amount,
            'state': 'draft',
            'origin_name': self.name,
            'note': self.note,
            'sell_id': False,
        })
        return money_order

    @api.multi
    def other_money_draft(self):
        '''其他收支单的反审核按钮'''
        self.ensure_one()
        if self.state == 'draft':
            raise UserError(u'请不要重复反审核！')
        # 查找产生的收款单并反审核删除
        if self.partner_id:
            source_line = self.env['source.order.line'].search(
                [('name', '=', self.invoice_id.id)])
            for line in source_line:
                if line.money_id.state == 'done':
                    line.money_id.money_order_draft()
                line.money_id.unlink()
        # 根据单据类型更新账户余额
        else:
            if self.type == 'other_pay':
                self.bank_id.balance += self.total_amount
            else:
                decimal_amount = self.env.ref('core.decimal_amount')
                if float_compare(self.bank_id.balance, self.total_amount, decimal_amount.digits) == -1:
                    raise UserError(u'账户余额不足。\n账户余额:%s 本次支出金额:%s' %
                                    (self.bank_id.balance, self.total_amount))
                self.bank_id.balance -= self.total_amount

        # 始初化单反审核只删除明细行
        voucher = self.voucher_id
        self.write({
            'voucher_id': False,
            'state': 'draft',
        })
        #删除产生的结算单
        invoice_ids = self.env['money.invoice'].search(
            [('name', '=', self.invoice_id.name)])
        #已经核销的结算单不能反审核
        for invoice in invoice_ids:
            if invoice.to_reconcile == 0 and invoice.reconciled == invoice.amount:
                raise UserError(u'其他收支单已经核销，不能反审核！')
        if invoice_ids.state == 'done':
            invoice_ids.money_invoice_draft()
        invoice_ids.unlink()
        # 反审初始化单的凭证并删除
        if not self.partner_id:
            if voucher.state == 'done':
                voucher.voucher_draft()
        # 始初化单反审核只删除明细行
        if self.is_init:
            vouch_obj = self.env['voucher'].search([('id', '=', voucher.id)])
            vouch_obj_lines = self.env['voucher.line'].search([
                ('voucher_id', '=', vouch_obj.id),
                ('account_id', '=', self.bank_id.account_id.id),
                ('init_obj', '=', 'other_money_order-%s' % (self.id))])
            for vouch_obj_line in vouch_obj_lines:
                vouch_obj_line.unlink()
        else:
            if not self.partner_id:
                voucher.unlink()
        return True

    @api.multi
    def create_voucher(self):
        """创建凭证并审核非初始化凭证"""
        init_obj = ''
        # 初始化单的话，先找是否有初始化凭证，没有则新建一个
        if self.is_init:
            vouch_obj = self.env['voucher'].search([('is_init', '=', True)])
            if not vouch_obj:
                vouch_obj = self.env['voucher'].create({'date': self.date,
                                                        'is_init': True,
                                                        'ref': '%s,%s' % (self._name, self.id)})
        else:
            vouch_obj = self.env['voucher'].create({'date': self.date, 'ref': '%s,%s' % (self._name, self.id)})
        if self.is_init:
            init_obj = 'other_money_order-%s' % (self.id)

        if self.type == 'other_get':  # 其他收入单
            self.other_get_create_voucher_line(vouch_obj, init_obj)
        else:  # 其他支出单
            self.other_pay_create_voucher_line(vouch_obj)

        # 如果非初始化单则审核
        if not self.is_init:
            vouch_obj.voucher_done()
        return vouch_obj

    def other_get_create_voucher_line(self, vouch_obj, init_obj):
        """
        其他收入单生成凭证明细行
        :param vouch_obj: 凭证
        :return:
        """
        vals = {}

        for line in self.line_ids:
            if not line.category_id.account_id:
                raise UserError(u'请配置%s的会计科目' % (line.category_id.name))

            rate_silent = self.env['res.currency'].get_rate_silent(
                self.date, self.bank_id.currency_id.id)
            vals.update({'vouch_obj_id': vouch_obj.id, 'name': self.name, 'note': line.note or '',
                         'credit_auxiliary_id': line.auxiliary_id.id,
                         'amount': abs(line.amount + line.tax_amount),
                         'credit_account_id': line.category_id.account_id.id,
                         'debit_account_id': self.partner_id.s_category_id.account_id.id or self.bank_id.account_id.id,'partner_credit':'',
                         'partner_debit': self.partner_id.id,
                         'sell_tax_amount': line.tax_amount or 0,
                         'init_obj': init_obj,
                         #外币币别
                         'currency_id': self.currency_id.id,
                         #外币合计
                         'currency_amount': self.currency_amount,
                         'rate_silent': rate_silent,
                         })

            # 贷方行
            if not init_obj:
                self.env['voucher.line'].create({
                    'name': u"%s %s" % (vals.get('name'), vals.get('note')),
                    'partner_id': vals.get('partner_credit', ''),
                    'account_id': vals.get('credit_account_id'),
                    'credit': line.amount - self.discount_amount,
                    'voucher_id': vals.get('vouch_obj_id'),
                    'auxiliary_id': vals.get('credit_auxiliary_id', False),
                })
            # 销项税行
            if vals.get('sell_tax_amount'):
                if not self.env.user.company_id.output_tax_account:
                    raise UserError(
                        u'您还没有配置公司的销项税科目。\n请通过"配置-->高级配置-->公司"菜单来设置进项税科目!')
                self.env['voucher.line'].create({
                    'name': u"%s %s" % (vals.get('name'), vals.get('note')),
                    'account_id': self.env.user.company_id.output_tax_account.id,
                    'credit': line.tax_amount or 0,
                    'voucher_id': vals.get('vouch_obj_id'),
                })
        # 借方行
        self.env['voucher.line'].create({
            'name': u"%s" % (vals.get('name')),
            'account_id': vals.get('debit_account_id'),
            'debit': self.total_amount,  # 借方和
            'voucher_id': vals.get('vouch_obj_id'),
            'partner_id': vals.get('partner_debit', ''),
            'auxiliary_id': vals.get('debit_auxiliary_id', False),
            'init_obj': vals.get('init_obj', False),
            'currency_id': vals.get('currency_id', False),
            'currency_amount': vals.get('currency_amount'),
            'rate_silent': vals.get('rate_silent'),
        })

    def other_pay_create_voucher_line(self, vouch_obj):
        """
        其他支出单生成凭证明细行
        :param vouch_obj: 凭证
        :return:
        """
        vals = {}
        for line in self.line_ids:
            if not line.category_id.account_id:
                raise UserError(u'请配置%s的会计科目' % (line.category_id.name))

            rate_silent = self.env['res.currency'].get_rate_silent(
                self.date, self.bank_id.currency_id.id)
            vals.update({'vouch_obj_id': vouch_obj.id, 'name': self.name, 'note': line.note or '',
                         'debit_auxiliary_id': line.auxiliary_id.id,
                         'amount': abs(line.amount + line.tax_amount),
                         'credit_account_id': self.partner_id.c_category_id.account_id.id or self.bank_id.account_id.id,
                         'debit_account_id': line.category_id.account_id.id,
                         'partner_credit': self.partner_id.id,
                         'partner_debit': self.partner_id.id,
                         'buy_tax_amount': line.tax_amount or 0,
                         'currency_id': self.bank_id.currency_id.id,
                         'currency_amount': self.currency_amount,
                         'rate_silent': rate_silent,
                         })
            # 借方行
            self.env['voucher.line'].create({
                'name': u"%s %s " % (vals.get('name'), vals.get('note')),
                'account_id': vals.get('debit_account_id'),
                'debit': line.amount - self.discount_amount,
                'voucher_id': vals.get('vouch_obj_id'),
                'partner_id': vals.get('partner_debit', ''),
                'auxiliary_id': vals.get('debit_auxiliary_id', False),
                'init_obj': vals.get('init_obj', False),
            })
            # 进项税行
            if vals.get('buy_tax_amount'):
                if not self.env.user.company_id.import_tax_account:
                    raise UserError(u'请通过"配置-->高级配置-->公司"菜单来设置进项税科目')
                self.env['voucher.line'].create({
                    'name': u"%s %s" % (vals.get('name'), vals.get('note')),
                    'account_id': self.env.user.company_id.import_tax_account.id,
                    'debit': line.tax_amount or 0,
                    'voucher_id': vals.get('vouch_obj_id'),
                })
        # 贷方行
        self.env['voucher.line'].create({
            'name': u"%s" % (vals.get('name')),
            'partner_id': vals.get('partner_credit', ''),
            'account_id': vals.get('credit_account_id'),
            'credit': self.total_amount,  # 贷方和
            'voucher_id': vals.get('vouch_obj_id'),
            'auxiliary_id': vals.get('credit_auxiliary_id', False),
            'init_obj': vals.get('init_obj', False),
            'currency_id': vals.get('currency_id', False),
            'currency_amount': vals.get('currency_amount'),
            'rate_silent': vals.get('rate_silent'),
        })

    @api.multi
    #查看其他收支单的结算单
    def action_view_delivery(self):
        '''
        This function returns an action that display existing deliverys of given sells order ids.
        When only one found, show the delivery immediately.
        '''

        self.ensure_one()
        name = (self.type == 'sell' and u'销售发库单' or u'销售退货单')
        action = {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sell.delivery',
            'view_id': False,
            'target': 'current',
        }

        delivery_ids = self.delivery_ids.ids
        if len(delivery_ids) > 1:
            action['domain'] = "[('id','in',[" + \
                ','.join(map(str, delivery_ids)) + "])]"
            action['view_mode'] = 'tree,form'
        elif len(delivery_ids) == 1:
            view_id = (self.type == 'sell'
                       and self.env.ref('sell.sell_delivery_form').id
                       or self.env.ref('sell.sell_return_form').id)
            action['views'] = [(view_id, 'form')]
            action['res_id'] = delivery_ids and delivery_ids[0] or False
        return action

class OtherMoneyOrderLine(models.Model):
    _inherit = 'other.money.order.line'

    @api.one
    @api.depends('quantity', 'price_taxed', 'tax_rate')
    def _compute_all_amount(self):
        '''当订单行的数量、含税单价、折扣额、税率改变时，改变销售金额、税额、价税合计'''
        if self.tax_rate > 100:
            raise UserError(u'税率不能输入超过100的数!\n输入税率:%s' % self.tax_rate)
        if self.tax_rate < 0:
            raise UserError(u'税率不能输入负数\n 输入税率:%s' % self.tax_rate)
        if self.other_money_id.currency_id.id == self.env.user.company_id.currency_id.id:
            self.subtotal = self.price_taxed * self.quantity - self.discount_amount  # 价税合计
            self.tax_amount = self.subtotal / \
                (100 + self.tax_rate) * self.tax_rate  # 税额
            self.amount = self.subtotal - self.tax_amount  # 金额
        else:
            rate_silent = self.env['res.currency'].get_rate_silent(
                self.other_money_id.date, self.other_money_id.currency_id.id) or 1
            currency_amount = self.quantity * self.price_taxed - self.discount_amount
            self.subtotal = (self.price_taxed * self.quantity - self.discount_amount ) * rate_silent  # 价税合计
            self.tax_amount = self.subtotal / \
                (100 + self.tax_rate) * self.tax_rate  # 税额
            self.amount = self.subtotal - self.tax_amount  # 本位币金额
            self.currency_amount = currency_amount  # 外币金额

    quantity = fields.Float(u'数量',
                            default=1,
                            required=True,
                            digits=dp.get_precision('Quantity'),
                            help=u'收支明细的数量')
    price_taxed = fields.Float(u'单价',
                     store=True,
                     digits=dp.get_precision('Price'),
                     help=u'收支明细价格')
    discount_rate = fields.Float(u'折扣率%',
                                 help=u'折扣率')
    discount_amount = fields.Float(u'折扣额',
                                   digits=dp.get_precision('Amount'),
                                   help=u'输入折扣率后自动计算得出，也可手动输入折扣额')
    amount = fields.Float(u'金额', compute=_compute_all_amount,store=True,
                          digits=dp.get_precision('Amount'),
                          help=u'其他收支单行上的金额')

    @api.onchange('quantity', 'price_taxed', 'discount_rate')
    def onchange_discount_rate(self):
        '''当数量、单价或优惠率发生变化时，优惠金额发生变化'''
        self.price = self.price_taxed / (1 + self.tax_rate * 0.01)
        self.discount_amount = (self.quantity * self.price *
                                self.discount_rate * 0.01)
