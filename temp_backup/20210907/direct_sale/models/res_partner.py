# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class res_partner(models.Model):
    _inherit = "res.partner"
    
    @api.multi
    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''

            if partner.company_name or partner.parent_id:
                if not name and partner.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            if self._context.get('show_street') and partner.street:
                name = "%s" % (partner.street)
            res.append((partner.id, name))
        return res    
    
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