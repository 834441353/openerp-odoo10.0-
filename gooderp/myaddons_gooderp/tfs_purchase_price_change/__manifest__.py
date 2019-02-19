# -*- coding: utf-8 -*-
# Copyright 2018 上海开阖软件 ((http://www.osbzr.com).)

{
    'name': '采购价格调整',
    'version': '11.11',
    'author': 'tfs',
    'website': 'http://www.tfsodoo.com',
    'category': 'gooderp',
    'summary': '采购价格',
    'description': """修改带批次的采购价格""",
    'depends': [
        'buy','sell','finance'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/stock_request_data.xml',
        'views/tfs_purchase_price_change.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': False,
}
