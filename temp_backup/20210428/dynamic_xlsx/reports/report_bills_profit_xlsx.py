# _*_ coding: utf-8
from odoo import models, fields, api, _

from datetime import datetime
try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
    from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
    ReportXlsx = object

DATE_DICT = {
    '%m/%d/%Y' : 'mm/dd/yyyy',
    '%Y/%m/%d' : 'yyyy/mm/dd',
    '%m/%d/%y' : 'mm/dd/yy',
    '%d/%m/%Y' : 'dd/mm/yyyy',
    '%d/%m/%y' : 'dd/mm/yy',
    '%d-%m-%Y' : 'dd-mm-yyyy',
    '%d-%m-%y' : 'dd-mm-yy',
    '%m-%d-%Y' : 'mm-dd-yyyy',
    '%m-%d-%y' : 'mm-dd-yy',
    '%Y-%m-%d' : 'yyyy-mm-dd',
    '%f/%e/%Y' : 'm/d/yyyy',
    '%f/%e/%y' : 'm/d/yy',
    '%e/%f/%Y' : 'd/m/yyyy',
    '%e/%f/%y' : 'd/m/yy',
    '%f-%e-%Y' : 'm-d-yyyy',
    '%f-%e-%y' : 'm-d-yy',
    '%e-%f-%Y' : 'd-m-yyyy',
    '%e-%f-%y' : 'd-m-yy'
}

