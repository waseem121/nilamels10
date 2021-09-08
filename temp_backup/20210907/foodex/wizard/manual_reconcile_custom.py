# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class ManualReconcileCustom(models.TransientModel):
    _name = "manual.reconcile.custom"
    _description = "Manual Reconcile"

    @api.multi
    def reconcile(self):
        return {'type': 'ir.actions.act_window_close'}