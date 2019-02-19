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
    "name": "GOODERP 检查单据的amount金额",
    "version": '1.1',
    "author": 'lonelyleaves',
    "website": "http://www.odoo.com",
    "category": "Generic Modules",
    "depends": ['warehouse',
                'sell','buy'],
    "description":
    '''
                        该模块在审核的时候检查单据的合计金额是否等于单据的明细行金额的和
                        如果不相等则报错
    ''',
    'demo': [
    ],
    'installable': True,
    # "active": False,
}
