# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoorpc


class ReportStockWizard(models.TransientModel):
    _inherit = 'report.stock.transceive.wizard'


    @api.multi
    def open_report(self):
        # rpc_messes = self.env['gooderp.db.message']
        # print rpc_messes
        #
        # for rpc_mess in rpc_messes:
        date_start=self.date_start
        date_end=self.date_end
        print date_start,date_end
        url ='localhost'# rpc_mess.url
        port ='8069'# rpc_mess.port
        db ='test'# rpc_mess.db_name
        user_name ='admin'# rpc_mess.user_name
        pwd ='admin'#rpc_mess.pwd
        odoo = odoorpc.ODOO(url,'jsonrpc',port)
        odoo.login(db,user_name,pwd)
        stock = odoo.env['report.stock.transceive.wizard']
        data1=stock.search_read([])
        print data1
        self._cr.execute("delete from report_stock_report_all")
        for data in data1:
            self.env['report.stock.report.all'].create(data)


        return {
            'type': 'ir.actions.act_window',
            'res_model': 'report.stock.report.all',
            'view_mode': 'tree',
            'name': u'商品收发明细表 %s 至  %s ' % (self.date_start, self.date_end),
            # 'context': self.read(['date_start', 'date_end', 'warehouse_id', 'goods_id'])[0],
            'limit': 65535,
        }