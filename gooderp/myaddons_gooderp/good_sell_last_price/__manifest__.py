# -*- coding: utf-8 -*-
{
    'name': 'GoodERP Sell Lats price',
    'author': "lonelyleaves",
    'category': 'sale',
    'summary': 'sale order line show last price',
    'version': '1.0',
    'description': """
        销售订单明细的查询最近销售价格
        """,
    'depends': [
        'sell',
    ],
    'data': [
        'views/sell_last_price_view.xml',
    ],
}
