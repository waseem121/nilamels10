import odoo
from odoo import http
from odoo import fields
from odoo.http import request
from odoo import SUPERUSER_ID

from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.website.models.website import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.addons.website_sale.controllers.main import WebsiteSale

class claricoWishlist(http.Controller):   
    
    @http.route(['/wishlist_products'], type='json', auth="public", website=True)    
    def wlist(self,product_id=None, **kwargs):
        curr_user_id=request.env.user.id
        user_c = request.env['website'].sudo().search_count([['user_id.id','=',request.env.user.id]])
        if user_c != 0:
            return {'user':False};
        else:
            ids = request.env['wishlist.wishlist'].search([['user_id.id','=',request.env.user.id]])
            if product_id : 
                if not ids :
                    wishlist_create = request.env['wishlist.wishlist'].create({'user_id':curr_user_id,'wishlist_ids':[(0,0,{'product_id':product_id})]})
                else:
                    product_in_list = request.env['wishlist.wishlist.line'].search([('product_id.id','=',product_id),('wishlist_id.id','=',ids.id)])
                    if not product_in_list :
                        wishlist_line_id = request.env['wishlist.wishlist.line'].create({'product_id' : product_id,'wishlist_id' :ids.id})    
                      
                           
            if ids :                            
                select_product_list = []                                   
                wishcount = request.env['wishlist.wishlist.line'].search_count([['wishlist_id.id','=',ids.id]])                        
                wishbrowse = request.env['wishlist.wishlist.line'].search([['wishlist_id.id','=',ids.id]])                
                for wlid in wishbrowse:                    
                    select_product_list.append(wlid.product_id.id)            
            
            if not ids :                
                select_product_list = []                                   
                wishcount = request.env['wishlist.wishlist'].search_count([['user_id.id','=',request.env.user.id]])                        
                wishbrowse = request.env['wishlist.wishlist'].search([['user_id.id','=',request.env.user.id]])                
                for wlid in wishbrowse:                    
                    select_product_list.append(wlid.wishlist_ids.product_id.id)            
            return {'wishcount':wishcount,'wish_product':select_product_list};
        
             
    @http.route(['/login_web'], type='json', auth="public", website=True)    
    def login(self,userid=None,passwd=None,**kwargs):           
        uid = request.session.authenticate(request.session.db, str(userid), str(passwd))
        if uid == 0:
            return {'loginstatus':False,'userid':userid};
        else:
            return {'loginstatus':True,'userid':userid}
        
    @http.route(['/wishlist'], type='http', auth="public", website=True)
    def wishproduct(self,page=0, category=None, search='', **kwargs):
        ids = request.env['wishlist.wishlist'].search([['user_id.id','=',request.env.user.id]])
        product =request.env['wishlist.wishlist.line'].search([['wishlist_id.id','=',ids.id]])
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)
        
        Rating = request.env['rating.rating']
          
        rating_templates = {}
        compute_currency=""
        for product_t in product :
            products = request.env['product.template'].browse(product_t.product_id.id)          
            ratings = Rating.search([('message_id', 'in', products.website_message_ids.ids)])
            rating_message_values = dict([(record.message_id.id, record.rating) for record in ratings])
            rating_product = products.rating_get_stats([('website_published', '=', True)])
            rating_templates[products.id] = rating_product
            
        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: from_currency.compute(price, to_currency)
        
        products={
            'object': product,
            'compute_currency': compute_currency,
            'pricelist': pricelist,

            'rating_product': rating_templates,
            }
        return request.render("clarico_wishlist.clarico_wishlist_wishlist_template",products)
       
    @http.route(['/wishlist_products_popout'], type='json', auth="public", website=True)
    def wishpopout(self,page=0, category=None, search='', **kwargs):
            ids = request.env['wishlist.wishlist'].search([['user_id.id','=',request.env.user.id]])
            product =request.env['wishlist.wishlist.line'].search([['wishlist_id.id','=',ids.id]])
            
            pricelist = request.website.get_current_pricelist()
                
            from_currency = request.env.user.company_id.currency_id
            to_currency = pricelist.currency_id
            compute_currency = lambda price: from_currency.compute(price, to_currency)
            products={
                 'object': product,
                 'compute_currency': compute_currency,
                 }
            response = http.Response(template="clarico_wishlist.clarico_wishlist_popover_data",qcontext=products)            
            return response.render()
        
    @http.route(['/remove_wishlist_product'], type='json', auth="public", website=True)
    def wishremove(self,product_id=None,**kwargs):
        ids = request.env['wishlist.wishlist'].search([['user_id.id','=',request.env.user.id]])
        product = request.env['wishlist.wishlist.line'].search([['product_id.id','=',product_id]]).unlink()
        wishcount = request.env['wishlist.wishlist.line'].search_count([['wishlist_id.id','=',ids.id]])
        if wishcount == 0 :
            request.env['wishlist.wishlist'].search([['id','=',ids.id]]).unlink()
        return {'wishcount':wishcount};
    
    @http.route(['/removeall_wishlist_product'], type='json', auth="public", website=True)
    def wishremoveall(self,product_id=None,**kwargs):
        ids = request.env['wishlist.wishlist'].search([['user_id.id','=',request.env.user.id]])
        wishcount_null = request.env['wishlist.wishlist.line'].search([['wishlist_id','=',ids.id]]).unlink()
        wishcount = request.env['wishlist.wishlist.line'].search_count([['wishlist_id.id','=',ids.id]])
        if wishcount == 0 :
            request.env['wishlist.wishlist'].search([['id','=',ids.id]]).unlink()
        
    
    @http.route(['/wish_product_alert'], type='json', auth="public", website=True)    
    def wishalert(self,last_product_id=False,**kwargs):
        products = request.env['product.template'].search([['id','=',last_product_id]])
        values = {}
        values['product'] = products
        return request.env.ref("clarico_wishlist.clarico_wishlist_wishlist_product").render(values)
        
def rating_get_stats(self, domain=None):
        data = self.rating_get_repartition(domain=domain, add_stats=True)
        result = {
            'avg': data['avg'],
            'total': data['total'],
            'percent': dict.fromkeys(range(1, 11), 0),
        }
        for rate in data['repartition']:
            result['percent'][rate] = (data['repartition'][rate] * 100) / data['total'] if data['total'] > 0 else 0
        return result
