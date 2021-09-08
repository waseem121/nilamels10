# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class res_partner(models.Model):
    _inherit = "res.partner"
    
    is_salesman = fields.Boolean(string="Is Salesman?")
    is_collector = fields.Boolean(string="Is Collector?")
    vendor_group_id = fields.Many2one('vendor.group', string=_("Vendor Group"))
    customer_division_id = fields.Many2one('customer.division', string=_("Customer Division"))
    customer_department_id = fields.Many2one('customer.department', string=_("Customer Department"))
    customer_type = fields.Selection([('dental', 'Dental'),
                                    ('pharma', 'Pharma'),],
                                   string='Customer Type', default=False,
                                   help='For report based on customer group')
    customer_group = fields.Selection([('private', 'Private'),
                                       ('moh_institutes', 'Moh / Institutes'), ],
                                      string='Customer Group', default=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: