# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import time

class stock_picking(models.Model):
    _inherit = "stock.picking"
    
    @api.multi
    def _get_account_analytic_invoice(self, picking, account_id, move_line):
        partner_id = picking and picking.partner_id and picking.partner_id.id or False
        company_id= (picking and picking.company_id.id ) or (move_line.company_id.id) or False
        
        categ_ids = {}
        categ = move_line.product_id.categ_id
        while categ:
            categ_ids[categ.id] = True
            categ = categ.parent_id
        categ_ids = categ_ids.keys()

        location_id = (move_line.location_id.usage == 'internal' and move_line.location_id.id) or \
                            (move_line.location_dest_id.usage == 'internal' and move_line.location_dest_id.id) or False
                        
        
        rec = self.env['account.analytic.default'].account_get(move_line.product_id.id, partner_id, user, time.strftime('%Y-%m-%d'), 
                        company_id=company_id, account_id=account_id, category_ids=categ_ids, location_id=location_id)

        if rec:
            return rec.analytic_id.id

        return False

class account_analytic_default(models.Model):
    _inherit = "account.analytic.default"
    
    account_id = fields.Many2one('account.account', 'Account', ondelete='cascade', help="Select an account which will use analytic account specified in analytic default.")
    journal_id = fields.Many2one('account.journal', 'Journal', ondelete='cascade', help="Select a journal which will use analytic account specified in analytic default.")
    category_id = fields.Many2one('product.category', 'Product Category', help="Select a category which will use analytic account specified in analytic default.")
    location_id = fields.Many2one('stock.location', 'Location', domain=[('usage', '=', 'internal')], help="Select a location which will use analytic account specified in analytic default.")
    
    
    @api.model
    def account_get(self, product_id=None, partner_id=None, user_id=None, date=None, company_id=None, account_id=False, category_ids=False, location_id=False, journal_id=False):
        domain = []
        if account_id:
            domain += ['|', ('account_id', '=', account_id)]
        domain += [('account_id','=', False)]
        if journal_id:
            domain += ['|', ('journal_id', '=', journal_id)]
        domain += [('journal_id','=', False)]
        if category_ids:
            if type(category_ids) != list:
                category_ids = [category_ids]
            domain += ['|', ('category_id', 'in', category_ids)]
        domain += [('category_id','=', False)]
        if location_id:
            domain += ['|', ('location_id', '=', location_id)]
        domain += [('location_id','=', False)]
        if product_id:
            domain += ['|', ('product_id', '=', product_id)]
        domain += [('product_id','=', False)]
        if partner_id:
            domain += ['|', ('partner_id', '=', partner_id)]
        domain += [('partner_id', '=', False)]
        if company_id:
            domain += ['|', ('company_id', '=', company_id)]
        domain += [('company_id', '=', False)]
        if user_id:
            domain += ['|',('user_id', '=', user_id)]
        domain += [('user_id','=', False)]
        if date:
            domain += ['|', ('date_start', '<=', date), ('date_start', '=', False)]
            domain += ['|', ('date_stop', '>=', date), ('date_stop', '=', False)]
        best_index = -1
        res = self.env['account.analytic.default']
        for rec in self.search(domain):
            index = 0
            if rec.account_id: index += 1
            if rec.category_id: index += 1
            if rec.location_id: index += 1
            if rec.product_id: index += 1
            if rec.partner_id: index += 1
            if rec.company_id: index += 1
            if rec.user_id: index += 1
            if rec.date_start: index += 1
            if rec.date_stop: index += 1
            if index > best_index:
                res = rec
                best_index = index
        return res