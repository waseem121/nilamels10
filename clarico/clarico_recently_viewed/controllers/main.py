import odoo
from odoo import http
from odoo import fields
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.clarico_wishlist.controller.main import claricoWishlist

class claricoRecentlyViewed(WebsiteSale):
    
    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **post):
        response = super(claricoRecentlyViewed, self).product(product=product, category=category, search=search, **post)
        recently_viewed_product_ids = self.update_recently_viewed_items(product.id)
        response.qcontext.update(active_id=product.id)
        if request.session['recently_viewed_product_ids'] :
            product = request.env['product.template'].search([('id','in',request.session['recently_viewed_product_ids'])])
            response.qcontext['recently_viewed_product'] = product
        return response
    
    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        response = super(claricoRecentlyViewed, self).cart(**post)
        recently_viewed_product_ids = request.session.get( 'recently_viewed_product_ids', False)
        if recently_viewed_product_ids :
            product = request.env['product.template'].search([('id','in',request.session['recently_viewed_product_ids'])])
            response.qcontext['recently_viewed_product'] = product
        return response
    

    def update_recently_viewed_items(self,product_id):
        recently_viewed_product_ids = request.session.get( 'recently_viewed_product_ids', False)
        if recently_viewed_product_ids :
            if product_id not in request.session['recently_viewed_product_ids'] :
                tmp = recently_viewed_product_ids
                tmp.append(product_id)    
                request.session['recently_viewed_product_ids'] = tmp
        else :
            request.session['recently_viewed_product_ids'] = [product_id]
        return request.session['recently_viewed_product_ids']
    
class claricoWishlist(claricoWishlist):  
    @http.route(['/wishlist'], type='http', auth="public", website=True)
    def wishproduct(self,page=0, category=None, search='', **kwargs):
        response = super(claricoWishlist, self).wishproduct(page=page, category=category, search=search, **kwargs)
        recently_viewed_product_ids = request.session.get('recently_viewed_product_ids', False)
        if recently_viewed_product_ids :
            product = request.env['product.template'].search([('id','in',request.session['recently_viewed_product_ids'])])
            response.qcontext['recently_viewed_product'] = product
        return response


   
