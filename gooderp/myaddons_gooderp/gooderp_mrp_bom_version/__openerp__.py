# -*- coding: utf-8 -*-


{
    "name": "MRP -Gooderp BoM version",
    "summary": "BoM versioning",
    "version": "10.0.1.0.0",
    "author":  "lonely leaves",
    "website": "http://www.odoo.com",
    "category": "Generic Modules",
    "depends": [
        "warehouse",
    ],
    "description":
    '''
                        该模块实现了 GoodERP 物料清单版本管理功能
    ''',
    "data": [
        #"data/mrp_bom_data.xml",
        #"security/mrp_bom_version_security.xml",
        #"views/res_config_view.xml",
        "views/mrp_bom_view.xml",
    ],
    "installable": True,
    "post_init_hook": "set_active_bom_active_state",
}
