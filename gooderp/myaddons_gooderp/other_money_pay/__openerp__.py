# -*- coding: utf-8 -*-
{
    'name': "GoodERP Other Money Order Pay模块",
    'author': "lonelyleaves",
    'website': "http://www.osbzr.com",
    'category': 'gooderp',
    'summary': 'GoodERP其他收支单扩展',
    "description":
    '''
    该模块实现了 GoodERP 其他收支单没有客户的生成结算单，关联应收应付，通过资金单结算，没有客户的按照原来的逻辑。
    同时修改现金流量报表，不统计有客户名称的其他收支单的资金（因为已经生成了收付款单）
    思路：有partner的其它收支单创建结算单并通过系统的收付款单收付款，同时修改结算单的逻辑，结算金额为0的单据生成结算单不生成凭证，计入业务伙伴账单
    1、其他收支单的partner非空，则属于对应的业务伙伴费用记相应的科目
    2、修改结算单的审核逻辑，如果为其他收支单，审核的时候不生成凭证，凭证为结算单的凭证，如果为0金额的结算单，审核的时候没有凭证
    3、修改现金银行报表和资金收支报表，不需要统计有业务伙伴的其他收支单，其他不变
    4、修改销售&采购如果金额为0的情况不生成发票，调整成生成发票不生成凭证
    ''',
    'version': '10.1',
    'application': True,
    'depends': ['money',
                'finance', 'sell','buy'],
    'data': [
        'security/group.xml',
        'views/other_money_order_view.xml',
        'data/finance_data.xml',
    ],
    'demo': [
        'data/demo.xml',
    ]
}
