# -*- coding: utf-8 -*-
# Copyright 2015 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{

    'name': 'Rewrite Archive',
    "summary": 'Gooderp模型重写归档和取消归档的方法',
    'version': '10.0.1.1.2',
    'author': "lonelyleaves",
    'category': 'Gooderp',
    "description":
    '''
    该模块实现部分模块归档的校验方法
    1、partner 归档的时候校验业务伙伴是否存在应收应付余额
    2、goods 归档时校验商品的当前数量是否为０
    ''',
    'depends': [
        'core',
        'sell','buy',
    ],
    "website": "",
    "license": "LGPL-3",
    "data": [
    ],
    'installable': True,
}
