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
import time,datetime

class aspl_gift_card(models.Model):
    _name = 'aspl.gift.card'
    _rec_name = 'card_no'
    _order = 'id'

    def random_cardno(self):
        return int(time.time())

    card_no =fields.Char(string="Card No", default=random_cardno, readonly=True)
    card_value=fields.Float(string="Card Value")
    card_type=fields.Many2one('aspl.gift.card.type',string="Card Type")
    customer_id = fields.Many2one('res.partner',string="Customer")
    issue_date=fields.Date(string="Issue Date", default=datetime.datetime.now())
    expire_date=fields.Date(string="Expire Date")
    is_active = fields.Boolean('Active',default=True)
    used_line= fields.One2many('aspl.gift.card.use','card_id',string="Used Line")
    recharge_line= fields.One2many('aspl.gift.card.recharge','card_id',string="Recharge Line")

    @api.multi
    def write(self,vals):
        return super(aspl_gift_card, self).write(vals)

class aspl_gift_card_use(models.Model):
    _name = 'aspl.gift.card.use'
    _rec_name = 'order_name'

    card_id=fields.Many2one('aspl.gift.card',string="Card", readonly=True)
    customer_id = fields.Many2one('res.partner',string="Customer")
    order_name =fields.Char(string="Order Name")
    order_date=fields.Date(string="Order Date")
    amount=fields.Float(string="amount")

class aspl_gift_card_recharge(models.Model):
    _name= 'aspl.gift.card.recharge'
    _rec_name = 'amount'

    card_id=fields.Many2one('aspl.gift.card',string="Card",readonly=True)
    customer_id = fields.Many2one('res.partner',string="Customer")
    recharge_date=fields.Date(string="Recharge Date")
    user_id = fields.Many2one('res.users',string="User")
    amount=fields.Float(string="amount")

class aspl_gift_card_type(models.Model):
    _name = 'aspl.gift.card.type'
    _rec_name = 'name'

    name =fields.Char(string="Name")
    code=fields.Char(string=" Code")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.depends('used_ids','recharged_ids')
    def compute_amount(self):
        total_used_amount = 0
        total_recharged_amount = 0
        for ids in self:
            for used_id in ids.used_ids:
                total_used_amount += used_id.amount
            for recharge_id in ids.recharged_ids:
                total_recharged_amount += recharge_id.amount
            ids.remaining_amount = total_recharged_amount - total_used_amount

    card_ids = fields.One2many('aspl.gift.card','customer_id',string="List of card")
    used_ids = fields.One2many('aspl.gift.card.use','customer_id',string="List of used card")
    recharged_ids = fields.One2many('aspl.gift.card.recharge','customer_id',string="List of recharged card")
    remaining_amount=fields.Char(compute = compute_amount ,string="Remaining Amount",readonly=True)

class account_journal(models.Model):
    _inherit="account.journal"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('pos_journal'):
            if self._context.get('journal_ids') and \
               self._context.get('journal_ids')[0] and \
               self._context.get('journal_ids')[0][2]:
               args += [['id', 'in', self._context.get('journal_ids')[0][2]]]
            else:
                return False;
        return super(account_journal, self).name_search(name, args=args, operator=operator, limit=limit)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: