# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_is_zero
from odoo import fields, models, api, tools


class ReconcileOrder(models.Model):
    _inherit = 'reconcile.order'

    @api.multi
    def _get_or_pay(self, business_type,partner_id,this_reconcile,
                                 to_partner_id,name,category):

        """
        核销单 核销时 对具体核销单行进行的操作
        :param line:
        :param business_type:
        :param partner_id:
        :param to_partner_id:
        :param name:
        :return:
        """
         # 应收转应收、应付转应付
        if business_type in ['get_to_get', 'pay_to_pay']:
            if business_type in [ 'get_to_get']:
                category_id = self.env.ref('money.core_category_sale')
            else:
                category_id = self.env.ref('money.core_category_purchase')
            if not float_is_zero(this_reconcile, 2):
                # 转入业务伙伴往来增加
                self.env['money.invoice'].create({
                    'name': name,
                    'category_id': category_id.id ,
                    'amount': this_reconcile,
                    'date': self.date,
                    'reconciled': 0,  # 已核销金额
                    'to_reconcile': this_reconcile,  # 未核销金额
                    'date_due': self.date,
                    'partner_id': to_partner_id.id,
                    'note': u'核销冲账',
                })
                # 转出业务伙伴往来减少
                to_invoice_id = self.env['money.invoice'].create({
                    'name': name,
                    'category_id': category_id.id,
                    'amount': -this_reconcile,
                    'date': self.date,
                    'date_due': self.date,
                    'partner_id': partner_id.id,
                    'note': u'核销冲账',
                })
                # 核销 转出业务伙伴 的转出金额
                to_invoice_id.to_reconcile = 0
                to_invoice_id.reconciled = -this_reconcile

        # 应收冲应付，应收行、应付行分别生成负的结算单，并且核销
        if business_type in ['get_to_pay']:
            if not float_is_zero(this_reconcile, 2):
                invoice_id = self.env['money.invoice'].create({
                    'name': name,
                    'category_id': category.id,
                    'amount': -this_reconcile,
                    'date': self.date,
                    'date_due': self.date,
                    'partner_id': partner_id.id,
                    'note': u'核销冲账',
                })
                # 核销 业务伙伴 的本次核销金额
                invoice_id.to_reconcile = 0
                invoice_id.reconciled = -this_reconcile
        return True


    @api.multi
    def reconcile_order_done(self):
        '''核销单的审核按钮'''
        # 核销金额不能大于未核销金额
        decimal_amount = self.env.ref('core.decimal_amount')
        for order in self:
            if order.state == 'done':
                raise UserError(u'核销单%s已确认，不能再次确认。' % order.name)
            order_reconcile, invoice_reconcile = 0, 0
            if order.business_type in ['get_to_get', 'pay_to_pay'] and order.partner_id == order.to_partner_id:
                raise UserError(u'业务伙伴和转入往来单位不能相同。\n业务伙伴:%s 转入往来单位:%s'
                                % (order.partner_id.name, order.to_partner_id.name))

            # 核销预收预付
            for line in order.advance_payment_ids:
                order_reconcile += line.this_reconcile
                if float_compare(line.this_reconcile, line.to_reconcile, precision_digits=decimal_amount.digits) == 1:
                    raise UserError(u'核销金额不能大于未核销金额。\n核销金额:%s 未核销金额:%s' % (
                        line.this_reconcile, line.to_reconcile))

                # 更新每一行的已核销余额、未核销余额
                line.name.to_reconcile -= line.this_reconcile
                line.name.reconciled += line.this_reconcile

            # 核销应收结算单行
            for line in order.receivable_source_ids:
                invoice_reconcile += line.this_reconcile
                #如果核销金额和未核销金额都是负数
                if line.amount > 0 :
                    if float_compare(line.this_reconcile, line.to_reconcile, precision_digits=decimal_amount.digits) == 1:
                        raise UserError(u'核销金额不能大于未核销金额。\n核销金额:%s 未核销金额:%s' %
                                        (line.this_reconcile, line.to_reconcile))
                # 更新每一行的已核销余额、未核销余额
                line.name.to_reconcile -= line.this_reconcile
                line.name.reconciled += line.this_reconcile
            #生成结算单
            if order.receivable_source_ids:
                #核销单行生成的结算单只要一笔明细
                category = self.env.ref('money.core_category_sale')
                this_reconcile = invoice_reconcile
                self._get_or_pay(order.business_type,
                                 order.partner_id,this_reconcile,
                                 order.to_partner_id,order.name,category)
            # 核销应付结算单行
            for line in order.payable_source_ids:
                if self.business_type == 'adv_get_to_pay':
                    invoice_reconcile += line.this_reconcile
                else:
                    order_reconcile += line.this_reconcile
                #如果核销金额和未核销金额都是负数
                if line.amount > 0 :
                    if float_compare(line.this_reconcile, line.to_reconcile, precision_digits=decimal_amount.digits) == 1:
                        raise UserError(u'核销金额不能大于未核销金额。\n核销金额:%s 未核销金额:%s' %
                                        (line.this_reconcile, line.to_reconcile))
                # 更新每一行的已核销余额、未核销余额
                line.name.to_reconcile -= line.this_reconcile
                line.name.reconciled += line.this_reconcile
            #生成结算单
            if order.payable_source_ids:
                category = self.env.ref('money.core_category_purchase')
                if self.business_type == 'adv_get_to_pay':
                    this_reconcile = invoice_reconcile
                else:
                    this_reconcile = order_reconcile
                self._get_or_pay(order.business_type,
                                 order.partner_id,this_reconcile,
                                 order.to_partner_id,order.name,category)

            # 核销金额必须相同
            if order.business_type in ['adv_pay_to_get',
                                      'adv_get_to_pay', 'get_to_pay']:
                decimal_amount = self.env.ref('core.decimal_amount')
                if float_compare(order_reconcile, invoice_reconcile, precision_digits=decimal_amount.digits) != 0:
                    raise UserError(u'核销金额必须相同, %s 不等于 %s'
                                    % (order_reconcile, invoice_reconcile))

            order.state = 'done'
        return True
