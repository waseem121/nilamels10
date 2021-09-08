odoo.define('health_planet.models', function (require) {
    "use strict";

var models = require('point_of_sale.models');
var _t  = require('web.core')._t;

var _super_posmodel = models.PosModel.prototype;
var _super_order = models.Order.prototype;

models.PosModel = models.PosModel.extend({
    initialize: function (session, attributes) {

        var partner_model = _.find(this.models, function(model){
            return model.model === 'res.partner';
        });
        partner_model.fields.push('is_instructor');
        partner_model.loaded = function(self, partners){
         self.partners = partners;
         self.db.add_partners(partners);

        }

        return _super_posmodel.initialize.call(this, session, attributes);
        },

    get_instructor: function() {
        var order = this.get_order();
        if (order) {
            return order.get_instructor();
        }
        return null;
    },
//    add_new_order: function(){
//        var order = _super_posmodel.add_new_order.call(this,arguments);
//        console.log('custom load',$('.order-instructor'));
//        $('.order-instructor').text('Doctor');
//
//        return order;
//    },
    });

models.Order = models.Order.extend({
     initialize: function(attributes,options) {
        _super_order.initialize.apply(this,arguments);
        this.instructor = this.instructor || null;
    },
    init_from_JSON: function(json){
        _super_order.init_from_JSON.apply(this,arguments);
//        this.instructor = json.instructor || null;
        var instructor
        if (json.instructor_id) {
            instructor = this.pos.db.get_partner_by_id(json.instructor_id);
            if (!instructor) {
                console.error('ERROR: trying to load a Instructor not available in the pos');
            }
        } else {
            instructor = null;
        }
        this.set_instructor(instructor);
    },

    export_as_JSON: function(opts) {
        opts = opts || {};
        var json = _super_order.export_as_JSON.apply(this,arguments);
        json.instructor_id = this.get_instructor() ? this.get_instructor().id : null;
        return json;
    },
    set_instructor: function(instructor){
        this.set('instructor', instructor);
        this.trigger('change');

    },
    get_instructor: function(){
        return this.get('instructor');
    },
    get_instructor_name: function(){
        var instructor = this.get('instructor');
        return instructor ? instructor.name : "";
    },
    add_product: function(product, options){
        if(this._printed){
            this.destroy();
            return this.pos.get_order().add_product(product, options);
        }
        this.assert_editable();
        options = options || {};
        var attr = JSON.parse(JSON.stringify(product));
        attr.pos = this.pos;
        attr.order = this;
        var line = new exports.Orderline({}, {pos: this.pos, order: this, product: product});

        if(options.quantity !== undefined){
            line.set_quantity(options.quantity);
        }

        if(options.price !== undefined){
            line.set_unit_price(options.price);
        }

        //To substract from the unit price the included taxes mapped by the fiscal position
        this.fix_tax_included_price(line);

        if(options.discount !== undefined){
            line.set_discount(options.discount);
        }

        if(options.extras !== undefined){
            for (var prop in options.extras) {
                line[prop] = options.extras[prop];
            }
        }

        var last_orderline = this.get_last_orderline();
        if( last_orderline && last_orderline.can_be_merged_with(line) && options.merge !== false){
            last_orderline.merge(line);
        }else{
            this.orderlines.add(line);
        }
        this.select_orderline(this.get_last_orderline());

//        if(line.has_product_lot){
//            this.display_lot_popup();
//        }
    },

    display_lot_popup: function() {
        var order_line = this.get_selected_orderline();
        if (order_line){
            var pack_lot_lines =  order_line.compute_lot_lines();
            /*this.pos.gui.show_popup('packlotline_custom', {
                'title': _t('Lot/Serial Number(s) Required'),
                'pack_lot_lines': pack_lot_lines,
                'order': this
            });*/
        }
    },

});



});
