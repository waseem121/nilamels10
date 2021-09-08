# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_inventory_adjustment_scrap_account = fields.Many2one(
        'account.account', string='Scrap(Damage) Adjustment Account',
        company_dependent=True,
        help="Define the Financial Accounts to be used as the balancing "
             "account in the transaction created by the inventory adjustment.")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_product_accounts(self, fiscal_pos=None):
        """ Add the stock journal related to product to the result of super()
        @return: dictionary which contains all needed information regarding stock accounts and journal and super (income+expense accounts)
        """
        accounts = super(ProductTemplate, self).get_product_accounts(fiscal_pos=fiscal_pos)
        # if self._context.get('damage_account'):
        if self._context.get('damage_account'):
            # print "----after context check self.categ_id.property_inventory_adjustment_scrap_account---", self.categ_id.property_inventory_adjustment_scrap_account
            if self.categ_id.property_inventory_adjustment_scrap_account:
                accounts.update(
                    {'stock_adjustment': self.categ_id.property_inventory_adjustment_scrap_account or False})
            else:
                raise Warning(_("Please set the 'scrap adjustment account' in %s.") % self.categ_id.name)
        # print "-------account-----", accounts.get('stock_adjustment')
        return accounts

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
