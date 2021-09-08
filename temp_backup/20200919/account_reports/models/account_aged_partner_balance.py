# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta

class report_account_aged_partner(models.AbstractModel):
    _name = "account.aged.partner"
    _description = "Aged Partner Balances"

    def _format(self, value):
        if self.env.context.get('no_format'):
            return value
        currency_id = self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        return formatLang(self.env, value, currency_obj=currency_id)

    @api.model
    def _lines(self, context, line_id=None):
        lines = []
        results, total, amls = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines([self._context['account_type']], self._context['date_to'], 'posted', 30)
        for values in results:
            if line_id and values['partner_id'] != line_id:
                continue
            vals = {
                'id': values['partner_id'],
                'name': values['name'],
                'level': 0,
                'type': 'partner_id',
                'footnotes': context._get_footnotes('partner_id', values['partner_id']),
                'columns': [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': values['partner_id'] in context.unfolded_partners.ids,
            }
            vals['columns'] = map(self._format, vals['columns'])
            lines.append(vals)
            if values['partner_id'] in context.unfolded_partners.ids:
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name if aml.move_id.name else '/',
                        'move_id': aml.move_id.id,
                        'action': aml.get_model_id_and_name(),
                        'level': 1,
                        'type': 'move_line_id',
                        'footnotes': context._get_footnotes('move_line_id', aml.id),
                        'columns': [line['period'] == 6-i and self._format(line['amount']) or '' for i in range(7)],
                    }
                    lines.append(vals)
                vals = {
                    'id': values['partner_id'],
                    'type': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'footnotes': self.env.context['context_id']._get_footnotes('o_account_reports_domain_total', values['partner_id']),
                    'columns': [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']],
                    'level': 1,
                }
                vals['columns'] = map(self._format, vals['columns'])
                lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'level': 0,
                'type': 'o_account_reports_domain_total',
                'footnotes': context._get_footnotes('o_account_reports_domain_total', 0),
                'columns': [total[6], total[4], total[3], total[2], total[1], total[0], total[5]],
            }
            total_line['columns'] = map(self._format, total_line['columns'])
            lines.append(total_line)
        return lines


class report_account_aged_receivable(models.AbstractModel):
    _name = "account.aged.receivable"
    _description = "Aged Receivable"
    _inherit = "account.aged.partner"

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.aged.receivable'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_to': context_id.date_to,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'account_type': 'receivable',
        })
        return self.with_context(new_context)._lines(context_id, line_id)

    @api.model
    def get_title(self):
        return _("Aged Receivable")

    @api.model
    def get_name(self):
        return 'aged_receivable'

    @api.model
    def get_report_type(self):
        return self.env.ref('account_reports.account_report_type_nothing')

    def get_template(self):
        return 'account_reports.report_financial'


class account_context_aged_receivable(models.TransientModel):
    _name = "account.context.aged.receivable"
    _description = "A particular context for the aged receivable"
    _inherit = "account.report.context.common"

    fold_field = 'unfolded_partners'
    unfolded_partners = fields.Many2many('res.partner', 'aged_receivable_context_to_partner', string='Unfolded lines')

    def get_report_obj(self):
        return self.env['account.aged.receivable']

    def get_columns_names(self):
        return [_("Not due on %s") % self.date_to, _("0 - 30"), _("30 - 60"), _("60 - 90"), _("90 - 120"), _("Older"), _("Total")]

    @api.multi
    def get_columns_types(self):
        return ["number", "number", "number", "number", "number", "number", "number"]


class report_account_aged_payable(models.AbstractModel):
    _name = "account.aged.payable"
    _description = "Aged Payable"
    _inherit = "account.aged.partner"

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.aged.payable'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_to': context_id.date_to,
            'aged_balance': True,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'account_type': 'payable',
        })
        return self.with_context(new_context)._lines(context_id, line_id)

    @api.model
    def get_title(self):
        return _("Aged Payable")

    @api.model
    def get_name(self):
        return 'aged_payable'

    @api.model
    def get_report_type(self):
        return self.env.ref('account_reports.account_report_type_nothing')

    def get_template(self):
        return 'account_reports.report_financial'


