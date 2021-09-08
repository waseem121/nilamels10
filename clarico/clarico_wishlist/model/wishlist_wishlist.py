from odoo import models, fields, api
 
 
class wishlist_wishlist(models.Model):
    _name = 'wishlist.wishlist'
    _rec_name="id"   

    name= fields.Char( 'Wishlist Reference', readonly=True, )
    user_id=fields.Many2one('res.users','User')
    partner_id= fields.Many2one('res.partner', 'Customer')
    wishlist_ids= fields.One2many('wishlist.wishlist.line', 'wishlist_id', 'Wishlist Lines' )
