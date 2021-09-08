# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import math

class AccountAccount(models.Model):
    _inherit = "account.account"
    
    serial_no = fields.Integer('Serial No', hep='Technial field to store the serial number for tha Account, so it can be used in sorting the accounts in reports.')
    
    @api.model
    def create(self, vals):
        account = super(AccountAccount, self).create(vals)
        if account.parent_id:
            account.action_generate_serial_no()
        return account

    @api.multi
    def write(self, vals):
        result = True
        old_parent_id = self.parent_id and self.parent_id.id or False
        result = super(AccountAccount, self).write(vals)
        
        if vals.get('parent_id'):
            if old_parent_id and (old_parent_id == vals.get('parent_id')):
                return result
            self.action_generate_serial_no()
        return result
    
    def action_generate_serial_no(self):
        print"action_generate_serial_no calledddddddddddddddd"
        account = self[0]
        print"Account: ",account
        parent = account.parent_id or False
        if not parent:
            raise UserError(_('Please Assign Parent Account.'))
        s1 = 0
        max_serial_account_ids = self.search([
                                ('parent_id','=',parent.id),
                                ('id','!=',self.id),
                                ('serial_no','>',parent.serial_no),
                                ], 
                                order='serial_no desc', limit=1)
        print"max_serial_account_ids: ",max_serial_account_ids
        if max_serial_account_ids:
            s1=max_serial_account_ids.serial_no
            print"S1 max: ",s1
        if s1==0:
            s1 += parent.serial_no
#            s1 = parent.serial_no + 1
        print"S1: ",s1
        serial = s1
        
        child_accounts = self.search([
                                ('id','!=',self.id),
                                ('parent_id','=',parent.id)])
        print"child_accounts: ",child_accounts
        # if not child accounts, add +1 to parent serial
        if not child_accounts:
            serial += 1
        else:
            # check max serial, and s1+s2 / 2
            all_max_serial_account_ids = self.search([
                                    ('id','!=',self.id),
                                    ('serial_no','!=',False),
                                    ('serial_no','>',serial)], 
                                    order='serial_no ASC', limit=1)
            print"all_max_serial_account_ids: ",all_max_serial_account_ids
            if all_max_serial_account_ids:
                s2 = all_max_serial_account_ids.serial_no
                print"S2: ",s2
                if s2:
                    serial = float((s1+s2) / 2.0)
                    serial = int(math.ceil(serial))
                    
        print"serial: ",serial
        # add 1+serial_no to all other accounts having serial no equal/greater than calculated serial
#        existing_serial_account = self.search([('serial_no','>=',serial), 
#                            ('serial_no','!=',False)],
#                            order='serial_no desc')
        existing_serial_account = self.search([('serial_no','=',serial),
                            ('serial_no','!=',False)],
                            order='serial_no desc')
        print"existing_serial_account: ",existing_serial_account
        if existing_serial_account:
            existing_serial_account = self.search([('serial_no','>=',serial), 
                                ('serial_no','!=',False)],
                                order='serial_no desc')
            for acc in existing_serial_account:
                acc.with_context({'serial_update':True}).write({'serial_no':acc.serial_no+1})
                print"updated old account serial to +1"
            
        print"serialLast: ",serial
        self.with_context({'serial_update':True}).write({'serial_no':serial})
        return True
    
    def action_generate_serial_no_old(self):
        print"action_generate_serial_no calledddddddddddddddd"
        account = self[0]
        print"Account: ",account
        parent = account.parent_id or False
        if not parent:
            raise UserError(_('Please Assign Parent Account.'))
        s1 = 0
        max_serial_account_ids = self.search([
                                ('parent_id','=',parent.id),
                                ('id','!=',self.id)], 
                                order='serial_no desc', limit=1)
        print"max_serial_account_ids: ",max_serial_account_ids
        if max_serial_account_ids:
            s1=max_serial_account_ids.serial_no
            print"S1 max: ",s1
        if s1==0:
            s1 += parent.serial_no
        print"S1: ",s1
        serial = s1
        
        child_accounts = self.search([
                                ('id','!=',self.id),
                                ('parent_id','=',parent.id)])
        print"child_accounts: ",child_accounts
        # if not child accounts, add +1 to parent serial
        if not child_accounts:
            serial += 1
        else:
            # check max serial, and s1+s2 / 2
            all_max_serial_account_ids = self.search([
                                    ('id','!=',self.id),
                                    ('serial_no','!=',False),
                                    ('serial_no','>',serial)], 
                                    order='serial_no ASC', limit=1)
            print"all_max_serial_account_ids: ",all_max_serial_account_ids
            if all_max_serial_account_ids:
                s2 = all_max_serial_account_ids.serial_no
                print"S2: ",s2
                if s2:
                    serial = float((s1+s2) / 2.0)
                    serial = int(math.ceil(serial))
                    
        print"serial: ",serial
        # add 1+serial_no to all other accounts having serial no equal/greater than calculated serial
#        existing_serial_account = self.search([('serial_no','>=',serial), 
#                            ('serial_no','!=',False)],
#                            order='serial_no desc')
        existing_serial_account = self.search([('serial_no','=',serial),
                            ('serial_no','!=',False)],
                            order='serial_no desc')
        print"existing_serial_account: ",existing_serial_account
        if existing_serial_account:
            existing_serial_account = self.search([('serial_no','>=',serial), 
                                ('serial_no','!=',False)],
                                order='serial_no desc')
            for acc in existing_serial_account:
                acc.with_context({'serial_update':True}).write({'serial_no':acc.serial_no+1})
                print"updated old account serial to +1"
            
#        existing_serials = self.search([]).mapped('serial_no')
#        existing_serials = list(set(existing_serials))
#        print"existing_serials: ",existing_serials
#        if serial in existing_serials:
#            while serial in existing_serials:
#                serial += 1
        
        print"serialLast: ",serial
        self.with_context({'serial_update':True}).write({'serial_no':serial})
        return True