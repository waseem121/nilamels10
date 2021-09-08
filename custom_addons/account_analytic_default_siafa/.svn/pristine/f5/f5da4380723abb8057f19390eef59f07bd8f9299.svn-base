# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class account_move_line(models.Model):
    _inherit = "account.move.line"
    
    location_id = fields.Many2one('stock.location', string='Stock Location', help="Stock location if any for fetching analytic accounts.")
    
    @api.model
    def create(self, vals):
#        print "account_move_line create vals before: ",vals
        if not vals.get('analytic_account_id'):
            product_id = False
            section_id = False
#            location_id = False
            category_ids = []
            account_move = self.env['account.move']
            company_id = vals.get('company_id',False) or account_move.browse(vals['move_id']).company_id.id or self.env.user.company_id.id

            if vals.get('product_id',False):
                product_id = vals['product_id']
                product = self.env['product.product'].browse(product_id)

                categ_ids = {}
                categ = product.categ_id
                while categ:
                    categ_ids[categ.id] = True
                    categ = categ.parent_id
                category_ids = categ_ids.keys()
                
            if vals.get('move_id',False):
                account_move_obj = self.env['account.move']
                account_move = account_move_obj.browse(vals['move_id'])
#                ref = account_move.ref
                journal_id = account_move.journal_id.id
#                
            rec = self.env['account.analytic.default'].account_get(product_id=product_id, account_id=vals['account_id'], category_ids=category_ids, location_id=vals.get('location_id',False), journal_id=journal_id, company_id=company_id)
            if rec:
                vals['analytic_account_id'] = rec.analytic_id.id
#        print "account_move_line create vals after: ",vals
        return super(account_move_line, self).create(vals)
        