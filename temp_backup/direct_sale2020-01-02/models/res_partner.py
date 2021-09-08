# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class CustomerDivision(models.Model):
    _name = 'customer.division'
    
    name = fields.Char(default='Name')
    
class VendorDepartment(models.Model):
    _name = 'customer.department'
    
    name = fields.Char(default='Name')

class res_partner(models.Model):
    _inherit = "res.partner"
    
    is_salesman = fields.Boolean(string="Is Salesman?")
    is_collector = fields.Boolean(string="Is Collector?")

    customer_division_id = fields.Many2one('customer.division', string=_("Customer Division"))
    customer_department_id = fields.Many2one('customer.department', string=_("Customer Department"))
   


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: