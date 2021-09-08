# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class AdjustDifferenceCostWizard(models.TransientModel):
    _name = "adjust.difference.cost.wizard"
    _description = "Adjust Difference Cost"

    calculation_method = fields.Selection(
        [('amount', 'By amount of the line'),
         ('qty', 'By line quantity')], string='Calculation method', required=True)

    @api.multi
    def action_calculate(self):
        self.ensure_one()
        calculation_method = self.calculation_method
        distribution_id = self.env.context['active_id']
        distribution = self.env['purchase.cost.distribution'].browse(distribution_id)
        difference = distribution.amount_total - distribution.calculated_amount_total
        
        if calculation_method == 'qty':
            self.env.cr.execute("select max(product_qty) from purchase_cost_distribution_line where distribution=%s" % (distribution.id,))
            value = self.env.cr.dictfetchall()[0]['max']
            
        elif calculation_method == 'amount':
            value = 0
            total_amount_list = []
            for line in distribution.cost_lines:
                total_amount_list.append(line.total_amount)
            if len(total_amount_list):
                value = max(total_amount_list)
        
        for x in distribution.cost_lines:
            if calculation_method == 'qty':
                if x.product_qty == value:
                    cost_difference = difference/x.product_qty
                    cost_difference = round(cost_difference, 4)
                    x.write({'cost_difference':cost_difference})
                    break
                    
            if calculation_method == 'amount':
                if x.total_amount == value:
                    cost_difference = difference/x.product_qty
                    cost_difference = round(cost_difference, 4)
                    x.write({'cost_difference':cost_difference})
                    break
        return True