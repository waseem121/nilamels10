# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class CustomerDivision(models.Model):
    _name = 'customer.division'
    
    name = fields.Char(default='Name')
    
class VendorDepartment(models.Model):
    _name = 'customer.department'
    
    name = fields.Char(default='Name')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: