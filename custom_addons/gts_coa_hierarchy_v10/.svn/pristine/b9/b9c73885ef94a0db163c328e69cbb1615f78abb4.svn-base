from openerp import api, models, fields
from operator import itemgetter
from openerp.osv import expression


class account_account(models.Model):
    _inherit='account.account'

    @api.multi
    def check_cycle(self):
        """ climbs the ``self._table.parent_id`` chains for 100 levels or
        until it can't find any more parent(s)

        Returns true if it runs out of parents (no cycle), false if
        it can recurse 100 times without ending all chains
        """
        ids=self.ids
        cr=self.env.cr
        level = 100
        while len(ids):
            cr.execute('SELECT DISTINCT parent_id ' \
                       'FROM ' + self._table + ' ' \
                                               'WHERE id IN %s ' \
                                               'AND parent_id IS NOT NULL', (tuple(ids),))
            ids = map(itemgetter(0), cr.fetchall())
            if not level:
                return False
            level -= 1
        return True

#    def _search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
#        """ Override search() to put account type filter"""
#        if context is None: context = {}
#        if not context.get('view_all', False):
#            args.append(eval('[' + "'type'," + "'!=', 'view']"))
#        return super(account_account, self)._search(cr, user, args, offset=offset, limit=limit, order=order, context=context,
#                                                count=count, access_rights_uid=access_rights_uid)

    @api.one
    @api.depends('level', 'parent_id')
    def _get_level(self):
        for account in self:
            # we may not know the level of the parent at the time of computation, so we
            # can't simply do res[account.id] = account.parent_id.level + 1
            level = 0
            parent = account.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            self.level = level

    @api.multi
    def _get_children_and_consol(self):
        # this function search for all the children and all consolidated children (recursively) of the given account ids
        ids = [val.id for val in self]
        ids2 = self.search([('parent_id', 'child_of', ids)])
        return ids2

    @api.one
    def _get_child_ids(self):
        for record in self:
            if record.child_parent_ids:
                child_ids = [x.id for x in record.child_parent_ids]
                self.child_id = child_ids
            else:
                self.child_id = []

    @api.multi
    def __compute(self):
        """ compute the balance, debit and/or credit for the provided
        account ids
        Arguments:
        `ids`: account ids
        `field_names`: the fields to compute (a list of any of
                       'balance', 'debit' and 'credit')
        `arg`: unused fields.function stuff
        `query`: additional query filter (as a string)
        `query_params`: parameters for the provided query string
                        (__compute will handle their escaping) as a
                        tuple
        """
        query = ''
        query_params = ()
        field_names = ['debit','credit','balance']
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
            # by convention, foreign_balance is 0 when the account has no secondary currency, because the amounts may be in different currencies
            'foreign_balance': "(SELECT CASE WHEN currency_id IS NULL THEN 0 ELSE COALESCE(SUM(amount_currency), 0) END FROM account_account WHERE id IN (account_id)) as foreign_balance",
        }
        # get all the necessary accounts
        children_and_consolidated = self._get_children_and_consol()
        # compute for each account the balance/debit/credit from the move lines
        accounts = {}
        res = {}
        if children_and_consolidated:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY account_id"
            params = (tuple(children_and_consolidated._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            params = (tuple(children_and_consolidated._ids),) + tuple(where_params)
            self._cr.execute(request, params)

            for row in self._cr.dictfetchall():
                accounts[row['id']] = row

            # consolidate accounts with direct children
            children_and_consolidated = list(children_and_consolidated.ids)
            # children_and_consolidated.reverse()
            list(children_and_consolidated).reverse()
            brs = list(self.search([('id','in',children_and_consolidated)], order="id desc"))
            sums = {}
            currency_obj = self.env['res.currency']
            while brs:
                current = brs.pop(0)

                #                can_compute = True
                #                for child in current.child_id:
                #                    if child.id not in sums:
                #                        can_compute = False
                #                        try:
                #                            brs.insert(0, brs.pop(brs.index(child)))
                #                        except ValueError:
                #                            brs.insert(0, child)
                #                if can_compute:
                for fn in field_names:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
                    for child in current.child_id:
                        # FIX
                        if not sums.has_key(child.id):
                            sums.setdefault(child.id, {})[fn] = accounts.get(child.id, {}).get(fn, 0.0)
                        if sums.has_key(child.id) and not sums[child.id].has_key(fn):
                            sums.setdefault(child.id, {})[fn] = accounts.get(child.id, {}).get(fn, 0.0)
                        if child.company_id.currency_id.id == current.company_id.currency_id.id:
                            sums[current.id][fn] += sums[child.id][fn]
                        else:
                            sums[current.id][fn] += currency_obj.compute(self._cr, self._uid, child.company_id.currency_id.id,
                                                                         current.company_id.currency_id.id,
                                                                         sums[child.id][fn])

                # as we have to relay on values computed before this is calculated separately than previous fields

            for acc in self:
                res = sums.get(acc.id,{})
                acc.debit = res.get('debit',0.0)
                acc.credit = res.get('credit',0.0)
                acc.balance = res.get('balance', 0.0)


    type = fields.Selection([
        ('view', 'View'),
        ('other', 'Regular'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
        ('consolidation', 'Consolidation'),
        ('closed', 'Closed'),
    ], 'Account Type', help="The 'Internal Type' is used for features available on " \
                                            "different types of accounts: view can not have journal items, consolidation are accounts that " \
                                            "can have children accounts for multi-company consolidations, payable/receivable are for " \
                                            "partners accounts (for debit/credit computations), closed for depreciated accounts.")
    parent_id = fields.Many2one('account.account', 'Parent', domain=[('type' ,'=' ,'view')])
    level = fields.Integer(string='Account Level',compute=_get_level, store=True )
    child_parent_ids = fields.One2many('account.account', 'parent_id', 'Children')
    child_id = fields.Many2many("account.account",compute=_get_child_ids, string="Child Accounts")
    balance = fields.Float(string = "Balance", compute =__compute, multi='balance')
    credit = fields.Float(compute=__compute, string='Credit', multi='balance')
    debit = fields.Float(compute=__compute,string='Debit', multi='balance')

    _check_recursion = check_cycle
    _constraints = [
        (_check_recursion, 'Error!\nYou cannot create recursive accounts.', ['parent_id'])
    ]


class AccountAccountType(models.Model):
    _inherit = "account.account.type"

    type = fields.Selection([
        ('other', 'Regular'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
        ('view','View'),
        ('asset','Asset View'),
        ('liability','Liability View'),
        ('expense','Expense View'),
        ('income','Income View'),
    ], required=True, default='other',
        help="The 'Internal Type' is used for features available on "\
        "different types of accounts: liquidity type is for cash or bank accounts"\
        ", payable/receivable is for vendor/customer accounts.")
