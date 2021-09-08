from odoo import http
from odoo.http import request
from odoo import SUPERUSER_ID
from odoo import models, fields, api


class claricoClearCart(http.Controller):

    @http.route(['/shop/clear_cart'], type='json', auth="public", methods=['POST'], website=True)
    def clear_cart(self, **kw):
        order = request.website.sale_get_order(force_create=1)
        order_line = request.env['sale.order.line'].sudo()
        line_ids = order_line.search([('order_id','=',order.id)])
        for line in line_ids :
            line_obj = order_line.browse([int(line)])
            if line_obj :
                line_obj.unlink()