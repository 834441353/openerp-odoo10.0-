# -*- coding: utf-8 -*-
{
    'name': "GoodERP 零金额单据生成结算单",
    'author': "lonelyleaves",
    'website': "http://www.osbzr.com",
    'category': 'gooderp',
    'summary': 'GoodERP结算单扩展',
    "description":
    '''
    该模块实现了 GoodERP 的没有金额的出入库单生成结算单不生成凭证的功能
    解决gooderp赠送商品不加入客户账单的问题
    ''',
    'version': '10.1',
    'application': True,
    'depends': ['money','sell','buy'],
    'data': [
        #'security/ir.model.access.csv',
        #'views/zero_order_make_involice_view.xml',
        #'data/finance_data.xml',
    ],
    'demo': [
        'data/demo.xml',
    ]
}
