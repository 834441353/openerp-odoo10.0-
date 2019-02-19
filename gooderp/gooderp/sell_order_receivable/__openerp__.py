# -*- coding: utf-8 -*-
{
    'name': "GoodERP 销售订单显示客户欠款",
    'author': "lonelyleaves",
    'website': "http://www.osbzr.com",
    'category': 'gooderp',
    'summary': 'GoodERP销售订单显示当前客户欠款',
    "description":
    '''
                        该模块实现了 GoodERP 销售订单创建时显示客户当前欠款。
    ''',
    'version': '11.11',
    'application': False,
    'depends': ['sell'],
    'data': [
        'views/sell_order_receivable_view.xml',
    ],
    'demo': [
    ]
}
