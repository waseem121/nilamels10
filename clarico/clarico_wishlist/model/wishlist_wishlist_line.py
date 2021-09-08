from odoo import models, fields, api
 
class wishlist_wishlist_line(models.Model):
    _name = 'wishlist.wishlist.line'
            
    product_id=fields.Many2one('product.template', 'Product')
    wishlist_id=fields.Many2one('wishlist.wishlist', 'Wishlist')
