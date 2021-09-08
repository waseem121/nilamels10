from odoo.addons.report_xls.report.report_xls import ReportXls
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.tools.translate import _
import xlwt

_column_sizes = [
    ('date', 12),
    ('period', 12),
    ('move', 20),
    ('journal', 12),
    ('account_code', 12),
    ('partner', 30),
    ('label', 45),
    ('counterpart', 30),
    ('debit', 15),
    ('credit', 15),
    ('cumul_bal', 15),
    ('curr_bal', 15),
    ('curr_code', 7),
]
# styles
_pfc = '26'  # default pattern fore_color
_bc = '22'   # borders color
decimal_format = '#,##0.00'
date_format = 'YYYY-MM-DD'

xls_styles = {
    'xls_title': 'font: bold true, height 240;',
    'bold': 'font: bold true;',
    'underline': 'font: underline true;',
    'italic': 'font: italic true;',
    'fill': 'pattern: pattern solid, fore_color %s;' % _pfc,
    'fill_blue': 'pattern: pattern solid, fore_color 27;',
    'fill_grey': 'pattern: pattern solid, fore_color 22;',
    'borders_all':
        'borders: '
        'left thin, right thin, top thin, bottom thin, '
        'left_colour %s, right_colour %s, '
        'top_colour %s, bottom_colour %s;'
        % (_bc, _bc, _bc, _bc),
    'left': 'align: horz left;',
    'center': 'align: horz center;',
    'right': 'align: horz right;',
    'wrap': 'align: wrap true;',
    'top': 'align: vert top;',
    'bottom': 'align: vert bottom;',
    }
