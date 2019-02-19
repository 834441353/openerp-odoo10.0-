# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright JLaloux
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'All voucher done',
    'version': '0.0.1',
    'author': "lonelyleaves",
    'category': 'gooderp',
    'summary': 'GoodERP批量审核会计凭证',
    'description':
     '''
        批量审核会计凭证,勾选多笔凭证之后可以一次性审核
    ''',
    'depends': ['finance'],
    'data': [
        'views/finance.xml'
    ],
    'installable': True,
}