class account_context_aged_payable(models.TransientModel):
    _name = "account.context.aged.payable"
    _description = "A particular context for the aged payable"
    _inherit = "account.report.context.common"

    fold_field = 'unfolded_partners'
    unfolded_partners = fields.Many2many('res.partner', 'aged_payable_context_to_partner', string='Unfolded lines')

    def get_report_obj(self):
        return self.env['account.aged.payable']

    def get_columns_names(self):
        return [_("Not due on %s") % self.date_to, _("0 - 30"), _("30 - 60"), _("60 - 90"), _("90 - 120"), _("Older"), _("Total")]

    @api.multi
    def get_columns_types(self):
        return ["number", "number", "number", "number", "number", "number", "number"]


class AccountAgedTrialBalance(models.TransientModel):
    _inherit = "account.aged.trial.balance"

    sales_man_id = fields.Many2one("res.users", string="Salesman")
    based_on_date = fields.Selection([
        ('due_date', 'Due Date'),
        ('invoice_date', 'Invoice Date')],
        string='Based on Date', default='invoice_date',
        help="Report based on Due date or the Invoice dates")


class ReportAgedPartnerBalance(models.AbstractModel):
    _inherit = 'report.account.report_agedpartnerbalance'
    
    def _get_invoice_totals(self, args_query, args_value, invoice_type):
#        print"invoice_type: ",invoice_type
#        print"args_query: ",args_query
#        print"args_value: ",args_value
        cr = self.env.cr
        if invoice_type=='invoice':
            new_query = '''SELECT sum(i.amount_total)
                FROM account_invoice i,res_partner p
                WHERE i.partner_id=p.id AND 
                i.type in ('out_invoice','out_refund') AND 
                i.refund_without_invoice!=True AND i.state='draft' AND 
                '''+args_query
            
        elif invoice_type == 'refund':
            new_query = '''SELECT sum(i.amount_total)
                FROM account_invoice i,res_partner p
                WHERE i.partner_id=p.id AND 
                i.type in ('out_invoice','out_refund') AND 
                i.refund_without_invoice=True AND i.state='draft' AND 
                '''+args_query
        cr.execute(new_query, args_value)
        invoice_totals =  cr.dictfetchall()
        amount = 0.0
        if invoice_totals:
            amount = invoice_totals[0]['sum'] or 0.0
