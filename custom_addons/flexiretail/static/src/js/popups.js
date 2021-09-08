odoo.define('flexiretail.popups', function (require) {
	"use strict";
	var gui = require('point_of_sale.gui');
	var keyboard = require('point_of_sale.keyboard').OnscreenKeyboardWidget;
	var Model = require('web.DataModel');
	var chrome = require('point_of_sale.chrome');
	var utils = require('web.utils');
	var PopupWidget = require('point_of_sale.popups');
	var models = require('point_of_sale.models');
	var formats = require('web.formats');
	
	var core = require('web.core');
	var QWeb = core.qweb;
	var round_pr = utils.round_precision;
    var round_di = utils.round_decimals;
	var _t = core._t;
	
	/* Product POPUP */
	var ProductPopup = PopupWidget.extend({
	    template: 'ProductPopup',
	    show: function(options){
	    	var self = this;
			this._super();
			this.product_list = options.product_list || "";
			this.order_id = options.order_id || "";
			this.state = options.state || "";
			this.renderElement();
//			self = this;
			$(".del_order").click(function(){
				var result = self.pos.db.get_order_by_id(self.order_id);
				if(result && result.state == 'draft'){
					self.gui.show_popup('confirm',{
		                'title': _t('Delete Order'),
		                'body': _t("Are you sure you want to delete "+ result.pos_reference +" ?"),
		                confirm: function(){
		                	new Model("pos.order").get_func("unlink")(result.id).then(function(){
		        				$(".reload").click();
		        				self.gui.close_popup();
		        			});
		                },
		            });
				}
			});
	    },
	    click_confirm: function(){
	    	var self = this;
	        if (this.state == "paid" || this.state == "done"){
                $( "#re_order_duplicate" ).data("id",self.order_id);
    			$( "#re_order_duplicate" ).trigger("click");
	        } else if(this.state == "draft") {
                $( "#re_order" ).data("id",self.order_id);
                $( "#re_order" ).trigger("click");
			}
			this.gui.close_popup();
	    },
    	click_cancel: function(){
    		this.gui.close_popup();
    	}
	    
	});
	gui.define_popup({name:'product_popup', widget: ProductPopup});

	/* Delivery Date POPUP */
	var DeliveryDatePopup = PopupWidget.extend({
	    template: 'DeliveryDatePopup',
	    show: function(options){
	    	var self = this;
			this._super();
		    var options = options || {}
		    if(options){
		        this.payment_obj = options.payment_obj;
		        this.new_date = options.new_date;
		        this.to_be_update_order = options.order;
		        this.draft = options.draft;
		    }
		    var order = this.pos.get_order();
			self.renderElement();
			if(order.get_reserved_delivery_date()){
		        $('#delivery_datepicker').val(order.get_reserved_delivery_date());
		    }
		    $('#delivery_datepicker').focus();
	    },
	    click_confirm: function(){
	        var self = this;
            var order = this.pos.get_order();
            order.set_delivery_date($('#delivery_datepicker').val() || false);
            if(this.new_date){
                if(!this.draft && this.payment_obj){
                    if(order.get_total_paid() != 0){
                        if(!order.get_reservation_mode()){
                            order.set_partial_pay(true);
                        }
                        self.payment_obj.finalize_validation();
                        $('.js_reservation_mode').removeClass('highlight');
                    }
				} else if(this.draft){
				    this.pos.push_order(order);
				    this.gui.show_screen('receipt');
				}
            }else {
                if(order && self.to_be_update_order.delivery_date != $('#delivery_datepicker').val()){
        	        new Model('pos.order').call('update_delivery_date',
        	            [self.to_be_update_order.id, $('#delivery_datepicker').val()])
        	            .then(function(res){
        	                self.pos.db.add_orders(res);
        	                var temp_orders = self.pos.get('pos_order_list');
        	                $.extend(temp_orders, res);
        	                self.pos.set({ 'pos_order_list' : temp_orders });
        	            });
        	    }
        	}
			this.gui.close_popup();
	    },
        renderElement: function(){
            var self = this;
            this._super();
            $('#delivery_datepicker').datepicker({
               dateFormat: 'yy-mm-dd',
               minDate: new Date(),
               closeText: 'Clear',
               showButtonPanel: true,
            }).focus(function(){
                var thisCalendar = $(this);
                $('.ui-datepicker-close').click(function() {
                    thisCalendar.val('');
                });
            });
            $('#delivery_datepicker').datepicker('setDate', new Date());
        },
	});
	gui.define_popup({name:'delivery_date_popup', widget: DeliveryDatePopup});

	var CancelOrderPopup = PopupWidget.extend({
	    template: 'CancelOrderPopup',
	    init: function(parent, args) {
	    	var self = this;
	        this._super(parent, args);
	        this.options = {};
	        this.line = [];
	        this.select_all = function(e){
                $('.ac_selected_product').prop('checked', $('.check_all_items_checkbox').prop('checked'));
                var contents = self.$el[0].querySelector('div.product_info ul');
                $(contents).empty();
                $('.ac_selected_product').trigger('change');
	        }
	        this.update_qty = function(ev){
	        	ev.preventDefault();
	            var $link = $(ev.currentTarget);
                self._update_qty($link);
	            return false;
	        };
	        this.keydown_qty = function(e){
	        	if($(this).val() > $(this).data('max')){
	        		$(this).val($(this).data('max'))
	        	}
	        	if($(this).val() < $(this).data('min')){
	        		$(this).val($(this).data('min'))
	        	}
	        	if (/\D/g.test(this.value)){
                    // Filter non-digits from input value.
                    this.value = this.value.replace(/\D/g, '');
                }
                self.update_line(self.generate_line($(this).attr('name')));
	        };
	    },
	    _update_qty: function($link){
	        var self = this;
	        var $input = $link.parent().parent().find("input");
            var min = parseFloat($input.data("min") || 0);
            var max = parseFloat($input.data("max") || Infinity);
            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
            $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
            $('input[name="'+$input.attr("name")+'"]').val(quantity > min ? (quantity < max ? quantity : max) : min);
            $input.change();
            self.update_line(self.generate_line($($input).attr('name')));
	    },
	    show: function(options){
	    	var self = this;
	        options = options || {};
	        this._super(options);
	        this.order_tobe_cancel = options.order;
	        if (this.order_tobe_cancel){
                new Model('pos.order.line').call('search_read', [[['id', 'in', this.order_tobe_cancel.lines], ['qty', '>', 0]]], {}, {'async': false})
                .then(function(lines){
                    _.each(lines, function(line){
                        self.line[line.id] = line
                    });
                    self.lines = lines;
                });
	        }
	        this.renderElement();
	        self.update_summary();
	    },
	    update_line: function(line){
	        var self = this;
	        var contents = this.$el[0].querySelector('div.product_info ul');
            var li = $(contents).find('li[data-id="'+ line.id +'"]')
	        if(li.length){
	            var new_line = self.rerender_line(line);
	            $(li).replaceWith(new_line);
	            self.update_summary()
	        }
	    },
	    rerender_line: function(line){
	        var self = this;
	        var el_str  = QWeb.render('CancelLines',{widget:this, line:line});
            var el_ul = document.createElement('ul');
            el_ul.innerHTML = el_str;
            el_ul = el_ul.childNodes[1];
            el_ul.querySelector('.remove_line').addEventListener('click', function(e){
                $('.ac_selected_product[data-name="'+ line.id +'"]').prop('checked', false);
                self.render_lines(line, "remove");
                if(!$('.ac_selected_product:checked').length){
                    $('.check_all_items_checkbox').prop('checked', false);
                }
            });

            return el_ul;
	    },
	    render_lines: function(line, operation){
            var self = this;
            var contents = this.$el[0].querySelector('div.product_info ul');
            if(operation == "remove"){
                $(contents).find('li[data-id="'+ line.id +'"]').remove();
                self.update_summary()
                return
            }
            var el_ul = self.rerender_line(line);
            contents.appendChild(el_ul);
            self.update_summary()
            var line_count = $(contents).find('ul li').length;
            this.el.querySelector('.product_info').scrollTop = 100 * line_count;
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var selectedOrder = this.pos.get_order();
	    	this.total = 0.00;
	    	this.remaining_item_total = 0.00;
	    	var temp_orderline_ids = [];
            _.each($('.ac_selected_product:checked'), function(item){
                var orderline = self.line[$(item).data('name')];
                temp_orderline_ids.push($(item).data('name'));
                var product = self.pos.db.get_product_by_id(orderline.product_id[0]);
                var qty = $('input[name="'+orderline.id+'"').val();
                selectedOrder.add_product(product, {quantity: qty * -1, price: 0.00 });
                if(selectedOrder.get_selected_orderline()){
                    selectedOrder.get_selected_orderline().set_cancel_process(orderline.order_id);
                    selectedOrder.get_selected_orderline().set_cancel_item(true);
                    selectedOrder.get_selected_orderline().set_cancel_item_id(orderline.id);
                    if((orderline.qty - qty) <= 0){
                        selectedOrder.get_selected_orderline().set_line_status("full");
                    } else {
                        selectedOrder.get_selected_orderline().set_line_status("partial");
                    }
                    if(product.type != "service"){
                        selectedOrder.get_selected_orderline().set_consider_qty(orderline.qty - qty);
                    }
                }
                self.total += orderline.price_unit * qty;
            });
            if(temp_orderline_ids.length > 0){
                _.each(self.lines, function(line){
                    if($.inArray(line.id, temp_orderline_ids) == -1){
                        self.remaining_item_total += line.price_subtotal_incl;
                    }
                })
                self.add_charge_product();
                if(self.new_amount_due < 0){
                    self.add_refund_product();
                } else {
                    self.add_paid_amount();
                }
                if (this.order_tobe_cancel.partner_id && this.order_tobe_cancel.partner_id[0]) {
                    var partner = self.pos.db.get_partner_by_id(this.order_tobe_cancel.partner_id[0])
                    selectedOrder.set_client(partner);
                }
                selectedOrder.set_reservation_mode(true);
                selectedOrder.set_pos_reference(this.order_tobe_cancel.pos_reference);
                selectedOrder.set_sequence(this.order_tobe_cancel.name);
                selectedOrder.set_cancel_order(true);
                selectedOrder.set_order_id(this.order_tobe_cancel.id);
                selectedOrder.set_reserved_delivery_date(this.order_tobe_cancel.delivery_date);
                selectedOrder.set_amount_paid(this.order_tobe_cancel.amount_paid);
                selectedOrder.set_cancellation_charges(self.cancel_charge);
                selectedOrder.set_refund_amount(self.refundable_total);
                if(self.refundable_total > 0){
                    selectedOrder.set_reservation_mode(false);
                }
                self.pos.gui.show_screen('payment');
                this.gui.close_popup();
            }
	    },
	    get_product_image_url: function(product_id){
    		return window.location.origin + '/web/image?model=product.product&field=image_medium&id='+product_id;
    	},
    	generate_line: function(line_id){
    	    var self = this;
            var selected_line = self.line[line_id]
            var qty = $('.js_quantity[name="'+ line_id +'"]').val();
            var line = false
            if(selected_line){
                var line = {
                    product_name: selected_line.display_name,
                    price: qty*selected_line.price_unit,
                    qty: self.get_qty_str(selected_line.product_id[0], qty) || 0.00,
                    id: selected_line.id,
                }
                return line
            }
            return false
    	},
    	get_qty_str: function(product_id, qty){
            var self = this;
            var qty;
            var product = self.pos.db.get_product_by_id(product_id);
            if(product){
                var unit = self.pos.units_by_id[product.uom_id[0]]
                var new_qty = '';
                if(unit){
                    qty    = round_pr(qty, unit.rounding);
                    var decimals = self.pos.dp['Product Unit of Measure'];
                    new_qty = formats.format_value(round_di(qty, decimals), { type: 'float', digits: [69, decimals]});
                    return new_qty + '/' + unit.display_name
                }
            }
        },
    	renderElement: function(){
    	    var self = this;
            this._super();
            this.$('.input-group-addon').delegate('a.js_qty','click', this.update_qty);
            this.$('div.input-group').delegate('.js_quantity','input', this.keydown_qty);
            $('.ac_selected_product').change(function(){
                var line_id = $(this).data('name');
                var line = self.generate_line(line_id)
                if(line){
                    if($(this).prop('checked')){
                        self.render_lines(line);
                        if($('.ac_selected_product:checked').length === $('.ac_selected_product').length){
                            $('.check_all_items_checkbox').prop('checked', true);
                        }
                    } else {
                        self.render_lines(line, "remove");
                        $('.check_all_items_checkbox').prop('checked', false);
                    }
                }
            })
            this.$('.check_all_items').delegate('.label', 'click', function(e){
                $('.check_all_items_checkbox').prop('checked', !$('.check_all_items_checkbox').prop('checked'));
                self.select_all(e);
            });
            this.$('.check_all_items').delegate('.check_all_items_checkbox', 'click', this.select_all);
    	},
    	get_total: function(){
    	    var self = this;
    	    var total = 0.00;
    	    var temp_orderline_ids = [];
    	    _.each($('.ac_selected_product:checked'), function(item){
                var orderline = self.line[$(item).data('name')];
                if(orderline){
                    temp_orderline_ids.push($(item).data('name'));
                    var qty = $('input[name="'+orderline.id+'"').val();
                    total += orderline.price_unit * qty;
                }
            });
            return total;
    	},
    	update_summary: function(){
    	    var self = this;
            self.cancel_charge = self._calculate_cancellation_charges();
            self.refundable_total = self._calculate_refund_amount() ? self._calculate_refund_amount() + self.cancel_charge : self._calculate_refund_amount();
            var cancel_order_total = self.get_total();
            var new_order_total = self.order_tobe_cancel.amount_total - cancel_order_total + self.cancel_charge;
            self.new_amount_due = new_order_total - self.order_tobe_cancel.amount_paid;
            this.el.querySelector('.cancel_order_summary .cancel_order_total > .value').textContent = this.format_currency(cancel_order_total);
            this.el.querySelector('.cancel_order_summary .new_order_total > .value').textContent = this.format_currency(new_order_total);
            this.el.querySelector('.cancel_order_summary .new_amount_due > .value').textContent = this.format_currency(self.new_amount_due > 0 ? self.new_amount_due : 0.00);
    	    this.el.querySelector('.cancel_order_summary .refundable_total > .value').textContent = this.format_currency(Math.abs(self.refundable_total));
    	    this.el.querySelector('.cancel_order_summary .cancel_charge > .value').textContent = this.format_currency(self.cancel_charge);
    	},
    	_calculate_cancellation_charges: function(){
    	    var self = this;
    	    var price = 0.00;
    	    if(self.pos.config.cancellation_charges_type == "percentage"){
                price = (self.get_total() * self.pos.config.cancellation_charges) / 100;
            } else {
                price = self.pos.config.cancellation_charges;
            }
            return price
    	},
    	add_charge_product: function(){
    	    var self = this;
    	    var selectedOrder = self.pos.get_order();
    	    var price = self._calculate_cancellation_charges();
    	    if(self.pos.config.cancellation_charges_product_id){
                var cancel_product = self.pos.db.get_product_by_id(self.pos.config.cancellation_charges_product_id[0]);
                if(cancel_product){
                    selectedOrder.add_product(cancel_product, {quantity: 1, price: price });
                    selectedOrder.get_selected_orderline().set_cancel_item(true);
                } else {
                    alert(_t("Cannot Find Cancellation Product"));
                }
            } else {
                alert(_t("Please configure Cancellation product from Point of Sale Configuration"));
            }
    	},
    	_calculate_refund_amount: function(){
    	    var self = this;
    	    var current_order_total = self.order_tobe_cancel.amount_total - self.get_total();
    	    var customer_paid = (self.order_tobe_cancel.amount_total - self.order_tobe_cancel.amount_due);
            var final_amount = 0.00
            if(current_order_total < customer_paid){
                final_amount = current_order_total - customer_paid;
            }
            return final_amount;
    	},
    	add_refund_product: function(){
    	    var self = this;
    	    var selectedOrder = self.pos.get_order();
    	    var price = self._calculate_refund_amount();
    	    if(self.pos.config.refund_amount_product_id){
                var refund_product = self.pos.db.get_product_by_id(self.pos.config.refund_amount_product_id[0]);
                if(refund_product){

                    selectedOrder.add_product(refund_product, {quantity: 1, price: price });
                } else {
                    alert(_t("Cannot Find Refund Product"));
                }
            } else {
                alert(_t("Please configure Refund product from Point of Sale Configuration"));
            }
    	},
    	add_paid_amount: function(){
    	    var self = this;
    	    var selectedOrder = self.pos.get_order();
    	    if(self.pos.config.prod_for_payment){
    	        var paid_product = self.pos.db.get_product_by_id(self.pos.config.prod_for_payment[0]);
                if(paid_product){
                    selectedOrder.add_product(paid_product, {quantity: -1, price: self.order_tobe_cancel.amount_paid });
                } else {
                    alert(_t("Cannot Find Refund Product"));
                }
    	    } else {
                alert(_t("Please configure Paid Amount product from Point of Sale Configuration"));
            }
    	},
	});
	gui.define_popup({name:'cancel_order_popup', widget: CancelOrderPopup});

    var MaxCreditExceedPopupWidget = PopupWidget.extend({
	    template: 'MaxCreditExceedPopupWidget',
        events: _.extend({}, PopupWidget.prototype.events, {
            'click .button.override_payment':  'click_override_payment',
        }),
        click_override_payment: function(){
        	var self = this;
        	var currentOrder = this.pos.get_order();
        	if(!currentOrder.get_reserved_delivery_date()){
                this.gui.close_popup();
                self.gui.show_popup("delivery_date_popup", {
                    'payment_obj': self.options.payment_obj,
                    'new_date': true,
                    'draft': self.options.draft_order,
                });
                return
            }
        	if(self.options.payment_obj){
        	    if(!currentOrder.get_paying_due() && !currentOrder.get_cancel_order()){
            		currentOrder.set_fresh_order(true);
            	}
                if(currentOrder.get_total_paid() != 0){
                    this.options.payment_obj.finalize_validation();
                    this.gui.close_popup();
                }
                $('.js_reservation_mode').removeClass('highlight');
            } else if(self.options.draft_order){
            	this.pos.push_order(this.pos.get_order());
            	self.gui.show_screen('receipt');
            	this.gui.close_popup();
            }

        },
	});
	gui.define_popup({name:'max_limit', widget: MaxCreditExceedPopupWidget});
	
	var AssignSerialLotPopupWidget = PopupWidget.extend({
	    template: 'AssignSerialLotPopupWidget',
	    show: function(options){
	    	var self = this;
			this._super();
			self.product = options.product;
			this.renderElement()
			if(self.product){
				this.$('#serial_no').focus();
				if(self.product.tracking=="serial"){
					this.$("#serial_no").attr("placeholder", "Enter Serial Number");
					this.$('#div_quantity').hide();
				} else{
					this.$("#serial_no").attr("placeholder", "Enter Lot Number");
					this.$('#div_quantity').show();
				}
			}
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var data = {};
	    	if(self.product.tracking=="serial"){
				var serial_no = this.$('#serial_no').val();
				if(!serial_no){
					alert("Please enter serial number.")
					this.$('#serial_no').focus();
					return
				} else{
					data = {
						'serial_no' : serial_no,
						'qty' : 1,
						'location_id' : self.pos.config.stock_location_id[0],
					}
				}
			} else{
				var lot_no = this.$('#serial_no').val();
				var qty = Number(this.$('#qty').val());
				if(!lot_no || !qty){
					alert("Please Enter both value lot number and quantity.");
					this.$('#serial_no').focus();
					return
				} else{
					data = {
						'serial_no' : lot_no,
						'qty' : qty,
						'location_id' : self.pos.config.stock_location_id[0],
					}
				}
			}
	    	if(data){
	    		new Model('product.template').call('assign_lot',[self.product.product_tmpl_id, data])
                .then(function(res){
                    if(res){
                    	self.gui.close_popup();
                    }
                },function(err,event){
                	console.log("err",err);
    	            event.preventDefault();
    	            self.gui.show_popup('error',{
    	                'title': _t('Error: Could not Save Changes'),
    	                'body': _t('The combination of serial number and product must be unique'),
    	            });
    	        });
	    	}
	    },
    	click_cancel: function(){
    		this.gui.close_popup();
    	},
	    
	});
	gui.define_popup({name:'assign_serial_lot', widget: AssignSerialLotPopupWidget});
});
