# -*- coding: utf-8 -*-
{
    'name': "GoodERP销售收发货单据批量审核功能",
    'author': "lonely_leaves",
    'website': "http://www.osbzr.com",
    'category': 'gooderp',
    'summary': 'GoodERP 销售发货单批量审核',
    "description":
    '''
    该模块可以批量审核销售发货单和销售退货单
    ''',
    'version': '11.11',
    'application': True,
    'depends': ['sell'],
    'data': [
        'views/sell_delivery_all_done_view.xml'
    ],
}
