# -*- coding: utf-8 -*-
{
    'name': "GoodERP 核销单生成结算单",
    'author': "lonelyleaves",
    'website': "http://www.osbzr.com",
    'category': 'gooderp',
    'summary': 'GoodERP核销单扩展',
    "description":
    '''
    该模块实现了 GoodERP 核销如果有多条核销明细会生成多条结算单，该功能修复了 只生成一条结算单
    ''',
    'version': '10.1',
    'application': True,
    'depends': ['money',
                'finance','other_money_pay'],
    # 'data': [
    #     # 'security/group.xml',
    #     # 'views/other_money_order_view.xml',
    #     # 'data/finance_data.xml',
    #     # 'data/partner_data.xml',
    # ],
    # 'demo': [
    #     'data/demo.xml',
    # ]
}
