# -*- coding: utf-8 -*-

import logging

import odoo
from odoo import exceptions
from odoo.osv import fields, osv

from datetime import datetime

from odoo.addons.base.res import res_users

_logger = logging.getLogger(__name__)


class LockIPUser(osv.osv):
    _name = 'toproerp.lock.ip.user'
    _description = u'记录同ＩＰ同账号的登录错误次数'

    _columns = {
        'login': fields.char(string=u'登陆账号',invisible=True,copy=False),
        'ip' : fields.char(string=u'IP地址',invisible=True,copy=False),
        'error_number' : fields.integer(string=u'错误次数', invisible=True, copy=False),
        'lock_time' : fields.datetime(string=u'锁定时间', invisible=True, copy=False),
    }

    def check_error_number(self, cr, uid, login,ip, max_number=3,lock_timeout=10):
        # 检查是否达到最大错误次数以及是否达到锁定时长

        cr.execute('SELECT id,error_number, lock_time FROM toproerp_lock_ip_user WHERE login=%s AND ip=%s', (login,ip,))
        cr.commit()

        if cr.rowcount:
            id,error_number, lock_time_str = cr.fetchone()
            now = datetime.now()
            if error_number >= max_number:
                lock_time = datetime.strptime(lock_time_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                lock_login_time = (now - lock_time).seconds/60
                if lock_login_time <= lock_timeout:
                    #如果已经超次数，并且锁定时长未过，就显示锁定
                    return False
                else:
                    #如果已经过锁定时长,则复原
                    self.init_error_number(cr,login,ip)
                    self.invalidate_cache(cr,id)

            return error_number
        return 1

    def init_error_number(self, cr, login,ip):
        '''
        将错误次数清0
        :param cr:
        :param login:
        :return:
        '''
        cr.execute(
            "Delete From toproerp_lock_ip_user WHERE login=%s and ip=%s",
            (login,ip,))
        cr.commit()
        _logger.info(u'解锁锁定的记录 ip:%s login:%s' % (ip,login))

    def add_error_number(self, cr, uid, login, ip):
        '''
        增加一次错误次数
        :param cr:
        :param uid:
        :param login:
        :param context:
        :return:
        '''

        cr.execute('SELECT id,error_number, lock_time FROM toproerp_lock_ip_user WHERE login=%s AND ip=%s', (login,ip,))

        if cr.rowcount:
            _logger.info(u'增加一次次数 ip:%s login:%s' % (ip,login))
            cr.execute(
                "UPDATE toproerp_lock_ip_user SET error_number=error_number+1, lock_time=%s WHERE login=%s and ip=%s",
                (datetime.now(), login,ip))
        else:
            _logger.info(u'增加一条检查记录 ip:%s login:%s' % (ip,login))
            cr.execute(
                "INSERT INTO toproerp_lock_ip_user (login,ip,error_number,lock_time) values(%s,%s,1,%s)",
                (login,ip,datetime.now()))

        cr.commit()
