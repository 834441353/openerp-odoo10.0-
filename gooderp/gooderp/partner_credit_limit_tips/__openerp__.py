# -*- coding: utf-8 -*-
{
    'name': "GOODERP 客户超额提示",
    'author': "leaves",
    'category': 'gooderp',
    'version': '11.11',
    'depends': ['core'],
    "description":
    '''
                        该模块实现了 GoodERP 中 客户欠款如果超出客户的信用额度，通过红色区分。
                        增加业务员字段
    ''',
    'data': [
        'views/partner_credit_limit_tips.xml',
    ],
    'installable': True,
}
