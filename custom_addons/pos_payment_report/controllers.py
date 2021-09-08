# -*- coding: utf-8 -*-
from openerp import http

# class PosPaymentReport(http.Controller):
#     @http.route('/pos_payment_report/pos_payment_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_payment_report/pos_payment_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_payment_report.listing', {
#             'root': '/pos_payment_report/pos_payment_report',
#             'objects': http.request.env['pos_payment_report.pos_payment_report'].search([]),
#         })

#     @http.route('/pos_payment_report/pos_payment_report/objects/<model("pos_payment_report.pos_payment_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_payment_report.object', {
#             'object': obj
#         })