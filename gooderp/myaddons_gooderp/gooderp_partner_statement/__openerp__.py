# -*- coding: utf-8 -*-

{
    'name': "财务对账单",
    'version': '1.1',
    'author': 'lonelyleaves',
    'category': 'Account',
    'sequence': 21,
    'website': 'https://www.odoo.com',
    'description': """
1：销售-销售-客户账单
2：采购-采购-供应商对账单
每月的最后一天创建一份业务伙伴的账单余额
有问题可以邮件 979581151@qq.com
    """,
    'images': [
    ],
    'depends': ['sell','buy','money'],
    'data': [
        'partner_statement_view.xml',
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
