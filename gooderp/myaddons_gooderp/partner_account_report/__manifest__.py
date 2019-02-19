# -*- coding: utf-8 -*-
# Copyright 2018 上海开阖软件 ((http://www.osbzr.com).)

{
    'name': '应收应付账款汇总表',
    'version': '11.11',
    'author': 'lonelyleaves',
    'website': 'http://www.odoo.com',
    'category': 'gooderp',
    'summary': '客户&供应商应收账款汇总表',
    'description': """查询客户&供应商任意时间任意客户的应收应付金额""",
    'depends': [
        'buy','sell','money'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/groups.xml',
        'wizard/customer_balance_wizard_view.xml',
        'wizard/supplier_balance_wizard_view.xml',
        'report/customer_balance_view.xml',
        'report/supplier_balance_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
}
