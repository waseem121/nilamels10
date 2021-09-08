# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import date
import datetime


class collection_report(models.TransientModel):
    _name = "collection.report"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    partner_id = fields.Many2one('res.partner', string='Collector', 
        domain=[('is_collector','=',True)], required=True)
    states = fields.Selection([('all', 'All'), ('posted', 'Posted')],
                        default='all',
                        string="States")

    @api.multi
    def generate_collection_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'date_from':self.date_from,
            'date_to':self.date_to,
        }
        return self.env['report'].get_action(self, 'weekly_account_report.collection_report_template', data=datas)
    
    
class report_weekly_account_report_collection_report_template(models.AbstractModel):
    _name = 'report.weekly_account_report.collection_report_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('weekly_account_report.collection_report_template')
        print"report: ",report
        docids = self.env[data['model']].browse(data['docids'])
        print"docids: ",docids
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'get_cash_collection':self.get_cash_collection,
        }
        return report_obj.render('weekly_account_report.collection_report_template', docargs)
    
    def get_cash_collection(self, obj):

        res = []
        move_obj = self.env['account.move']
        partner = obj.partner_id
        
        
        states = ('draft','posted')
        if obj.states == 'posted':
            states = ('posted',)
        print"states: ",states
        
#        self.env.cr.execute("select id from account_payment where collector_id=%s and "\
#            "state in %s and payment_type='inbound' and payment_date>=%s and payment_date<=%s order by id desc", (partner.id,states,obj.date_from,obj.date_to))
        self.env.cr.execute("select id from account_move where collector_id=%s and "\
            "state in %s and date>=%s and date<=%s order by date asc", (partner.id,states,obj.date_from,obj.date_to))
        query_results = self.env.cr.dictfetchall()

        balance = 0.0
        for each in query_results:
            each_dict = {}
            move = move_obj.browse(each.get('id'))

            date = move.date
            date = date.split('-')
            date = str(date[2])+'-'+str(date[1])+'-'+str(date[0])
            balance += move.amount
            each_dict['date'] = date
            each_dict['name'] = move.ref
            each_dict['customer'] = move.partner_id.name
            each_dict['amount'] = move.amount
            each_dict['balance'] = balance
            res.append(each_dict)
#        print"res: ",res
        return res
