# -*- coding: utf-8 -*-

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class tfs_purchase_price_change(models.Model):
    """
        采购价格调整

    """
    _name = "tfs.purchase.price.change"
    _inherit = ['mail.thread']
    _rec_name = 'receipt_id'

    name = fields.Char(u'单号')
    receipt_id = fields.Many2one('buy.receipt', u'入库单')
    partner_id = fields.Many2one('partner', u'供应商', related='receipt_id.partner_id')
    date = fields.Date(u'开单日期', default=lambda self: fields.Date.today())
    order_lines = fields.One2many('tfs.purchase.price.change.line', 'change_id', u'入库单明细')
    state = fields.Selection([('draft', u'修改前'), ('done', u'修改完成')], u'状态', default='draft')
    note = fields.Text(u'关联单号')

    # 生成采购差异凭证(凭证、{产品:[差异金额，差异数量，新价格]})
    def new_change_voucher(self, voucher_id, change_dict, is_return=False):
        voucher_line_obj = self.env['voucher.line']
        # 复制新的差异凭证
        new_voucher_id = voucher_id.copy({'change_id':self.id})
        # 获取所有的产品列表
        goods_ids = change_dict.keys()
        all_money = 0 # 计算总金额
        log = False # 标识是否有明细处理过
        # 循环处理凭证中的明细
        for line_id in new_voucher_id.line_ids:
            # 如果明细有产品
            if line_id.goods_id:
                # 如果产品在产品列表中
                if line_id.goods_id in goods_ids:
                    # 从产品列表中移除此产品
                    goods_ids.remove(line_id.goods_id)
                    # 差异数量
                    new_good_qty = change_dict[line_id.goods_id][1]
                    # 修改后价格
                    new_price = change_dict[line_id.goods_id][2]
                    log = True
                    if is_return:
                        if line_id.debit:
                            # 计算原成本价
                            old_price = line_id.debit / line_id.goods_qty
                            # 获取差异金额
                            amount = (new_price + old_price) * new_good_qty
                            if amount == 0:
                                raise UserError(u'凭证%s 的原成本价为%s, 调整后价格为%s, 数量为%s, 总数据为%s'%(voucher_id.name, old_price, new_price, new_good_qty,change_dict))
                            # 计算总差异金额
                            all_money += amount
                            line_id.debit = amount
                            line_id.credit = 0
                        if line_id.credit:
                            # 计算原成本价
                            old_price = line_id.credit / line_id.goods_qty
                            # 获取差异金额
                            amount = (new_price + old_price) * new_good_qty
                            if amount == 0:
                                raise UserError(u'凭证%s 的原成本价为%s, 调整后价格为%s, 数量为%s, 总数据为%s'%(voucher_id.name, old_price, new_price, new_good_qty,change_dict))
                            # 计算总差异金额
                            all_money += amount
                            line_id.credit = amount
                            line_id.debit = 0
                    else:
                        amount = change_dict[line_id.goods_id][0]
                        all_money += amount
                        if line_id.debit:
                            line_id.debit = amount
                            line_id.credit = 0
                        if line_id.credit:
                            line_id.credit = amount
                            line_id.debit = 0
                    # 更新差异数量
                    line_id.goods_qty = new_good_qty
                else:
                    # 删除该明细
                    line_id.unlink()
        if not all_money:
            for line in change_dict.values():
                all_money += line[0]
        if log and all_money:
            voucher_line_ids = voucher_line_obj.search([('goods_id', '=', False), ('voucher_id', '=', new_voucher_id.id)])
            for voucher_line_id in voucher_line_ids:
                if voucher_line_id.debit:
                    voucher_line_id.debit = all_money
                    voucher_line_id.credit = 0
                if voucher_line_id.credit:
                    voucher_line_id.credit = all_money
                    voucher_line_id.debit = 0
            new_voucher_id.amount_text = str(sum([line.debit for line in new_voucher_id.line_ids]))
            new_voucher_id.voucher_done()
        else:
            new_voucher_id.unlink()

    @api.one
    def _wrong_delivery_done(self):
        '''审核时不合法的给出报错'''
        if self.state == 'done':
            raise UserError(u'请不要重复发货')
        if self.receipt_id.invoice_id.reconciled != 0:
            raise UserError(u'该采购入库单已经收款或者部分收款,不能审核采购调价单')
        for line in self.order_lines:
            if line.new_price < 0:
                raise UserError(u'商品 %s 的单价不能小于0！' % line.goods_id.name)

    # 更新对应销售出库单价格(移库明细ID)
    def update_sale_price(self, line_id, difference_one, new_price):
        # 更新对应销售出库单价格
        matching_obj = self.env['wh.move.matching'] #匹配规则
        delivery_obj = self.env['sell.delivery'] # 销售出库单
        sell_list = [] # 出货单列表
        sell_dict = {} # # {产品：金额}
        product_qty = {} # # {产品：金额}
        sell_return_list = [] # 退货单列表
        sell_return_dict = {} # {产品：金额}
        good_ids = []
        real_list = []
        lot_sell_ids = matching_obj.search([('line_in_id','in',line_id),('line_out_id.move_id.origin','=','sell.delivery.sell')])
        sale_order_list = []
        if lot_sell_ids:
            for lot_sell_id in lot_sell_ids:
                #FIXME 采购单价分为俩种情况
                #采购的数量全部被这个销售单使用，且还有其他采购单，则 采购单价=（原来的单价+调整的数量*调整的差额）/销售数量
                cost_unit = lot_sell_id.line_out_id.with_context(type='out').cost_unit   #销售明细对应的采购金额
                sell_qty = lot_sell_id.line_out_id.with_context(type='out').goods_qty #销售明细的数量
                cost_qty = lot_sell_id.qty    #销售明细对应的要调整的采购数量
                self_change_cost= cost_qty*(difference_one)     # 销售明细对应的需调整的采购金额
                new_cost_unit = (cost_unit*sell_qty+self_change_cost)/lot_sell_id.line_out_id.goods_qty   #新的采购成本单价
                lot_sell_id.line_out_id.with_context(type='out').cost_unit = new_cost_unit  #修改销售明细的采购成本
                lot_sell_id.line_out_id.with_context(type='out').cost = new_cost_unit * sell_qty
                delivery_id = delivery_obj.search([('sell_move_id', '=', lot_sell_id.line_out_id.move_id.id)], limit=1)
                if delivery_id not in sell_list:
                    sell_list.append(delivery_id)
                if delivery_id.order_id and delivery_id.order_id.id not in sale_order_list:
                    sale_order_list.append(delivery_id.order_id.id)
                if delivery_id in sell_dict:
                    if lot_sell_id.line_out_id.goods_id in sell_dict[delivery_id]:
                        sell_dict[delivery_id][lot_sell_id.line_out_id.goods_id][0] += difference_one * lot_sell_id.qty
                        product_qty[delivery_id][lot_sell_id.line_out_id.goods_id][0] += difference_one * lot_sell_id.qty
                        sell_dict[delivery_id][lot_sell_id.line_out_id.goods_id][1] += lot_sell_id.qty
                        product_qty[delivery_id][lot_sell_id.line_out_id.goods_id][1] += lot_sell_id.qty
                    else:
                        good_ids.append(lot_sell_id.line_out_id.goods_id.id)
                        sell_dict[delivery_id][lot_sell_id.line_out_id.goods_id] = [difference_one * lot_sell_id.qty, lot_sell_id.qty, new_price]
                        product_qty[delivery_id][lot_sell_id.line_out_id.goods_id] = [difference_one * lot_sell_id.qty, lot_sell_id.qty, new_price]
                else:
                    good_ids.append(lot_sell_id.line_out_id.goods_id.id)
                    sell_dict[delivery_id] = {lot_sell_id.line_out_id.goods_id:[difference_one * lot_sell_id.qty, lot_sell_id.qty, new_price]}
                    product_qty[delivery_id] = {lot_sell_id.line_out_id.goods_id:[difference_one * lot_sell_id.qty, lot_sell_id.qty, new_price]}
        if sell_list:
            # 更新销售退货单价格
            sell_return_list = delivery_obj.search([('order_id','in',sale_order_list),('is_return','=',True)])
            if sell_return_list:
                for delivery_id in sell_return_list:
                    new_product_qty = product_qty.get(delivery_id.origin_id)
                    real_list = delivery_id.line_in_ids.filtered(lambda line:line.goods_id.id in good_ids)
                    for line_in_id in real_list:
                        if line_in_id.goods_id in new_product_qty:
                            if line_in_id.goods_qty <= new_product_qty[line_in_id.goods_id][1]:
                                line_in_id.with_context(type='in').cost_unit = new_price
                                new_product_qty[line_in_id.goods_id][1] -= line_in_id.goods_qty
                                line_num = line_in_id.goods_qty
                            else:
                                line_in_id.copy({'goods_qty':line_in_id.goods_qty - new_product_qty[line_in_id.goods_id][1]})
                                line_num = new_product_qty[line_in_id.goods_id][1]
                                line_in_id.with_context(type='in').cost_unit = new_price
                                line_in_id.goods_qty = new_product_qty[line_in_id.goods_id][1]
                            if line_in_id.goods_id in sell_return_dict:
                                sell_return_dict[line_in_id.goods_id][0] -= difference_one * line_num
                                sell_return_dict[line_in_id.goods_id][1] += line_num
                            else:
                                sell_return_dict[line_in_id.goods_id] = [-difference_one * line_num,line_num,new_price]
        return [sell_list, sell_return_list, sell_dict, sell_return_dict, real_list]

    # 确认修改价格
    @api.multi
    def btn_done(self):
        matching_obj = self.env['wh.move.matching'] #匹配规则
        receipt_obj = self.env['buy.receipt'] # 采购入库单
        assembly_obj = self.env['wh.assembly'] # 组装单
        disassembly_obj = self.env['wh.disassembly'] # 拆卸单
        outsource_obj = self.env['outsource'] # 委外加工单
        for record in self:
            record._wrong_delivery_done() # 检测发票和商品金额的问题
            buy_dict = {}  # {产品：[差异金额、差异数量、修改后单价]}
            buy_return_dict = {}  # {产品：[差异金额、差异数量、修改后单价]}
            buy_return = []
            sell_dict = {}  # {销售单：{产品：金额}}
            sell_list = []
            sell_return_list = []
            sell_return_dict = {}  # {产品：金额}
            invoice_list = []
            assembly_list = []
            assembly_dict = {}
            disassembly_list = []
            disassembly_dict = {}
            outsource_list = []
            outsource_dict = {}
            for line in record.order_lines:
                # 如果价格变动了
                if line.new_price and line.new_price != line.price:
                    difference_one = line.new_price - line.price # 单价差异
                    difference_price = difference_one * line.goods_qty # 差异金额
                    self.partner_id.payable += difference_price # 更新客户的应付金额
                    if line.goods_id in buy_dict: # 统计产品差异数量和金额
                        buy_dict[line.goods_id][0] += difference_price
                        buy_dict[line.goods_id][1] += line.goods_qty
                    else:
                        buy_dict[line.goods_id] = [difference_price,line.goods_qty,line.new_price]
                    line.line_id.with_context(type='in').price = line.new_price # 更新入库价格
                    line.line_id.with_context(type='in').cost_unit = line.new_price # 更新入库成本
                    line.line_id.with_context(type='in').price_taxed = line.new_price * (1 + line.line_id.tax_rate * 0.01) # 更新入库含税单价
                    # 修改采购结算单
                    if self.receipt_id.invoice_id:
                        # 获取结算单的列表
                        if self.receipt_id.invoice_id.voucher_id and self.receipt_id.invoice_id.voucher_id not in invoice_list:
                            invoice_list.append(self.receipt_id.invoice_id.voucher_id)
                        # 更新结算单差异金额
                        self.receipt_id.invoice_id.amount += difference_price
                        self.receipt_id.invoice_id.to_reconcile += difference_price
                    # 更新对应组装单明细
                    zhd_ids = matching_obj.search([('line_in_id','=',line.line_id.id),('line_out_id.move_id.origin','=','wh.assembly')])
                    if zhd_ids:
                        for zhd_id in zhd_ids:
                            # 修改组装单价格、含税单价
                            zhd_id.line_out_id.with_context(type='out').price = line.new_price
                            zhd_id.line_out_id.with_context(type='out').price_taxed = line.new_price
                            assembly_id = assembly_obj.search([('move_id','=',zhd_id.line_out_id.move_id.id)], limit=1)
                            if assembly_id not in assembly_list:
                                assembly_list.append(assembly_id)
                            if zhd_id.line_out_id.goods_id in assembly_dict:
                                assembly_dict[zhd_id.line_out_id.goods_id][0] += difference_one * zhd_id.qty
                                assembly_dict[zhd_id.line_out_id.goods_id][1] += zhd_id.qty
                            else:
                                assembly_dict[zhd_id.line_out_id.goods_id] = [difference_one * zhd_id.qty,zhd_id.qty,line.new_price]
                    # 更新对应拆卸单明细
                    cxd_ids = matching_obj.search([('line_in_id','=',line.line_id.id),('line_out_id.move_id.origin','=','wh.disassembly')])
                    if cxd_ids:
                        for cxd_id in cxd_ids:
                            cxd_id.line_out_id.with_context(type='out').price = line.new_price
                            cxd_id.line_out_id.disassembly_obj(type='out').price_taxed = line.new_price
                            disassembly_id = disassembly_obj.search([('move_id','=',cxd_id.line_out_id.move_id.id)], limit=1)
                            if disassembly_id not in disassembly_list:
                                disassembly_list.append(disassembly_id)
                            if cxd_id.line_out_id.goods_id in disassembly_dict:
                                disassembly_dict[cxd_id.line_out_id.goods_id][0] += difference_one * cxd_id.qty
                                disassembly_dict[cxd_id.line_out_id.goods_id][1] += cxd_id.qty
                            else:
                                disassembly_dict[cxd_id.line_out_id.goods_id] = [difference_one * cxd_id.qty,cxd_id.qty,line.new_price]
                    # 更新对应委外加工单明细
                    wwjgd_ids = matching_obj.search([('line_in_id','=',line.line_id.id),('line_out_id.move_id.origin','=','outsource')])
                    if wwjgd_ids:
                        for wwjgd_id in wwjgd_ids:
                            wwjgd_id.line_out_id.with_context(type='out').price = line.new_price
                            wwjgd_id.line_out_id.with_context(type='out').price_taxed = line.new_price
                            outsource_id = outsource_obj.search([('move_id','=',wwjgd_id.line_out_id.move_id.id)], limit=1)
                            if outsource_id not in outsource_list:
                                outsource_list.append(outsource_id)
                            if wwjgd_id.line_out_id.goods_id in outsource_dict:
                                outsource_dict[wwjgd_id.line_out_id.goods_id][0] += difference_one * wwjgd_id.qty
                                outsource_dict[wwjgd_id.line_out_id.goods_id][1] += wwjgd_id.qty
                            else:
                                outsource_dict[wwjgd_id.line_out_id.goods_id] = [difference_one * wwjgd_id.qty,wwjgd_id.qty,line.new_price]
                    # 更新对应采购退货单明细
                    lot_ids = matching_obj.search([('line_in_id','=',line.line_id.id),('line_out_id.move_id.origin','=','buy.receipt.return')])
                    if lot_ids:
                        for lot_id in lot_ids:
                            lot_id.line_out_id.with_context(type='out').price = line.new_price
                            lot_id.line_out_id.with_context(type='out').price_taxed = line.new_price
                            receipt_id = receipt_obj.search([('buy_move_id', '=', lot_id.line_out_id.move_id.id)], limit=1)
                            if receipt_id and receipt_id.invoice_id:
                                receipt_id.invoice_id.amount -= (difference_one * lot_id.qty)
                                receipt_id.invoice_id.to_reconcile -= (difference_one * lot_id.qty)
                            if receipt_id not in buy_return:
                                buy_return.append(receipt_id)
                            if lot_id.line_out_id.goods_id in buy_return_dict:
                                buy_return_dict[lot_id.line_out_id.goods_id][0] -= difference_price
                                buy_return_dict[lot_id.line_out_id.goods_id][1] += lot_id.qty
                            else:
                                buy_return_dict[lot_id.line_out_id.goods_id] = [-difference_price,lot_id.qty, line.new_price]
                    diff_line = [line.line_id.id]
                    while diff_line:
                        # 更新对应销售出库单价格
                        sale_delivery_list, sale_return_delivery_list, sale_dict, sale_return_dict, real_list = self.update_sale_price(diff_line, difference_one, line.new_price)
                        # 销售出货单集合
                        for sale_del in sale_delivery_list:
                            if sale_del not in sell_list:
                                sell_list.append(sale_del)
                        # 销售退货单集合
                        for sale_return_del in sale_return_delivery_list:
                            if sale_return_del not in sell_return_list:
                                sell_return_list.append(sale_return_del)
                        print 'sale_dict is ',sale_dict
                        for key, value in sale_dict.items():
                            if key in sell_dict:
                                for key1,value1 in value.items():
                                    if key1 in sell_dict[key]:
                                        sell_dict[key][key1][0] += value1[0]
                                        sell_dict[key][key1][1] += value1[1]
                                    else:
                                        sell_dict[key][key1] = value1
                            else:
                                sell_dict[key] = value
                        for key, value in sale_return_dict.items():
                            if key in sell_return_dict:
                                sell_return_dict[key][0] -= value[0]
                                sell_return_dict[key][1] += value[1]
                            else:
                                sell_return_dict[key] = value
                        diff_line = real_list.ids if real_list else []
            note = ''
            # 生成采购差异凭证
            if record.receipt_id.voucher_id and buy_dict:
                note += (record.receipt_id.name + ',')
                record.new_change_voucher(record.receipt_id.voucher_id, buy_dict)
            # 生成采购结算单差异凭证
            if invoice_list and buy_dict:
                for voucher_id in invoice_list:
                    record.new_change_voucher(voucher_id, buy_dict)
            # 生成采购退货差异凭证
            if buy_return and buy_return_dict:
                for return_id in buy_return:
                    receipt_id = receipt_obj.search([('buy_move_id', '=', return_id.id)], limit=1)
                    if receipt_id and receipt_id.voucher_id:
                        note += (receipt_id.name + ',')
                        record.new_change_voucher(receipt_id.voucher_id, buy_return_dict)
            # 生成销售差异凭证
            if sell_list and sell_dict:
                for sell in sell_list:
                    if sell.voucher_id:
                        note += (sell.name + ',')
                        record.new_change_voucher(sell.voucher_id, sell_dict.get(sell))
            # 生成组装单差异凭证
            if assembly_list and assembly_dict:
                for assembly in assembly_list:
                    if assembly.out_voucher_id:
                        note += (assembly.name + ',')
                        record.new_change_voucher(assembly.out_voucher_id, assembly_dict)
            # 生成拆卸单差异凭证
            if disassembly_list and disassembly_dict:
                for disassembly in disassembly_list:
                    if disassembly.voucher_id:
                        note += (disassembly.name + ',')
                        record.new_change_voucher(disassembly.voucher_id, disassembly_dict)
            # 生成委外加工单差异凭证
            if outsource_list and outsource_dict:
                for outsource in outsource_list:
                    if outsource.out_voucher_id:
                        note += (outsource.name + ',')
                        record.new_change_voucher(outsource.out_voucher_id, outsource_dict)
            # 生成销售退货差异凭证
            if sell_return_list and sell_return_dict:
                for sell_return in sell_return_list:
                    if sell_return.voucher_id:
                        note += (sell_return.name + ',')
                        record.new_change_voucher(sell_return.voucher_id, sell_return_dict, is_return=True)
            record.state = 'done'
            record.note = note
            record.receipt_id.change_id = record.id

    # 反确认
    @api.multi
    def btn_draft(self):
        receipt_obj = self.env['buy.receipt']
        delivery_obj = self.env['sell.delivery']
        matching_obj = self.env['wh.move.matching']
        assembly_obj = self.env['wh.assembly'] # 组装单
        disassembly_obj = self.env['wh.disassembly'] # 拆卸单
        outsource_obj = self.env['outsource'] # 委外加工单
        # 判断新生成的数据是否已经完成审核了
        voucher_ids = self.env['voucher'].search([('change_id','=',self.id),('state','!=','cancel')])
        if voucher_ids:
            for voucher_id in voucher_ids:
                voucher_id.voucher_draft()
                voucher_id.unlink()
        for line in self.order_lines:
            # 如果价格变动了
            if line.new_price and line.new_price != line.price:
                difference_one = line.new_price - line.price
                difference_price = (line.new_price - line.price) * line.goods_qty
                self.partner_id.payable -= difference_price
                # 更新入库单价格
                line.line_id.with_context(type='in').price = line.price # 更新入库价格
                line.line_id.with_context(type='in').cost_unit = line.price # 更新入库成本
                line.line_id.with_context(type='in').price_taxed = line.price * (1 + line.line_id.tax_rate * 0.01) # 更新入库含税单价
                # 修改结算单
                if self.receipt_id.invoice_id:
                    self.receipt_id.invoice_id.amount -= difference_price
                    self.receipt_id.invoice_id.to_reconcile -= difference_price
                # 更新对应组装单明细
                zhd_ids = matching_obj.search([('line_in_id','=',line.line_id.id),('line_out_id.move_id.origin','=','wh.assembly')])
                if zhd_ids:
                    for zhd_id in zhd_ids:
                        # 修改组装单价格、含税单价
                        zhd_id.line_out_id.with_context(type='out').price = line.price
                        zhd_id.line_out_id.with_context(type='out').price_taxed = line.price
                # 更新对应拆卸单明细
                cxd_ids = matching_obj.search([('line_in_id','=',line.line_id.id),('line_out_id.move_id.origin','=','wh.disassembly')])
                if cxd_ids:
                    for cxd_id in cxd_ids:
                        cxd_id.line_out_id.with_context(type='out').price = line.price
                        cxd_id.line_out_id.disassembly_obj(type='out').price_taxed = line.price
                # 更新对应委外加工单明细
                wwjgd_ids = matching_obj.search([('line_in_id','=',line.line_id.id),('line_out_id.move_id.origin','=','outsource')])
                if wwjgd_ids:
                    for wwjgd_id in wwjgd_ids:
                        wwjgd_id.line_out_id.with_context(type='out').price = line.price
                        wwjgd_id.line_out_id.with_context(type='out').price_taxed = line.price
                # 更新对应采购退货单明细
                lot_ids = matching_obj.search([('line_in_id','=',line.line_id.id),('line_out_id.move_id.origin','=','buy.receipt.return')])
                if lot_ids:
                    for lot_id in lot_ids:
                        lot_id.line_out_id.with_context(type='out').price = line.price
                        lot_id.line_out_id.with_context(type='out').cost_unit = line.price # 更新入库成本
                        lot_id.line_out_id.with_context(type='out').price_taxed = line.price * (1 + line.line_id.tax_rate * 0.01) # 更新入库含税单价
                        receipt_id = receipt_obj.search([('buy_move_id', '=', lot_id.line_out_id.move_id.id)], limit=1)
                        if receipt_id and receipt_id.invoice_id:
                            receipt_id.invoice_id.amount -= (difference_one * lot_id.qty)
                            receipt_id.invoice_id.to_reconcile -= (difference_one * lot_id.qty)
                # 更新对应销售出库单价格
                diff_line = [line.line_id.id]
                while diff_line:
                    # 更新对应销售出库单价格
                    sale_delivery_list, sale_return_delivery_list, sale_dict, sale_return_dict, real_list = self.update_sale_price(diff_line, -difference_one, line.price)
                    diff_line = real_list.ids if real_list else []
        self.state = 'draft'
        self.note = ''
        self.receipt_id.change_id = ''

    @api.onchange('receipt_id')
    def onchange_receipt_id(self):
        line_ids = self.env['tfs.purchase.price.change.line'].search([('change_id', '=', self.id)])
        line_ids.unlink()
        if self.receipt_id:
            if self.receipt_id.change_id:
                raise UserError(u'该入库单已调整过价格，请直接反确认原调整价格单！')
            order_lines = []
            for line in self.receipt_id.line_in_ids:
                order_lines.append((0, 0, {'line_id': line, 'goods_id': line.goods_id.id, 'lot_id': line.lot,
                                           'goods_qty': line.goods_qty,'price':line.price,
                                           'uom_id': line.uom_id.id}))
            self.order_lines = order_lines

    @api.model
    def create(self, values):
        if values.get('order_lines'):
            for order_line in values.get('order_lines'):
                if order_line[2].get('line_id') and type(order_line[2].get('line_id')) == list:
                    line_id = order_line[2]['line_id'][0]
                    order_line[2].update({
                        'line_id': line_id
                    })
        if not values.get('name'):
            values['name'] = self.env['ir.sequence'].next_by_code('tfs.purchase.price.change')
        res = super(tfs_purchase_price_change, self).create(values)
        if res.receipt_id.change_id:
            raise UserError(u'该入库单已调整过价格，请直接反确认原调整价格单！')
        return res


class tfs_purchase_price_change_line(models.Model):
    """
        采购价格调整明细
    """
    _name = "tfs.purchase.price.change.line"

    change_id = fields.Many2one('tfs.purchase.price.change', u'采购价格调整')
    line_id = fields.Many2one('wh.move.line', u'入库明细')
    goods_id = fields.Many2one('goods', u'商品')
    lot_id = fields.Char(u'批号')
    goods_qty = fields.Float(u'数量',
                             digits=dp.get_precision('Quantity'))
    uom_id = fields.Many2one('uom', u'单位')
    price = fields.Float(u'单价',digits=dp.get_precision('Price'))
    new_price = fields.Float(u'调整后价格',
                             digits=dp.get_precision('Price'))


class tfs_buy_receipt_inherit(models.Model):
    _inherit = 'buy.receipt'

    change_id = fields.Many2one('tfs.purchase.price.change',u'调整单')


class tfs_voucher_inherit(models.Model):
    _inherit = 'voucher'

    change_id = fields.Many2one('tfs.purchase.price.change',u'调整单')
