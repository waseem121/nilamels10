# -*- coding: utf-8 -*-
from odoo import http

# class AccountSerial(http.Controller):
#     @http.route('/account_serial/account_serial/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_serial/account_serial/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_serial.listing', {
#             'root': '/account_serial/account_serial',
#             'objects': http.request.env['account_serial.account_serial'].search([]),
#         })

#     @http.route('/account_serial/account_serial/objects/<model("account_serial.account_serial"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_serial.object', {
#             'object': obj
#         })