# -*- coding: utf-8 -*-
from odoo import http

# class AccountReportTechnicalSiafa(http.Controller):
#     @http.route('/account_report_technical_siafa/account_report_technical_siafa/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_report_technical_siafa/account_report_technical_siafa/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_report_technical_siafa.listing', {
#             'root': '/account_report_technical_siafa/account_report_technical_siafa',
#             'objects': http.request.env['account_report_technical_siafa.account_report_technical_siafa'].search([]),
#         })

#     @http.route('/account_report_technical_siafa/account_report_technical_siafa/objects/<model("account_report_technical_siafa.account_report_technical_siafa"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_report_technical_siafa.object', {
#             'object': obj
#         })