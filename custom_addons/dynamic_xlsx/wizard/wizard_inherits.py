# -*- coding: utf-8 -*-

from odoo import api, models, fields
import re

from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta


class InsFinancialReport(models.TransientModel):
    _inherit = "ins.financial.report"
    _description = "Financial Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.ins_financial_report_xlsx',
                'datas': {},
                'context': {}
                }


class InsGeneralLedger(models.TransientModel):
    _inherit = "ins.general.ledger"
    _description = "General Ledger Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.ins_general_ledger_xlsx',
                'datas': {},
                'context': {}
                }


class InsPartnerLedger(models.TransientModel):
    _inherit = "ins.partner.ledger"
    _description = "Partner Ledger Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.ins_partner_ledger_xlsx',
                'datas': {},
                'context': {}
                }


class InsPartnerAgeing(models.TransientModel):
    _inherit = "ins.partner.ageing"
    _description = "Partner Ageing Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.ins_partner_ageing_xlsx',
                'datas': {},
                'context': {}
                }


class InsTrialBalance(models.TransientModel):
    _inherit = "ins.trial.balance"
    _description = "Trial Balance Reports"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.ins_trial_balance_xlsx',
                'datas': {},
                'context': {}
                }
                
class ProductProfitReport(models.TransientModel):
    _inherit = "product.profit.report"
    _description = "Product Profit Report"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.product_profit_xlsx',
                'datas': {},
                'context': {}
                }
                
class BillsProfitReport(models.TransientModel):
    _inherit = "bills.profit.report"
    _description = "Bills Profit Report"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.bills_profit_xlsx',
                'datas': {},
                'context': {}
                }
                
class ProductStockReport(models.TransientModel):
    _inherit = "product.stock.report"
    _description = "Product Stock Report"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.product_stock_xlsx',
                'datas': {},
                'context': {}
                }
                
class ProductActivityReport(models.TransientModel):
    _inherit = "product.activity.report"
    _description = "Product Activity Report"

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        return {'type': 'ir.actions.report.xml',
                'report_name': 'dynamic_xlsx.product_activity_xlsx',
                'datas': {},
                'context': {}
                }