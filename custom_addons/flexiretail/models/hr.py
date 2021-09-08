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


class hr_employee_point(models.Model):
    _name = "hr.employee.point"
    _description = 'Employee Point'

    order_name =  fields.Char(string='Order Name', readonly=1)
    employee_id = fields.Many2one('hr.employee', 'Member', readonly=1)
    pos_order_id = fields.Many2one('pos.order', 'POS Order', readonly=1)
    sale_id = fields.Many2one('sale.order', 'Sale Order', readonly=1)
    amount_total = fields.Float('Total Amount', readonly=1)
    date = fields.Datetime('Date', readonly=1, default=datetime.now())
    point = fields.Float('Point', readonly=1)


class hr_employee_point_redeem(models.Model):
    _name = "hr.employee.point.redeem"
    _description = 'Employee Point Redeem'

    employee_id = fields.Many2one('hr.employee', 'Member', readonly=1)
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', readonly=1)
    payslip_name = fields.Char(related='payslip_id.name', store=True, string="Payslip Name", readonly=1)
    date = fields.Datetime('Date', readonly=1, default=datetime.now())
    point = fields.Float('Point', readonly=1)


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    @api.depends('employee_point_ids')
    def get_total_points(self):
        for each in self:
            for point_line in each.employee_point_ids:
                each.total_points += point_line.point

    @api.multi
    def get_total_points_redeem(self):
        for each in self:
            for pay_ship in each.employee_point_redeem_ids:
                if pay_ship.point:
                    each.points_redeem += pay_ship.point

    @api.multi
    def get_remaining_points(self):
        for each in self:
            each.remaining_points = each.total_points - each.points_redeem

    @api.multi
    def get_computed_amount(self):
        loyalty_group_obj = self.env['loyalty.group']
        for each in self:
            if each.remaining_points:
                group_id = loyalty_group_obj.search([('type', '=', 'employee_group'),
                                                     ('employee_ids', 'in', each.id)])
                if group_id:
                    rate = group_id.to_amount / group_id.points
                    each.points_to_amount = each.remaining_points * rate

    employee_point_ids = fields.One2many('hr.employee.point', 'employee_id', string="Points")
    employee_point_redeem_ids = fields.One2many('hr.employee.point.redeem', 'employee_id', string="Points")
    total_points = fields.Float(compute='get_total_points', string="Total Points")
    points_redeem = fields.Float(compute='get_total_points_redeem', string="Redeem Points")
    remaining_points = fields.Float(compute='get_remaining_points', string="Remaining Points")
    points_to_amount = fields.Float(compute="get_computed_amount", string="Amount to Points")


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    @api.depends('employee_id')
    def get_remaining_points(self):
        for each in self:
            if each.employee_id and each.employee_id.points_to_amount:
                each.points_to_used = each.employee_id.points_to_amount

    points_to_used = fields.Float(compute='get_remaining_points', string='Redeem Point Amount')

    @api.multi
    def process_sheet(self):
        if self.points_to_used > 0.0:
            red_points_data = {
                'employee_id': self.employee_id.id,
                'payslip_id':self.id,
                'payslip_name': self.name,
                'point': self.points_to_used,
            }
            self.env['hr.employee.point.redeem'].create(red_points_data)
        return self.write({'paid': True, 'state': 'done'})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: