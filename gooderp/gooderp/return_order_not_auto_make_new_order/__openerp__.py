# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 上海开阖软件有限公司 (http://www.osbzr.com).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
{
    'name': 'GOODERP 退货单手动创建分拣单',
    'author': 'lonelyleaves',
    'website': 'www.gooderp.org',
    'category': 'sell',
    'description':
    '''
                            Gooderp的销售/采购退货单会自动创建一张新的分拣出货单，该模块限制退货单不会生成新的分拣出货单
    ''',
    'version': '11.11',
    'depends': ['sell','buy'],
    'data': [
        'views/sell_return_view.xml',
        'views/buy_return_view.xml',
        ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
}