#        print"amt: ",amount
        return amount

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        wiz_id = self.env['account.aged.trial.balance'].browse(self._context.get('active_id'))
        # 5/0
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            periods[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        print"periods: ",periods
        print"periods len: ",len(periods)

        res = []
        total = []
        cr = self.env.cr
        user_company = self.env.user.company_id
        user_currency = user_company.currency_id
        ResCurrency = self.env['res.currency'].with_context(date=date_from)
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        if wiz_id and wiz_id.sales_man_id:
            arg_list += (date_from, tuple(company_ids),str(wiz_id.sales_man_id.id))
        else:
            arg_list += (date_from, tuple(company_ids))
        if wiz_id and wiz_id.sales_man_id:
            query = '''
                SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
                FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
                WHERE (l.account_id = account_account.id)
                    AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND ''' + reconciliation_clause + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    AND res_partner.user_id = %s
                ORDER BY UPPER(res_partner.name)'''
            cr.execute(query, arg_list)
        else:
            query = '''
                    SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
                    FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
                    WHERE (l.account_id = account_account.id)
                        AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ''' + reconciliation_clause + '''
                        AND (l.date <= %s)
                        AND l.company_id IN %s
                    ORDER BY UPPER(res_partner.name)'''
            cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        print"partners: ",partners
        print"date from: ",date_from
        
#        invoices = self.env['account.invoice'].search([('user_id','=',wiz_id.sales_man_id.id),
#                    ('date_invoice','<=',date_from)
#                    ])
#        invoices = self.env['account.invoice'].search([('number','=','2020/00183')
#                    ])

        if wiz_id.sales_man_id:
            new_query = '''SELECT p.id AS partner_id,UPPER(p.name) 
                        FROM res_partner p,res_users u
                        WHERE p.user_id=u.id AND
                        u.id=%s
                        '''
            cr.execute(new_query, (wiz_id.sales_man_id.id,))
        else:
            new_query = '''SELECT id AS partner_id,UPPER(name) 
                        FROM res_partner 
                        WHERE customer=True
                        '''
            cr.execute(new_query)

        invoices_partner =  cr.dictfetchall()
#        print"invoices_partner: ",invoices_partner
#        partners += invoices_partner
        invoice_partner_ids = [partner_inv['partner_id'] for partner_inv in invoices_partner if partner_inv['partner_id']]
#        invoice_partner_ids = [1750]
#        invoice_partner_ids = [681]
#        invoice_partner_ids = [701]
        print"invoice_partner_ids: ",invoice_partner_ids
        
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
#        partner_ids = [1750]
#        partner_ids = [681]
#        partner_ids = [701]
        print"partner_idss : ",partner_ids
        print"date_from: ",date_from
        print"wiz_id.based_on_date: ",wiz_id.based_on_date
        
#        stop
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        if wiz_id.based_on_date == 'due_date':
            query = '''SELECT l.id
                                FROM account_move_line AS l, account_account, account_move am
                                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                                    AND (am.state IN %s)
                                    AND (account_account.internal_type IN %s)
                                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                                    AND (l.partner_id IN %s)
                                AND (l.date <= %s)
                                AND l.company_id IN %s'''
        else:
            query = '''SELECT l.id
                                FROM account_move_line AS l, account_account, account_move am
                                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                                    AND (am.state IN %s)
                                    AND (account_account.internal_type IN %s)
                                    AND (COALESCE(l.date,l.date_maturity) > %s)\
                                    AND (l.partner_id IN %s)
                                AND (l.date <= %s)
                                AND l.company_id IN %s'''            
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = ResCurrency._compute(line.company_id.currency_id, user_currency, line.balance)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount += ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)
            for partial_line in line.matched_credit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount -= ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            if wiz_id.based_on_date == 'due_date':
                dates_query = '(COALESCE(l.date_maturity,l.date)'
            else:
                dates_query = '(COALESCE(l.date,l.date_maturity)'
                
            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
#            if wiz_id and wiz_id.sales_man_id:
#                args_list += (date_from, tuple(company_ids),str(wiz_id.sales_man_id.id))
#            else:
            args_list += (date_from, tuple(company_ids))
            query = '''SELECT l.id
                                    FROM account_move_line AS l, account_account, account_move am
                                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                                        AND (am.state IN %s)
                                        AND (account_account.internal_type IN %s)
                                        AND (l.partner_id IN %s)
                                        AND ''' + dates_query + '''
                                    AND (l.date <= %s)
                                    AND l.company_id IN %s
                                    '''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if not partner_id:
                    continue
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = ResCurrency._compute(line.company_id.currency_id, user_currency, line.balance)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount += ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)
                for partial_line in line.matched_credit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount -= ResCurrency._compute(partial_line.company_id.currency_id, user_currency, partial_line.amount)

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)
#        print"history: ",history
        
        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
#                print"iii: ",i
#                print"total: ",total
#                print"values: ",values
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
                values['code'] = browsed_partner.property_account_receivable_id and browsed_partner.property_account_receivable_id.code or ''
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False
                values['code'] = ''
#            print"valuess: ",values

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
#        t_dict = {'direction': 0.0, 'trust': u'normal', 'name': u'Waseem', '1': 0.0, '0': 0.0, '3': 0.0, '2': 0.0, '4': -5.0, 'total': -5.0, 'partner_id': 1373}

#        print"invoice_partner_ids last8888888888888888: ",invoice_partner_ids
        total_amount = 0
        for partner_id in invoice_partner_ids:
            
            not_due_added=False
            for i in range(5):
                if not not_due_added:
                    not_due_added=True
                    
                    if wiz_id.based_on_date == 'due_date':
#                        args_query = ('p.id=%s AND i.date_due>=%s')
                        args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)<=%s')
                        args_value = (partner_id,date_from)
                    else:
                        # TODO 
#                        args_query = ('p.id=%s AND i.date_invoice>=%s')
                        args_query = ('p.id=%s AND i.date_invoice>%s AND i.date_invoice<=%s')
                        args_value = (partner_id,date_from,date_from)
                        
                    partner = self.env['res.partner'].browse(partner_id)
                        
#                    args_value = (partner_id,date_from)
                    dict_res = {}
                    amount = self._get_invoice_totals(args_query,args_value,'invoice')
                    print"invoice amount: ",amount

                    # refunds
                    refund_amount = self._get_invoice_totals(args_query,args_value,'refund')
                    print"refund_amount: ",refund_amount

                    amount -= refund_amount
                    if float(amount) == 0.0:
                        print"amount zero skip00"
                        continue

                    partner_found =False
#                    print"ress: ",res
                    for d in res:
                        i= str(i)
                        print"iiii: ",i
                        if partner_id == d['partner_id']:
                            d['direction']+=amount
                            d['total']+=amount
                            partner_found=True

                    print"partner_found: ",partner_found
                    if not partner_found:
                        dict_res['direction']= amount   #Not due
                        dict_res['trust']= 'normal'
                        dict_res['code'] = partner.property_account_receivable_id and partner.property_account_receivable_id.code or ''
                        dict_res['name']= partner.name
                        dict_res['0']= 0    #+120
                        dict_res['1']= 0    #90-120
                        dict_res['2']= 0    #60-90
                        dict_res['3']= 0    #30-60
                        dict_res['4']= 0   #0-30

#                        dict_res[i] += amount
#                        dict_res['total'] += amount
                        dict_res['total'] = amount
                        dict_res['partner_id']= partner_id
                        res.append(dict_res)
                        
                    total[5] += amount
                    total[6] += amount
                    
                    
                    
                    
                    
                print"i called: ",i
                if wiz_id.based_on_date == 'due_date':
#                    args_query = ('p.id=%s AND i.date_due<=%s')
#                    args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)>=%s')
                    args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)<=%s')
                else:
                    args_query = ('p.id=%s AND i.date_invoice<=%s')
                    
                args_value = (partner_id,date_from)

                if periods[str(i)]['start'] and periods[str(i)]['stop']:
                    if wiz_id.based_on_date == 'due_date':
                        args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)>=%s AND COALESCE(i.date_due,i.date_invoice)<=%s')
                    else:
                        args_query = ('p.id=%s AND i.date_invoice>=%s AND i.date_invoice<=%s')
                    args_value = (partner_id,periods[str(i)]['start'], periods[str(i)]['stop'])
                elif periods[str(i)]['start']:
                    if wiz_id.based_on_date == 'due_date':
                        args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)>=%s')
                    else:
                        args_query = ('p.id=%s AND i.date_invoice>=%s')
                    args_value = (partner_id,periods[str(i)]['start'])
                else:
                    if wiz_id.based_on_date == 'due_date':
                        args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)<=%s')
                    else:
                        args_query = ('p.id=%s AND i.date_invoice<=%s')
                    args_value = (partner_id,periods[str(i)]['stop'])

            
                partner = self.env['res.partner'].browse(partner_id)
                dict_res = {}
                amount = self._get_invoice_totals(args_query,args_value,'invoice')
                print"inv amount: ",amount

                # refunds
                refund_amount = self._get_invoice_totals(args_query,args_value,'refund')
                print"refund_amount: ",refund_amount
                
                amount -= refund_amount
                print"amount after substracting: ",amount
                if float(amount) == 0.0:
                    print"amount zero skip"
                    continue


                partner_found =False
                for d in res:
                    i= str(i)
                    if partner_id == d['partner_id']:
                        d[i] += amount
#                        d['direction']+=amount
                        d['total']+=amount
                        partner_found=True
                        
                print"partner_found: ",partner_found
                if not partner_found:
                    dict_res['direction']= 0   #Not due
                    dict_res['trust']= 'normal'
                    dict_res['code'] = partner.property_account_receivable_id and partner.property_account_receivable_id.code or ''
                    dict_res['name']= partner.name
                    dict_res['0']= 0    #+120
                    dict_res['1']= 0    #90-120
                    dict_res['2']= 0    #60-90
                    dict_res['3']= 0    #30-60
                    dict_res['4']= 0   #0-30

                    dict_res[str(i)] = amount
#                    dict_res['total'] += amount
                    dict_res['total'] = amount
                    dict_res['partner_id']= partner_id
                
                    res.append(dict_res)
                    
                    
                    
                    
                print"total00: ",total
                i = int(i)
#                print"total00 ii: ",total[i]
                total[i] += amount
                total_amount+=amount
        print"total_amount: ",total_amount
#        print"res: ",res
#        print"total: ",total
#        print"lines: ",lines

        total[5]+=total_amount
#        total[6]+=total_amount
        return res, total, lines

