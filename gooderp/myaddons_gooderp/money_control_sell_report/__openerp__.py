# -*- coding: utf-8 -*-
{
    'name': "GoodERP Finance Control Sale Report 模块",
    'author': "lonely_leaves",
    'website': "http://www.osbzr.com",
    'category': 'gooderp',
    'summary': 'GoodERP 出纳经理查看销售报表菜单权限',
    "description":
    '''
    该模块在资金菜单下增加销售报表菜单，允许相关权限人员查看销售报表并分析销售报表
    ''',
    'version': '11.11',
    'application': True,
    'depends': ['money','sell'],
    'data': [
        'report/money_control_sell_report_view.xml'
    ],
}
