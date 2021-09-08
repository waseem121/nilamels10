# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'Acespritech Flexi Retail',
    'version': '1.5',
    'category': 'Point of Sale',
    'summary': 'Complete Retail Solution',
    'description': """
This module allows user to use multiple functionality from pos interface.
""",
    'price': 330,
    'currency': 'EUR',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'depends': ['base', 'account', 'sale', 'point_of_sale', 'hr', 'hr_payroll', 'hr_payroll_account', 'purchase','stock_restrict_locations'],
    "data": [
             'security/security.xml',
        'security/ir.model.access.csv',
        'views/cash_points_view.xml',
        'views/pos_cross_selling.xml',
        'views/account_view.xml',
        'views/product_view.xml',
        'views/pos_view.xml',
        'views/res_config_view.xml',
        'views/dynamic_prod_page_rpt.xml',
        'views/prod_small_lbl_rpt.xml',
        'wizard/generate_product_ean13_view.xml',
        'wizard/wizard_product_page_report_view.xml',
        'wizard/wizard_product_small_label_report.xml',
        'wizard/wizard_pos_sale_report_view.xml',
        'wizard/wizard_sales_details_view.xml',
        'wizard/wizard_add_product_pack_view.xml',
        'wizard/wizard_pos_x_report.xml',
        'data/data.xml',
        'data/template.xml',
        'data/page_design_data.xml',
        'data/small_design_data.xml',
        'data/gift_voucher_sequence.xml',
        'data/gift_card_product.xml',
#         'data/account_journal.xml',
        'data/product.xml',
        'views/front_sales_report_template.xml',
        'views/front_sales_report_pdf_template.xml',
        'views/pos_sales_report_pdf_template.xml',
        'views/pos_sales_report_template.xml',
        'views/sales_details_pdf_template.xml',
        'views/sales_details_template.xml',
        'views/front_sales_thermal_report_template_xreport.xml',
        'views/front_sales_report_pdf_template_xreport.xml',
        'views/res_users_view.xml',
        # 'views/pos_coupon_security.xml',
        # 'views/pos_coupon_view.xml',
        'views/res_company_view.xml',
        'views/loyalty_view.xml',
        'views/res_partner_view.xml',
        # 'views/bonus_return_view.xml',
        'report.xml',
        'views/flexiretail.xml',
        'views/gift_card.xml',
        'views/wallet_management_view.xml',
        'views/pos_mirror_image_template.xml',
        'views/aspl_voucher_view.xml',
        'report/report_deliveryslip.xml',
        'report/sale_custom_report_view.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
        'views/pos_order_analysis_report_view.xml',
        'wizard/wizard_pos_doctor_sale_report_view.xml',
        'views/report_doctor_sale_template.xml',
    ],
    'images': ['static/description/2_main_screen.png'],
    'qweb': [
        'static/src/xml/pos.xml',
        'static/src/xml/reservation.xml',
        'static/src/xml/widget.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
