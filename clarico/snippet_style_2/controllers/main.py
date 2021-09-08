from odoo import http
from odoo.http import request
from odoo import SUPERUSER_ID

class timer(http.Controller):
    @http.route(['/timer/render'], type='json', auth='public', website=True , csrf=False, cache=300)
    def render_timer_template(self):
        print("Aaaaaaaaaa")
        values={}
        return request.env.ref("snippet_style_2.snippet_style_2_template").render(values)