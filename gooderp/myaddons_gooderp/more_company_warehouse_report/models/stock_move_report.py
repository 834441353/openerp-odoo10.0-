# -*- coding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
import datetime


class ReportStockTransceive(models.Model):
    _name = 'report.stock.report.all'
    _description = u'商品收发明细表汇总'

    company=fields.Char(u'公司')
    goods = fields.Char(u'商品')
    attribute = fields.Char(u'属性')
    id_lists = fields.Text(u'库存调拨id列表')
    uom = fields.Char(u'单位')
    warehouse = fields.Char(u'仓库')
    goods_qty_begain = fields.Float(
        u'期初数量', digits=dp.get_precision('Quantity'))
    cost_begain = fields.Float(
        u'期初成本', digits=dp.get_precision('Amount'))
    goods_qty_end = fields.Float(
        u'期末数量', digits=dp.get_precision('Quantity'))
    cost_end = fields.Float(
        u'期末成本', digits=dp.get_precision('Amount'))
    goods_qty_out = fields.Float(
        u'出库数量', digits=dp.get_precision('Quantity'))
    cost_out = fields.Float(
        u'出库成本', digits=dp.get_precision('Amount'))
    goods_qty_in = fields.Float(
        u'入库数量', digits=dp.get_precision('Quantity'))
    cost_in = fields.Float(
        u'入库成本', digits=dp.get_precision('Amount'))