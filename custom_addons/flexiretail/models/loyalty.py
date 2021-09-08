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
from datetime import datetime


class loyalty_group(models.Model):
    _name = 'loyalty.group'

    @api.model
    def _get_currency_id(self):
        company_id = self.env['res.users'].browse([self._uid]).company_id
        if company_id and company_id.currency_id:
            return company_id.currency_id.id

    @api.one
    @api.constrains('customer_ids', 'employee_ids')
    def check_padding(self):
        if self.customer_ids:
            for customer in self.customer_ids:
                for group in self.search([('id', '!=', self.id),
                                          ('type', '=', self.type)]):
                    if customer in group.customer_ids:
                        raise Warning(_('%s customer exists into %s group.' % (customer.name, group.name)))
        elif self.employee_ids:
            for employee in self.employee_ids:
                for group in self.search([('id', '!=', self.id),
                                          ('type', '=', self.type)]):
                    if employee in group.employee_ids:
                        raise Warning(_('%s employee exists into %s group.' % (employee.name, group.name)))

    @api.model
    def create(self,vals):
        res = super(loyalty_group, self).create(vals)
        if vals.get('customer_ids'):
            for customer in vals.get('customer_ids')[0][2]:
                self.env['res.partner'].browse(customer).write({'group_name':res.id})
        if vals.get('employee_ids'):
            for customer in vals.get('employee_ids')[0][2]:
                self.env['res.partner'].browse(customer).write({'group_name':res.id})
        return res

    name = fields.Char(string="Group Name")
    type = fields.Selection([('employee_group', 'Employee'),
                             ('customer_group', 'Customer'),
                             ('ref_customer_group', 'Referral Customer')],
                             string="Group Type", default="customer_group")
    customer_ids = fields.Many2many('res.partner', 'loyalty_partner_relation',
                                    'loyalty_id', 'partner_id',string='Customers')
    employee_ids = fields.Many2many('hr.employee', 'loyalty_employee_relation',
                                    'loyalty_id', 'employee_id', string="Employees")
    is_perpetuity = fields.Boolean(string='Is Perpetuity')
    ref_cust_maximum_points = fields.Float(string="Maximum Points to Referral")
    customer_loyalty_point = fields.Float(string="Customer Loyalty")
    employee_loyalty_point = fields.Float(string="Employee Sales Commission")
    referral_customer_point = fields.Float(string="Referral Customer Loyalty")
    points = fields.Integer(string="Points", default=1)
    to_amount = fields.Float(string="To Amount")
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_currency_id, readonly=True)
    minimum_purchase = fields.Integer('Minimum Purchase')
    mini_pur_currency = fields.Many2one('res.currency', string='Currency',
                                        default=_get_currency_id, readonly=True)
    minimum_return = fields.Integer('Minimum Return')


class res_partner(models.Model):
    _inherit = 'res.partner'

    group_name = fields.Many2one("loyalty.group",string="Group Name");

    @api.multi
    @api.depends('partner_point_ids')
    def get_total_points(self):
        for each in self:
            for point_line in each.partner_point_ids:
                each.total_points += point_line.point

    @api.multi
    def get_total_points_discount(self):
        for each in self:
            for use_point in each.partner_point_used_ids:
                if use_point.sale_id or use_point.pos_order_id:
                    each.points_discount += use_point.point

    @api.multi
    def get_remaining_points(self):
        for each in self:
            each.remaining_points = each.total_points - (each.points_discount + each.points_redeem)

    @api.multi
    def get_total_points_redeem(self):
        for each in self:
            for use_point in each.partner_point_used_ids:
                if (use_point.order_name == "Cash Out") and not use_point.sale_id and not use_point.pos_order_id:
                    each.points_redeem += use_point.point

    @api.multi
    def get_computed_amount(self):
        group_obj = self.env['loyalty.group']
        for each in self:
            if each.remaining_points:
                group_id = group_obj.search([('type', '=', 'customer_group'),
                                             ('customer_ids', 'in', each.id)])
                if group_id:
                    rate = group_id.to_amount / group_id.points
                    each.points_to_amount = each.remaining_points * rate
                    each.per_point_amount = group_id.to_amount
                    each.single_point = group_id.points

    partner_point_ids = fields.One2many('res.partner.point', 'partner_id', string="Points")
    partner_point_used_ids = fields.One2many('res.partner.point.redeem', 'partner_id', string="Redeem Points")
    total_points = fields.Float(compute='get_total_points', string="Total Points")
    points_discount = fields.Float(compute='get_total_points_discount', string="Points (SO/POS)")
    points_redeem = fields.Float(compute='get_total_points_redeem', string="Points (Cash Out)")
    remaining_points = fields.Float(compute='get_remaining_points', string="Remaining Points")
    points_to_amount = fields.Float(compute="get_computed_amount", string="Points to Amount")
    single_point = fields.Float(compute="get_computed_amount", string="Point")
    per_point_amount = fields.Float(compute="get_computed_amount", string="Amount per Point")


class res_partner_point(models.Model):
    _name = "res.partner.point"
    _description = 'Customer Point'

    order_name =  fields.Char(string='Order Name', readonly=1)
    partner_id = fields.Many2one('res.partner', 'Member', readonly=1)
    ref_partner_id = fields.Many2one('res.partner', 'Member', readonly=1)
    pos_order_id = fields.Many2one('pos.order', 'POS Order', readonly=1)
    sale_id = fields.Many2one('sale.order', 'Sale Order', readonly=1)
    amount_total = fields.Float('Total Amount', readonly=1)
    date = fields.Datetime('Date', readonly=1, default=datetime.now())
    point = fields.Float('Point', readonly=1)


class res_partner_point_redeem(models.Model):
    _name = "res.partner.point.redeem"
    _description = 'Customer Point Redeem'

    partner_id = fields.Many2one('res.partner', 'Member', readonly=1)
    order_name =  fields.Char(string='Order Name')
    pos_order_id = fields.Many2one('pos.order', 'POS Order', readonly=1)
    sale_id = fields.Many2one('sale.order', 'Sale Order', readonly=1)
    amount_total = fields.Float('Total Amount', readonly=1)
    date = fields.Datetime('Date', readonly=1, default=datetime.now())
    point = fields.Float('Point', readonly=1)


class res_company(models.Model):
    _inherit = 'res.company'

    discount_account_id = fields.Many2one('account.account', string="Discount")
    cash_out_account_id = fields.Many2one('account.account', string="Cash Out")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: