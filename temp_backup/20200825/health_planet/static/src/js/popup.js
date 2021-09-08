odoo.define('health_planet.popups', function (require) {
"use strict";

var popups = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');
var _t  = require('web.core')._t;


 var PackLotLinePopupWidgetCustom = popups.extend({
    template: 'PackLotLinePopupWidgetCustom',
    events: _.extend({}, popups.prototype.events, {
        'click .remove-lot': 'remove_lot',
        'keydown': 'add_lot',
        'blur .packlot-line-input': 'lose_input_focus'
    }),

    show: function(options){
        this._super(options);
        this.focus();
    },

    click_confirm: function(){
        var pack_lot_lines = this.options.pack_lot_lines;

        this.$('.packlot-line-input').each(function(index, el){
            var cid = $(el).attr('cid'),
                lot_name = $(el).val();
            var pack_line = pack_lot_lines.get({cid: cid});
            pack_line.set_lot_name(lot_name);
        });
        pack_lot_lines.remove_empty_model();
        pack_lot_lines.set_quantity_by_lot();

        this.options.order.save_to_db();

        this.gui.close_popup();

    },

    add_lot: function(ev) {
        if (ev.keyCode === $.ui.keyCode.ENTER){
            var pack_lot_lines = this.options.pack_lot_lines,
                $input = $(ev.target),
                cid = $input.attr('cid'),
                lot_name = $input.val();


            var lot_model = pack_lot_lines.get({cid: cid});
            lot_model.set_lot_name(lot_name);  // First set current model then add new one
            if(!pack_lot_lines.get_empty_model()){
                var new_lot_model = lot_model.add();
                this.focus_model = new_lot_model;
            }

            pack_lot_lines.set_quantity_by_lot();
            this.renderElement();
            this.focus();

        }

    },

    remove_lot: function(ev){
        var pack_lot_lines = this.options.pack_lot_lines,
            $input = $(ev.target).prev(),
            cid = $input.attr('cid');
        var lot_model = pack_lot_lines.get({cid: cid});
        lot_model.remove();
        pack_lot_lines.set_quantity_by_lot();
        this.renderElement();
    },

    lose_input_focus: function(ev){
        var $input = $(ev.target),
            cid = $input.attr('cid');
        var lot_model = this.options.pack_lot_lines.get({cid: cid});
        lot_model.set_lot_name($input.val());
    },

    focus: function(){
        this.$("input[autofocus]").focus();
        this.focus_model = false;   // after focus clear focus_model on widget
    },
    close: function(){
        var order = this.pos.get_order()
        var pack_lot_lines = this.options.pack_lot_lines;
        console.log("lot lines", pack_lot_lines);
        var plots = []
        _.each(pack_lot_lines.models, function(plot){
            if(plot.attributes.lot_name != null){
                plots.push(plot.lot_name )
            }
        });

        var line = this.pos.get_order().get_selected_orderline();

        if((line !==undefined && line.quantity != plots.length) || line.quantity ==0.0){
            console.log();
            order.remove_orderline(line);
        }
        if (this.pos.barcode_reader) {
            this.pos.barcode_reader.restore_callbacks();
        }
    },
    click_cancel: function(){

        this.gui.close_popup();
        if (this.options.cancel) {
            this.options.cancel.call(this);
        }
    },
});
   gui.define_popup({name:'packlotline_custom', widget: PackLotLinePopupWidgetCustom});
});