class ProfitAndLossXls(ReportXls):
    column_sizes = [x[1] for x in _column_sizes]
    
    
    def generate_xls_report(self, workbook, data, lines):
        print "inside generate_xlsx_report: ",data
        print "inside lines: ",lines
        start_date = data['date_from']
        end_date = data['date_to']
        
        sheet = workbook.add_sheet("Account Financial Report")
        sheet.panes_frozen = True
        sheet.remove_splits = True
        sheet.portrait = 0  # Landscape
        sheet.fit_width_to_pages = 1
        row_pos = 0
        
        # Title
        cell_style = xlwt.easyxf(xls_styles['xls_title'])
        report_name = data['report_name']
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            sheet, row_pos, row_data, row_style=cell_style)
        
        # write empty row to define column sizes
        c_sizes = self.column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None)
                   for i in range(0, len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            sheet, row_pos, row_data, set_column_size=True)
        
        # Header Table
        cell_format = xls_styles['bold'] + xls_styles['fill_blue'] + xls_styles['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + xls_styles['center'])
        c_specs = [
            ('tm', 2, 0, 'text', _('Target Moves')),
            ('fy', 2, 0, 'text', _('Date from')),
            ('df', 2, 0, 'text', _('Date to')),
            

        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            sheet, row_pos, row_data, row_style=cell_style_center)
        
        
        cell_format = xls_styles['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + xls_styles['center'])
        if start_date:
            start_date = start_date
        else:
            start_date = ''
        if end_date:
            end_date = end_date
        else:
            end_date = ''
        c_specs = [
            ('tm', 2, 0, 'text', data['target_moves_name']),
            ('fy', 2, 0, 'text', start_date),
            ('sb', 2, 0, 'text', end_date),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            sheet, row_pos, row_data, row_style=cell_style_center)
        sheet.set_horz_split_pos(row_pos)
        row_pos += 1
        
        # Column Title Row
        cell_format = xls_styles['bold']
        c_title_cell_style = xlwt.easyxf(cell_format)
        
        
        # Column Header Row
        cell_format = xls_styles['bold'] + xls_styles['fill'] + xls_styles['borders_all']
        c_hdr_cell_style = xlwt.easyxf(cell_format)
        c_hdr_cell_style_right = xlwt.easyxf(cell_format + xls_styles['right'])
        c_hdr_cell_style_center = xlwt.easyxf(cell_format + xls_styles['center'])
        c_hdr_cell_style_decimal = xlwt.easyxf(
            cell_format + xls_styles['right'],
            num_format_str=decimal_format)
            
        # Column Initial Balance Row
        cell_format = xls_styles['italic'] + xls_styles['borders_all']
        c_init_cell_style = xlwt.easyxf(cell_format)
        c_init_cell_style_decimal = xlwt.easyxf(
            cell_format + xls_styles['right'],
            num_format_str=decimal_format)
        
        
        # cell styles for ledger lines
        ll_cell_format = xls_styles['borders_all']
        ll_cell_style = xlwt.easyxf(ll_cell_format)
        ll_cell_style_center = xlwt.easyxf(ll_cell_format + xls_styles['center'])
        ll_cell_style_date = xlwt.easyxf(
            ll_cell_format + xls_styles['left'],
            num_format_str=date_format)
        ll_cell_style_decimal = xlwt.easyxf(
            ll_cell_format + xls_styles['right'],
            num_format_str=decimal_format)
        ll_cell_style_decimal_bold = xlwt.easyxf(
            ll_cell_format + xls_styles['right']+xls_styles['bold'],
            num_format_str=decimal_format)
            
        if data['debit_credit']:
            c_specs = [
                ('period', 3, 0, 'text', _('Name'), None, c_hdr_cell_style),
                ('debit', 1, 0, 'text', _('Debit'), None, c_hdr_cell_style_right),
                ('credit', 1, 0, 'text', _('Credit'),None, c_hdr_cell_style_right),
                ('cumul_bal', 1, 0, 'text', _('Balance'),None, c_hdr_cell_style_right),
            ]
            c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        elif not data['enable_filter'] and not data['debit_credit']:
            c_specs = [
                ('period', 3, 0, 'text', _('Name'), None, c_hdr_cell_style),
                ('cumul_bal', 3, 0, 'text', _('Balance'),None, c_hdr_cell_style_right),
            ]
            c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        elif data['enable_filter'] and not data['debit_credit']:
            c_specs = [
                ('period', 3, 0, 'text', _('Name'), None, c_hdr_cell_style),
                ('cumul_bal', 2, 0, 'text', _('Balance'),None, c_hdr_cell_style_right),
                ('label_filter', 1, 0, 'text', data['label_filter'],None, c_hdr_cell_style_right),
            ]
            c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        cnt = 0
        liness= data['lines']
        ## handling to avoide odoo crashing if lines > 65000
        custom_row_counter = len(liness)
        if custom_row_counter>65000:
            raise UserError("Report contains more lines!! Unable to print.")
        row_pos = self.xls_write_row(sheet, row_pos, c_hdr_data)
        for line in liness:
            if line['level'] != 0:
                if data['debit_credit']:
                    if line['level'] > 3:
                        c_specs = [
                            ('name', 3, 0, 'text','    '+line['name'],None,ll_cell_style),
                            ('debit', 1, 0, 'number', line['debit'],None, ll_cell_style_decimal),
                            ('credit', 1, 0, 'number', line['credit'],None, ll_cell_style_decimal),
                            ('balance', 1, 0, 'number', line['balance'],None, ll_cell_style_decimal),
                        ]
                    if not line['level'] > 3:
                        c_specs = [
                                ('name', 3, 0, 'text',line['name'],None, c_title_cell_style),
                                ('debit', 1, 0, 'number', line['debit'],None, ll_cell_style_decimal_bold),
                                ('credit', 1, 0, 'number', line['credit'],None, ll_cell_style_decimal_bold),
                                ('balance', 1, 0, 'number', line['balance'],None, ll_cell_style_decimal_bold),
                            ]
                    
                elif not data['enable_filter'] and not data['debit_credit']:
                    if line['level'] > 3:
                        c_specs = [
                                ('name', 3, 0, 'text','    '+line['name'],None,ll_cell_style),
                                ('balance', 3, 0, 'number', line['balance'],None, ll_cell_style_decimal),
                            ]
                    elif not line['level'] > 3:
                        c_specs = [
                                ('name', 3, 0, 'text',line['name'],None, c_title_cell_style),
                                ('balance', 3, 0, 'number', line['balance'],None, ll_cell_style_decimal_bold),
                            ]
                elif data['enable_filter'] and not data['debit_credit']:
                    if line['level'] > 3:
                        c_specs = [
                                ('name', 3, 0, 'text','    '+line['name'],None,ll_cell_style),
                                ('balance', 2, 0, 'number', line['balance'],None, ll_cell_style_decimal),
                                ('enable_filter', 1, 0, 'number', line['balance_cmp'],None, ll_cell_style_decimal),
                            ]
                    elif not line['level'] > 3:
                        c_specs = [
                                ('name', 3, 0, 'text',line['name'],None, c_title_cell_style),
                                ('balance', 2, 0, 'number', line['balance'],None, ll_cell_style_decimal_bold),
                                ('enable_filter', 1, 0, 'number', line['balance_cmp'],None, ll_cell_style_decimal_bold),
                            ]

                row_data = self.xls_row_template(
                        c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(
                    sheet, row_pos, row_data, c_title_cell_style)
    
    
ProfitAndLossXls('report.account_report_xls.profit_and_loss_xls.xls', 'account.account')