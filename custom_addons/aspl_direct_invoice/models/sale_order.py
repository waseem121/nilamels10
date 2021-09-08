
# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from openerp import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from itertools import groupby
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = 'sale.order'


    stock_location_id = fields.Many2one(comodel_name='stock.location',string="Location")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: