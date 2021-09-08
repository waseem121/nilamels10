# -*- coding: utf-8 -*-
from odoo import http

# class FoodexClient(http.Controller):
#     @http.route('/foodex_client/foodex_client/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/foodex_client/foodex_client/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('foodex_client.listing', {
#             'root': '/foodex_client/foodex_client',
#             'objects': http.request.env['foodex_client.foodex_client'].search([]),
#         })

#     @http.route('/foodex_client/foodex_client/objects/<model("foodex_client.foodex_client"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('foodex_client.object', {
#             'object': obj
#         })