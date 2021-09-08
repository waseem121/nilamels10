# -*- coding: utf-8 -*-
from odoo import http

# class Provision(http.Controller):
#     @http.route('/provision/provision/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/provision/provision/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('provision.listing', {
#             'root': '/provision/provision',
#             'objects': http.request.env['provision.provision'].search([]),
#         })

#     @http.route('/provision/provision/objects/<model("provision.provision"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('provision.object', {
#             'object': obj
#         })