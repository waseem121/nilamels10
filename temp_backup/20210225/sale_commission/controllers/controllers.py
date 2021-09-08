# -*- coding: utf-8 -*-
from odoo import http

# class SaleCommission(http.Controller):
#     @http.route('/sale_commission/sale_commission/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_commission/sale_commission/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_commission.listing', {
#             'root': '/sale_commission/sale_commission',
#             'objects': http.request.env['sale_commission.sale_commission'].search([]),
#         })

#     @http.route('/sale_commission/sale_commission/objects/<model("sale_commission.sale_commission"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_commission.object', {
#             'object': obj
#         })