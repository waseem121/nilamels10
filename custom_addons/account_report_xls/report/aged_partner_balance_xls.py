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

class AgedPartnerBalanceXls(ReportXls):
    column_sizes = [x[1] for x in _column_sizes]
    
    
    def generate_xls_report(self, workbook, data, lines):
        print "inside generate_xlsx_report: ",data
        print "inside lines: ",lines
        start_date = data['date_from']
        
        sheet = workbook.add_sheet("Aged Partner Balance")
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
            ('coa', 3, 0, 'text', _('Start Date')),
            ('fy', 1, 0, 'text', _('Period Length (days)')),
            ('df', 3, 0, 'text', _("Partner's")),
            ('tm', 2, 0, 'text', _('Target Moves')),

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
            
            
        c_specs = [
            ('coa', 3, 0, 'text', start_date),
            ('fy', 1, 0, 'number', data['period_length']),
            ('sb', 3, 0, 'text', data['result_selection_name']),
            ('tm', 2, 0, 'text', data['target_moves_name']),
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
        
        c_specs = [
            ('date', 2, 0, 'text', _('Partners'), None, c_hdr_cell_style),
            ('period', 1, 0, 'text', _('Not due'), None, c_hdr_cell_style),
            
            ('name_4', 1, 0, 'text',data['4']['name'], None, c_hdr_cell_style_right),
            ('name_3', 1, 0, 'text',data['3']['name'],None, c_hdr_cell_style_right),
            ('name_2', 1, 0, 'text',data['2']['name'],None, c_hdr_cell_style_right),
            ('name_1', 1, 0, 'text',data['1']['name'],None, c_hdr_cell_style_right),
            ('name_0', 1, 0, 'text',data['0']['name'],None, c_hdr_cell_style_right),
            ('journal', 1, 0, 'text', _('Total'), None, c_hdr_cell_style_right),
        ]
        
        c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(sheet, row_pos, c_hdr_data)
        c_specs = [
            ('date', 2, 0, 'text', _('Account Total'), None, c_hdr_cell_style),
            
            ('get_direction_6', 1, 0, 'number',data['get_direction'][6], None, c_hdr_cell_style_right),
            ('get_direction_4', 1, 0, 'number',data['get_direction'][4],None, c_hdr_cell_style_right),
            ('get_direction_3', 1, 0, 'number',data['get_direction'][3],None, c_hdr_cell_style_right),
            ('get_direction_2', 1, 0, 'number',data['get_direction'][2],None, c_hdr_cell_style_right),
            ('get_direction_1', 1, 0, 'number',data['get_direction'][1],None, c_hdr_cell_style_right),
            ('get_direction_0', 1, 0, 'number',data['get_direction'][0],None, c_hdr_cell_style_right),
            ('get_direction_5', 1, 0, 'number',data['get_direction'][5],None, c_hdr_cell_style_right),
        ]
        
        c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(sheet, row_pos, c_hdr_data)
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
          
        cnt = 0
        lines_datas= data['get_partner_lines']
        ## handling to avoide odoo crashing if lines > 65000
        print'line_data',lines_datas
        custom_row_counter = len(lines_datas)
        if custom_row_counter>65000:
            raise UserError("Report contains more lines!! Unable to print.")
            
        for partner_line in lines_datas:
            c_specs = [
                    ('acc_title', 2, 0, 'text',partner_line['name']),
                    ('direction', 1, 0, 'number', partner_line['direction'],None, ll_cell_style_decimal),
                    ('partner_line_4', 1, 0, 'number', partner_line['4'],None, ll_cell_style_decimal),
                    ('partner_line_3', 1, 0, 'number', partner_line['3'],None, ll_cell_style_decimal),
                    ('partner_line_2', 1, 0, 'number', partner_line['2'],None, ll_cell_style_decimal),
                    ('partner_line_1', 1, 0, 'number', partner_line['1'],None, ll_cell_style_decimal),
                    ('partner_line_0', 1, 0, 'number', partner_line['0'],None, ll_cell_style_decimal),
                    ('partner_line_total', 1, 0, 'number', partner_line['total'],None, ll_cell_style_decimal),
                ]
            row_data = self.xls_row_template(
                    c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                sheet, row_pos, row_data, ll_cell_style)
                    
        
AgedPartnerBalanceXls('report.account_report_xls.aged_partner_balance_xls.xls', 'account.account')