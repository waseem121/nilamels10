odoo.define('pos_promotion_models', function (require) {
    var models = require('point_of_sale.models');
//    var screens = require('point_of_sale.screens');
    
//    var utils = require('web.utils');
//    var round_pr = utils.round_precision;
//    var round_di = utils.round_decimals;
//    
//    var formats = require('web.formats');

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attributes, options) {
            _super_orderline.initialize.apply(this, arguments);
            this.promotion = false;
        },
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.apply(this,arguments);
            if (this.promotion) {
                json.promotion = this.promotion;
            }
            if (this.reason) {
                json.reason = this.reason;
            }
            if (this.orig_price_unit) {
                json.orig_price_unit = this.orig_price_unit;
            }
            return json;
        },
        init_from_JSON: function (json) {
            _super_orderline.init_from_JSON.apply(this,arguments);
            if (json.promotion) {
                this.promotion = json.promotion;
            }
            if (json.reason) {
                this.reason = json.reason;
            }
            if (json.orig_price_unit) {
                this.orig_price_unit = json.orig_price_unit;
            }
        },
//        set_quantity: function(quantity) {
//            console.log("set_quantity called: " + quantity);
//            _super_orderline.set_quantity.apply(this,arguments);
//            if (quantity && quantity != 'remove') {
//                this.checking_promotion();
//            }
//        },
        
//        set_unit_price: function(price) {
//            console.log("set_unit_price called");
//            _super_orderline.set_unit_price.apply(this,arguments);
//            this.checking_promotion();
//        },
//        set_discount: function(discount) {
//            console.log("set_discount called");
//            _super_orderline.set_discount.apply(this,arguments);
//            this.checking_promotion();
//        },
//        checking_promotion: function() {
//            if (!this.pos.checking_promotion || this.pos.checking_promotion == false) {
//                this.pos.trigger('update:promotion');
//            }
//        }
    });
    var _super_order = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes, options){
            _super_order.prototype.initialize.apply(this, arguments);
        },
        
//        add_product: function(product, options){
//            _super_order.prototype.add_product.apply(this, arguments);
//            this.pos.trigger('update:promotion');
//        }
    });
    models.load_models([
        {
            model: 'pos.config',
            fields: ['promotion_ids', 'pack_ids'],
            domain: function(self) {return [['id','=', self.pos_session.config_id[0]]]},
            context:{ 'pos': true},
            loaded: function(self, results){
                self.promotion_config_ids = [];
                self.promotion_pack_ids = [];
                for (var i=0; i < results.length; i ++) {
                    for (var j=0; j < results[i].promotion_ids.length; j ++) {
                        self.promotion_config_ids.push(results[i].promotion_ids[j])
                    }
                    for (var j=0; j < results[i].pack_ids.length; j ++) {
                        self.promotion_pack_ids.push(results[i].pack_ids[j])
                    }
                }
            },
        },
        {
            model: 'pos.promotion',
            fields: [
                'id', 'sequence', 'name', 'type',
                'method', 'product_gift_ids', 'categ_ids', 'percent_total', 'product_discount_ids',
                'discount_total', 'min_total_order', 'product_id',
            ],
            domain: function(self) {return [['state', '=', 'active']]},
            context:{ 'pos': true},
            loaded: function(self, results, tmp){
                var promotion_ids = [];
                for (var i=0; i < results.length; i ++)
                    for ( var j=0; j < self.promotion_config_ids.length; j ++) {
                        if (results[i].id == self.promotion_config_ids[j]) {
                            promotion_ids.push(results[i])
                        }
                }
                self.promotion_ids =  promotion_ids;
                tmp.product_gift_ids = [];
                tmp.product_discount_ids = [];
                for (var i=0; i < results.length; i ++) {
                    for (var j=0; j < results[i].product_gift_ids.length; j ++) {
                        tmp.product_gift_ids.push(results[i].product_gift_ids[j]);
                    }
                    for (var j=0; j < results[i].product_discount_ids.length; j ++) {
                        tmp.product_discount_ids.push(results[i].product_discount_ids[j]);
                    }
                }
                console.log("pos.promotion tmp.product_gift_ids: " + JSON.stringify(tmp.product_gift_ids));
            },
        },
        {
            model: 'pos.promotion.product.gift',
            fields: ['product_id', 'qty', 'price', 'promotion_id'],
            domain: function(self, tmp){ return [['id', 'in', tmp.product_gift_ids]]; },
            loaded: function(self, results) {
                self.product_gift_vals = results;
            }
        },
        {
            model: 'pos.promotion.product.discount',
            fields: ['product_id', 'qty', 'percent', 'promotion_id'],
            domain: function(self, tmp){ return [['id', 'in', tmp.product_discount_ids]]; },
            loaded: function(self, results) {
                self.product_discount_vals = results;
            }
        },
        {
            model: 'pos.promotion.line',
            fields: [
                'product_from_id',
                'product_to_id',
                'min_qty',
                'gift_qty',
                'promotion_id',
            ],
            domain: function(self) {return []},
            context:{ 'pos': true},
            loaded: function(self, lines){
                var $promotion_line_ids = [];
                for (var i=0; i < self.promotion_ids.length; i ++) {
                    for ( var j=0; j < lines.length; j ++) {
                        if (lines[j].promotion_id[0] == self.promotion_ids[i].id) {
                            $promotion_line_ids.push(lines[j])
                        }
                    }
                }
                self.promotion_line_ids =  $promotion_line_ids;
            },
        },
        {
            model: 'pos.promotion.category',
            fields: [
                'promotion_id',
                'category_id',
                'type',
                'discount',
            ],
            domain: function(self) {return []},
            context:{},
            loaded: function(self, lines){
                self.promotion_categories =  lines;
            },
        },
        {
            model: 'pos.promotion.pack',
            fields: ['id','name','product_apply_ids','product_free_ids'],
            domain: function(self) {return [['id', 'in', self.promotion_pack_ids]]},
            context:{},
            loaded: function(self, results){
                self.promotion_packs =  results;
                self.promotion_pack_ids =  [];
                for (var i=0; i < results.length; i++) {
                    self.promotion_pack_ids.push(results[i]['id'])
                }
            },
        },

        {
            model: 'pos.promotion.pack.product.apply',
            fields: [
                'id',
                'product_id',
                'qty_apply',
                'pack_id'
            ],
            domain: function(self) {return [['pack_id', 'in', self.promotion_pack_ids]]},
            context:{},
            loaded: function(self, results){
                self.promotion_pack_product_apply =  results;
                self.db.add_pos_promotion_pack_product_apply(results);
            },
        },

        {
            model: 'pos.promotion.pack.product.free',
            fields: [
                'id',
                'product_id',
                'qty_free',
                'pack_id'
            ],
            domain: function(self) {return [['pack_id', 'in', self.promotion_pack_ids]]},
            context:{},
            loaded: function(self, results){
                self.promotion_pack_product_free =  results;
                self.db.add_pos_promotion_pack_product_free(results);
                console.log('END loading PROMOTIONS');
            },
        },
        {
            model: 'pos.promotion.line.total',
            fields: [
                'id',
                'total_from',
                'total_to',
                'value',
                'promotion_id'
            ],
            domain: function(self) {return []},
            context:{},
            loaded: function(self, results){
                self.promotion_line_total_ids = results;
            },
        },

    ]);

});
