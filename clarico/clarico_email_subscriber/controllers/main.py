from odoo.api import call_kw, Environment
from odoo import http
from odoo.http import request
from odoo.models import check_method_name

class claricoEmailSubscriber(http.Controller):
    
    def _call_kw(self, model, method, args, kwargs):
        check_method_name(method)
        return call_kw(request.env[model], method, args, kwargs)
    
    @http.route('/web/dataset/call-public', type='json', auth="public")
    def get_email_popup(self, model, method, args, domain_id=None, context_id=None):
        return self._call_kw(model, method, args, {})
    
    @http.route('/web/session/email_subscriber/get_session_info', type='json', auth="none")
    def get_session_info(self):
        if not request.session.uid:
            session = {'uid': 0}
            return session
        request.session.check_security()
        request.uid = request.session.uid
        request.disable_db = False
        return request.env['ir.http'].session_info()
    
        
