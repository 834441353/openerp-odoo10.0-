# -*- coding: utf-8 -*-

from datetime import date, timedelta
from odoo import models, fields, api
import odoorpc


class ReportStockTransceive(models.Model):
    _inherit = 'report.stock.transceive'
