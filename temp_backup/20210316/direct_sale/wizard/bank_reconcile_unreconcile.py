from odoo import models, api


class AccountBankUnreconcile(models.TransientModel):
    _name = "account.bank.unreconcile"
    _description = "Account Bank Unreconcile"

    @api.multi
    def bank_unrec(self):
        context = dict(self._context or {})
        if context.get('active_ids', False):
            self.env['account.move.line'].browse(context.get('active_ids')).write({'bank_reconcile':False})
        return {'type': 'ir.actions.act_window_close'}




class AccountBankReconcile(models.TransientModel):
    _name = "account.bank.reconcile"
    _description = "Account Bank Reconcile"

    @api.multi
    def bank_rec(self):
        context = dict(self._context or {})
        if context.get('active_ids', False):
            self.env['account.move.line'].browse(context.get('active_ids')).write({'bank_reconcile':True})
        return {'type': 'ir.actions.act_window_close'}
