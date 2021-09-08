import odoo
from odoo import http
from odoo.http import request

class claricoHomePage1(http.Controller):    
    @http.route(['/home/1'], type='http', auth="public", website=True)    
    def service(self, **kwargs):        
        return request.render("clarico_layout1.clarico_layout1_homepage")
