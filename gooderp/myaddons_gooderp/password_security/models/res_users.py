# -*- coding: utf-8 -*-
# Copyright 2015 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import re

from datetime import datetime, timedelta

from odoo import api, fields, models, _

from ..exceptions import PassError


def delta_now(**kwargs):
    dt = datetime.now() + timedelta(**kwargs)
    return fields.Datetime.to_string(dt)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def write(self, vals):
        if vals.get('password'):
            self._check_password(vals['password'])
            vals['password_write_date'] = fields.Datetime.now()
        return super(ResUsers, self).write(vals)

    @api.multi
    def password_match_message(self):
        self.ensure_one()
        company_id = self.company_id
        message = []
        if company_id.password_lower:
            message.append('\n* ' + _('Lowercase letter'))
        if company_id.password_upper:
            message.append('\n* ' + _('Uppercase letter'))
        if company_id.password_numeric:
            message.append('\n* ' + _('Numeric digit'))
        if company_id.password_special:
            message.append('\n* ' + _('Special character'))
        if message:
            message = [_('Must contain the following:')] + message
        if company_id.password_length:
            message = [
                _('Password must be %d characters or more.') %
                company_id.password_length
            ] + message
        return '\r'.join(message)

    @api.multi
    def _check_password(self, password):
        self._check_password_rules(password)
        return True

    @api.multi
    def _check_password_rules(self, password):
        self.ensure_one()
        if not password:
            return True
        company_id = self.company_id
        password_regex = ['^']
        if company_id.password_lower:
            password_regex.append('(?=.*?[a-z])')
        if company_id.password_upper:
            password_regex.append('(?=.*?[A-Z])')
        if company_id.password_numeric:
            password_regex.append(r'(?=.*?\d)')
        if company_id.password_special:
            password_regex.append(r'(?=.*?[\W_])')
        password_regex.append('.{%d,}$' % company_id.password_length)
        if not re.search(''.join(password_regex), password):
            raise PassError(self.password_match_message())
        return True

