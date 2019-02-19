# -*- coding: utf-8 -*-
# Copyright 2015 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{

    'name': 'Password Security',
    "summary": "Allow admin to set password security requirements.",
    'version': '10.0.1.1.2',
    'author': "lonelyleaves",
    'category': 'Base',
    'depends': [
        'auth_crypt',
        'auth_signup',
    ],
    "website": "",
    "license": "LGPL-3",
    "data": [
        'views/res_company_view.xml',
    ],
    'installable': True,
}
