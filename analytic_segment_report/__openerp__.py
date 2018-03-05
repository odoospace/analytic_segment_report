# -*- coding: utf-8 -*-
{
    'name': "Analytic Segment Reports",

    'summary': """
        Module that adds analytic segments to accounting reports
        """,

    'description': """
        
        + Add analytic segments to General Ledger
    """,

    'author': "Impulzia",
    'website': "http://impulzia.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '8.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'analytic_segment'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo.xml',
    #],
}
