from odoo import api, fields, models, _

class Currency(models.Model):
    _inherit = "res.currency"
    
    @api.model
    def _get_conversion_rate_custom(self, from_currency, to_currency, rate):
        from_currency = from_currency.with_env(self.env)
        to_currency = to_currency.with_env(self.env)
        print"from_currency: name",from_currency.name
        print"to_currency: name",to_currency.name
        if not rate:
            rate=1.0
#        return to_currency.rate / from_currency.rate    
        return to_currency.rate / rate
    
    @api.multi
    def compute_custom(self, from_amount, to_currency, rate, round=True):
        """ Convert `from_amount` from currency `self` to `to_currency`. """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "compute from unknown currency"
        assert to_currency, "compute to unknown currency"
        # apply conversion rate
        if self == to_currency:
            to_amount = from_amount
        else:
            to_amount = from_amount * self._get_conversion_rate_custom(self, to_currency, rate)
#            to_amount = from_amount * self._get_conversion_rate(self, to_currency)
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount
