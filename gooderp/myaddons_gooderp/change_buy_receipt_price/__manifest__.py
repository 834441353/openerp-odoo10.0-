# -*- coding: utf-8 -*-
{
    'name': 'GoodERP change buy receipt price',
    'author': "lonelyleaves",
    'category': 'buy',
    'summary': 'change buy receipt price when state is done',
    'version': '1.0',
    'description': """
        当采购单已经入库且当前会计区间未结账，修改采购入库单价以及关联的出入库单据和会计凭证
        """,
    'depends': [
        'buy',
    ],
    'data': [
        'views/sell_last_price_view.xml',
    ],
}
