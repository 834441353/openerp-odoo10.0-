# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.odoo.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "GOODERP 多公司库存报表",
    "version": '1.1',
    "author": 'lonelyleaves',
    "website": "http://www.odoo.com",
    "category": "Generic Modules",
    "depends": ['warehouse',
                'more_company_report_base'],
    "description":
    '''
                        该模块实现了 GoodERP 中 库存收发明细表查看集团公司库存收发
    ''',
    "data": [
        'models/stock_move_report_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    # "active": False,
}
