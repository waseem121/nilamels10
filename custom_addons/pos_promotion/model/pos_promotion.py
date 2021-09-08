from openerp import fields, api, models, _
from openerp.exceptions import  Warning

import logging

class PosPromotion(models.Model):

    _name = "pos.promotion"
    __logger = logging.getLogger(_name)

#    @api.model
#    def auto_stop_promotion(self):
#        promotions = self.search([('state', '=', 'active')])
#        for pro in promotions:
#            if fields.Datetime.now() >= pro.end_dt:
#                pro.write({
#                    'state': 'reject'
#                })

    @api.multi
    def apply_promotion_for_all_config(self):
        configs = self.env['pos.config'].sudo().search([])
        for promotion in self:
            configs.sudo().write({
                'promotion_ids': [(4, [promotion.id])]
            })
        return 1

    @api.multi
    def remove_out_all_config(self):
        for record in self:
            record.sudo().write({
                'state': 'reject'
            })
        return 1


    type = fields.Selection([
        ('total_order', "Discount on Total Order"),
        ('gift_total_order', "Gift on Total Order"),
        ('discount_product', "Percent % from Products"),
        ('product_discount_money', "Discount Money Product"),
        ('product_detail', "Free product X when by Product Y"),
        ('product_category', "Discount on Categories Product"),
    ], string='Type', required=1, default='total_order')
    method = fields.Selection([
        ('percent', 'Percent (%)'),
        ('discount', 'Discount Money')
    ], 'Method', required=True, default='percent')
    product_id = fields.Many2one('product.product', "Promotion service", domain=[('type', '=', 'service'), ('available_in_pos', '=', True)], help='Product service of promotion')
    product_gift_ids = fields.One2many('pos.promotion.product.gift', 'promotion_id', string="Products Gift")
    product_discount_ids = fields.One2many('pos.promotion.product.discount', 'promotion_id', string="Products Discount")
    categ_ids = fields.One2many('pos.promotion.category', 'promotion_id', 'Categories Apply')
    promotion_line_ids = fields.One2many('pos.promotion.line', 'promotion_id', 'Rule Details')
    percent_total = fields.Float('Percent Total (%)', help='Percent % Total Order you want down')
    discount_total = fields.Float('Discount Total', help='Example: 1000 USD you want discount 20 USD, input 20 USD here.')
    min_total_order = fields.Float('Min Order', default=0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('reject', 'Canceled'),
    ], string='State', default='active')
    multi_discount_thesame_product = fields.Boolean('Multi Discount the same Product', help='Set true if you want set multi product the same have discount, example: Product A sale quantity 10 free Product B (1) quantity 30 free product C (2) sequence (2) > sequence (1) auto get discount free Product C', default=False)
    line_total_ids = fields.One2many('pos.promotion.line.total', 'promotion_id', 'Rules')
#    start_dt = fields.Datetime('Start date', required=1)
#    end_dt = fields.Datetime('End date', required=1)
    start_dt = fields.Datetime('Start date')
    end_dt = fields.Datetime('End date')


    @api.model
    def create(self, vals):
        if vals['percent_total'] > 100 or vals['percent_total'] < 0:
            raise Warning(_('Error, Percent total can not > 100 or < 0'))
        if vals['min_total_order'] < 0:
            raise Warning(_('Error, Min Order can not < 0'))
        return super(PosPromotion, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.has_key('percent_total') and vals['percent_total'] and (vals['percent_total'] > 100 or vals['percent_total'] < 0):
            raise Warning(_('Error, Percent total can gread or equal  100 and  smaller 0'))
        if vals.has_key('min_total_order') and vals['min_total_order'] and vals['min_total_order'] < 0:
            raise Warning(_('Error, Min Order can not smaller 0'))
        return super(PosPromotion, self).write(vals)

    @api.onchange
    def change_type(self):
        if self.type:
            self.name = self.type

class pos_promotion_line_total(models.Model):

    _name = "pos.promotion.line.total"

    total_from = fields.Float('Total from', required=1)
    total_to = fields.Float('Total to', required=1)
    value = fields.Float('Percent % or Money will Apply', required=1)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1)

    @api.model
    def create(self, vals):
        if vals['total_from'] < 0 or vals['total_to'] < 0 or vals['value'] < 0:
            raise Warning(_('Total from, Total to and Value can not smaller 0'))
        if vals['total_from'] > vals['total_to']:
            raise Warning(_('Total to can not smaller total from'))
        return super(pos_promotion_line_total, self).create(vals)

    @api.multi
    def write(self, vals):
        if (vals.get('total_from',False) and vals['total_from'] < 0) or (vals.get('total_to',False) and vals['total_to'] < 0) or (vals.get('value',False) and vals['value'] < 0):
            raise Warning(_('Total from, Total to and Value can not smaller 0'))
        
        total_from = vals.get('total_from',False) or self.total_from
        total_to = vals.get('total_to',False) or self.total_to
        if total_from > total_to:
            raise Warning(_('Total to can not smaller total from'))
        return super(pos_promotion_line_total, self).write(vals)


