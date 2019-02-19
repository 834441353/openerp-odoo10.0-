# -*- encoding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, api, fields
from odoo.exceptions import Warning


class SaleOrderLine(models.Model):
    _inherit = 'sell.order.line'
    _order = "create_date desc"

    @api.multi
    def action_sale_product_prices(self):
        last_sale_order_line = self.env['sell.order.line'].search([('order_id.partner_id','=',self.order_id.partner_id.id),
                                                                   ('order_id.state', 'in', ['confirmed', 'done']),
                                                                   ('goods_id','=',self.goods_id.id)],limit=3)

        if not last_sale_order_line:
            raise Warning("No sales history found.!")
        else:
            return {
                'name': u'最近销售价',
                'view_type': 'tree',
                'view_mode': 'tree',
                'res_model': 'sell.order.line',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('id','in',last_sale_order_line.ids)],
            }