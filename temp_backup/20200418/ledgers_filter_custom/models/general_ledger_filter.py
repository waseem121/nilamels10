from odoo import models, fields, api, _
import time
from odoo.exceptions import UserError
from odoo.tools.amount_to_text_en import amount_to_text
from datetime import date


class general_ledger_filter_custom(models.TransientModel):
    #     _name = "general.ledger.filter.custom"
    _inherit = "account.report.general.ledger"
    _description = "This filter is on accounts basis."

    account_ids = fields.Many2many('account.account', string="Accounts")
    analytic_account_ids = fields.Many2many('account.analytic.account', string="Analytic Accounts")
    portrait_wo_header = fields.Boolean(string="Internal Use", default=True)
    date_from = fields.Date(string="Start Date", default=time.strftime('%Y-01-01'))
    date_to = fields.Date(string="End Date", default=date.today())
    # ageing added on 2-may-2019 by Dhruvesh
    ageing = fields.Boolean(string="Ageing")

    def _print_report(self, data):
        data = self.pre_print_report(data)
        # ageing added on 2-may-2019 by Dhruvesh
        if not self.date_from:
            raise UserError(_("You must define a Start Date"))
        if not self.date_to:
            raise UserError(_("You must define a Start Date"))
        data['form'].update({'portrait_wo_header': self.portrait_wo_header, 
            'ageing': self.ageing, 'date_from':self.date_from,'date_to':self.date_to})
        if self.account_ids:
            data['form'].update({'account_ids': self.account_ids.ids, })
            ids = [val.id for val in self.account_ids]
            child_account_ids = self.env['account.account'].search([('parent_id', 'child_of', ids)])
    #        child_account_ids = child_account_ids.filtered(lambda a: a.type != 'view')
            data['form'].update({'account_ids': child_account_ids.ids, })
            
        if self.analytic_account_ids:
            data['form'].update({'analytic_account_ids': self.analytic_account_ids.ids})
        if not self.portrait_wo_header:
            return super(general_ledger_filter_custom, self)._print_report(data)
        else:
            data['form'].update(self.read(['initial_balance', 'sortby'])[0])
            if data['form'].get('initial_balance') and not data['form'].get('date_from'):
                raise UserError(_("You must define a Start Date"))
            records = self.env[data['model']].browse(data.get('ids', []))
            return self.env['report'].get_action(records, 'account.report_generalledger',
                                                 data=data)


class ReportGeneralLedger(models.AbstractModel):
    _inherit = 'report.account.report_generalledger'
    
    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account, anyalytic_account=None):
        
#        # for view type of account, pull its child accounts
#        print"accounts: ",accounts
#        ids = [val.id for val in accounts]
#        child_account_ids = self.env['account.account'].search([('parent_id', 'child_of', ids)])
##        child_account_ids = child_account_ids.filtered(lambda a: a.type != 'view')
#        print"child_account_ids: ",child_account_ids
#        accounts = child_account_ids
            
        
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = dict(map(lambda x: (x, []), accounts.ids))


        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s""" + filters)
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            if anyalytic_account:
                sql += """ AND l.analytic_account_id IN (%s)""" % (','.join(map(str, anyalytic_account)))

            sql += """ GROUP BY l.account_id """
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id,l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE l.account_id IN %s ''' + filters)
        params = (tuple(accounts.ids),) + tuple(where_params)

        if anyalytic_account:
            sql += """ AND l.analytic_account_id IN (%s)""" % (','.join(map(str, anyalytic_account)))

        sql += ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort

        cr.execute(sql, params)
        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
                amount_text = amount_to_text(res['balance'], currency=currency.name)
                if currency.name == 'KWD':
                    amount_text = amount_text.replace('Cent', 'Fills')
                    amount_text = amount_text.replace('Cents', 'Fills')
                    amount_text = amount_text.replace('Filss', 'Fills')
                res['balance_words'] = amount_text
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
#        print "Geneal Ledger account_res: ",account_res
        return account_res

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]

        obj_account = self.env['account.account']
        get_accounts = data['form']['account_ids'] if data['form'].has_key('account_ids') else 0
        if get_accounts:
            accounts = obj_account.browse(get_accounts)
            
#            ids = [val.id for val in accounts]
#            child_account_ids = self.env['account.account'].search([('parent_id', 'child_of', ids)])
#    #        child_account_ids = child_account_ids.filtered(lambda a: a.type != 'view')
#            print"child_account_ids: ",child_account_ids
#            accounts = child_account_ids
        else:
            accounts = self.env['account.account'].search([])
            accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])

        anyalytic_account = None
        # if self._context.get('from_single_journal'):
        #     anyalytic_account = data['form'].get('analytic_account_ids') if data['form'].get('analytic_account_ids') else self.env['account.analytic.account'].search([]).ids
        if data['form'].get('analytic_account_ids'):
            anyalytic_account = data['form'].get('analytic_account_ids')
        
        accounts_res = self.with_context(data['form'].get('used_context', {}))._get_account_move_entry(accounts,
                                                                                                       init_balance,
                                                                                                       sortby,
                                                                                                       display_account,
                                                                                                      anyalytic_account)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
            'start_date': data['form'].get('date_from'),
            # ageing added on 2-may-2019 by Dhruvesh
            'ageing': data['form']['ageing'],
        }
        return self.env['report'].render('account.report_generalledger', docargs)
