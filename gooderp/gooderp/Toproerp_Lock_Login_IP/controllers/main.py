# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

import odoo

from odoo.addons.web.controllers.main import ensure_db
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# 锁定时长 分钟
LOCK_TIME = 1

# 最大允许错误次数
MAX_ERROR_NUMBER = 3


class AuthHome(openerp.addons.web.controllers.main.Home):

    @http.route()
    def web_login(self, *args, **kw):
        """
        重载web_login方法，在登录前进行相应的检查
        :param args:
        :param kw:
        :return:
        """

        max_error_number = int(self._get_max_error_number(request.cr))
        lock_timeout = int(self._get_lock_timeout(request.cr))
        error_number = 1

        ensure_db()
        lock = request.registry.get('toproerp.lock.ip.user')

        if 'login' in request.params:
            error_number = lock.check_error_number(request.cr, openerp.SUPERUSER_ID, request.params['login'],
                                                   request.httprequest.headers.environ['REMOTE_ADDR'], max_error_number,
                                                   lock_timeout)
            request.cr.commit()

        if error_number:
            response = super(AuthHome, self).web_login(*args, **kw)
            request.cr.commit()

            if 'login' in request.params:
                if 'error' in response.qcontext:
                    if (max_error_number - error_number) > 0:
                        response.qcontext.update({'error': u'账号或密码不正确。'
                                                           u'还有%s次尝试的机会,之后账号将被锁定.' % (max_error_number - error_number)})
                    else:
                        response.qcontext.update({'error': u'账号或密码不正确。'})
                    # 登陆失败，增加一次次数
                    lock.add_error_number(request.cr, openerp.SUPERUSER_ID, request.params['login'],
                                          request.httprequest.headers.environ['REMOTE_ADDR'])
                else:
                    # 登陆成功，次数归0
                    lock.init_error_number(request.cr, request.params['login'],
                                           request.httprequest.headers.environ['REMOTE_ADDR'])
        else:
            request.params['login_success'] = False
            values = request.params.copy()
            values['error'] = u"因连续登陆失败，账号已被锁定。" \
                              u" 请%s分钟以后，再尝试登陆。" % lock_timeout
            response = request.render('web.login', values)
            request.cr.commit()

        return response

    def _get_max_error_number(self, cr):
        """
        取得系统参数中的定义的允许错误的次数
        :param cr:
        :return:
        """
        icp = request.registry.get('ir.config_parameter')
        max_error_number = icp.get_param(cr, openerp.SUPERUSER_ID, 'lock_login_ip.max_error_number')
        if not max_error_number:
            icp.set_param(cr, openerp.SUPERUSER_ID, 'lock_login_ip.max_error_number', MAX_ERROR_NUMBER)
            max_error_number = MAX_ERROR_NUMBER

        return max_error_number

    def _get_lock_timeout(self, cr):
        """
        取得系统参数中的定义的允许错误的次数
        :param cr:
        :return:
        """
        icp = request.registry.get('ir.config_parameter')
        lock_timeout = icp.get_param(cr, openerp.SUPERUSER_ID, 'lock_login_ip.lock_timeout')
        if not lock_timeout:
            icp.set_param(cr, openerp.SUPERUSER_ID, 'lock_login_ip.lock_timeout', LOCK_TIME)
            lock_timeout = LOCK_TIME

        return lock_timeout