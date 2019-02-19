# -*- coding: utf-8 -*-

import odoo.addons.decimal_precision as dp
from odoo import fields, models, api, tools

from odoo.addons.report_docx.report.report_docx import ReportDocx, DataModelProxy
from odoo.addons.report_docx.report import report_helper
from docxtpl import DocxTemplate
from odoo.tools import misc
import tempfile
import os


class ReportSupplierBalance(models.Model):
    _name = "report.supplier.balance"
    _description = u"应付账款汇总表"
    _order = 'id, date'

    code = fields.Char(u'编号')
    partner_id = fields.Many2one('partner', string=u'业务伙伴', readonly=True)
    payable = fields.Float(u'当前应付余额',
                              digits=dp.get_precision('Amount'))
    payable_begain = fields.Float(
        u'期初应付', digits=dp.get_precision('Amount'))
    amount = fields.Float(string=u'本期发生', readonly=True,
                          digits=dp.get_precision('Amount'))
    pay_amount = fields.Float(string=u'本期付款', readonly=True,
                              digits=dp.get_precision('Amount'))
    balance_amount = fields.Float(string=u'应付款余额',
                                  compute='_compute_balance_amount',
                                  digits=dp.get_precision('Amount'))
    discount_money = fields.Float(string=u'收款折扣', readonly=True,
                                  digits=dp.get_precision('Amount'))

    def init(self):
        # union money_order(type = 'pay'), money_invoice(type = 'expense')
        cr = self._cr
        tools.drop_view_if_exists(cr, 'supplier_statements_report')
        cr.execute("""
            CREATE or REPLACE VIEW supplier_statements_report AS (
            SELECT  ROW_NUMBER() OVER(ORDER BY partner_id, date, amount desc) AS id,
                    partner_id,
                    name,
                    date,
                    done_date,
                    amount,
                    pay_amount,
                    discount_money,
                    balance_amount,
                    note
            FROM
                (
                SELECT m.partner_id,
                        m.name,
                        m.date,
                        m.write_date AS done_date,
                        0 AS amount,
                        m.amount AS pay_amount,
                        m.discount_amount AS discount_money,
                        0 AS balance_amount,
                        m.note
                FROM money_order AS m
                WHERE m.type = 'pay' AND m.state = 'done'
                UNION ALL
                SELECT  mi.partner_id,
                        mi.name,
                        mi.date,
                        mi.create_date AS done_date,
                        mi.amount,
                        0 AS pay_amount,
                        0 AS discount_money,
                        0 AS balance_amount,
                        Null AS note
                FROM money_invoice AS mi
                LEFT JOIN core_category AS c ON mi.category_id = c.id
                WHERE c.type = 'expense' AND mi.state = 'done'
                ) AS ps)
        """)

