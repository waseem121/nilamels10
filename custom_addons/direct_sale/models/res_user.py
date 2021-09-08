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

from odoo import models, fields, api, _


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.onchange('allowed_location_ids')
    def onchange_allowed_default_location(self):
        print "----------------------------"
        self.allowed_default_location = False
        if self.allowed_location_ids:
            return {'domain': {'allowed_default_location': [('id', 'in', [x.id for x in self.allowed_location_ids])]}}

    allowed_default_location = fields.Many2one('stock.location', string="Allowed Default Location")
