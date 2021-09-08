odoo.define('pos_promotion_db', function (require) {
"use strict";
    
var PosDB = require('point_of_sale.DB');

PosDB.include({
    init: function(options){
        this.pos_promotion_pack_product_apply = {};
        this.pos_promotion_pack_product_free = {};
        this._super(options);
    },
    
    add_pos_promotion_pack_product_apply: function(results){
        for(var i = 0, len = results.length; i < len; i++){
            var result = results[i];
            this.pos_promotion_pack_product_apply[result.id] = {
                "pack_id": result.pack_id[0], 
                "pack_name": result.pack_id[1], 
                "product_id": result.product_id[0], 
                "product_name": result.product_id[1], 
                "qty_apply": result.qty_apply, 
            };
        }
//        console.log("this.pos_promotion_pack_product_apply: " + JSON.stringify(this.pos_promotion_pack_product_apply));
    },
    
    get_pos_promotion_pack_product_apply: function(pack_id){
        var results = [];
        _.each(this.pos_promotion_pack_product_apply, function(value, index){
            if (value.pack_id === pack_id) {
                results.push(value);
            }
        });
//        console.log("get_pos_promotion_pack_product_apply results: " + JSON.stringify(results));
        return results;
    },
    
    add_pos_promotion_pack_product_free: function(results){
        for(var i = 0, len = results.length; i < len; i++){
            var result = results[i];
            this.pos_promotion_pack_product_free[result.id] = {
                "pack_id": result.pack_id[0], 
                "pack_name": result.pack_id[1], 
                "product_id": result.product_id[0], 
                "product_name": result.product_id[1], 
                "qty_free": result.qty_free, 
            };
        }
//        console.log("this.pos_promotion_pack_product_free: " + JSON.stringify(this.pos_promotion_pack_product_free));
    },
    
    get_pos_promotion_pack_product_free: function(pack_id){
        var results = [];
        _.each(this.pos_promotion_pack_product_free, function(value, index){
            if (value.pack_id === pack_id) {
                results.push(value);
            }
        });
        return results;
    }
});
    
});