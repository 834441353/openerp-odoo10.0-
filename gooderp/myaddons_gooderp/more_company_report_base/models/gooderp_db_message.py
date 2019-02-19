# -*- coding: utf-8 -*-

from odoo import models, fields, api

class GooderpDbMessage(models.Model):
    _name = 'gooderp.db.message'
    _description = u'账套列表'


    name = fields.Char(u'公司名称', required=True)
    db_name = fields.Char(u'账套名称', required=True)
    url = fields.Char(u'地址', required=True)
    port = fields.Char(u'端口', required=True)
    user_name = fields.Char(u'用户名')
    pwd = fields.Char(u'密码')
    date = fields.Datetime(u'创建日期', default=lambda self: fields.datetime.now())