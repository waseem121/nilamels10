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


from odoo import fields, models, api, _

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_cpv = fields.Boolean(string="Is CPV")
    is_bpv = fields.Boolean(string="Is BPV")
    is_rv = fields.Boolean(string="Is Receipt Vourcher")