import odoo
from odoo import http
from odoo import fields
from odoo.http import request
from odoo import SUPERUSER_ID
from odoo.addons.website.models.website import slug
from _ast import Compare
from __builtin__ import str


class claricoCompare(http.Controller):   
    
    @http.route(['/compare_product'], type='json', auth="public", website=True)    
    def clist(self, product_id=None, status=None, **kwargs):
        if product_id :
            pid = int(product_id)
            print status
            compare_template_ids = request.session.get('compare_template_ids', False)
    
            if compare_template_ids :
                if pid not in request.session.get('compare_template_ids') :
                    tmp = compare_template_ids
                    if status == True :
                        first_product = request.env['product.template'].browse(int(compare_template_ids[0]))
                        next_product = request.env['product.template'].search([['id', '=', product_id]])
                        print first_product.compare_product_id
                        if first_product.compare_product_id.id == next_product.compare_product_id.id: 
                            print next_product.compare_product_id.id
                            tmp.append(pid)
                        if not first_product.compare_product_id.id == next_product.compare_product_id.id:
                            return {"productcount":len(request.session['compare_template_ids']), "productids": request.session['compare_template_ids'],'productallow':False}    
                        request.session['compare_template_ids'] = tmp
                        return {"productcount":len(request.session['compare_template_ids']), "productids": request.session['compare_template_ids']}
                    
                    if not status:
                        return {"productcount":len(request.session['compare_template_ids']), "productids": request.session['compare_template_ids'],'productallow':False}
                     
                if pid in request.session.get('compare_template_ids') :      
                    if status == False :
                        tmp = compare_template_ids
                        tmp.remove(pid)
                        request.session['compare_template_ids'] = tmp
                        return {"productcount":len(request.session['compare_template_ids']), "productids": request.session['compare_template_ids']}
            else :
                compare_product = request.env['product.template'].search([['id', '=', product_id]])
                if compare_product.compare_product_id:
                    request.session['compare_template_ids'] = [pid]        
                    return {"productcount":len(request.session['compare_template_ids']), "productids": request.session['compare_template_ids']}
                if not compare_product.compare_product_id:
                    return {"productcount":0, "productids":'','productallow':False}
                    
        else :
            compare_template_ids = request.session.get('compare_template_ids', False)
            if compare_template_ids :
                return {"productcount":len(request.session['compare_template_ids']), "productids": request.session['compare_template_ids']}
            if not compare_template_ids :    
                return {"productcount":0, "productids":''}
    
    @http.route(['/compare'], type='http', auth="public", website=True)    
    def cproduct(self, **kwargs):
        compare_template_ids = request.session.get('compare_template_ids',False)
        product=""
        rating_templates = {}
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)
        
        products = {}
        
        if compare_template_ids :
            product = request.env['product.template'].browse(request.session['compare_template_ids'])
            Rating = request.env['rating.rating']                          
            for product_t in product :
                ratings = Rating.search([('message_id', 'in', product_t.website_message_ids.ids)])            
                rating_message_values = dict([(record.message_id.id, record.rating) for record in ratings])            
                rating_product = product_t.rating_get_stats([('website_published', '=', True)])            
                rating_templates[product_t.id] = rating_product  
                
            from_currency = request.env.user.company_id.currency_id
            to_currency = pricelist.currency_id
            compute_currency = lambda price: from_currency.compute(price, to_currency)
                      
            products = {
                'object': product,
                'compute_currency': compute_currency,
                'pricelist': pricelist,
                'rating_product': rating_templates,
            }
        return request.render("clarico_compare.clarico_compare_page_template", products)
        
    @http.route(['/compare_products_popout'], type='json', auth="public", website=True)    
    def comparepopout(self,page=0, category=None, search='', **kwargs):   
        compare_template_ids = request.session.get('compare_template_ids', False)        
        products = {}
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        if compare_template_ids :            
            product = request.env['product.template'].browse(request.session['compare_template_ids']) 
            
            from_currency = request.env.user.company_id.currency_id
            to_currency = pricelist.currency_id
            compute_currency = lambda price: from_currency.compute(price, to_currency)
            
            products={            
                'object': product, 
                'compute_currency': compute_currency,
                'pricelist': pricelist,           
            }        
        response = http.Response(template="clarico_compare.clarico_compare_popover_data",qcontext=products)                        
        return response.render()
    
           
    
