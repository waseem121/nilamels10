odoo.define('pos_promotion_button', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');

    var CheckPromotionButton = screens.ActionButtonWidget.extend({
        template: 'PromotionButton',
        start: function() {
            this._super();
            var self = this;
            var e2key = function(e) {
                console.log("e.which: " + e.which);
                if (!e) return '';
                if (e.which == 117) {
                    self.button_click();
                };
            };
            var page5Key = function(e, customKey) {
                if (e) e.preventDefault();
                switch(e2key(customKey || e)) {
                    case 'left': /*...*/ break;
                    case 'right': /*...*/ break;
                }
            };

//            $(document).bind('keyup', page5Key);
//            $(document).trigger('keyup', [{preventDefault:function(){},keyCode:37}]);
            this.pos.bind('update:promotion', function () {
                console.log("update:promotion called");
                self.button_click();
            });
        },

        button_click: function(){
            this.pos.checking_promotion = true;
            this.promotion_ids = this.pos.promotion_ids;
            this.promotion_line_ids = this.pos.promotion_line_ids;
            this.order = this.pos.get_order();
            this.lines = this.order.get_orderlines();
            this.remove_promotion_line();
            this.order.percent_category = [];
            this.order.discount_category = [];
            this.amount_total = this.order.get_total_with_tax();
            this.product_gift_vals = this.pos.product_gift_vals;

            this.product_discount_vals = this.pos.product_discount_vals;
            this.promotion_categories = this.pos.promotion_categories;
            this.promotion_pack_ids = this.pos.promotion_pack_ids;
            this.promotion_pack_product_apply = this.pos.promotion_pack_product_apply;
            this.promotion_pack_product_free = this.pos.promotion_pack_product_free;
            this.promotion_packs = this.pos.promotion_packs;
            this.promotion_line_total_ids = this.pos.promotion_line_total_ids;
            for (var i = 0; i < this.promotion_ids.length; i++) {
                var promotion = this.promotion_ids[i];
                if (promotion.type == 'total_order') {
                    this.validate_total_order(promotion);
                }
                if (promotion.type == 'product_category') {
                    this.validate_product_categ(promotion);
                }
                if (promotion.type == 'product_detail' && this.promotion_line_ids) {
                    for (var j = 0; j < this.promotion_line_ids.length; j++) {
                        if (this.promotion_line_ids[j].promotion_id[0] == this.promotion_ids[i].id) {
                            this.validate_product(this.promotion_line_ids[j]);
                        }
                    }
                }

                if (promotion.type == 'product_discount_money' && this.product_gift_vals) {
                    this.validate_product_discount_money(promotion);
                }
                if (promotion.type == 'gift_total_order' && this.product_gift_vals) {
                    this.validate_gift_total_order(promotion);
                }
                if (promotion.type == 'discount_product' && this.product_discount_vals) {
                    this.validate_discount_product(promotion);
                }
            }
            if (this.promotion_pack_ids.length > 0) {
                this.validate_pack();
            }
            this.pos.checking_promotion = false;
        },
        // Promotion Package
        add_pack_promotion: function(pack_id, qty_multiple) {
            var self = this;
            _.each(this.pos.db.get_pos_promotion_pack_product_free(pack_id), function(pack_free_value, index) {
                console.log("pack_free_value: " + JSON.stringify(pack_free_value));
                var product = self.pos.db.get_product_by_id(pack_free_value.product_id);
                self.order.add_product(product, {
                    price: 0,
                    quantity: pack_free_value.qty_free * qty_multiple,
                    promotion: pack_id
                });

                var selectedLine = self.order.get_selected_orderline();
                selectedLine.reason = ' Free ' + product.display_name + ' from Pack: ' + pack_free_value.pack_name;
                selectedLine.orig_price_unit = product.price;
                selectedLine.promotion = true;
                selectedLine.trigger('change', selectedLine);
            });
        },
        
        validate_pack: function() {
            var lines = this.lines;
            var self = this;
            var productObj = {};
            for (var z=0; z < lines.length; z ++) {
                //Skip if it is a promotion line
                if (lines[z].promotion) {
                    continue;
                }
                var product_id = lines[z].product.id;
                var quantity = lines[z].quantity;
                
                if (productObj.hasOwnProperty(product_id)) {
                    productObj[product_id] += quantity;
                }
                else {
                    productObj[product_id] = quantity;
                }
                    
            }
            
            for (var i=0; i < self.promotion_pack_ids.length; i++) {
//                console.log("promotion_pack_ids: " + JSON.stringify(self.promotion_pack_ids));
                var pack_id = self.promotion_pack_ids[i];
                var promotion_applicable = true;
                var total_line_qty = 0.0;
                var promotion_apply_qty = 0.0;
                var qty_multiple = 1;
                
                _.each(self.pos.db.get_pos_promotion_pack_product_apply(pack_id), function(pack_apply_value, index) {
                    var this_promotion_applicable = false;
                    _.each(productObj, function(line_quantity, line_product_id) {
//                        console.log("Promotion Apply " + pack_apply_value.pack_name + " " + line_product_id);
//                        console.log("line_product_id line_quantity: " + line_product_id + " " + line_quantity);
                    
                        if (pack_apply_value.product_id == line_product_id && pack_apply_value.qty_apply <= line_quantity) {
                            total_line_qty += line_quantity;
                            promotion_apply_qty += pack_apply_value.qty_apply;
                            this_promotion_applicable = true;
                        }
                    });
                    // this will ensure all condition is satisfied
//                    console.log("this_promotion_applicable: " + this_promotion_applicable);
                    promotion_applicable = promotion_applicable && this_promotion_applicable; 
                });
                
                // If all pack condition satisfies
                if (promotion_applicable) {
                    qty_multiple = Math.floor(total_line_qty / promotion_apply_qty);
                    self.add_pack_promotion(pack_id,qty_multiple);
                }

            }
        },
        
        //----------------------------------------------------------------------
        //  remove all promotion line before auto adding to order
        // ---------------------------------------------------------------------
        remove_promotion_line: function () {
            if (this.order && this.order.get_orderlines()) {
                var lines = this.lines;
                var lines_remove = [];
                for (var i = 0; i < lines.length; i++) {
                    if (lines[i].promotion)  {
                        lines_remove.push(lines[i])
                    };
                }
                for (var j = 0; j < lines_remove.length; j ++) {
                    this.order.remove_orderline(lines_remove[j]);
                }
            }
        },
        //----------------------------------------------------------------------
        //  If total order pass condition will apply discount money by product
        // ---------------------------------------------------------------------
        validate_product_discount_money: function(promotion) {
            var product_service_id = promotion.product_id[0];
            var product = this.pos.db.get_product_by_id(product_service_id);
            var min_order = promotion.min_total_order;
            var lines = this.lines;
            if (this.amount_total >= min_order && product) {
                for (var j = 0; j < lines.length; j++) {
                    if (!lines[j].promotion) {
                        for (var i=0; i < this.product_gift_vals.length; i++) {
                            var gift = this.product_gift_vals[i];
                            if (!lines[j].promotion && gift.promotion_id[0] == promotion.id && lines[j].product.id == gift.product_id[0] && lines[j].quantity >= gift.qty ) {
                                this.order.add_product(product, {
                                    price: -(gift.price),
                                    quantity: Math.floor(lines[j].quantity / gift.qty),
                                    promotion: true,
                                });
                                var selectedLine = this.order.get_selected_orderline();
                                selectedLine.reason = ' Buy ' + gift['qty'] + ' ' + gift['product_id'][1] + ' Discount ' + gift.price;
                                selectedLine.orig_price_unit = product.price;
                                selectedLine.promotion = true;
                                selectedLine.trigger('change', selectedLine);
                            }
                        }
                    }
                }
            }
        },
        //----------------------------------------------------------------------
        //  If total order pass condition will apply gift product
        // ---------------------------------------------------------------------
        validate_gift_total_order: function(promotion) {
            var min_order = promotion.min_total_order;
            var lines = this.lines;
            if (this.amount_total >= min_order) {
             
                for (var i=0; i < this.product_gift_vals.length; i++) {
                    var gift = this.product_gift_vals[i];
                    if (gift.promotion_id[0] === promotion.id ) {
                        var product_gift_id = gift.product_id[0];
                        var product = this.pos.db.get_product_by_id(product_gift_id);
                        var quantity = Math.floor(this.amount_total / min_order);
                        this.order.add_product(product, {
                            price: -(gift.price),
                            quantity: quantity,
                            promotion: true,
                        });
                        var selectedLine = this.order.get_selected_orderline();
                        selectedLine.reason = ' Buy min ' + min_order + ' free ' + gift['product_id'][1];
                        selectedLine.orig_price_unit = product.price;
                        selectedLine.promotion = true;
                        selectedLine.trigger('change', selectedLine);
                    }
                }
                    
            }
        },
        //----------------------------------------------------------------------
        //  Product discount percent filter by product
        // ---------------------------------------------------------------------
        validate_discount_product: function(promotion) {
            var product_service_id = promotion.product_id[0];
            var product = this.pos.db.get_product_by_id(product_service_id);
            if (product) {
                var lines = this.lines;
                for (var i=0; i < this.product_discount_vals.length; i++) {
                    for (var j = 0; j < lines.length; j++) {
                        if (!lines[j].promotion && lines[j].product.id == this.product_discount_vals[i].product_id[0] && lines[j].quantity >= this.product_discount_vals[i].qty)  {
                            var price = -(lines[j].quantity * lines[j].price * this.product_discount_vals[i].percent / 100);
                            this.order.add_product(product, {
                                price: price,
                                quantity: 1,
                                promotion: true,
                            });
                            var selectedLine = this.order.get_selected_orderline();
                            selectedLine.reason = ' Buy ' + lines[j].quantity + ' ' + this.product_discount_vals[i].product_id[1] + ' percent ' + this.product_discount_vals[i].percent + ' %'
                            selectedLine.orig_price_unit = product.price;
                            selectedLine.promotion = true;
                            selectedLine.trigger('change', selectedLine);
                        };
                    }
                }
            } else {
                console.error('Product Service promotion not available on pos, please change type to service and set available on pos is True')
            }

        },
        //----------------------------------------------------------------------
        // I will remove all line if promotion of line is TRUE
        // Clean all data of order before add new record line promotion
        //----------------------------------------------------------------------
        validate_total_order: function (promotion, discount) {
            var min_order = promotion.min_total_order;
            var product = this.pos.db.get_product_by_id(promotion.product_id[0]);
            var total_with_tax = this.order.get_total_with_tax()
            if (total_with_tax >= min_order) {
                var rule = null;
                var amount = 0;
                var promotion_line_total_ids = this.promotion_line_total_ids;
                for (var i = 0; i < promotion_line_total_ids.length; i ++) {
                    var rule_check = promotion_line_total_ids[i];
                    if (rule_check.promotion_id[0] == promotion.id && total_with_tax >= rule_check.total_from) {
                        if (rule_check.total_from >= amount) {
                            rule = rule_check;
                            amount = rule_check.total_from
                        }
                    }
                }
                if (rule) {
                    if (promotion.method == 'percent') {
                        var discount = -(this.amount_total * rule.value / 100);
                        this.order.add_product(product, {
                            price: discount,
                            quantity: 1,
                            promotion: true,
                        });
                        var line = this.order.get_selected_orderline();
                        line.reason = ' Total order Greater or equal: ' + min_order + ' percent: ' + rule.value + ' %';
                        line.orig_price_unit = product.price;
                        line.promotion = true;
                        line.trigger('change', line);
                    }
                    if (promotion.method == 'discount') {
                        var discount = -(rule.value );
                        this.order.add_product(product, {
                            price: discount,
                            quantity: 1,
                            promotion: true,
                        });
                        var line = this.order.get_selected_orderline();
                        line.reason = ' Total order Greater or equal: ' + min_order + ' percent: ' + rule.value;
                        line.orig_price_unit = product.price;
                        line.promotion = true;
                        line.trigger('change', line);
                    }
                }
            }
        },
        //----------------------------------------------------------------------
        // This is function apply promotion by product free product
        //----------------------------------------------------------------------
        validate_product: function (promotion_line) {
            var product_from_id = promotion_line.product_from_id[0];
            var minn_qty = promotion_line.min_qty;
            var lines = this.lines;
            for (var i = 0; i < lines.length; i++) {
                if (lines[i].product.id == product_from_id && lines[i].quantity >= minn_qty && lines[i].promotion != true) {
                    var rate = promotion_line.gift_qty / promotion_line.min_qty;
                    var gift_qty = parseInt(rate * lines[i].quantity);
                    var product = this.pos.db.get_product_by_id(promotion_line.product_to_id[0]);
                    this.order.add_product(product, {
                        price: 0,
                        quantity: gift_qty,
                        promotion: true,
                    });
                    var selectedLine = this.order.get_selected_orderline();
                    selectedLine.reason = ' Buy ' + lines[i].quantity + ' ' + lines[i].product.display_name+ ' free ' + gift_qty +' '+ selectedLine.product.display_name;
                    selectedLine.orig_price_unit = product.price;
                    selectedLine.promotion = true;
                    selectedLine.trigger('change', selectedLine);
                }
            }
        },
        //----------------------------------------------------------------------
        // This is function apply promotion by category products
        //----------------------------------------------------------------------
        validate_product_categ: function (promotion) {
            var min_order = promotion.min_total_order;
            var product = this.pos.db.product_by_id[promotion.product_id[0]];
            var lines = this.lines;
            if (this.amount_total >= min_order && product) {
                for (var i = 0; i < lines.length; i++) {
                    if (!lines[i].promotion) {
                        for (var j = 0; j < this.promotion_categories.length; j ++) {
                            var promotion_categ = this.promotion_categories[j]
                            if (lines[i].product.pos_categ_id[0] == promotion_categ.category_id[0]) {
                                var discount = 0
                                if (promotion_categ.type == 'percent') {
                                    discount = - (lines[i].quantity * lines[i].price / 100 * promotion_categ.discount);
                                } else {
                                    discount = - promotion_categ.discount;
                                }
                                this.order.add_product(product, {
                                    price: discount,
                                    quantity: 1,
                                    promotion: true,
                                });
                                var selectedLine = this.order.get_selected_orderline();
                                selectedLine.reason = ' Buy ' + lines[i].product.display_name + ' of Category : ' + promotion_categ.category_id[1];
                                selectedLine.orig_price_unit = product.price;
                                selectedLine.promotion = true;
                                selectedLine.trigger('change', selectedLine);
                            }
                        }
                    }
                }
            }
        },
    });
    screens.define_action_button({
        'name': 'promotionbutton',
        'widget': CheckPromotionButton,
        'condition': function () {
            var res = this.pos.promotion_ids;
            return res

        },
    });
    var CleanPromotionButton = screens.ActionButtonWidget.extend({
        template: 'CleanPromotionButton',

        start: function() {
            this._super();
            var self = this;
            var e2key = function(e) {
                if (!e) return '';
                if (e.which == 116) {
                    self.button_click();
                };
            };
            var page5Key = function(e, customKey) {
                if (e) e.preventDefault();
                switch(e2key(customKey || e)) {
                    case 'left': /*...*/ break;
                    case 'right': /*...*/ break;
                }
            };
            $(document).bind('keyup', page5Key);
            $(document).trigger('keyup', [{preventDefault:function(){},keyCode:37}]);
        },
        button_click: function(){
            this.order = this.pos.get_order();
            this.pos.checking_promotion = true;
            this.remove_promotion_line();
            this.pos.checking_promotion = false;
        },
        remove_promotion_line: function () {
            if (this.order && this.order.get_orderlines()) {
                var lines = this.order.get_orderlines();
                var lines_remove = [];
                for (var i = 0; i < lines.length; i++) {
                    if (lines[i].promotion != false)  {
                        lines_remove.push(lines[i])
                    };
                }
//                console.log("lines_remove: " + lines_remove);
                if (lines_remove.length == 0) {
                    return;
                } else {
                    for (var j = 0; j < lines_remove.length; j ++) {
                        this.order.remove_orderline(lines_remove[j]);
                    }
                }
            }
        }
    });
    screens.define_action_button({
        'name': 'cleanpromotionbutton',
        'widget': CleanPromotionButton,
        'condition': function () {
            var res = this.pos.promotion_ids;
            return res
        },
    });
});
