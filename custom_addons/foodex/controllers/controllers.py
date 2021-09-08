# -*- coding: utf-8 -*-
from odoo import http

# class Foodex(http.Controller):
#     @http.route('/foodex/foodex/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/foodex/foodex/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('foodex.listing', {
#             'root': '/foodex/foodex',
#             'objects': http.request.env['foodex.foodex'].search([]),
#         })

#     @http.route('/foodex/foodex/objects/<model("foodex.foodex"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('foodex.object', {
#             'object': obj
#         })