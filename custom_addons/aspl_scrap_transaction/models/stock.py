from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _get_accounting_data_for_valuation(self):
        self.ensure_one()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        if not self.inventory_id or not accounts_data.get('stock_adjustment'):
            return journal_id, acc_src, acc_dest, acc_valuation

        ### If it is inventory adjustment move

        if self.location_id.usage == 'internal':
            acc_dest = accounts_data.get('stock_adjustment').id
        else:
            acc_src = accounts_data.get('stock_adjustment').id
        # print "journal_id, acc_src, acc_dest, acc_valuation: ", journal_id, acc_src, acc_dest, acc_valuation
        return journal_id, acc_src, acc_dest, acc_valuation


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    is_scrap_adjustment = fields.Boolean(string="Scrap Adjustment")
