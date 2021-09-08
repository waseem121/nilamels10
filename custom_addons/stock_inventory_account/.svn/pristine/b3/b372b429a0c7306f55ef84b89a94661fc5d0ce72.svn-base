from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_inventory_adjustment_account_categ = fields.Many2one(
        'account.account', string='Inventory Adjustment Account',
        company_dependent=True,
        help="Define the Financial Accounts to be used as the balancing "
             "account in the transaction created by the inventory adjustment. ")

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_product_accounts(self, fiscal_pos=None):
        """ Add the stock journal related to product to the result of super()
        @return: dictionary which contains all needed information regarding stock accounts and journal and super (income+expense accounts)
        """
        accounts = super(ProductTemplate, self).get_product_accounts(fiscal_pos=fiscal_pos)
        accounts.update({'stock_adjustment': self.categ_id.property_inventory_adjustment_account_categ or False})
        return accounts