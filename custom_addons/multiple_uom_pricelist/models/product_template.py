# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from datetime import timedelta
from itertools import groupby
from odoo import _
from odoo import api
from odoo import fields
from odoo import models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_compare
from odoo.tools import float_is_zero
from odoo.tools import html2plaintext
from odoo.tools.misc import formatLang

class product_template_inherited(models.Model):
    _inherit = "product.template"

    def _get_default_uom_id(self):
        return self.env["product.uom"].search([], limit=1, order='id').id
		
    uom_so_id  = fields.Many2one('product.uom', 'Sale Unit of Measure', default=_get_default_uom_id, required=True)

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        if self.uom_id:
            self.uom_po_id = self.uom_id.id
            self.uom_so_id = self.uom_id.id


class Product_pricelist_items(models.Model):
	_inherit = "product.pricelist.item"

	uom_id = fields.Many2one('product.uom' , 'Pricelist UOM')