class BillsProfitXlsx(ReportXlsx):
    _name = 'report.dynamic_xlsx.bills_profit_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
        """
        self.format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
            'border': False
        })
        self.format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            #'border': True
        })
        self.content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'border': True,
            'font': 'Arial',
        })
        self.content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': True,
            'align': 'center',
            'font': 'Arial',
        })
        self.line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'bottom': True,
            'font': 'Arial',
        })
        self.line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'text_wrap': True,
            'font': 'Arial',
            'valign': 'top'
        })
        self.line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        self.line_header_light_initial = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'bottom': True,
            'font': 'Arial',
            'valign': 'top'
        })
        self.line_header_light_ending = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'valign': 'top'
        })

    def prepare_report_filters(self, filter):
        print"prepare_report_filters called: ",filter
        """It is writing under second page"""
#        print"filtererrrrr ",filter
        self.row_pos_2 += 2
        if filter:
            date_from = filter.get('date_from',False)
            if not date_from:
                filter['date_from'] = '2020-01-01'
            date_to = filter.get('date_to',False)
            if not date_to:
                filter['date_to'] = '2020-12-31'
            filter['product_code'] = 'True'
                
            # Date from
            self.sheet_2.write_string(self.row_pos_2, 0, _('Date from'),
                                    self.format_header)
            self.sheet_2.write_datetime(self.row_pos_2, 1, self.convert_to_date(str(filter['date_from']) or ''),
                                    self.content_header_date)
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Date to'),
                                    self.format_header)
            self.sheet_2.write_datetime(self.row_pos_2, 1, self.convert_to_date(str(filter['date_to']) or ''),
                                    self.content_header_date)
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Category'),
                                    self.format_header)

            category_list = ', '.join([ c or '' for c in filter['category_list']])
            self.sheet_2.write_string(self.row_pos_2, 1, (str(category_list) or ''), self.line_header_light)
                                    
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Store'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['location']) or ''), 
                                    self.line_header_light)
            
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Salesman'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['salesman']) or ''), 
                                self.line_header_light)
            
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Division'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['division']) or ''), 
                            self.line_header_light)
            
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Department'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['department']) or ''), 
                            self.line_header_light)
            
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('SortBy'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['sort_by']) or ''), 
                    self.line_header_light)
            
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Based ON'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['based_on']) or ''), 
                            self.line_header_light)
            
            self.row_pos_2 += 1
#            self.sheet_2.write_string(self.row_pos_2, 0, _('Customer'),
#                                    self.format_header)
#            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['customer']) or ''), 
#                            self.line_header_light)            
            self.sheet_2.write_string(self.row_pos_2, 0, _('Account'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['account']) or ''), 
                            self.line_header_light)
            
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('State'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['state']) or ''), 
                        self.line_header_light)            
            
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('GroupBy'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, (str(filter['group_by']) or ''), 
                        self.line_header_light)


            # Products
#            self.row_pos_2 += 1
#            self.sheet_2.write_string(self.row_pos_2, 0, _('Products'),
#                                                 self.format_header)


    def prepare_report_contents(self, data, acc_lines, filter):
        print"prepare_report_contents called"
        data = data[0]
        self.row_pos += 3
        
#        print"prepare_report_contents acc_lines: \n\n\n",acc_lines

        self.sheet.write_string(self.row_pos, 0, _('Bill Number'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 1, _('Date'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 2, _('Customer'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 3, _('Total'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 4, _('Discount'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 5, _('Extras'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 6, _('Net Sales'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 7, _('Cost'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 8, _('Profit'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 9, _('Profit Percent Sales'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 10, _('Profit Percent Cost'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 11, _('Profit Percent Net Profit'),
                                self.format_header)
                                
        if acc_lines:
            for line in acc_lines:
                self.row_pos += 1
                if line.get('bill_no')!='Total':
#                    print"linee: ",line
                    self.sheet.write_string(self.row_pos, 0, line.get('bill_no'),
                                            self.line_header_light)
                    self.sheet.write_string(self.row_pos, 1, line.get('date'),
                                            self.line_header_light)
                    self.sheet.write_string(self.row_pos, 2, line.get('customer') or '',
                                            self.line_header_light)
                    self.sheet.write_number(self.row_pos, 3,
                                            float(line.get('total')),self.line_header_light)
                    self.sheet.write_number(self.row_pos, 4,
                                            float(line.get('discount')),self.line_header_light)
                    self.sheet.write_number(self.row_pos, 5,
                                            float(line.get('extras')),self.line_header_light)
                    self.sheet.write_number(self.row_pos, 6,
                                            float(line.get('net_sales')),self.line_header_light)
                    self.sheet.write_number(self.row_pos, 7,
                                            float(line.get('cost')),self.line_header_light)
                    self.sheet.write_number(self.row_pos, 8,
                                            float(line.get('profit')),self.line_header_light)
                    self.sheet.write_number(self.row_pos, 9,
                                            float(line.get('profit_percent_sales')),self.line_header_light)
                    self.sheet.write_number(self.row_pos, 10,
                                            float(line.get('profit_percent_cost')),self.line_header_light)
                    self.sheet.write_number(self.row_pos, 11,
                                            float(line.get('profit_percent_net_profit')),self.line_header_light)
            else:
                # totals
                self.row_pos += 1                                            
                self.sheet.merge_range(self.row_pos, 0, self.row_pos, 2, 'Total', self.line_header)
                self.sheet.write_string(self.row_pos, 3, line.get('total_sales'), self.line_header)
                self.sheet.write_string(self.row_pos, 4, line.get('total_discount'), self.line_header)
                self.sheet.write_string(self.row_pos, 5, line.get('total_extras'), self.line_header)
                self.sheet.write_string(self.row_pos, 6, line.get('total_net_sales'), self.line_header)
                self.sheet.write_string(self.row_pos, 7, line.get('total_cost'), self.line_header)
                self.sheet.write_string(self.row_pos, 8, line.get('total_profit'), self.line_header)

                                            
    def prepare_report_contents_group(self, data, acc_lines, filter):
        data = data[0]
        self.row_pos += 3
        
#        print"prepare_report_contents acc_lines: \n\n\n",acc_lines
        if filter.get('group_by') == 'salesman':
            self.sheet.write_string(self.row_pos, 0, _('Salesman'),
                                    self.format_header)
        if filter.get('group_by') == 'customer':
            self.sheet.write_string(self.row_pos, 0, _('Customer'),
                                    self.format_header)
#        self.sheet.write_string(self.row_pos, 1, _('Date'),
#                                self.format_header)
#        self.sheet.write_string(self.row_pos, 2, _('Customer'),
#                                self.format_header)
        self.sheet.write_string(self.row_pos, 1, _('Total'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 2, _('Discount'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 3, _('Extras'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 4, _('Net Sales'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 5, _('Cost'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 6, _('Profit'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 7, _('Profit Percent Sales'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 8, _('Profit Percent Cost'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 9, _('Profit Percent Net Profit'),
                                self.format_header)
                                
        if acc_lines:
            if filter.get('group_by') == 'customer':
                for line in filter.get('sorted_partner_ids'):
                    line = int(line)
                    if line=='Total':
                        continue
                    self.row_pos += 1
    #                self.sheet.merge_range(self.row_pos, 0, self.row_pos, 0, acc_lines[line].get('name'), self.line_header)
                    self.sheet.write_string(self.row_pos, 0, acc_lines[line].get('name'), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 1, float(acc_lines[line].get('total_sales')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 2, float(acc_lines[line].get('discount')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 3, float(acc_lines[line].get('extras')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 4, float(acc_lines[line].get('net_sales')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 5, float(acc_lines[line].get('cost')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 6, float(acc_lines[line].get('profit')), self.line_header_light)
            else:
                for line in acc_lines:
                    if line=='Total':
                        continue
                    self.row_pos += 1
    #                self.sheet.merge_range(self.row_pos, 0, self.row_pos, 0, acc_lines[line].get('name'), self.line_header)
                    self.sheet.write_string(self.row_pos, 0, acc_lines[line].get('name'), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 1, float(acc_lines[line].get('total_sales')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 2, float(acc_lines[line].get('discount')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 3, float(acc_lines[line].get('extras')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 4, float(acc_lines[line].get('net_sales')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 5, float(acc_lines[line].get('cost')), self.line_header_light)
                    self.sheet.write_number(self.row_pos, 6, float(acc_lines[line].get('profit')), self.line_header_light)                
#                self.sheet.merge_range(self.row_pos, 0, self.row_pos, 2, acc_lines[line].get('name'), self.line_header)
#                self.sheet.write_number(self.row_pos, 3, float(acc_lines[line].get('total_sales')), self.line_header)
#                self.sheet.write_number(self.row_pos, 4, float(acc_lines[line].get('discount')), self.line_header)
#                self.sheet.write_number(self.row_pos, 5, float(acc_lines[line].get('extras')), self.line_header)
#                self.sheet.write_number(self.row_pos, 6, float(acc_lines[line].get('net_sales')), self.line_header)
#                self.sheet.write_number(self.row_pos, 7, float(acc_lines[line].get('cost')), self.line_header)
#                self.sheet.write_number(self.row_pos, 8, float(acc_lines[line].get('profit')), self.line_header)
#
#
#                count, offset, sub_lines = self.record.build_detailed_move_lines(offset=0, categ_id=line,
#                                                                                 fetch_range=1000000)
#                                                                                 
#                for sub_line in sub_lines:
#                    self.row_pos += 1
#                    
#                    self.sheet.write_string(self.row_pos, 0, sub_line.get('bill_no'),
#                                            self.line_header_light)
#                    self.sheet.write_string(self.row_pos, 1, sub_line.get('date'),
#                                            self.line_header_light)
#                    self.sheet.write_string(self.row_pos, 2, sub_line.get('customer') or '',
#                                            self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 3,
#                                            float(sub_line.get('total')),self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 4,
#                                            float(sub_line.get('discount')),self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 5,
#                                            float(sub_line.get('extras')),self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 6,
#                                            float(sub_line.get('net_sales')),self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 7,
#                                            float(sub_line.get('cost')),self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 8,
#                                            float(sub_line.get('profit')),self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 9,
#                                            float(sub_line.get('profit_percent_sales')),self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 10,
#                                            float(sub_line.get('profit_percent_cost')),self.line_header_light)
#                    self.sheet.write_number(self.row_pos, 11,
#                                            float(sub_line.get('profit_percent_net_profit')),self.line_header_light)

            # totals
            self.row_pos += 1
#            self.sheet.merge_range(self.row_pos, 0, self.row_pos, 0, 'Total', self.line_header)
            self.sheet.write_string(self.row_pos, 0, 'Total', self.line_header)
            self.sheet.write_number(self.row_pos, 1, float(acc_lines['Total'].get('sales')), self.line_header)
            self.sheet.write_number(self.row_pos, 2, float(acc_lines['Total'].get('discount')), self.line_header)
            self.sheet.write_number(self.row_pos, 3, float(acc_lines['Total'].get('extras')), self.line_header)
            self.sheet.write_number(self.row_pos, 4, float(acc_lines['Total'].get('net_sales')), self.line_header)
            self.sheet.write_number(self.row_pos, 5, float(acc_lines['Total'].get('cost')), self.line_header)
            self.sheet.write_number(self.row_pos, 6, float(acc_lines['Total'].get('profit')), self.line_header)
#            self.sheet.merge_range(self.row_pos, 0, self.row_pos, 2, 'Total', self.line_header)
#            self.sheet.write_number(self.row_pos, 3, float(acc_lines['Total'].get('sales')), self.line_header)
#            self.sheet.write_number(self.row_pos, 4, float(acc_lines['Total'].get('discount')), self.line_header)
#            self.sheet.write_number(self.row_pos, 5, float(acc_lines['Total'].get('extras')), self.line_header)
#            self.sheet.write_number(self.row_pos, 6, float(acc_lines['Total'].get('net_sales')), self.line_header)
#            self.sheet.write_number(self.row_pos, 7, float(acc_lines['Total'].get('cost')), self.line_header)
#            self.sheet.write_number(self.row_pos, 8, float(acc_lines['Total'].get('profit')), self.line_header)
                                                                

    def _format_float_and_dates(self, currency_id, lang_id):
        print"_format_float_and_dates called"

        self.line_header.num_format = currency_id.excel_format
        self.line_header_light.num_format = currency_id.excel_format
        self.line_header_light_initial.num_format = currency_id.excel_format
        self.line_header_light_ending.num_format = currency_id.excel_format


        self.line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        self.content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

    def convert_to_date(self, datestring=False):
        print"convert_to_date called"
        if datestring:
            datestring = fields.Date.from_string(datestring).strftime(self.language_id.date_format)
            return datetime.strptime(datestring, self.language_id.date_format)
        else:
            return False

    def generate_xlsx_report(self, workbook, data, record):
        self._define_formats(workbook)
        self.row_pos = 0
        self.row_pos_2 = 0

        self.record = record # Wizard object

        self.sheet = workbook.add_worksheet('Bills Profit Report')
        self.sheet_2 = workbook.add_worksheet('Filters')
        self.sheet.set_column(0, 0, 18)
        self.sheet.set_column(1, 1, 12)
        self.sheet.set_column(2, 2, 30)
        self.sheet.set_column(3, 3, 10)
        self.sheet.set_column(4, 4, 10)
        self.sheet.set_column(5, 5, 10)
        self.sheet.set_column(6, 6, 10)
        if record.group_by and record.group_by=='salesman':
            self.sheet.set_column(7, 7, 20)
            self.sheet.set_column(8, 8, 20)
            self.sheet.set_column(9, 9, 20)
        else:
            self.sheet.set_column(7, 7, 10)
            self.sheet.set_column(8, 8, 10)
            self.sheet.set_column(9, 9, 18)
        self.sheet.set_column(10, 10, 18)
        self.sheet.set_column(11, 11, 18)

            

        self.sheet_2.set_column(0, 0, 35)
        self.sheet_2.set_column(1, 1, 25)
        self.sheet_2.set_column(2, 2, 25)
        self.sheet_2.set_column(3, 3, 25)
        self.sheet_2.set_column(4, 4, 25)
        self.sheet_2.set_column(5, 5, 25)
        self.sheet_2.set_column(6, 6, 25)

        self.sheet.freeze_panes(4, 0)

        self.sheet.screen_gridlines = False
        self.sheet_2.screen_gridlines = False
        self.sheet_2.protect()

        # For Formating purpose
        lang = self.env.user.lang
        self.language_id = self.env['res.lang'].search([('code','=',lang)])[0]
        self._format_float_and_dates(self.env.user.company_id.currency_id, self.language_id)

        if record:
            data = record.read()
            self.sheet.merge_range(0, 0, 0, 8, 'Bills Profit Report'+' - '+data[0]['company_id'][1], self.format_title)
            self.dateformat = self.env.user.lang
#                filters, account_lines = record.get_report_datas()
#    #            # Filter section
#                self.prepare_report_filters(filters)
#    #            # Content section
#                self.prepare_report_contents(data, account_lines, filters)            

            filters, account_lines = record.get_report_datas()
            self.prepare_report_filters(filters)
            if record.group_by and record.group_by in ('salesman', 'customer'):
    #            # Content section
                self.prepare_report_contents_group(data, account_lines, filters)
            else:
                self.prepare_report_contents(data, account_lines, filters)

BillsProfitXlsx('report.dynamic_xlsx.bills_profit_xlsx','bills.profit.report')