class promotion_line(models.Model):

    _name = "pos.promotion.line"

    product_from_id = fields.Many2one('product.product', 'Product', domain=[('available_in_pos', '=', True)], required=True)
    product_to_id = fields.Many2one('product.product', 'Gift', domain=[('available_in_pos', '=', True)], required=True)
    min_qty = fields.Integer('Min Qty', required=True)
    gift_qty = fields.Integer('Gift Qty', required=True)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion')

    _sql_constraints = [
        ('product_unique', 'unique (product_from_id)', 'This product have promotion gift before, if you need update, please remove old promotion.')
    ]

class PromotionProductGift(models.Model):
    _name = "pos.promotion.product.gift"

    product_id = fields.Many2one('product.product', 'Gift', domain=[('available_in_pos', '=', True)], required=True)
    qty = fields.Float('Quantity', required=True, default=1)
    price = fields.Float('Value Percent % or Money discount', required=True, default=0)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=True)


class PromotionProductDiscount(models.Model):
    _name = "pos.promotion.product.discount"

    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=True)
    product_id = fields.Many2one('product.product', 'Gift', domain=[('available_in_pos', '=', True)], required=True)
    qty = fields.Float('Quantity', required=True, default=1)
    percent = fields.Float('Percent %', required=True)


class PromotionCategory(models.Model):

    _name = "pos.promotion.category"

    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1)
    category_id = fields.Many2one('pos.category', 'Category', required=1)
    type = fields.Selection([
        ('percent', 'Percent %'),
        ('money', 'Money')
    ], string='Type', default='percent', required=1)
    discount = fields.Float('Discount', required=1)

class PromotionPack(models.Model):

    _name = "pos.promotion.pack"
    
    @api.multi
    def apply_pack_for_all_config(self):
        configs = self.env['pos.config'].sudo().search([])
        for pack in self:
            configs.write({
                'pack_ids': [(4, [pack.id])],
            })
            pack.sudo().write({'state': 'active', 'active': True})
        return True

    @api.multi
    def remove_pack_for_all_config(self):
        configs = self.env['pos.config'].sudo().search([])
        for pack in self:
            configs.write({
                'pack_ids': [(3, pack.id)],
            })
            pack.sudo().write({'state': 'reject', 'active': False})
            
        return True

    name = fields.Char('Pack Name', required=1)
    active = fields.Boolean('Active', default=1)
    product_apply_ids = fields.One2many('pos.promotion.pack.product.apply', 'pack_id', string='Products Apply')
    product_free_ids = fields.One2many('pos.promotion.pack.product.free', 'pack_id', string='Products Free')
    start_dt = fields.Datetime('Start date')
    end_dt = fields.Datetime('End date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('reject', 'Canceled'),
    ], string='State', default='draft')


class PromotionPackProductApply(models.Model):

    _name = "pos.promotion.pack.product.apply"

    product_id = fields.Many2one('product.product', 'Product', required=1, domain=[('available_in_pos', '=', True)])
    qty_apply = fields.Float('Quantity Apply')
    pack_id = fields.Many2one('pos.promotion.pack', 'Pack', required=1)

    _sql_constraints = [
        ('product_pack_unique', 'unique (product_id,pack_id)',
         'One pack can not great or equal 1 product the same')
    ]

class PromotionPackProductFree(models.Model):

    _name = "pos.promotion.pack.product.free"

    product_id = fields.Many2one('product.product', 'Product', required=1, domain=[('available_in_pos', '=', True)])
    qty_free = fields.Float('Quantity Free')
    pack_id = fields.Many2one('pos.promotion.pack', 'Pack', required=1)

    _sql_constraints = [
        ('product_pack_unique', 'unique (product_id,pack_id)',
         'One pack can not great or equal 1 product the same')
    ]









