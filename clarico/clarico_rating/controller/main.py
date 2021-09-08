import json
import logging
from werkzeug.exceptions import Forbidden

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.website.models.website import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.addons.clarico_shop.controllers.main import claricoShop

        
class claricoRating(claricoShop):
    
    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        response = super(claricoRating, self).shop(page=page, category=category, search=search, **post)
        Rating = request.env['rating.rating']
        products = response.qcontext['products']
        rating_templates = {}
        for product in products :
            ratings = Rating.search([('message_id', 'in', product.website_message_ids.ids)])
            rating_message_values = dict([(record.message_id.id, record.rating) for record in ratings])
            rating_product = product.rating_get_stats([('website_published', '=', True)])
            rating_templates[product.id] = rating_product
        response.qcontext['rating_product'] = rating_templates
        return response   
    

