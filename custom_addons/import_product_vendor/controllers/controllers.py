# -*- coding: utf-8 -*-
from odoo import http

# class ImportProductVendor(http.Controller):
#     @http.route('/import_product_vendor/import_product_vendor/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/import_product_vendor/import_product_vendor/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('import_product_vendor.listing', {
#             'root': '/import_product_vendor/import_product_vendor',
#             'objects': http.request.env['import_product_vendor.import_product_vendor'].search([]),
#         })

#     @http.route('/import_product_vendor/import_product_vendor/objects/<model("import_product_vendor.import_product_vendor"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('import_product_vendor.object', {
#             'object': obj
#         })