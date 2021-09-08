from odoo import models, api, _, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pri_ids = fields.One2many(comodel_name='prod.pri', inverse_name='pri_id', string='Product Units Barcodes')

    @api.model
    def create(self, vals):
        prod = super(ProductTemplate, self).create(vals)
        if self.pri_ids:
            for d in self.pri_ids:
                self.env['prod.pri'].browse(d.id).write({'br': self.barcode})
        return prod
    @api.multi
    def write(self, vals):
        prod = super(ProductTemplate, self).write(vals)
        if self.pri_ids:
            for d in self.pri_ids:
                self.env['prod.pri'].browse(d.id).write({'br': self.barcode})
        return prod

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

class prod_pri(models.Model):
    _name = 'prod.pri'
    _order = "amou desc"

    pri_id = fields.Many2one(comodel_name='product.template', string='Units', ondelete='cascade', required=False)
    amou = fields.Integer(string='Quantity')
    pri = fields.Float(string='Price')
    bar = fields.Char(string='Barcode')
    br = fields.Char(string='BARCODE')
    pri_id_uni = fields.Many2one(comodel_name='product.uom', string='Unit', ondelete='cascade', required=False)

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
