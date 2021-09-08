odoo.define('pos_discount_amount.pos.models.amount', function (require) {
"use strict";

var models = require('point_of_sale.models');
var utils = require('web.utils');
var formats = require('web.formats');
var round_di = utils.round_decimals;
var round_pr = utils.round_precision;

var _super_posmodel = models.PosModel.prototype;

models.PosModel = models.PosModel.extend({
    initialize: function (session, attributes) {
    // Added new field in read
        var partner_model = _.find(this.models, function(model){
            return model.model === 'res.company';
        });
        partner_model.fields.push('discount_type');

        // Inheritance
        return _super_posmodel.initialize.call(this, session, attributes);
    },
    
    get_total_with_tax: function() {
        return this.get_total_without_tax() + this.get_total_tax();
    },  
    
});

var _super_order = models.Order.prototype;

models.Order = models.Order.extend({
    initialize: function() {
            _super_order.initialize.apply(this,arguments);
        },
    get_total_discount: function() {
        if (this.pos.company.discount_type === "amount"){
            return round_pr(this.orderlines.reduce((function(sum, orderLine) {
                return sum + (orderLine.get_discount() * orderLine.get_quantity());
                }), 0), this.pos.currency.rounding); 
        }
    else {
        return round_pr(this.orderlines.reduce((function(sum, orderLine) {
            return sum + (orderLine.get_unit_price() * (orderLine.get_discount()/100) * orderLine.get_quantity());
            }), 0), this.pos.currency.rounding);
        }
    },
});

// Extendting order line
var _super_orderline = models.Orderline.prototype;

models.Orderline = models.Orderline.extend({
    initialize: function(attr, options) {
        _super_orderline.initialize.call(this, attr, options);
    },
    
    // changes the base price of the product for this orderline
    set_unit_price: function(price){
        this.order.assert_editable();
        this.price = round_di(parseFloat(price) || 0, this.pos.dp['Product Price']);
        this.trigger('change',this);
    },

     // currunt pos system is running on % only so, to change the flow to amounting we have to override with this.
    set_discount: function(discount){
        _super_orderline.set_discount.call(this, discount);
        
        if (this.pos.company.discount_type === "amount"){
            var disc4amount = Math.max(parseFloat(discount) || 0, 0);
            this.discount = disc4amount;
            this.discountStr = '' + disc4amount;
            this.trigger('change',this);
        }
    },

    /* to calculate each line */
    get_base_price:    function(){
        var rounding = this.pos.currency.rounding;
        if (this.pos.company.discount_type === "amount"){
            return round_pr((this.get_unit_price() * this.get_quantity()) - (this.get_quantity() * this.get_discount()), rounding);
        }
        else{
        return round_pr(this.get_unit_price() * this.get_quantity() * (1 - this.get_discount()/100), rounding);
        }
    },
    
    get_display_price: function(){
        if (this.pos.config.iface_tax_included) {
            return this.get_price_with_tax();
        } else {
            return this.get_base_price();
        }
    },
    
    get_price_without_tax: function(){
        return this.get_all_prices().priceWithoutTax;
    },
    get_price_with_tax: function(){
        return this.get_all_prices().priceWithTax;
    },
    get_tax: function(){
        return this.get_all_prices().tax;
    },
    
    
    /* To display total in all line */
    
    get_all_prices: function(){
        var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
        if (this.pos.company.discount_type === "amount"){
           price_unit = this.get_unit_price() - this.get_discount();
        }
        var taxtotal = 0;
        var product =  this.get_product();
        var taxes_ids = product.taxes_id;
        var taxes =  this.pos.taxes;
        var taxdetail = {};
        var product_taxes = [];

        _(taxes_ids).each(function(el){
            product_taxes.push(_.detect(taxes, function(t){
                return t.id === el;
            }));
        });

        var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
        _(all_taxes.taxes).each(function(tax) {
            taxtotal += tax.amount;
            taxdetail[tax.id] = tax.amount;
        });

        return {
            "priceWithTax": all_taxes.total_included,
            "priceWithoutTax": all_taxes.total_excluded,
            "tax": taxtotal,
            "taxDetails": taxdetail,
        };
    },
  
});

});

