# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.osv import osv


class VoucherDone(models.Model):
    _name = 'voucher.done'
    _description = u'审核会计凭证'

    # 批量过账凭证
    def voucher_done(self):
        voucher = self.env['voucher'].browse(self.env.context.get('active_ids'))
        for line in voucher:
            if line.state != 'draft':
                raise osv.except_osv(_('警告!'),_('只能过账草稿状态的会计凭证.'))
            else:
                line.voucher_done()
        return True
