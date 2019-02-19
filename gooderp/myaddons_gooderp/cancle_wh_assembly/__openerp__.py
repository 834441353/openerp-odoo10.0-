# -*- coding: utf-8 -*-
{
    'name': "GoodERP组装单取消发料",
    'author': "lonely_leaves",
    'website': "http://www.osbzr.com",
    'category': 'gooderp',
    'summary': 'GoodERP 组装单发料之后不允许撤销，该功能为组装单取消发料的过程',
    "description":
    '''
    该模块实现撤销组装单发料的功能，可以取消发料
    ''',
    'version': '11.11',
    'application': True,
    'depends': ['warehouse'],
    'data': [
        'views/production_view.xml'
    ],
}
