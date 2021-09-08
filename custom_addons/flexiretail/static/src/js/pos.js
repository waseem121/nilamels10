odoo.define('flexiretail.pos', function (require) {
"use strict";
	var gui = require('point_of_sale.gui');
	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var chrome = require('point_of_sale.chrome');
	var device = require('point_of_sale.devices');
	var core = require('web.core');
	var PopupWidget = require('point_of_sale.popups');
	var framework = require('web.framework');
	var action = require('web.ActionManager');
	var Model = require('web.DataModel');
	var DB = require('point_of_sale.DB');
	var utils = require('web.utils');
	var core = require('web.core');
	var ActionManager = require('web.ActionManager');
	var common  = require('web.form_common');
	var data    = require('web.data');
	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var session = require('web.Session');
	var chat_manager = require('mail.chat_manager');
	var formats = require('web.formats');

	var _t = core._t;
	var QWeb = core.qweb;
	var round_pr = utils.round_precision;
    var round_di = utils.round_decimals;

    function decimalAdjust(value,flag){
	    var split_value = value.toFixed(3).split('.');
	    //convert string value to integer
	    for(var i=0; i < split_value.length; i++){
	        split_value[i] = parseInt(split_value[i]);
	    }
	    var reminder_value = split_value[1] % 10;
	    if(flag=="one_point"){
	    	var division_value = parseInt(split_value[1] / 1000);
	    }else if(flag=="two_point"){
	    	var division_value = parseInt(split_value[1] / 100);
	    } else if(flag=="three_point"){
	    	var division_value = parseInt(split_value[1] / 10);
	    } else{
	    	var division_value = parseInt(split_value[1] / 10);
	    }
	    var rounding_value;
	    var nagative_sign = false;
	    if(split_value[0] == 0 && value < 0){
	        nagative_sign = true;
	    }
	    if(flag=="two_point"){
	    	var round = split_value[1] - reminder_value;
	    	rounding_value = eval(split_value[0].toString() + '.' + round.toString())
	    } else if(flag=="one_point") {
	    	reminder_value = split_value[1] % 100;
	    	var round = split_value[1] - reminder_value;
	    	rounding_value = eval(split_value[0].toString() + '.' + round.toString())
	    } else if(flag=="50fills"){
	    	var fills_val = 0;
	    	var count = 0;
	    	for (var i=1;i<=Math.max(split_value[1]/50);i++){
	    		fills_val = 50 * i;
	    	}
	    	rounding_value = eval(split_value[0].toString() + '.' + fills_val.toString())
	    } else if(flag=="250fills"){
	    	var fills_val = 0;
	    	var count = 0;
	    	for (var i=1;i<=Math.max(split_value[1]/250);i++){
	    		fills_val = 250 * i;
	    	}
	    	rounding_value = eval(split_value[0].toString() + '.' + fills_val.toString())
	    } else{
		    if(_.contains(_.range(0,5), reminder_value)){
		        rounding_value = eval(split_value[0].toString() + '.' + division_value.toString() + '0' )
		    }else if(_.contains(_.range(5,10), reminder_value)){
		        rounding_value = eval(split_value[0].toString() + '.' + division_value.toString() + '5' )
		    }
	    }
	    if(nagative_sign){
	        return -rounding_value;
	    }else{
	        return rounding_value;
	    }
	}

	models.load_fields("product.product", ['qty_available','type',
		'is_packaging','tracking','can_not_return','attribute_value_ids','write_date',
		'categ_id','standard_price','name','taxes_id','type', 'is_product_pack', 'pack_management', 'product_pack_ids', 'pack_product_qty' ]);
	models.load_fields("account.journal", ['code','shortcut_key','debt','pos_front_display','apply_charges','fees_amount','fees_type','optional', 'is_cashdrawer']);
	models.load_fields("res.partner", ['debt', 'remaining_wallet_amount', 'remaining_amount',
	'property_product_pricelist', 'remaining_credit_limit', 'credit_limit']);
	models.load_fields("res.company", ['pos_price','pos_quantity','pos_discount','pos_search','pos_next','pos_back','pos_validate']);
	models.load_fields("res.users", ['can_give_discount','can_change_price', 'user_discount', 'login','allowed_picking_type_ids']);
	models.load_fields("pos.category", ['return_valid_days']);

	models.PosModel.prototype.models.push(
//		{
//	    	model:  'product.attribute',
//	        fields: [ 'name',
//	                  'value_ids',
//	                ],
//	        loaded: function(self,attributes){
//	        	self.db.add_product_attributes(attributes);
//	        },
//	    },
//	    {
//	    	model:  'product.attribute.value',
//	        fields: [  'name',
//	                   'attribute_id',
//	                ],
//	        loaded: function(self,values){
//	        	 self.db.add_product_attribute_values(values);
//	        },
//        },
//        {
//            model:  'product.template',
//            fields: ['name',
//                     'display_name',
//                     'product_variant_ids',
//                     'product_variant_count',],
//            domain: [['sale_ok','=',true],['available_in_pos','=',true]],
//            context: {
//                display_default_code: false,
//            },
//            loaded: function(self,templates){
//            	self.db.add_templates(templates);
//            },
//        },
		{
			model:  'quick.cash.payment',
		    fields: ['display_name','name_amt'],
		    loaded: function(self,quick_pays){
		        self.quick_pays = quick_pays;
		        self.db.add_quick_payment(quick_pays);
		    },
		},{
            model:  'res.country.state',
            fields: ['name'],
            loaded: function(self,states){
                self.states = states;
            },
        },{
            model:  'aspl.gift.card.type',
            fields: ['name'],
            loaded: function(self,card_type){
                self.card_type = card_type;
            },
        },{
        	model:  'stock.picking.type',
        	fields: [],
        	domain: [['code','=','internal']],
        	loaded: function(self,stock_pick_typ){
        		self.stock_pick_typ = stock_pick_typ;
        		self.db.add_picking_types(stock_pick_typ);
        	},
        },{
        	model:  'stock.location',
        	fields: [],
        	domain: [['usage','=','internal']],
        	loaded: function(self,stock_location){
        		self.stock_location = stock_location;
        	},
        },{
        	model:  'product.category',
            fields: ['id','display_name'],
            domain: null,
            loaded: function(self, product_category){
            	self.product_category = [];
                self.product_category = product_category;
            },
        },{
        	model: 'product.pricelist',
			fields: [],
			context: [['type', '=', 'sale']],
			loaded: function(self, prod_pricelists){
				self.prod_pricelists = [];
				self.prod_pricelists = prod_pricelists;
			},
        },{
		        model:  'stock.config.settings',
		        fields: ['group_stock_production_lot'],
		        domain: null,
		        loaded: function(self, group_stock_production_lot){
		        	self.group_stock_production_lot;
		            self.group_stock_production_lot = group_stock_production_lot[group_stock_production_lot.length-1];
		        },
        },{
            model:  'products.pack',
            loaded: function(self, pack_products){
                self.pack_products = [];
                _.each(pack_products, function(product){
                    if(self.pack_products && self.pack_products[product.product_tmpl_id[0]]){
                        self.pack_products[product.product_tmpl_id[0]].push(product);
                    } else {
                        self.pack_products[product.product_tmpl_id[0]] = [product]
                    }
                });
            },
        });

	chrome.Chrome.include({
		events: {
            "click .pos-message": "on_click_pos_message",
        },
		loading_hide: function(){
	        var self = this;
	        this._super();
//	        if(self.pos.config.require_cashier){
//		        this.widget.username.$el.html("");
//		        this.gui.select_user({
//		            'security':     true,
//		            'title':      _t('Login'),
//		        }).then(function(user){
//		            self.pos.set_cashier(user);
//		            self.widget.username.$el.html(user.name);
//		        });
//	        }
	    },
	    renderElement: function(){
	        var self = this;
	        this.filter = false;
	        chat_manager.bus.on("update_channel_unread_counter", this, this.update_counter);
	        chat_manager.is_ready.then(this.update_counter.bind(this));
	        return this._super();
	    },
	    is_open: function () {
	        return this.$el.hasClass('open');
	    },
	    update_counter: function () {
	        var counter = chat_manager.get_unread_conversation_counter();
	        this.$('.o_notification_counter').text(counter);
	        this.$el.toggleClass('o_no_notification', !counter);
	        this.$el.toggleClass('o_unread_chat', !!chat_manager.get_chat_unread_counter());
	        if (this.is_open()) {
	            this.update_channels_preview();
	        }
	    },
	    update_channels_preview: function () {
	        var self = this;
	        chat_manager.is_ready.then(function () {
	            var channels = _.filter(chat_manager.get_channels(), function (channel) {
	                if (self.filter === 'chat') {
	                    return channel.is_chat;
	                } else if (self.filter === 'channels') {
	                    return !channel.is_chat && channel.type !== 'static';
	                } else {
	                    return channel.type !== 'static';
	                }
	            });
	            chat_manager.get_channels_preview(channels).then(self._render_channels_preview.bind(self));
	        });
	    },
	    _render_channels_preview: function (channels_preview) {
	        channels_preview.sort(function (c1, c2) {
	            return Math.min(1, c2.unread_counter) - Math.min(1, c1.unread_counter) ||
	                   c2.is_chat - c1.is_chat ||
	                   c2.last_message.date.diff(c1.last_message.date);
	        });
	        _.each(channels_preview, function (channel) {
	            channel.last_message_preview = chat_manager.get_message_body_preview(channel.last_message.body);
	            if (channel.last_message.date.isSame(new Date(), 'd')) {  // today
	                channel.last_message_date = channel.last_message.date.format('LT');
	            } else {
	                channel.last_message_date = channel.last_message.date.format('lll');
	            }
	        });
	        this.gui.show_popup('message',{list:channels_preview});
	    },
	    on_click_pos_message: function () {
	        var self = this;
	        if (this.gui.current_popup) {
	            this.gui.close_popup();
	        }
	        else{
	             this.update_channels_preview();
	        }
	    },
	    on_click_new_message: function () {
            chat_manager.bus.trigger('open_chat');
        },
	});
	device.BarcodeReader.include({
		scan: function(code){
			var self = this;
			this._super(code);
			var def  = new $.Deferred();
			var order = self.pos.get_order(); 
			if(order.get_barcode_for_manager()){
				if(self.pos.users){
					self.pos.users.map(function(user){
						if(code === user.barcode){
							var discount = $('#discount_value').text();
							if($.inArray(user.id,self.pos.config.pos_managers_ids) !== -1){
								if(user.user_discount === 0){
									order.set_manager_name_for_discount([user.id,user.display_name]);
									$("#manager_name").text(order.get_manager_name_for_discount() ? order.get_manager_name_for_discount()[1] : "");
									$('div.confirm').prop('disabled', false);
									$('div.confirm').css('color','#555');
									$('div.dis_auth_confirm').trigger('click');
								}else if(user.user_discount > discount){
									order.set_manager_name_for_discount([user.id,user.display_name]);
									$("#manager_name").text(order.get_manager_name_for_discount() ? order.get_manager_name_for_discount()[1] : "");
									$('div.confirm').prop('disabled', false);
									$('div.confirm').css('color','#555');
									$('div.dis_auth_confirm').trigger('click');
								}else{
									alert(_t("you are not authorised to give discount."));
									$('#manager_barcode').focus();
								}
							}else{
								alert(_t("you are not authorised to give discount."));
								$('#manager_barcode').focus();
							}
						}
					});
				}
			}
			if (self.pos.product_list.length == 0) {
				var fields = ['display_name', 'list_price','price','pos_categ_id', 'taxes_id', 'ean13', 'default_code', 
                              'to_weight', 'uom_id', 'uos_id', 'uos_coeff', 'mes_type', 'description_sale', 'description',
                              'product_tmpl_id'];
                var domain = ['|',['barcode', '=', code],['barcode', '=', '0'+code]];
                var context = { 
                    pricelist: self.pos.pricelist.id, 
                    display_default_code: false, 
                }
                new Model("product.product").get_func("search_read")(domain=domain, fields=fields, 0, false, false, context=context)
                .pipe(function(result) {
                    if (result[0]) {
                        self.pos.get_order().add_product(result[0]);
                    }
                });
			}
		},
	});
	gui.Gui.include({
		ask_password: function(password) {
	        var self = this;
	        var ret = new $.Deferred();
	        if (password) {
	            this.show_popup('password',{
	                'title': _t('Password ?'),
	                confirm: function(pw) {
	                    if (pw !== password) {
	                    	alert(_t("Wrong Password."));
	                        self.select_user({
	            	            'security':     true,
	            	            'title':      _t('Login'),
	            	        }).then(function(user){
	            	            self.pos.set_cashier(user);
	            	            self.chrome.widget.username.$el.html(user.name);
	            	        });
	                        ret.reject();
	                    } else {
	                    	self.pos.db.notification('success','Successfull login!');
	                        ret.resolve();
	                    }
	                },
	                cancel: function(){
	                	self.select_user({
	        	            'security':     true,
	        	            'title':      _t('Login'),
	        	        }).then(function(user){
	        	            self.pos.set_cashier(user);
	        	            self.chrome.widget.username.$el.html(user.name);
	        	        });
	                }
	            });
	        } else {
	            ret.resolve();
	        }
	        return ret;
	    },
	    select_user: function(options){
	    	options = options || {};
	        var self = this;
	        var def  = new $.Deferred();
	        var list = [];
	        var cashier_ids = self.pos.shop.cashier_ids;
	        var users = self.pos.users;

	        if(cashier_ids.length != 0){
	        	for(var j=0;j<users.length;j++){
	        		if($.inArray(users[j].id, cashier_ids) != -1){
	        			list.push({
		                    'label': users[j].name,
		                    'item':  users[j],
		                });
	        		}
	        	}
	        }else{
	        	for(var j=0;j<users.length;j++){
        			list.push({
	                    'label': users[j].name,
	                    'item':  users[j],
	                });
	        	}
	        }

        	this.show_popup('selection',{
	            'title': options.title || _t('Select User'),
	            list: list,
	            confirm: function(user){ def.resolve(user); },
	            cancel:  function(){
	                if(self.pos.get_cashier()){
	                    def.resolve(self.pos.get_cashier());
	                }
	            },
	        });
	        return def.then(function(user){
	            if (options.security && user !== options.current_user && user.pos_security_pin) {
	                return self.ask_password(user.pos_security_pin).then(function(){
	                    return user;
	                });
	            } else {
	                return user;
	            }
	        });
	    },
	});

	var SideBarButton = screens.ActionButtonWidget.extend({
	    template: 'SideBarButton',
//	    button_click: function(){
//			$("#wrapper").removeClass('oe_hidden');
//			$("#wrapper").toggleClass("toggled ");
//			$(".sidebar").find('i').toggleClass('fa fa-angle-double-right fa fa-angle-double-left');
//	    },
	});

	screens.define_action_button({
	    'name': 'sidebarmenu',
	    'widget': SideBarButton,
	});

	screens.ProductScreenWidget.include({
		init: function(parent, options){
            var self = this;
            this._super(parent,options);
            //order_widget = new screens.OrderWidget(this, {});
            this.state = new models.NumpadState();
            var timeStamp = 0;
            var ok = true;

            this.handler_find_operation = function(e){
                var state = self.numpad.state; 
                var token = String.fromCharCode(e.which);
                var qty = self.pos.company.pos_quantity || '';
                var search = self.pos.company.pos_search || '';
                var discount = self.pos.company.pos_discount || '';
		        var price = self.pos.company.pos_price || '';
                var cashregisters = self.pos.cashregisters;
                var paymentLines_keys = [];
                if (!(token == discount || token == price || (e.which >= 48 && e.which <= 57) 
		    			|| e.which == 190 || token == qty || token == search || e.which == 8)) {
                    var flag = true;
		    		_.each(cashregisters, function(paymentline){
				        if (paymentline.journal.shortcut_key && paymentline.journal.shortcut_key == String.fromCharCode(e.which)) {
				        	flag = false;
				        }
					});
		    		if (flag) {
		    			return
		    		}
				}
                if(self.gui.get_current_screen()=='products'){
                    var flag = false;
                    _.each(cashregisters, function(paymentline){
                        if (paymentline.journal.shortcut_key && paymentline.journal.shortcut_key == String.fromCharCode(e.which)) {
                            flag = true;
                        }
                    });
                    if (flag) {
                        return
                    }
                }
                var order = self.pos.get('selectedOrder');
                var oldBuffer = self.numpad.state.get('buffer');
                if (oldBuffer === '0' || oldBuffer == undefined) {
                    self.numpad.state.set({
                        buffer: String.fromCharCode(e.which)
                    });
                } else if (oldBuffer === '-0') {
                    self.numpad.state.set({
                        buffer: "-" + String.fromCharCode(e.which)
                    });
                } else {
                    self.numpad.state.set({
                        buffer: (self.numpad.state.get('buffer')) + String.fromCharCode(e.which)
                    });
                }

                var cashregisters = self.pos.cashregisters;
                var paymentLines = order.paymentlines;
                var paymentLines_keys = [];
                _.each(cashregisters, function(paymentline){
                    if (paymentline.journal.shortcut_key) {
                        paymentLines_keys.push(paymentline.journal.shortcut_key);
                    }
                    if (paymentline.journal.shortcut_key && paymentline.journal.shortcut_key == String.fromCharCode(e.which)) {
                        order.add_paymentline(paymentline);
                        self.chrome.screens.payment.reset_input();
                        self.chrome.screens.payment.render_paymentlines();
                    }
                });

                var order_line = order.get_selected_orderline();
                if($( "div.searchbox" ).find( "input" ).is(':focus') || self.gui.get_current_screen()=='payment' || self.gui.get_current_screen() == 'receipt'){
                    return
                }
                else if(! self.gui.get_current_screen()=='payment'){
                if (e.which == 8 && order_line) {
                    if(state.get('buffer') === ""){
                        if(state.get('mode') === 'quantity'){
                            order_line.set_quantity('remove');
                        }else if( state.get('mode') === 'discount'){
                            order_line.set_discount(state.get('buffer'));
                        }else if( state.get('mode') === 'price'){
                            order_line.set_unit_price(state.get('buffer'));
                        }
                    }else{
                        var newBuffer = "";
                        state.set({ buffer: newBuffer });
                        if(state.get('mode') === 'quantity'){
                            if(state.get('buffer') === "") {
                                order_line.set_quantity('remove');
                            } else {
                                order_line.set_quantity(state.get('buffer'));
                            }
                        }else if( state.get('mode') === 'discount'){
                            order_line.set_discount(state.get('buffer'));
                        }else if( state.get('mode') === 'price'){
                            order_line.set_unit_price(state.get('buffer'));
                        }
                    }
                }
                }
                if($( "div.searchbox" ).find( "input" ).is(':focus') || self.gui.get_current_screen()=='payment' || self.gui.get_current_screen() == 'receipt')
                {
                    return;
                }
                else{
                if (token == search) {
                    $( "div.searchbox" ).find( "input" ).focus();
                    return;
                }else if(e.which == 118){
                    self.gui.show_screen('payment');
                }
                else if (token == discount) {
                    self.numpad.state.set('mode', 'discount');
                    state.set({
                        buffer: "0",
                        mode: 'discount'
                    });
                    self.numpad.changedMode();
                } else if (token == qty) {
                    self.numpad.state.set('mode', 'quantity');
                    state.set({
                        buffer: "0",
                        mode: 'quantity'
                    });
                    self.numpad.changedMode();
                } else if (token == price) {
                    self.numpad.state.set('mode', 'price');
                    state.set({
                        buffer: "0",
                        mode: 'price'
                    });
                    self.numpad.changedMode();
                } else if (order_line && e.which != 113 && e.which != 100 && e.which != 112) {
                    var mode = self.numpad.state.get('mode');
                    if( mode === 'quantity'){
                        if (order_line.get_quantity() == 1 || order_line.get_quantity() == 0 ) {
                            if (state.get('buffer').length >= 1) {
                                if ((state.get('buffer').length == 2 || state.get('buffer').length == 3) && state.get('buffer').slice(0,1) == '1') {
                                    order_line.set_quantity(state.get('buffer'));
                                }else{
                                    var qty = state.get('buffer').split('');
                                    state.set({
                                        buffer: qty[qty.length-1],
                                        mode: 'quantity'
                                    });
                                    order_line.set_quantity(qty[qty.length-1]);
                                }
                            }
                        } else {
                            order_line.set_quantity(state.get('buffer'));
                        }
                    }else if( mode === 'discount'){
                        order_line.set_discount(state.get('buffer'));
                    }else if( mode === 'price'){
                        order_line.set_unit_price(state.get('buffer'));
                    }
                } else {
                    return;
                }
            }
            },

            $('body').on('keypress', function(e){
            	var focus = $(":focus");
            	if(focus.length > 0){
            		if(focus[0].type){
            			return
            		}
            	}
                if (timeStamp + 50 > new Date().getTime()) {
                    ok = false;
                } else {
                    ok = true;
                }
                timeStamp = new Date().getTime();
                if(self.gui.get_current_screen()=='payment' && e.which === 8){
                	return;
                }
                setTimeout(function(){
                    if (ok) {self.handler_find_operation(e);}
                }, 50);
            });

            var rx = /INPUT|SELECT|TEXTAREA/i;
            $('body').on("keydown keypress", function(e){
                var order = self.pos.get('selectedOrder');
                if( e.which == 8 && order.get_selected_orderline() && self.gui.get_current_screen() != 'payment'){ // 8 == backspace
                    if(!rx.test(e.target.tagName) || e.target.disabled || e.target.readOnly ){
                        e.preventDefault();
                        var state = self.numpad.state; 
                        if (state.get('mode') == 'quantity') {
                            state.set({
                                buffer: state.get('buffer').slice(0,-1),
                                mode: 'quantity'
                            });
                            var qty = state.get('buffer')
                            if (qty == '' && order.get_selected_orderline().get_quantity() == 0) {
                                qty = 'remove';
                            }
                            order.get_selected_orderline().set_quantity(qty);
                        }
                        if (state.get('mode') == 'discount') {
                            state.set({
                                buffer: state.get('buffer').slice(0,-1),
                                mode: 'discount'
                            });
                            order.get_selected_orderline().set_discount(state.get('buffer'));
                        }
                        if (state.get('mode') == 'price') {
                            state.set({
                                buffer: state.get('buffer').slice(0,-1),
                                mode: 'price'
                            });
                            order.get_selected_orderline().set_unit_price(state.get('buffer'));
                        }
                    }
                } else if (e.which == 8 && self.gui.get_current_screen() != 'payment') {
                    if(!rx.test(e.target.tagName) || e.target.disabled || e.target.readOnly ){
                        e.preventDefault();
                    } 
                }
            });
        },
		start: function(){
			var self = this;
			this._super();
			var pos = this.pos;
			$('button.customer_button').click(function(){
				self.gui.show_screen('clientlist');
			});
			/* datepicker hide */
			$('body').on('click', function (e) {
				if($(e.target).attr('class') == "hasDatepicker" || $(e.target).attr('class') == "search_date hasDatepicker" || $(e.target).attr('class') == "date hasDatepicker" || $(e.target).attr('class') == "datetime hasDatepicker" || $(e.target).attr('class') == "ui-icon ui-icon-circle-triangle-e"){
					$("#ui-datepicker-div").show();
				} else{
				    if ($(e.target).closest("#ui-datepicker-div").length === 0 ) {
				        $("#ui-datepicker-div").hide();
				    }
				}
			});
			$('div#menu a#sale_mode').parent().click(function(event){
				var selectedOrder = pos.get_order();
                var id = $(event.target).data("category-id");
                selectedOrder.set_ret_o_id('');
                selectedOrder.set_sale_mode(true);
                selectedOrder.set_missing_mode(false);
                selectedOrder.set_ref_cust_label(false);
                var category = pos.db.get_category_by_id(id);
                self.product_categories_widget.set_category(category);
                self.product_categories_widget.renderElement();
                
                $("div#menu a#sale_mode").parent().css({'background':'#6EC89B','color':'#FFF'});
                $("div#menu a#return_order").parent().css({'background':'','color':'#000'});
                $("div#menu a#missing_return_order").parent().css({'background':'','color':'#000'});
                $('div#menu a#reservation_mode').parent().css({'background':'','color':'#000'});
                selectedOrder.set_ret_o_ref('');
                $('#return_order_ref').html('');
                $('#ref_customer_name').html("")
                $("span.remaining-qty-tag").css('display', 'none');
			});
			$('div#menu a.all_products').parent().click(function(event){
				var id = $(this).children().attr('id');
				if(id == 'on_hand_qty_mode'){
					var all_data = self.pos.db.get_all_product_data();
//					var delivery_product_id = self.pos.config.delivery_product_id[0];
//					for(var i=0;i<all_data.length;i++){
//						if(all_data[i].id == delivery_product_id){
//							all_data.splice(i,1);
//						}
//					}
					$(this).css({'background':'','color':'#000'});
					$(this).children().attr('class','all_products');
					$(this).children().attr('id','');
					$(this).find('img').attr('src', '/flexiretail/static/src/img/icons/qty_on_hand_off.png');
					self.product_list_widget.set_product_list(all_data);
				}else{
					var result = self.pos.db.get_product_qty();
					$(this).css({'background':'#6EC89B','color':'#FFF'});
					$(this).children().attr('id','on_hand_qty_mode');
					$(this).children().attr('class','all_products');
					$(this).find('img').attr('src', '/flexiretail/static/src/img/icons/qty_on_hand_on.png');
					self.product_list_widget.set_product_list(result);
				}
			});
			$('div#menu a#reservation_mode').parent().click(function(){
				var order    = self.pos.get_order();
				order.set_reservation_mode(!order.get_reservation_mode());
//	        	order.get_reservation_mode() ? $(this).css({'background':'#6EC89B','color':'#FFF'}) : $(this).css({'background':'','color':'#000'});
				if(order.get_reservation_mode()){
	        		$(this).css({'background':'#6EC89B','color':'#FFF'});
	        		$("div#menu a#sale_mode").parent().css({'background':'','color':'#000'});
	        	}else{
	        		$(this).css({'background':'','color':'#000'});
	        		$("div#menu a#sale_mode").parent().css({'background':'#6EC89B'});
	        	}
			});

			$('div#menu a#missing_return_order').parent().click(function(event){
				var selectedOrder = pos.get_order();
                var id = $(event.target).data("category-id");
//                selectedOrder.set_ret_o_id('Missing Receipt');
                selectedOrder.set_sale_mode(false);
                selectedOrder.set_missing_mode(true);
                var category = pos.db.get_category_by_id(id);
                self.product_categories_widget.set_category(category);
                self.product_categories_widget.renderElement();
                
                $("div#menu a#sale_mode").parent().css({'background':'','color':'#000'});
                $("div#menu a#return_order").parent().css({'background':'','color':'#000'});
                $("div#menu a#missing_return_order").parent().css({'background':'#6EC89B','color':'#FFF'});
                selectedOrder.set_ret_o_ref('Missing Receipt');
                $('#return_order_ref').html('Missing Receipt');
                $("span.remaining-qty-tag").css('display', 'none');
			});
			$('div#menu a#return_order').parent().click(function(){
                var selectedOrder = pos.get_order();
                selectedOrder.set_sale_mode(false);
                selectedOrder.set_missing_mode(false);
                $("div#menu a#sale_mode").parent().css({'background':'','color':'#000'});
                $("div#menu a#return_order").parent().css({'background':'#6EC89B','color':'#FFF'});
                $("div#menu a#missing_return_order").parent().css({'background':'','color':'#000'});
                self.gui.show_popup('PosReturnOrderOption');
			});
			$('div#menu a#put_money_in').parent().click(function(){
			    var is_cashdrawer = false;
			    _.each(self.pos.cashregisters, function(cashregister){
			        if(cashregister.journal.is_cashdrawer && cashregister.journal.type === _t("cash")){
                        is_cashdrawer = true;
                        return
			        }
			    });
			    if (self.pos.config.cash_control && is_cashdrawer){
                    var msg_show_put_money_in = "";
                    msg_show_put_money_in += "<div class='container1'>" +
                                                "<div class='sub-container1'>" +
                                                    "<table id='tbl_id'>" +
                                                        "<tr>" +
                                                            "<td>Reason</td>" +
                                                            "<td id='td_id'><input id='txt_reason_in_id' type='text' name='txt_reason_in'></td>" +
                                                        "</tr>" +
                                                        "<tr>" +
                                                            "<td>Amount</td>" +
                                                            "<td id='td_id'><input id='txt_amount__in_id' type='text' name='txt_amount_in'></td>" +
                                                        "<tr>" +
                                                    "</table>" +
                                                "</div>" +
                                            "</div>";
                    self.gui.show_popup('put_money_in',{msg_show_put_money_in:msg_show_put_money_in});
				} else {
				    alert(_t('Please enable cash control from configuration and is drawer in cash journal.'));
				}
			});
			$('div#menu a#take_money_out').parent().click(function(){
			    var is_cashdrawer = false;
			    _.each(self.pos.cashregisters, function(cashregister){
			        if(cashregister.journal.is_cashdrawer && cashregister.journal.type === _t("cash")){
                        is_cashdrawer = true;
                        return
			        }
			    });
			    if (self.pos.config.cash_control && is_cashdrawer){
                    var msg_show_take_money_out = "<div class='container1'>" +
                                                    "<div class='sub-container1'>" +
                                                        "<table id='tbl_id'>" +
                                                            "<tr>" +
                                                                "<td>Reason</td>" +
                                                                "<td id='td_id'><input id='txt_reason_out_id' type='text' name='txt_reason_in'></td>" +
                                                            "</tr>" +
                                                            "<tr>" +
                                                                "<td>Amount</td>" +
                                                                "<td id='td_id'><input id='txt_amount__out_id' type='text' name='txt_amount_in'></td>" +
                                                            "<tr>" +
                                                        "</table>" +
                                                    "</div>" +
                                                "</div>";
                    self.gui.show_popup('take_money_out',{msg_show_take_money_out:msg_show_take_money_out});
				} else {
				    alert(_t('Please enable cash control from configuration and is drawer in cash journal.'));
				}
			});
			$('div#menu a#product_qty').parent().click(function(){
				var order = self.pos.get_order();
		        var lines = order.get_orderlines();
		        var orderLines = [];
		        var length = order.orderlines.length;
		        for (var i=0;i<length;i++){
		        		orderLines.push(lines[i].export_as_JSON());
		        }
		        if(orderLines.length === 0){
		        	alert(_t("No product selected !"));
		        }
		        if(self.pos.get_order().get_selected_orderline()){
		        	var prod = self.pos.get_order().get_selected_orderline().get_product()
		        	var prod_info = [];
	                var total_qty = 0;
	                var total_qty = 0;
	                new Model('stock.warehouse').call('disp_prod_stock',[prod.id,self.pos.shop.id]).then(function(result){
	                if(result){
	                	prod_info = result[0];
	                    total_qty = result[1];
	                    var prod_info_data = "";
	                    _.each(prod_info, function (i) {
	                    	prod_info_data += "<tr>"+
	                        "	<td style='color:gray;font-weight: initial !important;padding:5px;text-align: left;padding-left: 15px;'>"+i[0]+"</td>"+
	                        "	<td style='color:gray;font-weight: initial !important;padding:5px;text-align: right;padding-right: 15px;'>"+i[1]+"</td>"+
	                        "</tr>"
	                    });
	                    self.gui.show_popup('product_qty_popup',{prod_info_data:prod_info_data,total_qty: total_qty,'from_selected_line': true});
	                }
			    	}).fail(function (error, event){
				        if(error.code === -32098) {
				        	alert(_t("Odoo server down..."));
				        	event.preventDefault();
			           }
			    	});
		        }
			});
			$('div#menu a#order_list').parent().click(function(){
				self.gui.show_screen('orderlist');
			});
			$('div#menu a#x_report').parent().click(function(){
				var pos_session_id = self.pos.pos_session.id;
	        	new Model("report").call('get_html', [pos_session_id, 'flexiretail.front_sales_thermal_report_template_xreport']).done(
					function(report_html) {
						if(self.pos.config.iface_print_via_proxy && self.pos.proxy.get('status').status === "connected"){
	                        self.pos.proxy.print_receipt(report_html);
	                    } else {
	                    	var print = {'context': {'active_id': [pos_session_id],
	                            'active_ids':[pos_session_id]},
	                            'report_file': 'flexiretail.front_sales_report_pdf_template_xreport',
	                            'report_name': 'flexiretail.front_sales_report_pdf_template_xreport',
	                            'report_type': "qweb-pdf",
	                            'type': "ir.actions.report.xml"};
				                var options = {};
				                var action_manager = new ActionManager();
				                action_manager.ir_actions_report_xml(print);
	                    }
					});
			});
			$('div#menu a#save_as_draft').parent().click(function(){
	            var selectedOrder = self.pos.get_order();
	            selectedOrder.initialize_validation_date();
	            var currentOrderLines = selectedOrder.get_orderlines();
	            var client = selectedOrder.get_client();
	            var orderLines = [];
	            _.each(currentOrderLines,function(item) {
	                return orderLines.push(item.export_as_JSON());
	            });
	            if (orderLines.length === 0) {
	                return alert (_t('Please select product !'));
	            } else {
	            	if( self.pos.config.require_customer && !selectedOrder.get_client()){
	            		self.gui.show_popup('error',{
	                        message: _t('An anonymous order cannot be confirmed'),
	                        comment: _t('Please select a client for this order. This can be done by clicking the order tab')
	                    });
	                    return;
	            	}
	            	if(selectedOrder.get_reservation_mode() &&
	            	self.pos.config.allow_reservation_with_no_amount){
	            		if(!selectedOrder.get_client()){
							self.gui.show_screen('clientlist');
							return
						}
						var credit = selectedOrder.get_total_with_tax() - selectedOrder.get_total_paid();
						if (client && credit > client.remaining_credit_limit){
							self.gui.show_popup('max_limit',{
								remaining_credit_limit: client.remaining_credit_limit,
								draft_order: true,
							});
							return
						}
	            	}
	                self.pos.push_order(selectedOrder);
	                self.gui.show_screen('receipt');
	            }
			});
			$('div#menu a#referral_customer').parent().click(function(){
			    self.gui.show_screen('referral_customer');
			});
			$('div#menu a#pos_today_sale').parent().click(function(){
		    	var str_payment = '';
		    	new Model('pos.session').call('get_session_report',[]).then(function(result){
		            if(result['error']){
		            	alert(_t(result['error']));
		            }
		            if(result['payment_lst']){
						_.each(result['payment_lst'],function(val,key){
								str_payment+="<tr><td style='font-size: 14px;padding: 8px;'>"+key+"</td>" +
								"<td style='font-size: 14px;padding: 8px;'>"+self.format_currency(val.toFixed(3))+"</td>" +
								"</tr>";
						});
					}
		            self.gui.show_popup('pos_today_sale',{result:result,str_payment:str_payment});
		    	}).fail(function (error, event){
			        if(error.code === -32098) {
			        	alert(_t("Odoo server down..."));
			        	event.preventDefault();
		           }
		    	});
			});
			$('#print_lastorder').click(function(){
//				if(self.pos.product_list.length <= 0 && !self.pos.db.get_is_product_load()){
//                	alert("Please wait, Products are still loading...");
//				}
//				if(self.pos.get('pos_order_list').length > 0){
//					var last_order_id = Math.max.apply(Math,self.pos.get('pos_order_list').map(function(o){return o.id;}))
//					$('#print_order').trigger('click', [{data:last_order_id}]);
//				} else {
//					alert(_t("No order to print."));
//				}
				if (self.pos.old_receipt) {
		            self.pos.proxy.print_receipt(self.pos.old_receipt);
		        } else {
		            self.gui.show_popup('error', {
		                'title': _t('Nothing to Print'),
		                'body':  _t('There is no previous receipt to print.'),
		            });
		        }
			});
			$('#internal_transfer').click(function(){
				var selectedOrder = self.pos.get_order();
		        var currentOrderLines = selectedOrder.get_orderlines();
		        if(self.pos.stock_pick_typ.length == 0){
		        	return alert(_t("You can not proceed with 'Manage only 1 Warehouse with only 1 stock location' from inventory configuration."));
		        }
		        if(currentOrderLines.length == 0){
		        	return alert(_t("You can not proceed with empty cart."));
		        }
		        self.gui.show_popup('int_trans_popup',{'stock_pick_types':self.pos.stock_pick_typ,'location':self.pos.stock_location});
			});
			$('#manage_product_screen').click(function(){
				self.gui.show_screen('product_manage_list');
			});
			$('#open_calendar').click(function(){
				self.gui.show_popup('delivery_popup');
			});
			$('#bag').click(function(){
				self.gui.show_popup('bags_popup');
			});
			$('div#menu a#graph_view').parent().click(function(){
				self.gui.show_screen('graph_view');
			});
			$('div#menu a#gift_card').parent().click(function(){
				self.gui.show_screen('giftcardlistscreen');
			});
			$('div#menu a#gift_voucher').parent().click(function(){
				self.gui.show_screen('giftvoucherlistscreen');
			});
			$('#split_gift').click(function(){
				var order    = self.pos.get_order();
	            var lines    = order.get_orderlines();
	            var flag = false;
	            if(lines.length > 0) {
	            	lines.map(function(line){
	            		if(line.get_line_for_gift_receipt()){
	                		flag = true;
	                	}
	            	})
	            	if(flag){
	            		self.gui.show_popup('split_product_popup');
	            	}else{
	            		alert("Please select product for gift receipt.");
	            	}
	            } else {
	                $( ".order-empty" ).effect( "bounce", {}, 500 );
	            }
			});
			$('#gift_receipt').click(function(){
				var order    = self.pos.get_order();
	            var lines    = order.get_orderlines();
	            var selected_line = order.get_selected_orderline();
	            order.set_gift_receipt_mode(!order.get_gift_receipt_mode());
	            if(order.get_gift_receipt_mode()){
	                $('#gift_receipt').addClass('gift_mode_on');
	            } else {
	                $('#gift_receipt').removeClass('gift_mode_on')
	            }
	            if (selected_line) {
	                selected_line.set_line_for_gift_receipt(order.get_gift_receipt_mode());
	            }
			});

			$('#show_reserved_order_list').click(function(){
			    self.gui.show_screen('reserved_orderlist');
			});
			$('#product_pack_btn').click(function(){
			    self.gui.show_screen('pack_list');
//			    self.gui.show_screen('');
			});
			$('#global_discount_btn').click(function(){
				var order = self.pos.get_order();
	            var orderlines = order.get_orderlines();
				if(orderlines && orderlines[0]){
					self.gui.show_popup('custom_discount_popup');
				}
				else {
					alert("Please select product")
				}
			});
			
			$("#doctor_report_btn").click(function(){
				self.gui.show_popup('DoctorSalesReport');
			});
			$("#clear_discount").click(function(){
            	var order = self.pos.get_order();
    			var orderlines = order.get_orderlines();
    			if(orderlines && orderlines[0]){
    				_.each(orderlines,function(line){
    					line.set_share_discount(0);
    					if(line.get_discount()){
    						var base_disc = line.get_discount();
    						line.set_unit_price(line.product.price);
    						line.set_discount(base_disc);
    						line.set_share_discount_amount(0);
    						line.set_item_discount_amount(0);
    					} else{
    						line.set_unit_price(line.product.price);
    						line.set_share_discount_amount(0);
    						line.set_item_discount_amount(0);
    					}
    				});
    				self.pos.chrome.screens.products.order_widget.renderElement();
    			} else{
    				alert("Cart is empty!")
    			}
            });
			// add pricelist
			self.add_pricelist();
		},
		add_pricelist: function(){
		    var self = this;
		    var pricelist_list = this.pos.prod_pricelists;
	        var new_options = [];
	        new_options.push('<option value="">Select Pricelist</option>\n');
	        if(pricelist_list.length > 0){
	            for(var i = 0, len = pricelist_list.length; i < len; i++){
	                new_options.push('<option value="' + pricelist_list[i].id + '">' + pricelist_list[i].display_name + '</option>\n');
	            }
	            $('#price_list').html(new_options);
	            var order = self.pos.get_order();
	            if(order && order.get_client() && order.get_client().property_product_pricelist[0]){
	                $('#price_list').val(order.get_client().property_product_pricelist[0]);
	            }
	            $('#price_list').selectedIndex = 0;
	        }
	        $('#price_list').on('change', function() {
	            var order = self.pos.get_order();
	            var partner_id = self.pos.get_order().get_client() && parseInt(self.pos.get_order().get_client().id);
	            if(order.get_cancel_order()){
	                return
	            }
	            if (!partner_id && $(this).val()) {
	                $('#price_list').html(new_options);
	                alert('Pricelist will not work as customer is not selected !');
	                return;
	            } else {
	                var orderlines = order.get_orderlines() || false;
	                if(orderlines){
	                    if ($(this).val()){
	                        var new_products = [];
	                        var lines = [];
//	                        var product_ids = orderlines.map(function(o) { return o.get_product().id; })
							_.each(orderlines, function(line){
                                var id = line.get_product().id;
                                lines.push({
                                    id: line.get_product().id,
                                    qty: line.get_quantity(),
                                });
                            })
	                        if(lines.length > 0){
	                            new Model("product.product").call('get_product_price',[parseInt($(this).val()), lines], {}, {async: false})
	                            .then(function(result){
	                                if(result){
	                                    // Products
	                                    _.each(result, function(res){
	                                        var product = self.pos.db.get_product_by_id(res.product_id);
	                                        if (product){
	                                        	if(orderlines){
	                                        		_.each(orderlines, function(orderline){
		                                        		if(orderline.get_product().id === product.id && !orderline.get_cross_sell_id()){
		                                        			var old_price = orderline.get_product().price;
		                                        			orderline.set_unit_price(res.new_price);
//		                                        			orderline.set_discount_amount(old_price - orderline.get_unit_price());
		                                        			if(self.pos.config.discount_print_receipt == "public_price"){
		                                        				orderline.set_discount_amount_printing(old_price - orderline.get_unit_price());
	                                        				}
		                                        			if(self.pos.config.store_discount_based_on == "public_price"){
		                                        				orderline.set_discount_amount_storing(old_price - orderline.get_unit_price());
		                                                	}
		                                        		}
			                                        });
	                                        	}
//	                                            product['old_price'] = product['old_price'] || product.price
//	                                            product['price'] = res.new_price
//	                                            new_products.push(product)
//	                                            self.gui.screen_instances.products.product_list_widget.product_cache.clear_node(product.id)
	                                        }
	                                    })
//	                                    if(new_products.length > 0){
//	                                        self.pos.db.add_products(new_products);
//	                                    }
	                                    // Cart
//	                                    var orderlines = order.get_orderlines() || false;
//	                                    if(orderlines){
//	                                        _.each(orderlines, function(orderline){
//	                                            orderline.set_unit_price(orderline.get_product().price);
//	                                        });
//	                                    }
	                                }
	                            });
	                        }
	                    } else {
                            var orderlines = order.get_orderlines() || false;
                            if(orderlines){
                                _.each(orderlines, function(orderline){
                                    orderline.set_unit_price(orderline.get_product().price);
                                });
                            }
	                    }
	                }
	            }
	        });
		},
		show: function(){
			var self = this;
			var client = self.pos.get_client();
			if(client){
				$('.set-customer').html(client.name);
			}else{
				$('.set-customer').html("Customer");
			}
			if(self.pos.config.enable_product_sync){
				$('#searchHeader').find('.searchbox, .sync_products, .category_searchbox').show();
			}else{
				$('#searchHeader').find('.searchbox, .category_searchbox').show();
			}
			this._super();
		},
		close: function(){
			this._super();
			if(this.pos.config.enable_product_sync){
				$('#searchHeader').find('.searchbox, .sync_products, .category_searchbox').hide();
			}else{
				$('#searchHeader').find('.searchbox, .category_searchbox').hide();
			}
		},
	});

	chrome.HeaderButtonWidget.include({
		renderElement: function(){
	        var self = this;
	        this._super();
	        if(this.action){
	            this.$el.click(function(){
	            	self.gui.show_popup('POS_session_config');
	            });
	        }
	    },
	});

	var POSSessionConfig = PopupWidget.extend({
	    template: 'POSSessionConfig',
	    show: function(options){
	        options = options || {};
	        this._super(options);
	
	        this.renderElement();
	        
	    },
    	click_confirm: function(){
    		this.gui.close_popup();
	    	this.gui.close();
	    },
	    renderElement: function() {
            var self = this;
            this._super();
            $('.logout').click(function(){
            	framework.redirect('/web/session/logout');
            });
    	},
    	
	});
	gui.define_popup({name:'POS_session_config', widget: POSSessionConfig});

	var DoctorSalesReport = PopupWidget.extend({
	    template: 'DoctorSalesReport',
	    show: function(options){
	    	var self = this;
	        options = options || {};
	        this._super(options);
	        $("#report_start_date").focus();
	    },
	    click_confirm: function(){
	    	var start_date = $("#report_start_date").val();
	    	var end_date = $("#report_end_date").val();
	    	var config_id = self.pos.config.id;
	    	if(start_date && end_date){
	    		new Model("pos.order").call('sales_report_doctor',[config_id,start_date,end_date], {}, {async: false})
                .then(function(result){
                	if(result){
                		self.pos.get_order().set_doctor_report_data(result);
                    	self.gui.show_screen('SaleReportScreen',{});
                	} else{
                		alert("No Record Found!");
                	}
                });
	    	} else{
	    		alert("Please Select Date.");
	    	}
	    }
	});
	gui.define_popup({name:'DoctorSalesReport', widget: DoctorSalesReport});

	var SaleReportScreenWidget = screens.ScreenWidget.extend({
	    template: 'SaleReportScreenWidget',

	    start: function(){
	    	var self = this;
            this._super();
            this.$('.back').click(function(){
            	self.gui.show_screen('products');
            });
	    },
	    show: function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	var report_data = order.get_doctor_report_data();
	    	this._super();
	    	self.render_list(report_data);
	    },
	    render_list: function(report_data){
        	var self = this;
        	var order = self.pos.get_order();
            var contents = $('.report_container');
            contents.html("");
            var contents_summary = $('.report_summary');
            contents_summary.html("");
        	_.each(report_data['orders'],function(values,key){
                var clientline_html = QWeb.render('ReportlistLine',{widget: self,key:key,values:values});
				var clientline = document.createElement('tbody');
				clientline.innerHTML = clientline_html;
				clientline = clientline.childNodes[1];
				contents.append(clientline);
        	});
            var clientline_html = QWeb.render('ReportSummarylistLine',{widget: self,data:report_data['summary']});
			var clientline = document.createElement('tbody');
			clientline.innerHTML = clientline_html;
			clientline = clientline.childNodes[1];
			contents_summary.append(clientline);
        },
	});
	gui.define_screen({name:'SaleReportScreen', widget: SaleReportScreenWidget});
/*--------------------------------------*\
  |          ORDER LIST SCREEN        |  
\*======================================*/

//Order list screen display the list of orders,
//and allow cashier to reprint order, reorder, view Products,
//Filter orders by state and date, search orders.

	var OrderListScreenWidget = screens.ScreenWidget.extend({
	    template: 'OrderListScreenWidget',

	    init: function(parent, options){
	    	var self = this;
	        this._super(parent, options);
	        this.reload_btn = function(){
	        	$('.fa-refresh').toggleClass('rotate', 'rotate-reset');
	        	self.reloading_orders();
	        };
	        this.unlink_btn = function(){
	            if(confirm('Are you sure you want to delete this order?')){
                    if($(this).hasClass('highlight')){
                        var tobe_unlink_ids = []
                        _.each($('.order-list-contents').find('td #select_order'), function(select_order){
                            if($(select_order).prop('checked')){
                                tobe_unlink_ids.push($(select_order).data('id'));
                            }
                        });
                        if(tobe_unlink_ids.length > 0){
                            new Model('pos.order').call('unlink',[tobe_unlink_ids], {}, {'async': false})
                            .then(function(res){
                                self.reloading_orders();
                            });
                        }
                    }
                }
	        };
	        this._filter_unreserved_order();
	    },

        _filter_unreserved_order: function(){
            var self = this;
            self.unreserved_orders = []
            _.each(self.pos.get('pos_order_list'), function(order){
                if(order && !(order.reserved || order.partial_pay) ){
                    self.unreserved_orders.push(order)
                }
            });
        },
        _get_unreserved_orders: function(){
            if(this.unreserved_orders.length > 0){
                return this.unreserved_orders;
            }
            return false
        },

	    filter:"all",

        date: "all",

	    start: function(){
	    	var self = this;
            this._super();
            
            this.$('.back').click(function(){
                self.gui.back();
            });
            var orders = self._get_unreserved_orders();
            this.render_list(orders);

            $('input#datepicker').datepicker({
           		'dateFormat': 'yy-mm-dd',
               'autoclose': true,
           });

			this.$('#select_all_orders').change(function(){
                var orders = self.pos.get('pos_order_list');
                var unlink_order = false;
                _.each(orders, function(order){
                    if(order.state === "draft"){
                        var checkbox = $('.order-list-contents').find('td #select_order[data-id="'+ order.id +'"]');
                        checkbox.prop('checked', $('#select_all_orders').prop('checked'));
                        if(checkbox.prop('checked')){
                            unlink_order = true
                        }
                    }
                });
                if (unlink_order){
                    self.selected_all_drafts = true;
                    $('.unlink_order').addClass('highlight');
                } else {
                    self.selected_all_drafts = false;
                    $('.unlink_order').removeClass('highlight');
                }
            });

          //button draft
            this.$('.button.draft').click(function(){
            	var orders=self.pos.get('pos_order_list');
            	if(self.$(this).hasClass('selected')){
	        		self.$(this).removeClass('selected');
	        		self.filter = "all";
        		}else{
        			if(self.$('.button.paid').hasClass('selected')){
            			self.$('.button.paid').removeClass('selected');
            		}
        			if(self.$('.button.posted').hasClass('selected')){
            			self.$('.button.posted').removeClass('selected');
            		}
        			self.$(this).addClass('selected');
	        		self.filter = "draft";
        		}
        		self.render_list(orders);
            });

            //button paid
        	this.$('.button.paid').click(function(){
        		var orders=self.pos.get('pos_order_list');
        		if(self.$(this).hasClass('selected')){
	        		self.$(this).removeClass('selected');
	        		self.filter = "all";
        		}else{
        			if(self.$('.button.draft').hasClass('selected')){
            			self.$('.button.draft').removeClass('selected');
            		}
        			if(self.$('.button.posted').hasClass('selected')){
            			self.$('.button.posted').removeClass('selected');
            		}
        			self.$(this).addClass('selected');
	        		self.filter = "paid";
        		}
        		self.render_list(orders);
            });
        	
        	 //button posted
            this.$('.button.posted').click(function(){
            	var orders=self.pos.get('pos_order_list');
            	if(self.$(this).hasClass('selected')){
	        		self.$(this).removeClass('selected');
	        		self.filter = "all";
        		}else{
        			if(self.$('.button.paid').hasClass('selected')){
            			self.$('.button.paid').removeClass('selected');
            		}
        			if(self.$('.button.draft').hasClass('selected')){
            			self.$('.button.draft').removeClass('selected');
            		}
        			self.$(this).addClass('selected');
	        		self.filter = "done";
        		}
        		self.render_list(orders);
            });

            this.$('.order-list-contents').delegate('td #select_order', 'change', function(event){
                var delete_on = false;
                _.each($('.order-list-contents').find('td #select_order'), function(selected_order){
                    if($(selected_order).prop('checked')){
                        delete_on = true
                    }
                });
                if(delete_on){
                    $('.unlink_order').addClass('highlight');
                } else {
                    $('.unlink_order').removeClass('highlight');
                }
            });

            //print order btn
            var selectedOrder;
            this.$('.order-list-contents').delegate('#print_order','click',function(event,p1){
            	var order_id;
            	if(p1){
            		order_id = parseInt(p1.data);
            	} else {
            		order_id = parseInt($(this).data('id'));
            	}
                var result = self.pos.db.get_order_by_id(order_id);
                var selectedOrder = self.pos.get_order();
                selectedOrder.empty_cart();
                selectedOrder.set_client(null);
                if (result && result.lines.length > 0) {
                	var partner = null;
                    if (result.partner_id && result.partner_id[0]) {
                        partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                    }
                    selectedOrder.set_reprint_mode(true);
                    selectedOrder.set_amount_paid(result.amount_paid);
                    selectedOrder.set_amount_return(Math.abs(result.amount_return));
                    selectedOrder.set_amount_tax(result.amount_tax);
                    selectedOrder.set_amount_total(Number(result.amount_total));
                    selectedOrder.set_company_id(result.company_id[1]);
                    selectedOrder.set_date_order(result.date_order);
                    selectedOrder.set_client(partner);
                    selectedOrder.set_pos_reference(result.pos_reference);
                    selectedOrder.set_user_name(result.user_id && result.user_id[1]);
                    selectedOrder.set_order_note(result.note);
                    var statement_ids = [];
                    if (result.statement_ids) {
                    	new Model("account.bank.statement.line").get_func("search_read")([['id', 'in', result.statement_ids]], []).then(
                            function(st) {
                                if (st) {
                                	_.each(st, function(st_res){
                                    	var pymnt = {};
                                    	pymnt['amount']= st_res.amount;
                                        pymnt['journal']= st_res.journal_id[1];
                                        statement_ids.push(pymnt);
                                	});
                                }
                            });
                        selectedOrder.set_journal(statement_ids);
                    }
                    var count = 0;
//                    _.each(result.lines, function(line) {
                    	new Model("pos.order.line").get_func("search_read")([['id', 'in', result.lines]], []).then(
                            function(r) {
                                if (r) {
                                	_.each(r, function(res){
	                                    count += 1;
	                                    var product = self.pos.db.get_product_by_id(Number(res.product_id[0]));
	                                    var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
	                                    line.set_discount(res.discount);
	                                    line.set_quantity(res.qty);
	                                    line.set_unit_price(res.price_unit);
	                                    line.set_line_note(res.note);
	                                    line.set_bag_color(res.is_bag);
	                                    line.set_deliver_info(res.deliver);
	                                    line.set_share_discount_amount(res.discount_amount);
	                                    selectedOrder.add_orderline(line);
                                	});
                                	if (count == (result.lines).length) {
                                    	if(self.pos.config.iface_print_via_proxy){
                                            var receipt = selectedOrder.export_for_printing();
                                            var env = {
                                                receipt: receipt,
                                                widget: self,
                                                pos: self.pos,
                                                order: self.pos.get_order(),
                                                paymentlines: self.pos.get_order().get_paymentlines()
                                            }
                                            self.pos.proxy.print_receipt(QWeb.render('XmlReceipt',env));
                                            self.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                                        }else{
                                        	self.gui.show_screen('receipt');
                                        }
                                    }
                                }
                            }
                        );
//                    });
                    selectedOrder.set_order_id(order_id);
                }
            });

          //reorder btn
            this.$('.order-list-contents').delegate('#re_order','click',function(event){
            	var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_order_by_id(order_id);
                if(result.state == "paid"){
                	alert(_t("Sorry, This order is paid State"));
                	return
                }
                if(result.state == "done"){
                	alert(_t("Sorry, This Order is Done State"));
                	return
                }

                selectedOrder = self.pos.get('selectedOrder');
                if (result && result.lines.length > 0) {
               	 	var count = 0;
               	 	var currentOrderLines = selectedOrder.get_orderlines();
               	 	if(currentOrderLines.length > 0) {
	                 	selectedOrder.set_order_id('');
	                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
							_.each(currentOrderLines,function(item) {
								selectedOrder.remove_orderline(item);
							});
	                    }
               	 	}
                    var partner = null;
                    if (result.partner_id && result.partner_id[0]) {
                        var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                    }
                    selectedOrder.set_client(partner);
               	 	selectedOrder.set_pos_reference(result.pos_reference);
               	 	selectedOrder.set_order_note(result.note);
                    if (result.lines) {
//                    	 _.each(result.lines, function(line) {
                    	new Model("pos.order.line").get_func("search_read")([['id', 'in', result.lines]], []).then(
                                 function(r) {
                                	 if(r){
                                		 _.each(r, function(res){
		                                	 count += 1;
		                                     var product = self.pos.db.get_product_by_id(Number(res.product_id[0]));
		                                     if(product){
			                                     var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
			                                     line.set_discount(res.discount);
			                                     line.set_quantity(res.qty);
			                                     line.set_unit_price(res.price_unit);
			                                     line.set_line_note(res.note);
			                                	 selectedOrder.add_orderline(line);
			                                	 selectedOrder.select_orderline(selectedOrder.get_last_orderline());
			                                	 if (count == (result.lines).length) {
			                                     	self.gui.show_screen('products');
			                                     }
		                                     }
                                		 });
                                	 }
                                 });
                             
//                    	 });
                    	 selectedOrder.set_order_id(order_id);
                    }
                    selectedOrder.set_sequence(result.name);
                }
            });

            //product popup btn
            this.$('.order-list-contents').delegate('#products','click',function(event){
            	var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_order_by_id(order_id);
                if (result && result.lines.length > 0) {
               	 	var count = 0;
               	 	if(result.lines){
               	 		var product_list = "";
           	 			new Model("pos.order.line").get_func("search_read")([['id', 'in', result.lines]], []).then(
                            function(r) {
                           	 if(r){
                           		_.each(r, function(res){
                                	count += 1;
                                    product_list += "<tr>" +
                                    			"<td>"+count+"</td>"+
                                     			"<td>"+res.display_name+"</td>"+
                                     			"<td>"+res.qty+"</td>"+
                                     			"<td>"+res.price_unit.toFixed(3)+"</td>"+
                                     			"<td>"+res.discount+"%</td>"+
                                     			"<td>"+res.price_subtotal.toFixed(3)+"</td>"+
                                     		"</tr>";
                           		});
                           	 }
                           	self.gui.show_popup('product_popup',{product_list:product_list,order_id:order_id,state:result.state});
                        });
               	 	}
                }
            });

            this.$('.order-list-contents').delegate('#re_order_duplicate','click',function(event){
            	var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_order_by_id(order_id);

                selectedOrder = self.pos.get('selectedOrder');
                if (result && result.lines.length > 0) {
               	 	var count = 0;
               	 	var currentOrderLines = selectedOrder.get_orderlines();
               	 	if(currentOrderLines.length > 0) {
	                 	selectedOrder.set_order_id('');
	                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
							_.each(currentOrderLines,function(item) {
								selectedOrder.remove_orderline(item);
							});
	                    }
               	 	}
	               	 var partner = null;
	                 if (result.partner_id && result.partner_id[0]) {
	                     var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
	                 }
	                 selectedOrder.set_client(partner);
               	 	selectedOrder.set_order_note(result.note);

                    if (result.lines) {
//                    	 _.each(result.lines, function(line) {
                    	new Model("pos.order.line").get_func("search_read")([['id', 'in', result.lines]], []).then(
                                 function(r) {
                                	 if(r){
                                		 _.each(r, function(res){
		                                	 count += 1;
		                                     var product = self.pos.db.get_product_by_id(Number(res.product_id[0]));
		                                     if(product){
			                                     var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
			                                     line.set_discount(res.discount);
			                                     line.set_quantity(res.qty);
			                                     line.set_unit_price(res.price_unit)
			                                     line.set_line_note(res.note);
			                                	selectedOrder.add_orderline(line);
			                                	 selectedOrder.select_orderline(selectedOrder.get_last_orderline());
			                                	 if (count == (result.lines).length) {
			                                     	self.gui.show_screen('products');
			                                     }
		                                     }
                                		 });
                                	 }
                                 });

//                    	 });
                    	 selectedOrder.set_order_note(result.note);
                    }
//                    selectedOrder.set_sequence(result.name);
                }
            });

          //search box
            var search_timeout = null;
            if(this.pos.config.iface_vkeyboard && self.chrome.widget.keyboard){
            	self.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }
            this.$('.searchbox input').on('keyup',function(event){
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
	    },
	    show: function(){
	        this._super();
	        $('#select_all_orders').prop('checked', false);
	        this.selected_all_drafts = false;
	        $('.button.unlink_order').removeClass('highlight');
	        this.reload_orders();

	    },
	    perform_search: function(query, associate_result){
	    	var self = this;
            if(query){
                var orders = this.pos.db.search_order(query);
                if ( associate_result && orders.length === 1){
                    this.gui.back();
                }
                if(orders){
                	this.render_list(orders);
                }
            }else{
                var orders = this._get_unreserved_orders()
                if(orders){
                	this.render_list(orders);
        		}
            }
        },
        clear_search: function(){
            var self = this;
        	var orders = this._get_unreserved_orders()
            this.render_list(orders);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
	    render_list: function(orders){
        	var self = this;
            var contents = this.$el[0].querySelector('.order-list-contents');
            contents.innerHTML = "";
            var temp = [];
            if(self.filter !== "" && self.filter !== "all"){
	            orders = $.grep(orders,function(order){
	            	return order.state === self.filter;
	            });
            }
            if(self.date !== "" && self.date !== "all"){
            	var x = [];
            	for (var i=0; i<orders.length;i++){
                    var date_order = $.datepicker.formatDate("yy-mm-dd",new Date(orders[i].date_order));
            		if(self.date === date_order){
            			x.push(orders[i]);
            		}
            	}
            	orders = x;
            }
            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
                var order    = orders[i];
                if(order){
                	order.amount_total = parseFloat(order.amount_total).toFixed(3); 
                	var clientline_html = QWeb.render('OrderlistLine',{widget: this, order:order});
                    var clientline = document.createElement('tbody');
                    clientline.innerHTML = clientline_html;
                    clientline = clientline.childNodes[1];
                    contents.appendChild(clientline);
                }
            }
            $("table.order-list").simplePagination({
				previousButtonClass: "btn btn-danger",
				nextButtonClass: "btn btn-danger",
				previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
				nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
				perPage:self.pos.config.record_per_page > 0 ? self.pos.config.record_per_page : 10
			});
        },
	    reload_orders: function(){
	    	var self = this;
            self._filter_unreserved_order();
	        var orders = self._get_unreserved_orders()
	        this.render_list(orders);
	    },
	    reloading_orders: function(){
	    	var self = this;
	    	self.pos.load_new_orders();
	    	self.reload_orders();
//	    	var date = new Date();
//			var start_date;
//			if(self.pos.config.last_days){
//				date.setDate(date.getDate() - self.pos.config.last_days);
//			}
//			start_date = date.toJSON().slice(0,10);
//			var domain =['create_date','>=',start_date];
//	    	return new Model('pos.order').get_func('ac_pos_search_read')(self.pos.domain_order)
//	    	.then(function(result){
//	    		self.pos.db.add_orders(result);
//	    		self.pos.set({'pos_order_list' : result});
//	    		self.reload_orders();
//	    		return self.pos.get('pos_order_list');
//	    	}).fail(function (error, event){
//               if(error.code === 200 ){    // Business Logic Error, not a connection problem
//              	self.gui.show_popup('error-traceback',{
//                      message: error.data.message,
//                      comment: error.data.debug
//                  });
//              }
//              // prevent an error popup creation by the rpc failure
//              // we want the failure to be silent as we send the orders in the background
//              event.preventDefault();
//              console.error('Failed to send orders:', orders);
//              var orders=self.pos.get('pos_order_list');
//      	        self.reload_orders();
//      	        return orders
//              });
	    },
	    renderElement: function(){
	    	var self = this;
	    	self._super();
	    	self.el.querySelector('.button.reload').addEventListener('click',this.reload_btn);
	    	self.el.querySelector('.button.unlink_order').addEventListener('click',this.unlink_btn);
	    },
	});
	gui.define_screen({name:'orderlist', widget: OrderListScreenWidget});

	var _super_posmodel = models.PosModel;
	 models.PosModel = models.PosModel.extend({
		 initialize: function(session, attributes) {
			_super_posmodel.prototype.initialize.call(this, session, attributes);
	            this.product_list = [];
	            this.product_fields = [];
	            this.product_domain = [];
	            this.product_context = {};
	            this.partner_fields = [];
	            this.partner_domain = [];
	            this.partner_context = {};
	        },
		 fetch: function(model, fields, domain, ctx){
           this._load_progress = (this._load_progress || 0) + 0.05; 
           this.chrome.loading_message(('Loading')+' '+model,this._load_progress);
           return new Model(model).query(fields).filter(domain).context(ctx).all()
		 },
		 load_new_products: function(){
        	 var self = this;
             var def  = new $.Deferred();
             var fields =self.prod_model ? self.prod_model.fields : [];
             new Model('product.product')
             .query(fields)
             .filter([['sale_ok','=',true],['available_in_pos','=',true],['write_date','>',self.db.get_product_write_date()]])
             .context({ pricelist: self.pricelist.id, display_default_code: false, location: self.config.stock_location_id[0]})
             .all({'timeout':3000, 'shadow': true})
             .then(function(products){
                 if (self.db.add_products(products)) {
                     def.resolve();
                 } else {
                     def.reject();
                 }
             }, function(err,event){ event.preventDefault(); def.reject(); });
         return def;
        },
		load_server_data: function(){
			var self = this;
			_.each(this.models, function(model){
                if (model && model.model === 'product.product'){
                    self.prod_model = model;
                }
            });
//			var loaded = _super_posmodel.prototype.load_server_data.call(this);
			var loaded = new $.Deferred();
			var progress = 0;
            var progress_step = 1.0 / self.models.length;
            var tmp = {}; // this is used to share a temporary state between models loaders
            function load_model(index){
        	    var model = self.models[index];
                if(index >= self.models.length){
                    loaded.resolve();
                }else{
                    var model = self.models[index];
                    var cond = typeof model.condition === 'function'  ? model.condition(self,tmp) : true;
                    if (!cond) {
                        load_model(index+1);
                        return;
                    }

                    var fields =  typeof model.fields === 'function'  ? model.fields(self,tmp)  : model.fields;
                    var domain =  typeof model.domain === 'function'  ? model.domain(self,tmp)  : model.domain;
                    var context = typeof model.context === 'function' ? model.context(self,tmp) : model.context; 
                    var ids     = typeof model.ids === 'function'     ? model.ids(self,tmp) : model.ids;
                    var order   = typeof model.order === 'function'   ? model.order(self,tmp):    model.order;
                    if ( model.model && $.inArray(model.model,['product.product', 'res.partner']) == -1) {
//                    if ( model.model ){
                        self.chrome.loading_message(_t('Loading')+' '+(model.label || model.model || ''), progress);
                    } else if(model.model && model.model == 'product.product') {
                        self.product_domain = self.product_domain.concat(model.domain);
                        self.product_fields = self.product_fields.concat(model.fields);
                        self.product_context = $.extend(self.product_context, context);
                        self.product_context = $.extend(self.product_context, {'location': self.config.stock_location_id[0]});
                    } else if(model.model && model.model == 'res.partner') {
                        self.partner_domain = self.partner_domain.concat(model.domain);
                        self.partner_fields = self.partner_fields.concat(model.fields);
                        self.partner_fields = $.extend(self.partner_fields, context)
                    }
                    progress += progress_step;
                   
                    var records;
                    if( model.model && $.inArray(model.model,['product.product', 'product.template', 'res.partner']) == -1){
//                    if( model.model ){
                        if (model.ids) {
                            records = new Model(model.model).call('read',[ids,fields],context);
                        } else {
                            records = new Model(model.model)
                                .query(fields)
                                .filter(domain)
                                .order_by(order)
                                .context(context)
                                .all();
                        }
                        records.then(function(result){
                                try{    // catching exceptions in model.loaded(...)
                                    $.when(model.loaded(self,result,tmp))
                                        .then(function(){ load_model(index + 1); },
                                              function(err){ loaded.reject(err); });
                                }catch(err){
                                    console.error(err.stack);
                                    loaded.reject(err);
                                }
                            },function(err){
                                loaded.reject(err);
                            });
                    } else if ( model.loaded ){
                        try{    // catching exceptions in model.loaded(...)
                            $.when(model.loaded(self,tmp))
                                .then(  function(){ load_model(index +1); },
                                        function(err){ loaded.reject(err); });
                        }catch(err){
                            loaded.reject(err);
                        }
                    }else{
                        load_model(index + 1);
                    }
                }
            }

            try{
                load_model(0);
            }catch(err){
                loaded.reject(err);
            }
			var loaded1 = loaded.then(function(){
			    new Model('aspl.gift.voucher').get_func('search_read')()
			    .then(function(gift_vouchers){
                    self.db.add_gift_vouchers(gift_vouchers);
                    self.set({'gift_voucher_list' : gift_vouchers});
                });
				self.domain_order = [];
				var date = new Date();
                var start_date = self.config.start_date || new Date().toJSON().slice(0,10);
				var start_date;
				if(self.config.last_days){
					date.setDate(date.getDate() - self.config.last_days);
				}
				start_date = date.toJSON().slice(0,10);
				self.domain_order.push(['state','not in',['cancel']]);
				self.domain_order.push(['create_date','>=',start_date]);
				self.domain_order.push(['config_id', '=', self.config.id]);
				return new Model('pos.order').get_func('ac_pos_search_read')(self.domain_order)
               .then(function(orders){
               		self.db.add_orders(orders);
               		self.set({'pos_order_list' : orders});
               });
			});
			var loaded2 = loaded1.then(function(){
				return new Model('aspl.gift.card').get_func('search_read')([['is_active', '=', true]],[]).then(function(gift_cards){
                    self.db.add_giftcard(gift_cards);
                    self.set({'gift_card_order_list' : gift_cards});
                });
			});
	        return loaded2;
		},
		_save_to_server: function (orders, options) {
           if (!orders || !orders.length) {
               var result = $.Deferred();
               result.resolve([]);
               return result;
           }
           options = options || {};

           var self = this;
           var currentOrder = self.get_order();
           var timeout = typeof options.timeout === 'number' ? options.timeout : 7500 * orders.length;

           // we try to send the order. shadow prevents a spinner if it takes too long. (unless we are sending an invoice,
           // then we want to notify the user that we are waiting on something )
          
           var redeem_point = currentOrder.get_order_redeem_point();
           var redeem_point_amt = currentOrder.get_total_redeem_amt();
           var return_order = currentOrder.get_ret_o_ref()? true : false
           var context = {
        		'redeem_point': redeem_point, 
        		'redeem_amount': redeem_point_amt,
        		'return_order': return_order,
        	};
           var posOrderModel = new Model('pos.order');
           return posOrderModel.call('create_from_ui',
               [_.map(orders, function (order) {
                   order.to_invoice = options.to_invoice || false;
                   return order;
               }), context],
               undefined,
               {
                   shadow: !options.to_invoice,
                   timeout: timeout
               }
           ).then(function (server_ids) {
           	if(server_ids != []){
           		new Model('pos.order').get_func('ac_pos_search_read')
           		([['id','=',server_ids]])
           		.then(function(orders){
                       var orders_data= self.get('pos_order_list');
                       var new_orders = [];
                       var flag = true;
                       if(orders && orders[0]){
                       	for(var i in orders_data){
                       		if(orders_data[i].pos_reference == orders[0].pos_reference){
                       			new_orders.push(orders[0])
                       			flag = false
                       		} else {
                       			new_orders.push(orders_data[i])
                       		}
                       	}
                       	if(flag){
                       		new_orders = orders.concat(orders_data);
                       	}
                        self.db.add_orders(new_orders);
                           self.set({'pos_order_list' : new_orders}); 
                       } else {
                       	new_orders = orders.concat(orders_data);
                        self.db.add_orders(new_orders);
                           self.set({'pos_order_list' : new_orders}); 
                       }
                   });
                   _.each(orders, function(order) {
	        		var lines = order.data.lines;
	        		_.each(lines, function(line){
	        		    if(line[2].location_id === self.config.stock_location_id[0]){
                            var product_id = line[2].product_id;
                            var product_qty = line[2].qty;
                            var product = self.db.get_product_by_id(product_id);
                            if(product && product.qty_available){
                            	var remain_qty = product.qty_available - product_qty;
                                product.qty_available = remain_qty
                                self.gui.screen_instances.products.product_list_widget.product_cache.clear_node(product.id)
                            }
	        			}
	        		});
	        	});
              }
               _.each(orders, function (order) {
                   self.db.remove_order(order.id);
               });
               return server_ids;
           }).fail(function (error, event){
               if(error.code === 200 ){    // Business Logic Error, not a connection problem
//               	self.gui.show_popup('error-traceback',{
//                   message: error.data.message,
//                   comment: error.data.debug
//               });
	               	self.gui.show_popup('error-traceback',{
	                    'title': "Error",
	                    'body':  error.data.message,
	                });
               }
               // prevent an error popup creation by the rpc failure
               // we want the failure to be silent as we send the orders in the background
               event.preventDefault();
               console.error('Failed to send orders:', orders);
           });
       	},
       	add_new_order: function(){
    	   var order = _super_posmodel.prototype.add_new_order.call(this);
	       order.set_delivery(false);
	       order.set_delivery_date(false);
	       order.set_delivery_time(false);
	       $('#delivery_mode').removeClass('deliver_on');
	       $('#open_calendar').css({'background-color':''});
	       $('#return_order_ref,  #ref_customer_name').html('');
	       $("div#menu a#sale_mode").parent().css({'background':'#6EC89B'});
	       $("div#menu a#return_order").parent().css({'background':''});
           $('#return_order_ref').html('');
           $('#return_order_number').text('');
           $('#ref_customer_name').text('');
           $("span.remaining-qty-tag").css('display', 'none');
           if(order.get_gift_receipt_mode()){
		        $('.gift_receipt_btn').addClass('highlight');
		    } else {
		        $('.gift_receipt_btn').removeClass('highlight');
		    }
	       return order;
		},
		push_order: function(order){
            var self = this;
            var pushed = _super_posmodel.prototype.push_order.call(this, order);
            var client = order && order.get_client();
            if (client){
                _.each(order.get_paymentlines(),function(line){
                    var journal = line.cashregister.journal;
                    if (!journal.debt)
                        return;
                    var amount = line.get_amount();
                    client.debt += amount;
                })
            }
            return pushed;
        },
        get_order: function(){
        	var order = _super_posmodel.prototype.get_order.call(this);
        	if(order){
        		$('#ref_customer_name').text(order.get_ref_cust_label() ? 'Reference of: ' + order.get_ref_cust_label() : '');
        	}
        	return order;
        },
        //pricelist
        set_order: function(order){
        	_super_posmodel.prototype.set_order.apply(this, arguments);
	    	var order = this.get_order();
	    	if(order && order.get_client()){
	            order.set_pricelist_val(order.get_client().id);
	            $('#price_list').val(order.get_pricelist());
	        } else {
	            $('#price_list').val('');
	        }
	    },
	   	load_new_partners: function(){
            var self = this;
            var def  = new $.Deferred();
            var fields = _.find(this.models,function(model){ return model.model === 'res.partner'; }).fields;
            var domain = [['customer','=',true],['write_date','>',this.db.get_partner_write_date()]];
            var context = {'timeout':3000, 'shadow': true};
            new Model('res.partner').call('search_read',
            [domain, fields, 0, false, false, context], {}, { async: false })
            .then(function(partners){
                _.each(partners, function(partner){
                    if(self.db.partner_by_id[partner.id]){
                        var id = partner.id;
                        delete self.db.partner_by_id[partner.id]
                    }
                });
                if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                    def.resolve();
                } else {
                    def.reject();
                }
            }, function(err,event){ event.preventDefault(); def.reject(); });
            return def;
       	},
       	load_new_orders: function(){
       	    var self = this;
            return new Model('pos.order').call('ac_pos_search_read', [self.domain_order], {}, {async:false})
            .then(function(result){
                self.db.add_orders(result);
                self.set({ 'pos_order_list' : result });
                return self.get('pos_order_list');
            }).fail(function (error, event){
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                    self.gui.show_popup('error-traceback',{
                        message: error.data.message,
                        comment: error.data.debug
                    });
                }
                // prevent an error popup creation by the rpc failure
                // we want the failure to be silent as we send the orders in the background
                event.preventDefault();
                var orders=self.get('pos_order_list');
                return orders
            });
       	},
	});	

	screens.ProductCategoriesWidget.include({
		init: function(parent, options){
            var self = this;
            this._super(parent,options);
            var model = new Model("product.product");
            this.switch_category_handler = function(event){
            	$('.category_searchbox input').val('');
                self.set_category(self.pos.db.get_category_by_id(Number(this.dataset.categoryId)));
                self.renderElement();
            };
            new Model("product.product").call("calculate_product").then(function(result) {
            	$('div.product_progress_bar').css('display','');
			    if(result && result[0]){
			    	var total_products = parseInt(result[0][0]);
			    	var remaining_time;
			    	if(total_products){
			    		var product_limit = 1000;
			    		var count_loop = total_products;
			    		var count_loaded_products = 0;
			    		function ajax_product_load(){
			    			if(count_loop > 0){
			    				$.ajax({
					                type: "GET",
						            url: '/web/dataset/load_products',
						            data: {
						                    model: 'product.product',
						                    fields: JSON.stringify(self.pos.product_fields),
						                    domain: JSON.stringify(self.pos.product_domain),
						                    context: JSON.stringify(self.pos.product_context),
						                    product_limit:product_limit,
						                },
						            success: function(res) {
						            		var all_products = JSON.parse(res);
						            		count_loop -= all_products.length;
						            		remaining_time = ((total_products - count_loop) / total_products) * 100;
							            	product_limit += 1000;
							            	all_products.map(function(product){
							            		self.pos.product_list.push(product);
							            	});
							                self.pos.db.add_products(all_products);
							                self.renderElement();
							                $('.product_progress_bar').css('display','');
						            		$('.product_progress_bar').find('#bar').css('width', parseInt(remaining_time)+'%', 'important');
						            		$('.product_progress_bar').find('#progress_status').html(parseInt(remaining_time) + "% completed");
						            		count_loaded_products += all_products.length;
						            		all_products = [];
						            		if(count_loaded_products >= total_products){
						            			self.pos.db.set_is_product_load(true);
						            			$('.product_progress_bar').delay(3000).fadeOut('slow');
						            		}
							                ajax_product_load()
						            },
						            error: function() {
						                console.log('Product loading failed.');
						                $('.product_progress_bar').find('#bar').css('width', '100%', 'important');
					            		$('.product_progress_bar').find('#progress_status').html("Products loading failed...");
						            },
					            });
			    			}
			    		}
			    		ajax_product_load();
			    	}else{
			    		alert("Can't calculate products...");
			    	}
			    }
			});
	    },
	    renderElement: function(){
	        var el_str  = QWeb.render(this.template, {widget: this});
	        var el_node = document.createElement('div');

	        el_node.innerHTML = el_str;
	        el_node = el_node.childNodes[1];

	        if(this.el && this.el.parentNode){
	            this.el.parentNode.replaceChild(el_node,this.el);
	        }

	        this.el = el_node;

	        var withpics = this.pos.config.iface_display_categ_images;

	        var list_container = el_node.querySelector('.category-list');
	        if (list_container) { 
	            if (!withpics) {
	                list_container.classList.add('simple');
	            } else {
	                list_container.classList.remove('simple');
	            }
	            for(var i = 0, len = this.subcategories.length; i < len; i++){
	                list_container.appendChild(this.render_category(this.subcategories[i],withpics));
	            }
	        }

	        var buttons = el_node.querySelectorAll('.js-category-switch');
	        for(var i = 0; i < buttons.length; i++){
	            buttons[i].addEventListener('click',this.switch_category_handler);
	        }

	        var products = this.pos.db.get_product_by_category(this.category.id);
	        var id = $('div#menu a#on_hand_qty_mode').attr('id');
	        if(this.category.id == 0 && id == "on_hand_qty_mode"){
	        	var data = this.pos.db.get_product_qty();
	        	var all_filter_data = [];
	        	for(var i=0;i<data.length;i++){
	        		all_filter_data.push(data[i]);
	        	}
	        	this.product_list_widget.set_product_list(all_filter_data); // FIXME: this should be moved elsewhere ...
	        } else {
	        	this.product_list_widget.set_product_list(products); 
	        }

//	        this.el.querySelector('.searchbox input').addEventListener('keypress',this.search_handler);
//
//	        this.el.querySelector('.searchbox input').addEventListener('keydown',this.search_handler);
//
//	        this.el.querySelector('.search-clear').addEventListener('click',this.clear_search_handler);

	        if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
	            this.chrome.widget.keyboard.connect($(this.el.querySelector('.searchbox input')));
	        }
	    },
	    clear_search: function(){
	    	var products = this.pos.db.get_product_by_category(this.category.id);
	        this.product_list_widget.set_product_list(products);
//	        var input = this.el.querySelector('.searchbox input');
//	            input.value = '';
//	            input.focus();
        },
        perform_search: function(category, query, buy_result){
        	var self = this;
            var products;
            if(query){
                products = this.pos.db.search_product_in_category(category.id,query);
                if(buy_result && products.length === 1){
                    this.pos.get_order().add_product(products[0]);
                    this.clear_search();
                    if($('.all_products').attr('id') == 'on_hand_qty_mode'){
                		var data = this.pos.db.get_product_qty();
        	        	var all_filter_data = [];
        	        	for(var i=0;i<data.length;i++){
        	        		all_filter_data.push(data[i]);
        	        	}
        	        	this.product_list_widget.set_product_list(all_filter_data);
                	}
                }else{
                	if($('.all_products').attr('id') == 'on_hand_qty_mode'){
                		var data = this.pos.db.get_product_qty();
        	        	var all_filter_data = [];
        	        	for(var i=0;i<data.length;i++){
        	        		all_filter_data.push(data[i]);
        	        	}
        	        	this.product_list_widget.set_product_list(all_filter_data);
                	}else{
                		this.product_list_widget.set_product_list(products);
                	}
                }
                if(!self.pos.db.get_is_product_load() && buy_result){
                	var domain = [['sale_ok','=',true],['available_in_pos','=',true], '|', ['name', 'ilike', query], ['barcode', 'ilike', query]];
                	var model = new Model("product.product");
            		var fields = ['display_name', 'list_price','price','pos_categ_id', 'taxes_id', 'barcode', 'default_code',
            		                 'to_weight', 'uom_id', 'description_sale', 'description',
            		                 'product_tmpl_id','tracking','qty_available','type','is_packaging','can_not_return','attribute_value_ids'];
            		var context = {
                            'pricelist': self.pos.pricelist.id,
                            'display_default_code': false,
                        }
            		var offset;
            		model.call("search_read", [domain=domain, fields=fields, offset=0, false, false, context=context]).pipe(
                        function(result) {
                        	if(result.length > 0){
                        		if(!self.pos.db.get_is_product_load()){
                        			$('div.product_progress_bar').css('display','');
                        		}
                        		if(self.pos.product_list.length != undefined){
                        			self.pos.product_list = result;
                        			self.pos.db.add_products(result);
                        		}
                        		self.chrome.screens.products.product_list_widget.set_product_list(result);
                        		self.pos.get_order().add_product(result[0]);
                        	}else {
                        		self.chrome.screens.products.product_list_widget.set_product_list(result);
                        		return console.info("Products not found.");
                        	}
                        }).fail(function (error, event){
    						if(error.code === -32098) {
    				        	event.preventDefault();
    			           }
    			       });
                }
            }else{
                products = this.pos.db.get_product_by_category(this.category.id);
                if($('.all_products').attr('id') == 'on_hand_qty_mode'){
                	var data = this.pos.db.get_product_qty();
    	        	var all_filter_data = [];
    	        	for(var i=0;i<data.length;i++){
    	        		all_filter_data.push(data[i]);
    	        	}
    	        	this.product_list_widget.set_product_list(all_filter_data);
            	}else{
            		this.product_list_widget.set_product_list(products);
            	}
            }
        },
	});
	/* Product POPUP */
//	var ProductPopup = PopupWidget.extend({
//	    template: 'ProductPopup',
//	    show: function(options){
//	    	var self = this;
//			this._super();
//			alert("show")
//			this.product_list = options.product_list || "";
//			this.order_id = options.order_id || "";
//			this.state = options.state || "";
//			this.renderElement();
//	    },
//	    click_confirm: function(){
//	    	var self = this;
//	    	if (this.state == "paid" || this.state == "done"){
//	    		$( "#re_order_duplicate" ).data("id",self.order_id);
//    			$( "#re_order_duplicate" ).trigger("click");
//	        } else if(this.state == "draft") {
//                $( "#re_order" ).data("id",self.order_id);
//                $( "#re_order" ).trigger("click");
//			}
//	        this.gui.close_popup();
//	    },
//	    renderElement: function() {
//            var self = this;
//            this._super();
//            
//	    	this.$('.clear').click(function(){
//	        	self.$("#signature").jSignature("reset");
//	        });
//    	},
//    	click_cancel: function(){
//    		this.gui.close_popup();
//    	}
//	});
//	gui.define_popup({name:'product_popup', widget: ProductPopup});

	DB.include({
		init: function(options){
        	this._super.apply(this, arguments);
        	this.products_sorted = [];
        	this.product_search_string = "";
        	this.group_products = [];
        	this.order_write_date = null;
        	this.order_by_id = {};
        	this.order_sorted = [];
        	this.order_search_string = "";
        	this.user_by_barcode = [];
        	this.last_order = {};
        	this.last_order_id;
        	this.template_by_id = {};
            this.product_attribute_by_id = {};
            this.product_attribute_value_by_id = {};
            this.is_product_load = false;
            this.card_products = [];
            this.card_write_date = null;
            this.card_by_id = {};
            this.card_sorted = [];
            this.card_by_no = {};
            this.card_search_string = "";
            this.partners_name = [];
            this.partner_by_name = {};
            this.voucher_write_date = null;
            this.voucher_by_id = {};
            this.voucher_sorted = [];
            this.voucher_search_string = "";
            this.categories = [];
            this.pay_button_by_id = {}; // quick payemnt
            this.picking_type_by_id = {};
            this.all_categories = {};
	       	this.product_by_name = {};
	       	this.prod_name_list = [];
	       	this.prod_by_ref = {};
	       	this.product_by_tmpl_id = [];
	       	this.product_write_date = null;
			this.product_qty_list = [];
			this.all_products_list = [];
			this.package_product = [];
			this.productNameList = [];
            this._super(options);

        },
        add_products: function(products){
        	var self = this;
	    	var stored_categories = this.product_by_category_id;
	    	var updated_count = 0;
	    	var symbol = this.currency_symbol ? this.currency_symbol.symbol : "$";
	        if(!products instanceof Array){
	            products = [products];
	        }
	        var new_write_date = '';
	        var product;
	        var defined_product = false;
	        for(var i = 0, len = products.length; i < len; i++){
	            var product = products[i];
//	            if(product['list_price']) {
//                	product['price'] = product['list_price'];
                	var unit_name = product.uom_id[1] ? product.uom_id[1] : "";
//                	if(product.to_weight){
//                		$("[data-product-id='"+product.id+"']").find('.price-tag').html(symbol+" "+product['list_price'].toFixed(3)+'/'+unit_name);
//                	} else {
//                		$("[data-product-id='"+product.id+"']").find('.price-tag').html(symbol+" "+product['list_price'].toFixed(3));
//                	}
//                    $("[data-product-id='"+product.id+"']").find('.product-name').html(product.display_name);
//                }
	            _.each(self.products_sorted, function(p){
	                if(p.id === product.id){
	                    $.extend(p, product);
	                    defined_product = true;
	                }
	            })
	            if(!defined_product){
	                self.products_sorted.push(product);
	            }
	            var search_string = this._product_search_string(product);
	            var categ_id = product.pos_categ_id ? product.pos_categ_id[0] : this.root_category_id;
	            product.product_tmpl_id = product.product_tmpl_id[0];
	            if(products[i].qty_available > 0 || product.type.toLowerCase() === _t("service")){
	            	this.product_qty_list.push(products[i]);
	            }
	            if(products[i].is_packaging){
		            this.package_product.push(products[i]);
		        }else{
		        	this.all_products_list.push(products[i]);
		        }
	            if(!stored_categories[categ_id]){
	                stored_categories[categ_id] = [];
	            }
	            stored_categories[categ_id].push(product.id);

	            if(this.category_search_string[categ_id] === undefined){
	                this.category_search_string[categ_id] = '';
	            }
	            this.category_search_string[categ_id] += search_string;

	            var ancestors = this.get_category_ancestors_ids(categ_id) || [];

	            for(var j = 0, jlen = ancestors.length; j < jlen; j++){
	                var ancestor = ancestors[j];
	                if(! stored_categories[ancestor]){
	                    stored_categories[ancestor] = [];
	                }
	                stored_categories[ancestor].push(product.id);

	                if( this.category_search_string[ancestor] === undefined){
	                    this.category_search_string[ancestor] = '';
	                }
	                this.category_search_string[ancestor] += search_string; 
	            }
	            this.product_by_id[product.id] = product;
	            if(product.barcode){
	                this.product_by_barcode[product.barcode] = product;
	            }
	            if(product.display_name){
                	this.productNameList.push(product.display_name);
                }
	            if(product.name){
					 this.product_by_name[product.name] = product
					 this.prod_name_list.push(product.name);
					 this.prod_by_ref[product.default_code] = product;
					 this.product_by_tmpl_id[product.product_tmpl_id] = product;
				 }
	            if (    this.product_write_date && 
                        this.product_by_id[product.id] &&
                        new Date(this.product_write_date).getTime() + 1000 >=
                        new Date(product.write_date).getTime() ) {
                    // FIXME: The write_date is stored with milisec precision in the database
                    // but the dates we get back are only precise to the second. This means when
                    // you read partners modified strictly after time X, you get back partners that were
                    // modified X - 1 sec ago. 
                    continue;
                } else if ( new_write_date < product.write_date ) { 
                    new_write_date  = product.write_date;
                }
	            updated_count += 1;
	        }
	        this.product_write_date = new_write_date || this.product_write_date;
	        if (updated_count) {
	            this.product_search_string = "";
	            this.product_by_barcode = {};
	            this.product_by_default_code = {};
	            for (var id in this.product_by_id) {
	                product = this.product_by_id[id];

	                if(product.default_code){
	                	product = this.product_by_default_code[product.default_code] = product
	                }
	                if(product.barcode){
	                    this.product_by_barcode[product.barcode] = product;
	                }
	                this.product_search_string += this._product_search_string(product);
	            }
	        }
	        return updated_count 
        },
        _product_search_string: function(product){
	    	var str =  product.name;
	        if(product.barcode){
	            str += '|' + product.barcode;
	        }
	        if(product.categ_id){
	            str += '|' + product.categ_id;
	        }
	        if(product.default_code){
	            str += '|' + product.default_code;
	        }
	        if(str){
	        	str = '' + product.id + ':' + str.replace(':','') + '\n';
		        return str;
	        }
	        return false
	    },
        get_products_sorted: function(max_count){
        	max_count = max_count ? Math.min(this.products_sorted.length, max_count) : this.products_sorted.length;
        	var products = [];
        	for (var i = 0; i < max_count; i++) {
                products.push(this.products_sorted[i]);
            };
            return products
	    },
        search_product: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            for(var i = 0; i < this.limit; i++){
                var r = re.exec(this.product_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_product_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
	    get_product_by_name: function(name){
	        if(this.product_by_name[name]){
	            return this.product_by_name[name];
	        }
	        return undefined;
	    },
	    get_products_name: function(name){
	    	return this.prod_name_list;
	    },
	    get_product_by_reference: function(ref){
	    	return this.prod_by_ref[ref];
	    },
	    get_product_by_tmpl_id: function(id){
	    	return this.product_by_tmpl_id[id];
	    },
	    get_product_write_date: function(){
            return this.product_write_date || "1970-01-01 00:00:00";
        },
        get_product_qty: function() {
            return this.product_qty_list;
        },
        get_all_product_data: function() {
            return this.all_products_list;
        },
        // Quick payement
        add_quick_payment: function(quick_pays){
        	var self = this;
        	quick_pays.map(function(pay){
        		self.pay_button_by_id[pay.id] = pay
        	});
        },
        get_all_categories : function() {
			return this.all_categories;
		},
        get_button_by_id: function(id){
        	return this.pay_button_by_id[id]
        },
        set_is_product_load: function(is_product_load) {
            this.is_product_load = is_product_load;
        },
		get_is_product_load: function(){
        	return this.is_product_load;
        },
        add_orders: function(orders){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = orders.length; i < len; i++){
                var order = orders[i];
                if (    this.order_write_date && 
                        this.order_by_id[order.id] &&
                        new Date(this.order_write_date).getTime() + 1000 >=
                        new Date(order.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < order.write_date ) { 
                    new_write_date  = order.write_date;
                }
                if (!this.order_by_id[order.id]) {
                    this.order_sorted.push(order.id);
                }
                this.order_by_id[order.id] = order;
                updated_count += 1;
            }
            this.order_write_date = new_write_date || this.order_write_date;
            if (updated_count) {
                // If there were updates, we need to completely 
                this.order_search_string = "";
                for (var id in this.order_by_id) {
                    var order = this.order_by_id[id];
                    this.order_search_string += this._order_search_string(order);
                }
            }
            return updated_count;
        },
        _order_search_string: function(order){
            var str =  order.name;
            if(order.pos_reference){
                str += '|' + order.pos_reference;
            }
            str = '' + order.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_order_write_date: function(){
            return this.order_write_date;
        },
        get_order_by_id: function(id){
            return this.order_by_id[id];
        },
        search_order: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.order_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_order_by_id(id));
                    results.push(this.get_card_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        search_gift_card: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.card_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_card_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        /* 
         *
         * Bootstrap Alert Message
         * - The below function is working as a notification like Javascript alert()
         * @param type This param contains type of notification that user wants.
         * 				type param value may be success, warning, info, danger
         *		  message This param contains string for printing text in alert.
         *	
         */
        notification: function(type, message){
        	var types = ['success','warning','info', 'danger'];
        	if($.inArray(type.toLowerCase(),types) != -1){
        		$('div.span4').remove();
        		var newMessage = '';
        		message = _t(message);
        		switch(type){
        		case 'success' :
        			newMessage = '<i class="fa fa-check" aria-hidden="true"></i> '+message;
        			break;
        		case 'warning' :
        			newMessage = '<i class="fa fa-exclamation-triangle" aria-hidden="true"></i> '+message;
        			break;
        		case 'info' :
        			newMessage = '<i class="fa fa-info" aria-hidden="true"></i> '+message;
        			break;
        		case 'danger' :
        			newMessage = '<i class="fa fa-ban" aria-hidden="true"></i> '+message;
        			break;
        		}
	        	$('body').append('<div class="span4 pull-right">' +
	                    '<div class="alert alert-'+type+' fade">' +
	                    newMessage+
	                   '</div>'+
	                 '</div>');
        	    $(".alert").removeClass("in").show();
        	    $(".alert").delay(200).addClass("in").fadeOut(3000);
        	}
        },
        add_partners: function(partners){
        	var self = this;
        	var res = self._super(partners);
        	for(var i = 0, len = partners.length; i < len; i++){
        		var partner = partners[i];

        		if(partner.address){
	        		var temp = partner.address.split(",");
	        		temp.splice(temp.length - 1, 0, partner.state_id[1]);
	        		partner.address = temp.join();
        		}
        		if(partner.name){
        		    if($.inArray(partner.name, self.partners_name) == -1){
        		        self.partners_name.push(partner.name);
        		    }
        			self.partner_by_name[partner.name] = partner;
        		}
        	}
        	return res;
        },
        get_partners_name: function(){
        	return this.partners_name;
        },
        get_partner_by_name: function(name){
            if(this.partner_by_name[name]){
                return this.partner_by_name[name];
            }
            return undefined;
        },
        add_giftcard: function(gift_cards){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = gift_cards.length; i < len; i++){
                var gift_card = gift_cards[i];
                if (    this.card_write_date && 
                        this.card_by_id[gift_card.id] &&
                        this.card_by_no[gift_card.card_no] &&
                        new Date(this.card_write_date).getTime() + 1000 >=
                        new Date(gift_card.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < gift_card.write_date ) { 
                    new_write_date  = gift_card.write_date;
                }
                if (!this.card_by_id[gift_card.id]) {
                    this.card_sorted.push(gift_card.id);
                }
                this.card_by_id[gift_card.id] = gift_card;
                this.card_by_no[gift_card.card_no] = gift_card;
                updated_count += 1;
            }
            this.card_write_date = new_write_date || this.card_write_date;
            if (updated_count) {
                // If there were updates, we need to completely 
                this.card_search_string = "";
                for (var id in this.card_by_id) {
                    var gift_card = this.card_by_id[id];
                    this.card_search_string += this._card_search_string(gift_card);
                }
            }
            return updated_count;
        },
        _card_search_string: function(gift_card){
            var str =  gift_card.card_no;
            if(gift_card.customer_id){
                str += '|' + gift_card.customer_id[1];
            }
            str = '' + gift_card.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_card_write_date: function(){
            return this.card_write_date;
        },
        get_card_by_id: function(id){
            return this.card_by_id[id];
        },
        get_card_by_no: function(no){
        	return this.card_by_no[no];
        },
        get_all_products_name: function(){
            return this.productNameList;
        },
        add_gift_vouchers: function(gift_vouchers){
            var updated_count = 0;
            var new_write_date = '';
            for(var i = 0, len = gift_vouchers.length; i < len; i++){
                var gift_voucher = gift_vouchers[i];
                if (    this.voucher_write_date &&
                        this.voucher_by_id[gift_voucher.id] &&
                        new Date(this.voucher_write_date).getTime() + 1000 >=
                        new Date(gift_voucher.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < gift_voucher.write_date ) {
                    new_write_date  = gift_voucher.write_date;
                }
                if (!this.voucher_by_id[gift_voucher.id]) {
                    this.voucher_sorted.push(gift_voucher.id);
                }
                this.voucher_by_id[gift_voucher.id] = gift_voucher;
                updated_count += 1;
            }
            this.voucher_write_date = new_write_date || this.voucher_write_date;
            if (updated_count) {
                // If there were updates, we need to completely
                this.voucher_search_string = "";
                for (var id in this.voucher_by_id) {
                    var gift_voucher = this.voucher_by_id[id];
                    this.voucher_search_string += this._voucher_search_string(gift_voucher);
                }
            }
            return updated_count;
        },
        _voucher_search_string: function(gift_voucher){
            var str =  gift_voucher.voucher_name;
            if(gift_voucher.voucher_code){
                str += '|' + gift_voucher.voucher_code;
            }
            str = '' + gift_voucher.id + ':' + str.replace(':','') + '\n';
            return str;
        },
        get_voucher_write_date: function(){
            return this.voucher_write_date;
        },
        get_voucher_by_id: function(id){
            return this.voucher_by_id[id];
        },
        search_gift_vouchers: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.voucher_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_voucher_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
        add_categories: function(categories){
            var self = this;
            this.all_categories = categories;
            self._super(categories);
            this.categories = categories;
            for (var i=0; i<categories.length; i++){
                var category = categories[i];
            }
        },
        get_category_search_list: function(){
            var category_search_list = [];
            _.each(this.categories, function(category){
                category_search_list.push({
                    'id':category.id,
                    'value':category.name,
                    'label':category.name,
            	});
            });
            return category_search_list;
        },
        add_picking_types: function(stock_pick_typ){
    		var self = this;
    		stock_pick_typ.map(function(type){
    			self.picking_type_by_id[type.id] = type;
    		});
    	},
    	get_picking_type_by_id: function(id){
    		return this.picking_type_by_id[id]
    	}
	});

	var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
    	initialize: function(attributes,options){
        	_super_Order.initialize.apply(this, arguments);
            this.set({
            	get_wallet_status: false,
                ret_o_id:       null,
                ret_o_ref:      null,
                sale_mode:      false,
                missing_mode:   false,
                set_barcode_for_manager: false,
                manager_name_for_discount: [],
                popup_open: false,
                //Wallet
                type_for_wallet: false,
                change_amount_for_wallet: false,
                use_wallet: false,
        		used_amount_from_wallet: false,
        		// order return
        		applied_coupon: false,
        		whole_order: false,
        		gift_receipt_mode: false,
        		//reservation
        		reservation_mode: false,
                delivery_date: false,
                draft_order: false,
                paying_due: false,
                fresh_order: false,
                partial_pay: false,
            });
            this.voucher = [],
        	this.remaining_redeemption = false,
            this.receipt_type = 'receipt',  // 'receipt' || 'invoice'
            this.temporary = options.temporary || false,
            this.giftcard = [],
            this.redeem =[],
            this.recharge=[],
            this.date=[],
            this.serial_list = [],
    		this.print_serial = true,
    		this.rounding_status = false,
    		this.return_product_lots = [],
    		$('#price_list').val('').trigger('change',this),
    		$("div#menu a#reservation_mode").parent().css({'background':''}),
            $(".search-clear").click(),
            $('#gift_receipt').removeClass('gift_mode_on'),
    		this.set({
                'pricelist_val': '',
            })
            return this;
        },
        init_from_JSON: function(json) {
			var self = this;
	        var client;
	        this.sequence_number = json.sequence_number;
	        this.pos.pos_session.sequence_number = Math.max(this.sequence_number+1,this.pos.pos_session.sequence_number);
	        this.session_id    = json.pos_session_id;
	        this.uid = json.uid;
	        this.name = _t("Order ") + this.uid;
	        this.validation_date = json.creation_date;

	        if (json.fiscal_position_id) {
	            var fiscal_position = _.find(this.pos.fiscal_positions, function (fp) {
	                return fp.id === json.fiscal_position_id;
	            });

	            if (fiscal_position) {
	                this.fiscal_position = fiscal_position;
	            } else {
	                console.error('ERROR: trying to load a fiscal position not available in the pos');
	            }
	        }
//			set customer after refresh pos, if partner_id stored in cache then customer set into current order
	        if (json.partner_id) {
	        	new Model("res.partner").get_func("search_read")([['id', '=', json.partner_id]]).then(
	        		function(result) {
	        			if(result && result[0]){
	        				client = result[0];
	        				self.set_client(client);
	        				$('.set-customer').html(client.name);
	        			}else{
	        				client = null;
	        				self.set_client(client);
	        			}
	        		});
//	            client = this.pos.db.get_partner_by_id(json.partner_id);
//	            if (!client) {
//	                console.error('ERROR: trying to load a parner not available in the pos');
//	            }
	        } else {
	            client = null;
	        }
	        this.set_client(client);

	        this.temporary = false;     // FIXME
	        this.to_invoice = false;    // FIXME

//			when pos reload then skip stored orderlines and paymentlines

//	        var orderlines = json.lines;
//	        for (var i = 0; i < orderlines.length; i++) {
//	            var orderline = orderlines[i][2];
//	            this.add_orderline(new exports.Orderline({}, {pos: this.pos, order: this, json: orderline}));
//	        }

//	        var paymentlines = json.statement_ids;
//	        for (var i = 0; i < paymentlines.length; i++) {
//	            var paymentline = paymentlines[i][2];
//	            var newpaymentline = new exports.Paymentline({},{pos: this.pos, order: this, json: paymentline});
//	            this.paymentlines.add(newpaymentline);
//
//	            if (i === paymentlines.length - 1) {
//	                this.select_paymentline(newpaymentline);
//	            }
//	        }
	    },
	    set_inbalance_discount: function(disc){
	    	this.inbalance = disc;
	    },
	    get_inbalance_discount: function(){
	    	return this.inbalance;
	    },
	    set_doctor_report_data: function(report){
	    	this.set('report_data', report);
	    },
	    get_doctor_report_data: function(){
	    	return this.get('report_data');
	    },
	    set_return_product_lots: function(data){
        	this.return_product_lots = data;
        },
        get_return_product_lots_by_line_id: function(id){
        	return this.return_product_lots[id]
        },
        get_total_discount_amount: function(){
        	var orderlines = this.get_orderlines();
        	var total_discount = 0.00;
        	_.each(orderlines,function(line){
        		total_discount += line.get_total_discount_amount();
        	});
        	return total_discount
        },
        get_total_discount_amount_reprint: function(){
        	var orderlines = this.get_orderlines();
        	var total_discount = 0.00;
        	_.each(orderlines,function(line){
        		total_discount += line.get_total_discount_amount_reprint();
        	});
        	return Number(total_discount)
        },
        get_shared_total_discount_amount: function(){
        	var orderlines = this.get_orderlines();
        	var total_discount = 0.00;
        	_.each(orderlines,function(line){
        		total_discount += line.get_shared_total_discount_amount();
        	});
        	return total_discount
        },
	    empty_cart: function(){
	       	var self = this;
	          var currentOrderLines = this.get_orderlines();
	          var lines_ids = []
	       	if(!this.is_empty()) {
		       	_.each(currentOrderLines,function(item) {
			       	lines_ids.push(item.id);
			    });
			       	_.each(lines_ids,function(id) {
			       	self.remove_orderline(self.get_orderline(id));
			    });
	       	}
	    },
	    get_total_without_tax: function() {
    		var result = _super_Order.get_total_without_tax.call(this);
//    		if(this.get_share_discount_amount()){
    			return result - this.get_shared_total_discount_amount();
    	},
	    get_total_discount_amount_printing: function(){
        	var orderlines = this.get_orderlines();
        	var total_discount = 0.00;
        	_.each(orderlines,function(line){
        		total_discount = total_discount + (line.get_total_discount_amount_printing());
        	});
        	return total_discount
        },
        get_total_discount_amount_storing: function(){
        	var orderlines = this.get_orderlines();
        	var total_discount = 0.00;
        	_.each(orderlines,function(line){
        		total_discount = total_discount + (line.get_total_discount_amount_storing() * line.quantity);
        	});
        	return total_discount
        	
        },
	    set_return_via_wallet: function(flag){
	    	this.set('get_wallet_status', flag);
	    },
	    get_return_via_wallet: function(){
	    	return this.get('get_wallet_status');
	    },
	    set_print_serial: function(val) {
    		this.print_serial = val
    	},
    	get_print_serial: function() {
    		return this.print_serial;
    	},
    	set_print_stock_data: function(stock_data){
    		this.internal_trns_stock_data = stock_data;
    	},
    	get_print_stock_data: function(){
    		return this.internal_trns_stock_data;
    	},
    	display_lot_popup: function() {
    		var self = this;
            var order_line = this.get_selected_orderline();
            if(order_line){
            	var pack_lot_lines =  order_line.compute_lot_lines();
            	var product_id = order_line.get_product().id;
            	if(this.pos.config.enable_pos_serial && product_id){
                	if(order_line.get_quantity() > 0){
                		new Model('stock.quant').get_func('search_read')
                		([['location_id', '=', self.pos.config.stock_location_id[0]],
                		  ['product_id','=',product_id]],['lot_id','qty','product_id']).then(function(records){
            	            if(records && records[0]){
            	            	var lot_ids = [];
            	            	var lot_records = {};
            	            	var product = order_line.get_product();
            	            	if(product.tracking == 'lot'){
            	            		_.each(records, function(record){
                	            		if(record.lot_id){
                	            			lot_ids.push(record.lot_id[0]);
                	            			if(lot_records[record.lot_id[0]]){
                	            				lot_records[record.lot_id[0]] = lot_records[record.lot_id[0]] + record.qty;
                	            			} else {
                	            				lot_records[record.lot_id[0]] = record.qty;
                	            			}
                	            		}
                	            	});
            	            	} else {
            	            		_.each(records, function(record){
            	            			lot_ids.push(record.lot_id[0]);
                	            		if(record.lot_id){
                	            			lot_records[record.lot_id[0]] = record.qty;
                	            		}
                	            	});
            	            	}
            	            	new Model('stock.production.lot').get_func('search_read')([['id', 'in', lot_ids]],
    	        	            ['name', 'ref', 'product_id', 'create_date','remaining_qty','life_date'])
    	        	            .then(function(serials){
    	        	            	_.each(serials, function(serial){
                	            		serial['remaining_qty'] = lot_records[serial.id];
                	            	});
    	        	            	self.pos.gui.show_popup('packlotline', {
    	                                'title': _t('Lot/Serial Number(s) Required'),
    	                                'pack_lot_lines': pack_lot_lines,
    	                                'order': self,
    	                                'serials': serials
    	                            });
    	        	            });
            	            }
                	    });
        	        } else {
        	        	self.pos.gui.show_popup('packlotline', {
                            'title': _t('Lot/Serial Number(s) Required'),
                            'pack_lot_lines': pack_lot_lines,
                            'order': self,
                            'return': true,
                            'serials': ['abc','ayz'],
                        });
        	        }
                } else {
                	self.pos.gui.show_popup('packlotline', {
                        'title': _t('Lot/Serial Number(s) Required'),
                        'pack_lot_lines': pack_lot_lines,
                        'order': self,
                        'serials': []
                    });
                }
            }
        }, 
	    set_gift_receipt_data: function(receipt_data){
            this.set('receipt_data',receipt_data);
        },
        get_gift_receipt_data: function(){
            return this.get('receipt_data');
        },
        set_reprint_mode: function(mode){
        	this.set('reprint_mode',mode);
        },
        get_reprint_mode: function(){
        	return this.get('reprint_mode');
        },
        set_gift_receipt_mode: function(gift_receipt_mode){
            this.set('gift_receipt_mode', gift_receipt_mode);
        },
        get_gift_receipt_mode: function() {
            return this.get('gift_receipt_mode');
        },
        set_num_of_line: function(line_length){
            this.set('no_of_lines',line_length);
        },
        get_num_of_line: function(){
            return this.get('no_of_lines');
        },
	    set_ereceipt_mail: function(ereceipt_mail) {
            this.set('ereceipt_mail', ereceipt_mail);
        },
        get_ereceipt_mail: function() {
            return this.get('ereceipt_mail');
        },
        set_prefer_ereceipt: function(prefer_ereceipt) {
            this.set('prefer_ereceipt', prefer_ereceipt);
        },
        get_prefer_ereceipt: function() {
            return this.get('prefer_ereceipt');
        },
	    set_giftcard: function(giftcard) {
            this.giftcard.push(giftcard)
        },
        get_giftcard: function() {
            return this.giftcard;
        },
        set_recharge_giftcard: function(recharge) {
            this.recharge.push(recharge)
        },
        get_recharge_giftcard: function(){
            return this.recharge;
        },
        set_redeem_giftcard: function(redeem) {
            this.redeem.push(redeem)
        },
        get_redeem_giftcard: function() {
            return this.redeem;
        },
        remove_card:function(code){ 
            var redeem = _.reject(this.redeem, function(objArr){ return objArr.redeem_card == code });
            this.redeem = redeem
        },
        set_free_data: function(freedata) {
            this.freedata = freedata;
        },
        get_free_data: function() {
            return this.freedata;
        },
	    set_voucher: function(voucher) {
            this.voucher.push(voucher)
        },
        get_voucher: function() {
        	return this.voucher;
        },
        remove_voucher: function(barcode, pid){
        	this.voucher = _.reject(this.voucher, function(objArr){ return objArr.voucher_code == barcode && objArr.pid == pid; });
        },
        set_remaining_redeemption: function(vals){
            this.remaining_redeemption = vals;
        },
        get_remaining_redeemption: function(){
            return this.remaining_redeemption;
        },
        generate_unique_id: function() {
        	var timestamp = new Date().getTime();
            return Number(timestamp.toString().slice(-5) + performance.now().toString().substr(0,5));
        },
        // Order History
        set_sequence:function(sequence){
        	this.set('sequence',sequence);
        },
        get_sequence:function(){
        	return this.get('sequence');
        },
        set_order_id: function(order_id){
            this.set('order_id', order_id);
        },
        get_order_id: function(){
            return this.get('order_id');
        },
        set_amount_paid: function(amount_paid) {
            this.set('amount_paid', amount_paid);
        },
        get_amount_paid: function() {
            return this.get('amount_paid');
        },
        set_amount_return: function(amount_return) {
            this.set('amount_return', amount_return);
        },
        get_amount_return: function() {
            return this.get('amount_return');
        },
        set_amount_tax: function(amount_tax) {
            this.set('amount_tax', amount_tax);
        },
        get_amount_tax: function() {
            return this.get('amount_tax');
        },
        set_amount_total: function(amount_total) {
            this.set('amount_total', amount_total);
        },
        get_amount_total: function() {
            return this.get('amount_total');
        },
        set_company_id: function(company_id) {
            this.set('company_id', company_id);
        },
        get_company_id: function() {
            return this.get('company_id');
        },
        set_date_order: function(date_order) {
            this.set('date_order', date_order);
        },
        get_date_order: function() {
            return this.get('date_order');
        },
        set_pos_reference: function(pos_reference) {
            this.set('pos_reference', pos_reference)
        },
        get_pos_reference: function() {
            return this.get('pos_reference')
        },
        set_user_name: function(user_id) {
            this.set('user_id', user_id);
        },
        get_user_name: function() {
            return this.get('user_id');
        },
        set_journal: function(statement_ids) {
            this.set('statement_ids', statement_ids)
        },
        get_journal: function() {
            return this.get('statement_ids');
        },
        get_change: function(paymentline) {
        	if (!paymentline) {
//	            var change = this.get_total_paid() - this.get_total_with_tax();
        		var change = this.get_total_paid() - this.getNetTotalTaxIncluded();
        	} else {
	            var change = -this.getNetTotalTaxIncluded();
	            var lines  = this.paymentlines.models;
	            for (var i = 0; i < lines.length; i++) {
	                change += lines[i].get_amount();
	                if (lines[i] === paymentline) {
	                    break;
	                }
	            }
	        }
	        return round_pr(Math.max(0,change), this.pos.currency.rounding);
        },
        //Rounding
        getNetTotalTaxIncluded: function() {
        	var self = this;
        	var total = this.get_total_with_tax();
        	if(this.get_rounding_status()){
	        	if(this.pos.config.enable_rounding && this.pos.config.rounding_options == 'digits'){
	        		var value = round_pr(Math.max(0,total))//decimalAdjust(total);
	                return value;
	        	}else if(this.pos.config.enable_rounding && this.pos.config.rounding_options == 'points'){
	                var value = decimalAdjust(total);
	                return value;
	        	} else if(this.pos.config.enable_rounding && self.pos.config.rounding_options == '1decimal'){
	        		var value = decimalAdjust(total,"one_point");
	                return value;
		        } else if(this.pos.config.enable_rounding && self.pos.config.rounding_options == '2decimal'){
		        	var value = decimalAdjust(total,"two_point");
	                return value;
		        } else if(this.pos.config.enable_rounding && self.pos.config.rounding_options == '3decimal'){
		        	var value = decimalAdjust(total,"three_point");
	                return value;
		        } else if(this.pos.config.enable_rounding && this.pos.config.rounding_options == '50fills'){
		        	var value = decimalAdjust(total,'50fills');
		        	return value;
	        	} else if(this.pos.config.enable_rounding && this.pos.config.rounding_options == '250fills'){
	        		var value = decimalAdjust(total,'250fills');
	        		return value;
	        	}
        	}else {
        		return total
        	}
        },
        get_rounding : function(){
        	if(this.get_rounding_status()){
	            var total = this ? this.get_total_with_tax() : 0;
	            var rounding = this ? this.getNetTotalTaxIncluded() - total: 0;
	            return rounding;
        	}
        },
        get_due: function(paymentline) {
            if (!paymentline) {
                var due = this.getNetTotalTaxIncluded() - this.get_total_paid();
            } else {
                var due = this.getNetTotalTaxIncluded();
                var lines = this.paymentlines.models;
                for (var i = 0; i < lines.length; i++) {
                    if (lines[i] === paymentline) {
                        break;
                    } else {
                        due -= lines[i].get_amount();
                    }
                }
            }
            return round_pr(Math.max(0,due), this.pos.currency.rounding);
        },
        export_as_JSON: function() {
            var self = this;
        	var new_val = {};
            var orders = _super_Order.export_as_JSON.call(this);
            var parent_return_order = '';
            var ret_o_id = this.get_ret_o_id();
            var ret_o_ref = this.get_ret_o_ref();
            var return_seq = 0;
            if (ret_o_id) {
                parent_return_order = this.get_ret_o_id();
            }
            var backOrders = '';
            _.each(this.get_orderlines(),function(item) {
                if (item.get_back_order()) {
                    return backOrders += item.get_back_order() + ', ';
                }
            });
            //reservation
            var cancel_orders = '';
            _.each(self.get_orderlines(), function(line){
                if(line.get_cancel_item()){
                    cancel_orders += " "+line.get_cancel_item();
                }
            });
            //reservation over
            new_val = {
                old_order_id: this.get_order_id(),
                sequence: this.get_sequence(),
                pos_reference: this.get_pos_reference(),
                order_note: this.get_order_note(),
                parent_return_order: parent_return_order, // Required to create paid return order
                return_seq: return_seq || 0,
                back_order: backOrders,
                sale_mode: this.get_sale_mode(),
                delivery_date: this.get_delivery_date(),
        		delivery_time: this.get_delivery_time(),
        		points_to_use: this.get_order_redeem_point(),
        		redeem_point_amt:this.get_total_redeem_amt(),
        		ref_cust_id: this.get_ref_cust(),
        		wallet_type: this.get_type_for_wallet() || false,
        		change_amount_for_wallet: this.get_change_amount_for_wallet() || false,
        		wallet_type: this.get_type_for_wallet() || false,
        		change_amount_for_wallet: this.get_change_amount_for_wallet() || false,
        		used_amount_from_wallet: this.get_used_amount_from_wallet() || false,
        		voucher: this.get_voucher() || false,
        		giftcard: this.get_giftcard() || false,
                redeem: this.get_redeem_giftcard() || false,
                recharge: this.get_recharge_giftcard() || false,
                customer_email: this.get_ereceipt_mail(),
                prefer_ereceipt: this.get_prefer_ereceipt(),
                //reservation
                reserved: this.get_reservation_mode() || false,
                cancel_order_ref: cancel_orders || false,
                cancel_order: this.get_cancel_order() || false,
                set_as_draft: this.get_draft_order() || false,
                fresh_order: this.get_fresh_order() || false,
                partial_pay: this.get_partial_pay() || false,
                //reservation over
                rounding: this.get_rounding(),
                is_rounding: this.pos.config.enable_rounding,
                rounding_option: this.pos.config.enable_rounding ? this.pos.config.rounding_options : false,
                inbalance_disc: this.get_inbalance_discount(),
            }

            $.extend(orders, new_val);
            return orders;
        },
        export_for_printing: function(){
        	var new_val = {};
            var orders = _super_Order.export_for_printing.call(this);
            var order_no = this.pos.get('selectedOrder').get_pos_reference() ||  this.pos.get('selectedOrder').get_name() || false;
            if(order_no.indexOf(_t('Order')) > -1){
        		order_no = order_no.replace(_t('Order '),'');
            }
            new_val = {
            	reprint_payment: this.get_journal() || false,
            	order_no: order_no,
    			order_note: this.get_order_note() || false,
    			date_order: this.get_date_order() || false,
    			remaining_redeemption: this.get_remaining_redeemption() || false,
    			all_gift_receipt: this.get_gift_receipt_data() || false,
    			rounding: this.get_rounding(),
    			net_amount: this.getNetTotalTaxIncluded(),
    			free: this.get_free_data()|| false,
            };
            $.extend(orders, new_val);
            return orders;
        },
        is_paid: function(){
            var currentOrder = this.pos.get('selectedOrder');
            return (round_di(currentOrder.getNetTotalTaxIncluded(),3) < 0.000001
                   || currentOrder.get_total_paid() + 0.000001 >= round_di(currentOrder.getNetTotalTaxIncluded(),3));
        },
        is_ignore_prod: function(prod_id){
        	var self = this;
        	var product = self.pos.db.get_product_by_id(prod_id);
        	if(self.pos.config.debt_dummy_product_id && self.pos.config.debt_dummy_product_id[0] == prod_id){
        		return true;
        	} else if(self.pos.config.payment_product_id && self.pos.config.payment_product_id[0] == prod_id){
        		return true;
        	} else if(self.pos.config.delivery_product_id && self.pos.config.delivery_product_id[0] == prod_id){
        		return true;
        	} else if(self.pos.config.wallet_product && self.pos.config.wallet_product[0] == prod_id){
        		return true;
        	} else if(self.pos.config.gift_card_product_id && self.pos.config.gift_card_product_id[0] == prod_id){
        		return true;
        	} else if(product && product.is_packaging){
        		return true;
        	} else {
        		return false;
        	}
        },
        count_to_be_deliver:function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	var lines = order.get_orderlines();
	    	var count = 0;
			for(var i=0;i<lines.length;i++){
				if(lines[i].get_deliver_info()){
					count = count + 1;
				}
			}
			if(count === 0){
				for(var j=0; j<lines.length;j++){
					if(lines[j].get_delivery_charges_flag()){
						order.remove_orderline(lines[j]);
						order.set_is_delivery(false);
					}
				}
			}
	    },
	    remove_orderline: function( line ){
	    	if(line){
	    		if(line.delivery_charge_flag){
		        	this.assert_editable();
		        	this.orderlines.remove(line);
		        } else {
		        	_super_Order.remove_orderline.call(this, line);
		        }
	    	}
	    },
        set_delivery_date: function(delivery_date) {
            this.delivery_date = delivery_date;
        },
        get_delivery_date: function() {
            return this.delivery_date;
        },
        set_delivery_time: function(delivery_time) {
            this.delivery_time = delivery_time;
        },
        get_delivery_time: function() {
            return this.delivery_time;
        },
        set_delivery: function(delivery) {
            this.delivery = delivery;
        },
        get_delivery: function() {
            return this.delivery;
        },
        set_delivery_charges: function(delivery_state) {
            this.delivery_state = delivery_state;
        },
        get_delivery_charges: function() {
            return this.delivery_state;
        },
        set_is_delivery: function(is_delivery) {
            this.is_delivery = is_delivery;
        },
        get_is_delivery: function() {
            return this.is_delivery;
        },
//        Loyalty
        set_ref_cust: function(ref_cust){
            this.set('ref_cust', ref_cust);
        },
        get_ref_cust: function(){
            return this.get('ref_cust');
        },
        set_ref_cust_label: function(ref_cust){
            this.set('ref_cust_label', ref_cust);
        },
        get_ref_cust_label: function(){
            return this.get('ref_cust_label');
        },
        add_product:function(product, options){
        	var self = this;
            options = options || {};
            var attr = JSON.parse(JSON.stringify(product));
            attr.pos = this.pos;
            attr.order = this;
            var selectedOrder = this.pos.get_order();
            var is_sale_mode = this.get_sale_mode();
            var is_missing_mode = this.get_missing_mode();
            var retoid = this.pos.get_order().get_ret_o_id();
            var order_ref = this.pos.get_order().get_ret_o_ref() // to add backorder in line.
            if(options && !options.force_allow){
            	var product_quaty = self.cart_product_qnty(product.id, true);
                if(self.pos.config.restrict_order && product.type != "service"){
                    if(self.pos.config.prod_qty_limit){
                        var remain = product.qty_available-self.pos.config.prod_qty_limit
                        if(product_quaty>=remain){
                            if(self.pos.config.custom_msg){
                                alert(self.pos.config.custom_msg);
                            } else{
                                alert("Product Out of Stock");
                            }
                            return
                        }
                    }
                    if(product_quaty>=product.qty_available && !self.pos.config.prod_qty_limit){
                        if(self.pos.config.custom_msg){
                            alert(self.pos.config.custom_msg);
                        } else{
                            alert("Product Out of Stock");
                        }
                        return
                    }
                }
	        }
            if(is_missing_mode) {
                var line = new models.Orderline({}, {pos: attr.pos, order: self, product: product});
                if (retoid) {
                    line.set_oid(retoid);
                    line.set_back_order(order_ref);
                }
                if(options.quantity !== undefined){
                    line.set_quantity(options.quantity);
                }
                if(options.price !== undefined){
                    line.set_unit_price(options.price);
                }
                if(options.discount !== undefined){
                    line.set_discount(options.discount);
                }
                var last_orderline = this.get_last_orderline();
                if( last_orderline && last_orderline.can_be_merged_with(line) && options.merge !== false){
                    last_orderline.merge(line);
                }else{
                    line.set_quantity(line.get_quantity() * -1)
                    this.add_orderline(line);
                }
                this.select_orderline(this.get_last_orderline());
            } else {
            	if(!self.pos.config.enable_cross_selling || options.pack_product){
        			self.add_temp_product(product, options);
        		} else {
        			if(options){
        				var product_list = [];
        				if(options.ac_allow == 'No'){
        					self.add_temp_product(product, options);
        				} else {
         					(new Model('product.cross.selling')).call('find_cross_selling_products', [product.id], {}, {async: false})
         					.then(function(result){
                                if(result) {
                                    product_list = []
                                    for(var i=0;i<result.length;i++){
                                        var cross_product = self.pos.db.get_product_by_id(result[i][0]);
                                        cross_product.ac_subtotal = result[i][1]
                                        cross_product.base_product = product.id;
                                        product_list.push(cross_product);
                                    }
                                    self.pos.gui.show_popup('cross_selling',{'product_list':product_list});
                                } else {
                                    self.add_temp_product(product, options);
                                }
        					});
        				}
        			} else {
                        (new Model('product.cross.selling')).call('find_cross_selling_products', [product.id], 
                        		{}, {async: false})
                        .then(function(result){
                            if(result){
                                product_list = []
                                for(var i=0;i<result.length;i++){
                                    var cross_product = self.pos.db.get_product_by_id(result[i][0]);
                                    cross_product.ac_subtotal = result[i][1]
                                    cross_product.base_product = product.id;
                                    product_list.push(cross_product);
                                }
                                self.pos.gui.show_popup('cross_selling',{'product_list':product_list});
                            } else {
                                self.add_temp_product(product, options);
                            }
                        });
        			}
        		}
            }
            self.mirror_image_data();
    	},
    	add_temp_product:function(product, options){
        	var self = this;
        	var partner = this.get_client();
        	var pricelist_id = parseInt($('#price_list').val()) || this.get_pricelist();
    		if(this._printed){
                this.destroy();
                return this.pos.get_order().add_product(product, options);
            }
            this.assert_editable();
            options = options || {};
            var attr = JSON.parse(JSON.stringify(product));
            attr.pos = this.pos;
            attr.order = this;
            var line = new models.Orderline({}, {pos: this.pos, order: this, product: product});
			if(options.quantity !== undefined){
				line.set_quantity(options.quantity);
			}
			if(options.price !== undefined){
				line.set_unit_price(options.price);
			}
			if(options.discount !== undefined){
				line.set_discount(options.discount);
			}
			if(self.get_delivery() && $('#delivery_mode').hasClass('deliver_on')){
				line.set_deliver_info(true);
			}
			if(options.extras !== undefined){
				for (var prop in options.extras) {
					line[prop] = options.extras[prop];
				}
			}
			var orderlines = [];
			if (this.orderlines) {
				orderlines = this.orderlines.models;
			}
			var found = false;
			var qty = line.get_quantity();
			for (var i = 0; i < orderlines.length; i++) {
				var _line = orderlines[i];
				if (_line && _line.can_be_merged_with(line) && options.merge !== false) {
					_line.merge(line);
					this.select_orderline(_line);
					found = true;
					break;
				}
			}
			if (!found) {
				this.orderlines.add(line);
				this.select_orderline(line);
			}
			if(partner){
				if(pricelist_id && !options.child && !this.get_cancel_order() && this.get_giftcard().length <= 0 && this.get_recharge_giftcard().length <= 0){
					var added_line = this.get_selected_orderline();
					var qty = this.get_selected_orderline().get_quantity();
					new Model("product.pricelist").call('price_get', [pricelist_id, product.id, qty], {}, {async: false}).pipe(
						function(res){
							if (res[pricelist_id]) {
								var pricelist_value = parseFloat(res[pricelist_id].toFixed(3));
								if (pricelist_value) {
									var old_price = added_line.get_product().price;
									if(pricelist_value <= old_price){
										added_line.set_unit_price(pricelist_value);
										if(self.pos.config.discount_print_receipt == "public_price"){
											added_line.set_discount_amount_printing(old_price - added_line.get_unit_price());
										}
										if(self.pos.config.store_discount_based_on == "public_price"){
											added_line.set_discount_amount_storing(old_price - added_line.get_unit_price());
	                                	}
										added_line.set_is_pricelist_apply(true);
									}
								}
							}
						}
					);
				}
			}
			this.select_orderline(this.get_last_orderline());
			if($('.all_products').attr('id') == 'on_hand_qty_mode'){
				var data = self.pos.db.get_product_qty();
				var all_filter_data = [];
				for(var i=0;i<data.length;i++){
					all_filter_data.push(data[i]);
				}
				self.pos.chrome.screens.products.product_list_widget.set_product_list(all_filter_data);
			}
			//if(line.has_product_lot){
			//	this.display_lot_popup();
			//} 
//			else if(line.has_product_lot && !self.pos.config.enable_pos_serial){
//				alert("config off and has lot");
//				line.assign_serial_without_asking(line);
//			}
			var selected_line = self.pos.get_order().get_selected_orderline();
			if (selected_line){
				if(self.get_gift_receipt_mode()){
					selected_line.set_line_for_gift_receipt(self.get_gift_receipt_mode());
				}
			}
			var promo_price = 0;
			if(self.pos.config.discount_print_receipt == "public_price"){
				promo_price = product.lst_price - product.price;
				if(promo_price > 0){
					line.set_discount_amount_printing(promo_price);
				}
			}
			if(self.pos.config.store_discount_based_on == "public_price"){
				promo_price = product.lst_price - product.price;
				if(promo_price > 0){
					line.set_discount_amount_storing(promo_price);
				}
        	}
            self.mirror_image_data();
        },
        mirror_image_data:function(){
            var self = this;
            var selectedOrder = self.pos.get('selectedOrder');
            var payment_lines = selectedOrder['paymentlines'];
            var paymentLines = [];
            (payment_lines).each(_.bind(function(item){
                var payment_info = [item.name,item.amount]
                return paymentLines.push(payment_info);
            }, this));
            var paidTotal = selectedOrder.get_total_paid();
            var dueTotal = selectedOrder.get_total_with_tax();
            var remaining = dueTotal > paidTotal ? dueTotal - paidTotal : 0;
            var change = paidTotal > dueTotal ? paidTotal - dueTotal : 0;
            paymentLines.push([paidTotal, remaining, change]);
            var currentOrderLines = selectedOrder['orderlines'];
            var orderLines = [];
            (currentOrderLines).each(_.bind( function(item){
                var t = item.export_as_JSON();
                var product = self.pos.db.get_product_by_id(t.product_id);
                var pro_info = [product.display_name,t.price_unit,t.qty,product.uom_id[1],t.discount];
                return orderLines.push(pro_info);
            }, this));
            orderLines.push([selectedOrder.get_total_tax(),selectedOrder.get_total_with_tax()]);
            var customer_id = selectedOrder.get_client() && selectedOrder.get_client().id || '';
            var pos_mirror = new Model('mirror.image.order');
            pos_mirror.call('create_pos_data',[orderLines,selectedOrder.uid,self.pos.user.id,self.pos.currency.symbol,self.pos.config.id,paymentLines]).then(
                   function(result) { });
        },
//        generate_unique_id: function() {
//            var timestamp = new Date().getTime();
//            return Number(timestamp.toString().slice(-10));
//        },
    	set_order_note: function(order_note) {
            this.order_note = order_note;
        },
        get_order_note: function() {
            return this.order_note;
        },
        set_sale_mode: function(sale_mode) {
            this.set('sale_mode', sale_mode);
        },
        get_sale_mode: function() {
            return this.get('sale_mode');
        },
        set_missing_mode: function(missing_mode) {
            this.set('missing_mode', missing_mode);
        },
        get_missing_mode: function() {
            return this.get('missing_mode');
        },
        set_ret_o_id: function(ret_o_id) {
            this.set('ret_o_id', ret_o_id)
        },
        get_ret_o_id: function(){
            return this.get('ret_o_id');
        },
        set_ret_o_ref: function(ret_o_ref) {
            this.set('ret_o_ref', ret_o_ref)
        },
        get_ret_o_ref: function(){
            return this.get('ret_o_ref');
        },
        set_barcode_for_manager: function(val){
        	this.set('set_barcode_for_manager', val);
        },
        get_barcode_for_manager: function(){
        	return this.get('set_barcode_for_manager');
        },
        set_manager_name_for_discount: function(val){
        	this.set('manager_name_for_discount', val);
        },
        get_manager_name_for_discount: function(){
        	return this.get('manager_name_for_discount');
        },
        add_paymentline: function(cashregister) {
            this.assert_editable();
//            DEBIT
            var self = this;
            var journal = cashregister.journal;
            if (journal.debt && ! this.get_client()){
                setTimeout(function(){
//                    self.gui.show_screen('clientlist');
                }, 30);
            }
//            DEBIT OVER
            var newPaymentline = new models.Paymentline({},{order: this, cashregister:cashregister, pos: this.pos});
            if(cashregister.journal.type !== 'cash' || this.pos.config.iface_precompute_cash){
            	 var val;
            	 var charge = 0;
                 if (journal.debt)
                     val = -this.get_change() || 0
                 else{
                     val = this.get_due();
                     if(cashregister.journal.apply_charges){
                    	 if(cashregister.journal.fees_type === _t("percentage")){
                    		 charge = (cashregister.journal.fees_amount * val) / 100 ;
                    	 }
                     }
                 }
                newPaymentline.set_amount( val );
                newPaymentline.set_payment_charge( charge.toFixed(3) );
            }
            if(cashregister.journal.id === self.pos.config.loyalty_journal[0] && this.get_redeem_amt()){
                newPaymentline.set_amount( Number(this.get_redeem_amt()) );
            }
            if(cashregister.journal.code === self.pos.config.debt_journal[0] && this.get_client()){
                newPaymentline.set_amount( this.get_client().debt * -1 );
            }
            this.paymentlines.add(newPaymentline);
            this.select_paymentline(newPaymentline);
            self.pos.get_order().mirror_image_data();
        },
        remove_paymentline: function(line){
            this.assert_editable();
            if(this.selected_paymentline === line){
                this.select_paymentline(undefined);
            }
            if(line.cashregister.journal.id === self.pos.config.loyalty_journal[0]){
            	this.set_total_redeem_point(this.get_total_redeem_point() - line.get_amount());
            	this.set_redeem_amt(this.get_redeem_amt() - line.get_amount());
            }
            this.paymentlines.remove(line);
            this.pos.get_order().mirror_image_data();
        },
        set_popup_open: function(val){
        	this.set('popup_open',val);
        },
        get_popup_open: function(val){
        	return this.get('popup_open');
        },
        // loyalty
        set_redeem_amt: function(redeem_amt) {
            this.set('redeem_amt', redeem_amt)
        },
        get_redeem_amt: function() {
            return this.get('redeem_amt');
        },
        set_order_redeem_point: function(point) {
            this.set('point', point)
        },
        get_order_redeem_point: function() {
            return this.get('point');
        },
        set_total_redeem_amt: function(total_redeem_amt) {
            this.set('total_redeem_amt', total_redeem_amt)
        },
        get_total_redeem_amt: function() {
            return this.get('total_redeem_amt');
        },
        set_total_redeem_point: function(total_redeem_point) {
            this.set('total_redeem_point', total_redeem_point)
        },
        get_total_redeem_point: function() {
            return this.get('total_redeem_point');
        },
    	set_result: function(result) {
            this.set('result', result);
        },
        get_result: function() {
            return this.get('result');
        },
        set_type_for_wallet: function(type_for_wallet) {
            this.set('type_for_wallet', type_for_wallet);
        },
        get_type_for_wallet: function() {
            return this.get('type_for_wallet');
        },
        set_change_amount_for_wallet: function(change_amount_for_wallet) {
            this.set('change_amount_for_wallet', change_amount_for_wallet);
        },
        get_change_amount_for_wallet: function() {
            return this.get('change_amount_for_wallet');
        },
        set_use_wallet: function(use_wallet) {
            this.set('use_wallet', use_wallet);
        },
        get_use_wallet: function() {
            return this.get('use_wallet');
        },
        set_used_amount_from_wallet: function(used_amount_from_wallet) {
            this.set('used_amount_from_wallet', used_amount_from_wallet);
        },
        get_used_amount_from_wallet: function() {
            return this.get('used_amount_from_wallet');
        },
        set_whole_order: function(whole_order){
        	this.set('whole_order', whole_order);
        },
        get_whole_order: function() {
            return this.get('whole_order');
        },
        cart_product_qnty: function(product_id,flag){
	    	var self = this;
	    	var res = 0;
	    	var order = self.pos.get_order();
	    	var orderlines = order.get_orderlines();
	    	if (flag){
	    		_.each(orderlines, function(orderline){
					if(orderline.product.id == product_id){
						res += orderline.quantity
					}
	    		});
				return res;
	    	} else {
	    		_.each(orderlines, function(orderline){
					if(orderline.product.id == product_id && !orderline.selected){
						res += orderline.quantity
					}
	    		});
	    		return res;
	    	}
	    },
	    set_pricelist_val: function(client_id) {
	        var self = this;
	        if (client_id) {
	            new Model("res.partner").call("read", [parseInt(client_id), ['property_product_pricelist']], {}, {async: false})
	            .then(function(result) {
	                    if (result && result[0].property_product_pricelist) {
	                        self.set('pricelist_val', result[0].property_product_pricelist[0] || '');
	                        $('#price_list').val(result[0].property_product_pricelist[0]);
	                        $('#price_list').trigger('change',this);
	                    }
	                }
	            );
	        }
	    },
	    get_pricelist: function() {
	        return this.get('pricelist_val');
	    },
	    set_rounding_status: function(rounding_status) {
    		this.rounding_status = rounding_status
    	},
    	get_rounding_status: function() {
    		return this.rounding_status;
    	},
	    set_client: function(client){
			_super_Order.set_client.apply(this, arguments);
			if(client){
				this.set_pricelist_val(client.id);
			} else {
	            this.set_pricelist_val('');
	            $('#price_list').val('');
	            $('#price_list').trigger('change',this);
	        }
		},
		//reservation
		set_reservation_mode: function(mode){
            this.set('reservation_mode', mode)
        },
        get_reservation_mode: function(){
            return this.get('reservation_mode');
        },
        set_cancel_order: function(val){
            this.set('cancel_order', val)
        },
        get_cancel_order: function(){
            return this.get('cancel_order');
        },
        set_paying_due: function(val){
            this.set('paying_due', val)
        },
        get_paying_due: function(){
            return this.get('paying_due');
        },
        set_draft_order: function(val) {
            this.set('draft_order', val);
        },
        get_draft_order: function() {
            return this.get('draft_order');
        },
        set_cancellation_charges: function(val) {
            this.set('cancellation_charges', val);
        },
        get_cancellation_charges: function() {
            return this.get('cancellation_charges');
        },
        set_refund_amount: function(refund_amount) {
            this.set('refund_amount', refund_amount);
        },
        get_refund_amount: function() {
            return this.get('refund_amount');
        },
        set_fresh_order: function(fresh_order) {
            this.set('fresh_order', fresh_order);
        },
        get_fresh_order: function() {
            return this.get('fresh_order');
        },
        set_partial_pay: function(partial_pay) {
            this.set('partial_pay', partial_pay);
        },
        get_partial_pay: function() {
            return this.get('partial_pay');
        },
        set_reserved_delivery_date: function(reserved_delivery_date) {
            this.set('reserved_delivery_date', reserved_delivery_date);
        },
        get_reserved_delivery_date: function() {
            return this.get('reserved_delivery_date');
        },
        //reservation over
    });

    var _super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
       initialize: function(attributes, options) {
           var self = this;
           _super_paymentline.initialize.apply(this, arguments);
           this.payment_charge = 0;
        },
        set_giftcard_line_code: function(code) {
            this.code = code;
        },
        get_giftcard_line_code: function(){
            return this.code;
        },
        set_payment_charge: function(val){
        	this.set('payment_charge',val);
        },
        get_payment_charge: function(val){
        	return this.get('payment_charge');
        },
        set_gift_voucher_line_code: function(code) {
    		this.code = code;
    	},
    	get_gift_voucher_line_code: function(){
    		return this.code;
    	},
    	set_pid: function(pid) {
    		this.pid = pid;
    	},
    	get_pid: function(){
    		return this.pid;
    	},
    });

    var orderline_id = 1;
    
    var _super_packlotline = models.Packlotline.prototype;
    models.Packlotline = models.Packlotline.extend({
        initialize: function(attr,options){
        	_super_packlotline.initialize.call(this, attr, options);
        	this.set({
                lot_id : 0,
            });
        },
	    set_lot_id: function(id){
	        this.set({ 'lot_id' : id});
	    },
	    get_lot_id: function(){
	        return this.get('lot_id');
	    },
    });
    
    
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options){
            this.note = '';
            this.discount_amount = 0.00;
            this.oid = null;
            this.backorder = null;
            this.bag_color = false;
            this.delivery_charge_flag = false;
            this.prodlot_id = null;
            this.prodlot_id_id = null;
            this.is_bag = false;
            this.cancel_item = false;
            this.consider_qty = 0;
            this.location_id = false;
//            aspl_pos_product_pack
            this.set({
                'pack_products': false,
                orderline_id : false,
                scrap_item: false,
            })
            _super_orderline.initialize.call(this, attr, options);
        },
        set_orderline_id: function(orderline_id) {
            this.set('orderline_id', orderline_id)
        },
        get_orderline_id: function() {
            return this.get('orderline_id');
        },
        has_valid_product_lot: function() {
        	var self = this;
        	var res = _super_orderline.has_valid_product_lot.call(this);
        	var child_prods = this.get_pack_products();
        	var flag = true;
        	if(!res && this.pack_lot_lines){
        		var valid_product_lot = this.pack_lot_lines.get_valid_lots();
                return Math.abs(this.quantity) === valid_product_lot.length;
        	}
        	return res
        },
//        set_automatic_lot_serial: function(serial_name){
//        	var pack_lot_lines = this.pack_lot_lines;
//        	var len = pack_lot_lines.length;
//    		var cids = [];
//    		for(var i=0; i<len; i++){
//    			var lot_line = pack_lot_lines.models[i];
//    			if(_.contains(serial_name, lot_line.attributes.lot_name)){
//    				cids.push(lot_line.cid);
//    			}
//    		}
//    		for(var j in cids){
//    			var lot_model = pack_lot_lines.get({cid: cids[j]});
//    			lot_model.remove();
//    		}
//        	for(var k=0; k<serial_name.length; k++){
//    			var lot_model = new models.Packlotline({}, {'order_line': this});
//    			lot_model.set_lot_name(serial_name[k]);
//    			if(pack_lot_lines){
//    				pack_lot_lines.add(lot_model);
//    			}
//    		}
//        	pack_lot_lines.set_quantity_by_lot();
//    		this.trigger('change',this);
//        },
//        assign_serial_without_asking: function(line){
//	        new Model('pos.order').get_func('get_lot_near_by_expiry')
//	        (self.pos.get_order().get_selected_orderline().quantity,self.pos.get_order().get_selected_orderline().product.id).then(function(records){
//				console.log("Res",records);
//			});
//        	new Model('stock.quant').get_func('search_read')
//			([['location_id', '=', self.pos.config.stock_location_id[0]],
//			  ['product_id','=',line.product.id]],['lot_id','qty','product_id']).then(function(records){
//	            if(records && records[0]){
//	            	var lot_ids = [];
//	            	var lot_records = {};
//	            	var product = line.product;
//	            	if(product.tracking == 'lot'){
//	            		_.each(records, function(record){
//		            		if(record.lot_id){
//		            			lot_ids.push(record.lot_id[0]);
//		            			if(lot_records[record.lot_id[0]]){
//		            				lot_records[record.lot_id[0]] = lot_records[record.lot_id[0]] + record.qty;
//		            			} else {
//		            				lot_records[record.lot_id[0]] = record.qty;
//		            			}
//		            		}
//		            	});
//	            	} else {
//	            		_.each(records, function(record){
//	            			lot_ids.push(record.lot_id[0]);
//		            		if(record.lot_id){
//		            			lot_records[record.lot_id[0]] = record.qty;
//		            		}
//		            	});
//	            	}
//	            	var limit;
//	            	new Model('stock.production.lot').get_func('search_read')([['id', 'in', lot_ids]],
//		            ['name', 'ref', 'product_id', 'create_date','remaining_qty','life_date'] )
//		            .then(function(serials){
//		            	var shorted_lots = _.sortBy(serials, function(o) { return new moment(o.life_date); });
//		            	var order = self.pos.get_order();
//		            	var orderlines = order.get_orderlines();
//		            	var selected_line = order.get_selected_orderline();
//		            	_.each(orderlines ,function(orderline){
//		            		if(orderline.id == line.id){
//		            			selected_line = orderline;
//		            		}
//		            	})
//		            	for(var main=0;main<shorted_lots.length;main++){
//		            		if(selected_line.pack_lot_lines.length < shorted_lots[main].remaining_qty){
//		            			var lot_name = [];
//	    	            		for (var i=1;i<=selected_line.quantity;i++){
//	    	            			lot_name.push(shorted_lots[main].name);
//	    	            		}
//		            			selected_line.set_automatic_lot_serial(lot_name);
//		            			break;
//		            		}
//		            	}
//		            });
//	            }
//		    });
//        },
        set_input_lot_serial: function(serial_name) {
//        	 Remove All Lots
        	var pack_lot_lines = this.pack_lot_lines;
    		var len = pack_lot_lines.length;
    		var cids = [];
    		for(var i=0; i<len; i++){
    			var lot_line = pack_lot_lines.models[i];
    			cids.push(lot_line.cid);
    		}
    		for(var j in cids){
    			var lot_model = pack_lot_lines.get({cid: cids[j]});
    			lot_model.remove();
    		}
    		// Add new lots
    		for(var k=0; k<serial_name.length; k++){
    			var lot_model = new models.Packlotline({}, {'order_line': this});
    			lot_model.set_lot_name(serial_name[k].lot_name);
    			if(pack_lot_lines){
    				pack_lot_lines.add(lot_model);
    			}
    		}
    		this.trigger('change',this);
        },
        get_total_discount_amount_storing: function(){
        	var self = this;
        	var pricelist_disc_store = 0;
        	var pricelist_disc = 0;
        	var item_discount = this.get_item_discount_amount() || 0;
         	var discount_share = this.get_share_discount_amount() ? this.get_share_discount_amount() * this.quantity : 0;
         	if(self.pos.config.store_discount_based_on == 'public_price'){
         		pricelist_disc = this.get_discount_amount_storing() ? this.get_discount_amount_storing() * this.quantity : 0;
         	}
         	return item_discount + discount_share + pricelist_disc;
        },
        get_total_discount_amount_printing: function(){
        	var self = this;
        	var pricelist_disc = 0;
        	var item_discount = this.get_item_discount_amount() || 0;
         	var discount_share = this.get_share_discount_amount() ? this.get_share_discount_amount() * this.quantity : 0;
         	if(self.pos.config.discount_print_receipt == 'public_price'){
         		pricelist_disc = this.get_discount_amount_printing() ? this.get_discount_amount_printing() * this.quantity : 0;
         	}
         	return item_discount + discount_share + pricelist_disc ;
        },
        set_line_for_gift_receipt: function(line_for_gift_receipt) {
            this.set('line_for_gift_receipt', line_for_gift_receipt);
        },
        get_line_for_gift_receipt: function() {
            return this.get('line_for_gift_receipt');
        },
        set_line_note: function(note) {
            this.set('note', note);
        },
        get_line_note: function() {
            return this.get('note');
        },
        set_globle_discount_amount: function(amount){
        	this.discount_amount = amount;
        },
        get_globle_discount_amount: function(){
        	return this.discount_amount;
        },
        set_previous_discount: function(previous_discount){
        	this.previous_discount = previous_discount;
        },
        get_previous_discount: function(){
        	return this.previous_discount;
        },
        set_unit_discounted_price: function(price){
        	this.unit_discounted_price = price
        },
        get_unit_discounted_price: function(){
        	return this.unit_discounted_price;
        },
        set_is_bag: function(is_bag){
        	this.is_bag = is_bag;
        },
        get_is_bag: function(){
        	return this.is_bag;
        },
        set_share_discount: function(discount){
        	this.set('share_discount', discount);
//        	this.share_discount = discount;
        },
        get_share_discount: function(){
        	return this.get('share_discount');
//        	return this.share_discount;
        },
        set_share_discount_amount: function(discount_amount){
        	this.set('share_discount_amt', discount_amount);
//        	this.share_discount_amt = discount_amount;
        },
        get_share_discount_amount: function(){
        	return this.get('share_discount_amt');
//        	return this.share_discount_amt;
        },
        set_item_discount_amount: function(item_amount){
        	this.set('item_discount_amount', item_amount);
        },
        get_item_discount_amount: function(){
        	return this.get('item_discount_amount');
//        	return this.item_discount_amount;
        },
        set_scrap_item: function(scrap_item) {
            this.set('scrap_item', scrap_item);
        },
        get_scrap_item: function() {
            return this.get('scrap_item');
        },
        get_total_discount_amount_reprint: function(){
//        	var item_discount = this.get_item_discount_amount() || 0;
//         	var discount_share = this.get_share_discount_amount() ? this.get_share_discount_amount() * this.quantity : 0;
        	var item_discount = this.get_item_discount_amount() || 0;
         	var discount_share = this.get_share_discount_amount() || 0;
         	return item_discount + discount_share;
        },
        get_total_discount_amount:function(){
        	var item_discount = this.get_item_discount_amount() || 0;
         	var discount_share = this.get_share_discount_amount() ? this.get_share_discount_amount() * this.quantity : 0;
         	return item_discount + discount_share;
        },
        get_shared_total_discount_amount: function(){
        	return this.get_share_discount_amount() ? this.get_share_discount_amount() * this.quantity : 0;
        },
        export_as_JSON: function() {
        	var self = this;
            var lines = _super_orderline.export_as_JSON.call(this);
            var oid = this.get_oid();
            var return_process = oid;
            var return_qty = this.get_quantity();
            var order_ref = this.pos.get_order() ? this.pos.get_order().get_ret_o_id() : false;
            var line_discount = this.get_item_discount_amount() ? this.get_item_discount_amount() : 0;
            var pricelist_discount_line = this.get_discount_amount_storing() ? this.get_discount_amount_storing() : 0;
            //serial code
            var serials = "Serial No(s).: ";
            var back_ser = "";
            var serials_lot = [];
            var export_item_discount_amount = 0;
            var export_item_discount_share = 0;
            var export_total_discount_amount_storing = 0
            if(return_process){
            	export_item_discount_amount = Math.abs(line_discount + pricelist_discount_line);
            	export_item_discount_share = this.get_share_discount_amount() ? Math.abs(this.get_share_discount_amount() * this.quantity) : 0
    			export_total_discount_amount_storing = Math.abs(this.get_total_discount_amount_storing());
            } else {
            	export_item_discount_amount = line_discount + pricelist_discount_line;
            	export_item_discount_share = this.get_share_discount_amount() ? this.get_share_discount_amount() * this.quantity : 0;
    			export_total_discount_amount_storing = this.get_total_discount_amount_storing();
            }
//            aspl_pos_stock
            var default_stock_location = this.pos.config.stock_location_id ? this.pos.config.stock_location_id[0] : false
            if(this.pack_lot_lines && this.pack_lot_lines.models){
            	_.each(this.pack_lot_lines.models,function(lot) {
            		if(lot && lot.get('lot_name')){
        				if($.inArray(lot.get('lot_name'), serials_lot) == -1){
        					var count = 0;
        					serials_lot.push(lot.get('lot_name'));
        					_.each(self.pack_lot_lines.models,function(lot1) {
                        		if(lot1 && lot1.get('lot_name')){
                        			if(lot1.get('lot_name') == lot.get('lot_name')){
                        				count ++;
                        			}
                        		}
                            });
        					serials += lot.get('lot_name')+"("+count+")"+", ";
        				}
            		}
                });
            } else { serials = "";}
            this.lots = serials;
            var new_attr = {
        		discount_share_per: this.get_share_discount(),
            	product_mrp: this.product.list_price,
            	item_discount_amount: export_item_discount_amount,
            	item_discount_share: export_item_discount_share,
            	discount_amount: export_total_discount_amount_storing,
                note: this.get_line_note(),
                cross_sell_id: this.get_cross_sell_id(),
                return_process: return_process,
                return_qty: parseInt(return_qty),
                back_order: this.get_back_order(),
                scrap_item: this.get_scrap_item() || false,
                deliver: this.get_deliver_info(),
                serial_nums: serials,
                cancel_item: this.get_cancel_item() || false,
                cancel_process: this.get_cancel_process() || false,
                cancel_qty: this.get_quantity() || false,
                consider_qty : this.get_consider_qty() || false,
                cancel_item_id: this.get_cancel_item_id() || false,
                new_line_status: this.get_line_status() || false,
//                aspl_pos_stock
                location_id: this.get_location_id() || default_stock_location,
            }
            $.extend(lines, new_attr);
            return lines;
        },
        set_discount_amount_printing: function(discount_amount) {
            this.set('discount_amount', discount_amount);
        },
        get_discount_amount_printing: function() {
            return this.get('discount_amount');
        },
        set_discount_amount_storing: function(discount_amount_storing){
        	this.set('discount_amount_storing', discount_amount_storing);
        },
        get_discount_amount_storing: function() {
            return this.get('discount_amount_storing');
        },
        is_print_serial: function() {
        	var order = this.pos.get('selectedOrder');
        	return order.get_print_serial();
        },
        set_cross_sell_id: function(cross_sell_id) {
	        this.set('cross_sell_id', cross_sell_id)
	    },
	    get_cross_sell_id: function() {
	        return this.get('cross_sell_id');
	    },
	    set_quantity: function(quantity){
	    	var self = this;
            if(quantity === 'remove'){
                this.set_oid('');
                _.each(this.child_ids, function(child){
                	self.pos.get_order().remove_orderline(child);
                });
                this.pos.get_order().remove_orderline(this);
                return;
            }else{
           		_super_orderline.set_quantity.call(this, quantity);
            }
            this.trigger('change',this);
        },
        set_oid: function(oid) {
            this.set('oid', oid)
        },
        get_oid: function() {
            return this.get('oid');
        },
        set_back_order: function(backorder) {
            this.set('backorder', backorder);
        },
        get_back_order: function() {
            return this.get('backorder');
        },
        set_delivery_charges_color: function(delivery_charges_color) {
            this.delivery_charges_color = delivery_charges_color;
        },
        get_delivery_charges_color: function() {
            return this.get('delivery_charges_color');
        },
        merge: function(orderline){
            if (this.get_oid() || this.pos.get('selectedOrder').get_missing_mode()) {
                this.set_quantity(this.get_quantity() + orderline.get_quantity() * -1);
            } else {
                _super_orderline.merge.call(this, orderline);
            }
        },
        set_bag_color: function(bag_color) {
            this.bag_color = bag_color;
        },
        get_bag_color: function() {
            return this.get('bag_color');
        },
        set_deliver_info: function(deliver_info) {
            this.set('deliver_info', deliver_info);
          },
        get_deliver_info: function() {
          	return this.get('deliver_info');
        },
        set_delivery_charges_flag: function(delivery_charge_flag) {
            this.set('delivery_charge_flag',delivery_charge_flag);
        },
        get_delivery_charges_flag: function() {
            return this.get('delivery_charge_flag');
        },
        export_for_printing: function(){
        	var self = this;
        	var new_val = {};
        	var order = self.pos.get('selectedOrder');
            var orders = _super_orderline.export_for_printing.call(this);
            //serial code
            var serials = "Serial No(s).: ";
            var serials_lot = [];
            var self = this;
            if(this.pack_lot_lines && this.pack_lot_lines.models){
            	_.each(this.pack_lot_lines.models,function(lot) {
            		if(lot && lot.get('lot_name')){
        				if($.inArray(lot.get('lot_name'), serials_lot) == -1){
        					var count = 0;
        					serials_lot.push(lot.get('lot_name'));
        					_.each(self.pack_lot_lines.models,function(lot1) {
                        		if(lot1 && lot1.get('lot_name')){
                        			if(lot1.get('lot_name') == lot.get('lot_name')){
                        				count ++;
                        			}
                        		}
                            });
        					serials += lot.get('lot_name')+"("+count+")"+", ";
        				}
            		}
                });
            } else { serials = "";}
            new_val = {
            	line_note: this.get_line_note() || false,
            	gift_receipt: this.get_line_for_gift_receipt() || false,
            	serials: serials ? serials : false,
                is_print: order.get_print_serial(),
                line_discount_amount: this.get_discount_amount_printing() || false,
            };
            $.extend(orders, new_val);
            return orders;
        },
        set_line_random_number: function(random_number){
            this.set('line_random_number', random_number);
        },
        get_line_random_number: function(){
            return this.get('line_random_number');
        },
        set_is_pricelist_apply: function(val){
			this.is_pricelist_apply = val;
		},
		get_is_pricelist_apply: function(){
			return this.is_pricelist_apply;
		},
		set_manual_price: function (state) {
	        this.manual_price = state;
	    },
		can_be_merged_with: function (orderline) {
	        var result = _super_orderline.can_be_merged_with.call(this, orderline);
	        if(this.pos.get_order().get_sale_mode()){
        		if(this.quantity < 0){
        			return false
        		}
        	}else if(this.pos.get_order().get_missing_mode()){
        		if(this.quantity < 0){
        			return false
        		}else{
        			return true
        		}
        	}
	        if (!result) {
	            if (!this.manual_price) {
	                return (
	                    this.get_product().id === orderline.get_product().id
	                );
	            } else {
	                return false;
	            }
	        }
	        if(this.get_oid() && this.pos.get('selectedOrder').get_sale_mode()) {
                return false;
            } else if ((this.get_oid() != orderline.get_oid()) &&
                            (this.get_product().id == orderline.get_product().id)) {
                return false;
            }
            if(this.get_location_id() !== orderline.get_location_id()){
        		return false
        	}
	        return result;
	    },
	    set_discount_amount: function(discount_amount) {
            this.set('discount_amount', discount_amount);
        },
        get_discount_amount: function() {
            return this.get('discount_amount');
        },
        //reservation
        set_cancel_item: function(val){
            this.set('cancel_item', val)
        },
        get_cancel_item: function(){
            return this.get('cancel_item');
        },
        set_consider_qty: function(val){
            this.set('consider_qty', val)
        },
        get_consider_qty: function(){
            return this.get('consider_qty');
        },
        set_cancel_process: function(oid) {
            this.set('cancel_process', oid)
        },
        get_cancel_process: function() {
            return this.get('cancel_process');
        },
        set_cancel_item_id: function(val) {
            this.set('cancel_item_id', val)
        },
        get_cancel_item_id: function() {
            return this.get('cancel_item_id');
        },
        set_line_status: function(val) {
            this.set('line_status', val)
        },
        get_line_status: function() {
            return this.get('line_status');
        },
        set_location_id: function(location_id){
			this.location_id = location_id;
		},
		get_location_id: function(){
			return this.location_id;
		},
//		aspl_pos_product_pack
		set_pack_products: function(pack_products){
            this.set('pack_products',pack_products);
        },
        get_pack_products: function(){
            return this.get('pack_products');
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
                    return new_qty + ' ' + unit.display_name
                }
            }
        },
    });

    screens.PaymentScreenWidget.include({
    	init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            var currentOrder = self.pos.get_order();
            
            // Quick payement
            this.div_btns = "";
            var payment_buttons = this.pos.config.payment_buttons;
            for(var i in payment_buttons){
            	var btn_info = this.pos.db.get_button_by_id(payment_buttons[i]);
            	this.div_btns += "<div id="+btn_info.id+" class='control-button 1quickpay' data="+btn_info.display_name+">"+self.format_currency(btn_info.display_name)+"</div>"
            }
            this.validate_handler = function(event){
                var key = '';
                if (event.type === "keypress") {
//                    if (event.keyCode === 97) { // Enter
//                        self.validate_order();
//                    }
//                    if(event.keyCode == 98){
//                        self.gui.show_screen('products');
//                    }
                    if(self.pos.company.pos_back && (String.fromCharCode(event.which).toLowerCase() === self.pos.company.pos_back)){
						self.gui.back();
                    }else if(self.pos.company.pos_validate && (String.fromCharCode(event.which).toLowerCase() === self.pos.company.pos_validate)){
                		self.validate_order();
                	}
                }
            };
            this.keyboard_handler = function(event){
                var key = '';
                if(!currentOrder.get_popup_open()){
	                if (event.type === "keypress") {
	                    if (event.keyCode === 13) { // Enter
	                        self.validate_order();
	                    } else if ( event.keyCode === 190 || // Dot
	                                event.keyCode === 110 ||  // Decimal point (numpad)
	                                event.keyCode === 188 ||  // Comma
	                                event.keyCode === 46 ) {  // Numpad dot
	                        key = self.decimal_point;
	                    } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
	                        key = '' + (event.keyCode - 48);
	                    } else if (event.keyCode === 45) { // Minus
	                        key = '-';
	                    } else if (event.keyCode === 43) { // Plus
	                        key = '+';
	                    }
	                } else { // keyup/keydown
	                    if (event.keyCode === 46) { // Delete
	                        key = 'CLEAR';
	                    } else if (event.keyCode === 8) { // Backspace
	                        key = 'BACKSPACE';
	                    }
	                }
	                self.payment_input(key);
	                event.preventDefault();
                }
            };
            this.add_redeem_point = function(event){
            	if(self.pos.config.enable_pos_return){
            		var order = self.pos.get_order();
    	       		if(order && order.get_ret_o_ref() && order.get_ret_o_ref() == "Missing Receipt"){
    	       			return
    	       		}
    	       	}
                var client_id = self.pos.get_order().get_client();
                if (!client_id) {
                     alert (_t('Customer is not selected.'));
                } else {
                     new Model("res.partner").get_func("search_read")([['id', '=', client_id.id]],
                     ['id', 'remaining_points','single_point','per_point_amount','points_to_amount'])
                     .then(function(result) {
                        if(result && result[0]){
                            if(result[0].remaining_points > 0){
                                self.gui.show_popup('redeem_point_popup', {result: result});
                            } else {
                                alert(_t("There is no points for this customer"));
                            }

                        }
                     });
            	}
            };
            this.use_wallet = function(event){
            	var order = self.pos.get_order(); 
            	if(self.pos.config.enable_pos_return){
    	       		if(order.get_ret_o_ref() && order.get_ret_o_ref() == "Missing Receipt"){
    	       			return
    	       		}
    	       	}
    	    	order.set_use_wallet(!order.get_use_wallet());
                if (order.get_use_wallet()) {
                	if(order.get_client() && self.pos.config.wallet_product.length > 0){
                		$('div.js_use_wallet').addClass('highlight');
                		var product = self.pos.db.get_product_by_id(self.pos.config.wallet_product[0]);
                		new Model('res.partner').get_func('search_read')([['id', '=', order.get_client().id]], ['remaining_wallet_amount'])
                		.then(function(results){
                			_.each(results, function(result){
                				var line = new models.Orderline({}, {pos: self.pos, order: order, product: product});
                				if(order.get_total_with_tax() <= result.remaining_wallet_amount){
                					line.set_unit_price(order.get_total_with_tax() * -1);
                				}else if(order.get_total_with_tax() >= result.remaining_wallet_amount){
                					line.set_unit_price(result.remaining_wallet_amount * -1);
                				}
                				order.set_used_amount_from_wallet(Math.abs(line.get_unit_price()));
                				order.set_type_for_wallet('change');
                				line.set_quantity(1);
                				order.add_orderline(line);
                				self.renderElement()
                			});
                		});
                	}
                } else{
                    $('.js_use_wallet').removeClass('highlight');
                    order.set_used_amount_from_wallet(false)
                    _.each(order.get_orderlines(), function(line){
                    	if(line && line.get_product().id === self.pos.config.wallet_product[0]){
                    		order.remove_orderline(line);
                    	} 
                    });
                    self.renderElement();
                }
    	    };
        },
        show: function() {
            self = this;
            var order = self.pos.get_order();
			var lines = order.get_orderlines();
			var date = order.get_delivery_date();
        	var time = order.get_delivery_time();
        	var is_deliver = order.get_is_delivery();
        	if(!date && !time && is_deliver == true){
        		self.gui.show_popup('conf_delivery');
        	}else{
        		window.document.body.addEventListener('keypress',this.validate_handler);
        	}
        	this._super();
//            this._super();
        	if(self.pos.config.enable_order_note) {
        	    $("textarea#order_note").text(this.pos.get_order().get_order_note() || "");
	            $("textarea#order_note").focus(function() {
	                window.document.body.removeEventListener('keypress',self.keyboard_handler);
	                window.document.body.removeEventListener('keydown',self.keyboard_keydown_handler);
	            });
	            $("textarea#order_note").focusout(function() {
	                window.document.body.addEventListener('keypress',self.keyboard_handler);
	                window.document.body.addEventListener('keydown',self.keyboard_keydown_handler);
	            });
        	}
        	$("#email_id").focus(function() {
            	window.document.body.removeEventListener('keypress',self.keyboard_handler);
                window.document.body.removeEventListener('keydown',self.keyboard_keydown_handler);
            });
            $("#email_id").focusout(function() {
            	window.document.body.addEventListener('keypress',self.keyboard_handler);
                window.document.body.addEventListener('keydown',self.keyboard_keydown_handler);
            });
        },
        payment_input: function(input) {
        	var self = this;
        	self._super(input);
        	var order = self.pos.get_order();
        	if(order){
        		order.mirror_image_data();
        	}
        },
        click_invoice: function(){
        	var self = this;
        	var order = self.pos.get_order(); 
        	if(self.pos.config.enable_pos_return){
	       		if(order.get_ret_o_ref() && order.get_ret_o_ref() == "Missing Receipt"){
	       			return
	       		} else{
	       			self._super();
	       		}
	       	} else{
	       		self._super();
	       	}
        },
        hide: function(){
            window.document.body.removeEventListener('keypress',this.validate_handler);
            this._super();
        },
        fetch: function(model, fields, domain, ctx){
     	   return new Model(model).query(fields).filter(domain).context(ctx).all();
        },
        validate_order: function(force_validation) {
            var self = this;
            var order = this.pos.get_order();
            var closed_session = false;
            new Model('pos.order').call('check_valid_session', [self.pos.pos_session.id], {}, {async: false}).then(
            function(res) {
        		closed_session = res;
            });
            if(closed_session){
            	alert('You can not make an order in closed session!! Please logout and login again.');
            	framework.redirect('/web/session/logout');
            	return
            }
            order.set_ereceipt_mail($('#email_id').val());
            if($('#is_ereciept').is(':checked')){
                order.set_prefer_ereceipt(true);
            } else {
                order.set_prefer_ereceipt(false);
            }
            if (order.get_client() && order.get_client().id && $('#update_email').is(':checked')) {
                new Model("res.partner").get_func("write")(order.get_client().id, {'email': order.get_ereceipt_mail()});
            }
            if(this.pos.config.enable_order_note) {
            	order.set_order_note($('#order_note').val());
            }
            // FIXME: this check is there because the backend is unable to
            // process empty orders. This is not the right place to fix it.
            if (order.get_orderlines().length === 0) {
                this.gui.show_popup('error',{
                    'title': _t('Empty Order'),
                    'body':  _t('There must be at least one product in your order before it can be validated'),
                });
                return;
            }

            var plines = order.get_paymentlines();
//            for (var i = 0; i < plines.length; i++) {
//                if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
//                    this.gui.show_popup('error',{
//                        'message': _t('Negative Bank Payment'),
//                        'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
//                    });
//                    return;
//                }
//            }
            if (!order.is_paid() || this.invoicing) {
                return;
            }
            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.gui.show_popup('error',{
                        title: _t('Cannot return change without a cash payment method'),
                        body:  _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return;
                }
            }

            // if the change is too large, it's probably an input error, make the user confirm.
            if(order.get_total_with_tax() > 0){
	            if (!force_validation && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
	                this.gui.show_popup('confirm',{
	                    title: _t('Please Confirm Large Amount'),
	                    body:  _t('Are you sure that the customer wants to  pay') + 
	                           ' ' + 
	                           this.format_currency(order.get_total_paid()) +
	                           ' ' +
	                           _t('for an order of') +
	                           ' ' +
	                           this.format_currency(order.get_total_with_tax()) +
	                           ' ' +
	                           _t('? Clicking "Confirm" will validate the payment.'),
	                    confirm: function() {
	                        self.validate_order('confirm');
	                    },
	                });
	                return;
	            }
            }

//            DEBIT
            var isDebt = false;
            for (var i = 0; i < plines.length; i++) {
                if (plines[i].cashregister.journal.debt) {
                    isDebt = true;
                    break;
                }
            }

            if (isDebt && !order.get_client()){
//            	 this.gui.show_popup('error',{
//                    'message': _t('Unknown customer'),
//                    'comment': _t('You cannot use Debt payment. Select customer first.'),
//                });
            	alert(_t("Please Select Customer"));
                return;
            }

            if(isDebt && order.get_orderlines().length === 0){
            	 this.gui.show_popup('error',{
                    'message': _t('Empty Order'),
                    'comment': _t('There must be at least one product in your order before it can be validated. (Hint: you can use some dummy zero price product)'),
                });
                return;
            }
//            DEBIT OVER
            if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) { 

                    this.pos.proxy.open_cashbox();
            }

            order.initialize_validation_date();
            
            if (order.is_to_invoice()) {
                var invoiced = this.pos.push_and_invoice_order(order);
                this.invoicing = true;

                invoiced.fail(function(error){
                    self.invoicing = false;
                    if (error.message === 'Missing Customer') {
                        self.gui.show_popup('confirm',{
                            'title': _t('Please select the Customer'),
                            'body': _t('You need to select the customer before you can invoice an order.'),
                            confirm: function(){
                                self.gui.show_screen('clientlist');
                            },
                        });
                    } else if (error.code < 0) {        // XmlHttpRequest Errors
                        self.gui.show_popup('error',{
                            'title': _t('The order could not be sent'),
                            'body': _t('Check your internet connection and try again.'),
                        });
                    } else if (error.code === 200) {    // OpenERP Server Errors
                        self.gui.show_popup('error-traceback',{
                            'title': error.data.message || _t("Server Error"),
                            'body': error.data.debug || _t('The server encountered an error while receiving your order.'),
                        });
                    } else {                            // ???
                        self.gui.show_popup('error',{
                            'title': _t("Unknown Error"),
                            'body':  _t("The order could not be sent to the server due to an unknown error"),
                        });
                    }
                });

                invoiced.done(function(){
                    self.invoicing = false;
                    order.finalize();
                });
            } else {
            	var currentOrder = self.pos.get_order();
                if(self.pos.config.enable_bank_charges){
                	this.add_charge_product();
                }
                if(currentOrder.get_change() && self.pos.config.enable_wallet){
                	self.gui.show_popup('AddToWalletPopup');
                }else{
                    self.pos.push_order(order);
                    this.gui.show_screen('receipt');
                }
            }
        },
        renderElement: function() {
           var self = this;
           self._super();

           var order = self.pos.get_order();
           //Quick payment
           this.$('div.1quickpay').click(function(){
	   	    	var amt = $(this).attr('data') ? Number($(this).attr('data')) : false;
	   	    	if(amt){
	   	    		var cashregister = false;
	   	    		for(var i in self.pos.cashregisters){
	   	    			var reg = self.pos.cashregisters[i];
	   	    			if(reg.journal_id[0] == self.pos.config.cash_method[0] ){
	   	    				cashregister = reg;
	   	    			}
	   	    		}
	   	    		if (cashregister){
	   	    			var order = self.pos.get_order();
	   	    			if(!order.selected_paymentline){
   	    			    	order.add_paymentline(cashregister);
   	    			    }
    	    			var selected_amount = order.selected_paymentline.get_amount();
//                        order.add_paymentline(cashregister);
                        order.selected_paymentline.set_amount( Math.max(amt + selected_amount),0 );
                        self.chrome.screens.payment.reset_input();
                        self.chrome.screens.payment.render_paymentlines();
                        if(self.pos.config.validate_on_click){
                        	self.validate_order();
                        }
                   }
	   	    	}
	   	    });
           this.$('#is_print_serial').click(function(){
               var order = self.pos.get('selectedOrder');
               order.set_print_serial($('#is_print_serial').is(':checked'));
           });
           var order = this.pos.get_order();
           if(self.pos.config.enable_loyalty){
        	   self.el.querySelector('.js_redeem').addEventListener('click', this.add_redeem_point);
           }
           if(self.pos.config.enable_wallet){
        	   self.el.querySelector('.js_use_wallet').addEventListener('click', this.use_wallet);
           }
           this.$('.js_gift_voucher').click(function(){
        	   if(self.pos.config.enable_pos_return){
	   	       		if(self.pos.get_order().get_ret_o_ref() && self.pos.get_order().get_ret_o_ref() == "Missing Receipt"){
	   	       			return
	   	       		}
	   	       	}
        	   if(self.pos.get_order().get_client()){
	           		self.gui.show_popup('redeem_gift_voucher_popup', {'payment_self': self});
	           	} else {
	           		alert(_t("Customer is required"));
	           	}
	        });
           this.$('.js_gift_card').click(function(){
        	   if(self.pos.config.enable_pos_return){
	   	       		if(self.pos.get_order().get_ret_o_ref() && self.pos.get_order().get_ret_o_ref() == "Missing Receipt"){
	   	       			return
	   	       		}
	   	       	}
               var client = order.get_client();
               if(!order.get_giftcard().length > 0 && !order.get_recharge_giftcard().length > 0 ){
                   self.gui.show_popup('redeem_card_popup', {'payment_self': self});
               }
           });
           this.$('#is_ereciept').click(function(){
               var order = self.pos.get('selectedOrder');
               var customer_email = order.get_client() ? order.get_client().email : false;
               if($('#is_ereciept').is(':checked')) {
                   $('#email_id').fadeTo('fast', 1).css({ visibility: "visible" });
                   if(order.get_client()){
                	   $('.update_email').fadeTo('fast', 1).css({ visibility: "visible" });
                   }
                   $('#email_id').focus();
                   if(customer_email){
                       $('#email_id').val(customer_email);
                   } else {$('#email_id').val('');}
               } else {
                   $('#email_id').fadeTo('fast', 0, function () {
                       $('#email_id').css({ visibility: "hidden" });
                       $('.update_email').css({ visibility: "hidden" });
                   });
               }
           });
	    },
	    click_set_customer: function(){
	        var self = this;
	        var temp = true;
	        var lines = self.pos.get_order().get_paymentlines();
	        _.each(lines, function(line){
	            if(line.get_gift_voucher_line_code()){
                    temp = false;
	            }
	        });
	        if(temp){
	            this._super();
	        }
	    },

//	    DEBIT
	    render_paymentline: function(line){
            el_node = this._super(line);
            var self = this;
            if (line.cashregister.journal.debt){
                el_node.querySelector('.pay-full-debt')
                    .addEventListener('click', function(){self.pay_full_debt(line)});
            }
            return el_node;
        },
	    render_paymentlines: function() {
	        var self  = this;
	        var order = this.pos.get_order();
	        if (!order) {
	            return;
	        }
	        var lines = order.get_paymentlines();
	        var due   = order.get_due();
	        var extradue = 0;
	        var charge = Number($('.payment_charge_input').val()) || 0;
	        if (due && lines.length  && due !== order.get_due(lines[lines.length-1])) {
	            extradue = due;
	        }
	        if(self.pos.config.enable_bank_charges){
		        if (order.selected_paymentline && order.selected_paymentline.cashregister.journal.apply_charges) {
		        	if(!order.selected_paymentline.cashregister.journal.optional){
			        	if(order.selected_paymentline.cashregister.journal.fees_type === _t('percentage')){
			        		charge = (order.selected_paymentline.get_amount() * order.selected_paymentline.cashregister.journal.fees_amount) / 100;
			        	} else if(order.selected_paymentline.cashregister.journal.fees_type === _t('fixed')){
			        		charge = order.selected_paymentline.cashregister.journal.fees_amount;
			        	}
			        	$('.payment_charge_input').css("background", "#EAB364", "important")
		        	    $('.payment_charge_input').css("color", "#FFF", "important")
		        	} else {
		        	    $('.payment_charge_input').css("background", "#FFF", "important")
		        	    $('.payment_charge_input').css("color", "#EAB364", "important")
		        	}
		        	order.selected_paymentline.set_payment_charge(charge.toFixed(3));
		        }
	        }
	        this.$('.paymentlines-container').empty();
	        var payment_lines = $(QWeb.render('PaymentScreen-Paymentlines', { 
	            widget: this, 
	            order: order,
	            paymentlines: lines,
	            extradue: extradue,
	        }));
	        if(order.get_total_with_tax() < 0){
	        	payment_lines.find('.selected').find('.col-tendered').removeClass('edit');
	        }
	        payment_lines.on('click','.delete-button',function(){
	            self.click_delete_paymentline($(this).data('cid'));
	        });

	        payment_lines.on('click','.paymentline',function(){
	            self.click_paymentline($(this).data('cid'));
	        });
	        payment_lines.on('input','.payment_charge_input',function(){
	        	order.selected_paymentline.set_payment_charge($(this).val());
	        });
	        if(self.pos.config.enable_bank_charges) {
		        payment_lines.on('focus','.payment_charge_input',function(){
		        	window.document.body.removeEventListener('keypress',self.keyboard_handler);
	                window.document.body.removeEventListener('keydown',self.keyboard_keydown_handler);
		        });
		        payment_lines.on('focusout','.payment_charge_input',function(){
		        	window.document.body.addEventListener('keypress',self.keyboard_handler);
	                window.document.body.addEventListener('keydown',self.keyboard_keydown_handler);
		        });
	        }
	        payment_lines.on('click', '#pos-rounding', function(e){
	        	self.toggle_rounding_button();
	        })
	        payment_lines.appendTo(this.$('.paymentlines-container'));
	    },
	    toggle_rounding_button: function(){
	    	var self = this;
	    	var order = this.pos.get_order();
	    	var $rounding_elem = $('#pos-rounding');
	    	if($rounding_elem.hasClass('fa-toggle-off')){
	    		$rounding_elem.removeClass('fa-toggle-off');
	    		$rounding_elem.addClass('fa-toggle-on');
	    		order.set_rounding_status(true);
	    	} else if($rounding_elem.hasClass('fa-toggle-on')){
	    		$rounding_elem.removeClass('fa-toggle-on');
	    		$rounding_elem.addClass('fa-toggle-off');
	    		order.set_rounding_status(false);
	    	}
	    	this.render_paymentlines();
	    },
        pay_full_debt: function(line){
            partner = this.pos.get_order().get_client();
            // Now I write in the amount the debt x -1
            line.set_amount(partner.debt * -1);
            // refresh the display of the payment line
            this.rerender_paymentline(line);
        },
        add_charge_product: function(){
        	var self = this;
        	var selectedOrder = self.pos.get_order();
            var paylines = selectedOrder.get_paymentlines();
            var charge_exist = false;
            var total_charges = 0;
            if(paylines){
            	paylines.map(function(payline){
            		if(payline.cashregister.journal.apply_charges){
	            		var paycharge = Number(payline.get_payment_charge());
	            		total_charges += paycharge;
	            		payline.set_amount(payline.get_amount() + paycharge);
            		}
            	});
            	if(total_charges > 0){
	 				var product = self.pos.db.get_product_by_id(self.pos.config.payment_product_id[0]);
	 				var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
	 				line.set_unit_price(total_charges);
	 				line.set_quantity(1);
	 				selectedOrder.add_orderline(line);
//	 				selectedOrder.selectLine(selectedOrder.getLastOrderline());
            	}
            }
        },
//        click_delete_paymentline: function(cid){
//            this._super(cid);
//            var self  = this;
//            self.pos.get('selectedOrder').mirror_image_data();
//        },
        click_delete_paymentline: function(cid){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	var vouchers = order.get_voucher();
	    	self.pos.get('selectedOrder').mirror_image_data();
	        var lines = self.pos.get_order().get_paymentlines();
	        var get_redeem = order.get_redeem_giftcard();
	        for ( var i = 0; i < lines.length; i++ ) {
	            if (lines[i].cid === cid) {
	            	_.each(vouchers, function(j){
	            		if (lines[i].get_gift_voucher_line_code() == j.voucher_code && j.voucher_amount == lines[i].amount){
			            	order.remove_voucher(lines[i].get_gift_voucher_line_code(), lines[i].pid);
			            } 
	            	});
	            	_.each(get_redeem, function(redeem){
                        if(lines[i].get_giftcard_line_code() == redeem.redeem_card ){
                            order.remove_card(lines[i].get_giftcard_line_code());
                        }
                    });
	            	lines[i].set_amount(0);
	            	order.remove_paymentline(lines[i]);
	                self.reset_input();
	                self.render_paymentlines();
	                return;
	            }
	        }
	    },
        click_paymentline: function(cid){
            this._super(cid);
            var self  = this;
            self.pos.get('selectedOrder').mirror_image_data();
        },
        click_numpad: function(button) {
            this._super(button);
            var self  = this;
            self.pos.get('selectedOrder').mirror_image_data();
        },
        order_is_valid: function(force_validation) {
	    	var self = this;

	    	var order = this.pos.get_order();
	    	if (order.get_voucher().length > 0 && !order.get_client()) {
				this.gui.show_popup('error',{
					'title': _t('Voucher Used'),
					'body':  _t('Customer is required for using Voucher.'),
				});
            	return false;
        	}
        	return this._super(force_validation);
	    },
    });

    var ProductNotePopupWidget = PopupWidget.extend({
	    template: 'ProductNotePopupWidget',
	    show: function(options){
	        options = options || {};
	        this._super(options);
	
	        this.renderElement();
	        var order    = this.pos.get_order();
	    	var selected_line = order.get_selected_orderline();
	        $('textarea#textarea_note').html(selected_line.get_line_note());
	    },
	    click_confirm: function(){
	    	var order    = this.pos.get_order();
	    	var selected_line = order.get_selected_orderline();
	    	var value = this.$('#textarea_note').val();
	    	selected_line.set_line_note(value);
	    	this.gui.close_popup();
	    },
	    renderElement: function() {
            var self = this;
            this._super();
            $('textarea#textarea_note').focus();
    	},
	    
	});
	gui.define_popup({name:'add_note_popup', widget: ProductNotePopupWidget});

	var PutMoneyInPopup = PopupWidget.extend({
	    template: 'PutMoneyInPopup',
	    show: function(options){
	    	this.msg_show_put_money_in = options.msg_show_put_money_in || "";
	    	options = options || {};
	        this._super(options);

	        this.renderElement();
	        $('#txt_reason_in_id').focus();
	    },
	    click_confirm: function(){
	    	var name = '';
	    	var amount ='';
	    	name = $('#txt_reason_in_id').val();
	    	amount = $('#txt_amount__in_id').val();
	    	if(name =='' || amount == ''){
	    		alert(_t("Please fill all fields."));
	    	}else if(!$.isNumeric(amount)){
	    		alert(_t("please input valid amount"));
	    		$('#txt_amount__in_id').val('');
	    		$('#txt_amount__in_id').focus();
	    	}else{
	    		var session_id = '';
	    		session_id = posmodel.pos_session.id;
	    		if(amount <= 0){
	    			$('#txt_amount__in_id').val('');
		    		$('#txt_amount__in_id').focus();
	    			return alert("A transaction can't have a " +amount+ " amount.");
	    		}
	    		new Model('pos.session').call('put_money_in', [name,amount,session_id]).then(
						function(result) {
							if (result['error']) {
								alert(_t(result['error']));
							}
						}).fail(function(error, event) {
					if (error.code === -32098) {
						alert(_t("Odoo server down..."));
						event.preventDefault();
					}
				});
	    		this.gui.close_popup();
	    	}
	    },
	    renderElement: function() {
            var self = this;
            this._super();
    	},
	});
	gui.define_popup({name:'put_money_in', widget: PutMoneyInPopup});

	var TakeMoneyOutPopup = PopupWidget.extend({
	    template: 'TakeMoneyOutPopup',
	    show: function(options){
	    	this.msg_show_take_money_out = options.msg_show_take_money_out || "";
	        options = options || {};
	        this._super(options);

	        this.renderElement();
	        $('#txt_reason_out_id').focus();
	    },
	    click_confirm: function(){
	    	var name = '';
	    	var amount ='';
	    	name = $('#txt_reason_out_id').val();
	    	amount = $('#txt_amount__out_id').val();
	    	if(name =='' || amount == ''){
	    		alert(_t("Please fill all fields."));
	    	}else if(!$.isNumeric(amount)){
	    		alert(_t("please input valid amount"));
	    		$('#txt_amount__out_id').val('');
	    		$('#txt_amount__out_id').focus();
	    	}else{
	    		var session_id = '';
	    		session_id = posmodel.pos_session.id;
	    		if(amount <= 0){
	    			$('#txt_amount__out_id').val('');
		    		$('#txt_amount__out_id').focus();
	    			return alert("A transaction can't have a " +amount+ " amount.");
	    		}
	    		new Model('pos.session').call('take_money_out', [name,amount,session_id]).then(
						function(result) {
							if (result['error']) {
								alert(_t(result['error']));
							}
						}).fail(function(error, event) {
					if (error.code === -32098) {
						alert(_t("Odoo server down..."));
						event.preventDefault();
					}
				});
	    		this.gui.close_popup();
	    	}
	    },
	    renderElement: function() {
            var self = this;
            this._super();
    	},
	});
	gui.define_popup({name:'take_money_out', widget: TakeMoneyOutPopup});

	var TodayPosReportPopup = PopupWidget.extend({
	    template: 'TodayPosReportPopup',
	    show: function(options){
	    	this.str_main = options.str_main || "";
	    	this.str_payment = options.str_payment || "";
	        options = options || {};
	        this._super(options);
	        this.session_total = options.result['session_total'] || [];
	        this.payment_lst = options.result['payment_lst'] || [];
	        this.all_cat = options.result['all_cat'] || [];
	        this.renderElement();
	        $(".tabs-menu a").click(function(event) {
		        event.preventDefault();
		        $(this).parent().addClass("current");
		        $(this).parent().siblings().removeClass("current");
		        var tab = $(this).attr("href");
		        $(".tab-content").not(tab).css("display", "none");
		        $(tab).fadeIn();
		    });
	    },
	    click_confirm: function(){
	        this.gui.close_popup();
	    },
	    renderElement: function() {
            var self = this;
            this._super();
    	},
	});
	gui.define_popup({name:'pos_today_sale', widget: TodayPosReportPopup});

	var ProductSelectionPopupWidget = PopupWidget.extend({
	    template: 'ProductSelectionPopupWidget',
	    show: function(options){
	        options = options || {};
	        this._super(options);
	        this.product_list = options.product_list || {};
    		this.renderElement();
    		$('.ac_selected_product').change(function(event){
    		    if($(this).prop('checked')){
    		        $('.product_qty'+$(this).attr('name')).val('1');
    		    }else{
    		        $('.product_qty'+$(this).attr('name')).val('');
    		    }
    		});
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var fields = {}
			var currentOrder = self.pos.get_order();
			var product = this.product_list[0];
			var list_ids = [];
			$('.ac_selected_product').each(function(idx,el){
				if(el.checked){
					var qty = 0;
					var input_qty = $(".product_qty"+el.name).val();
					if(! isNaN(input_qty) && (input_qty != "") ){
						qty = parseFloat(input_qty);
					}
					if(qty > 0){
						product = self.pos.db.get_product_by_id(parseInt(el.name));
						currentOrder.add_product(product,{'ac_allow':'No', price:product.ac_subtotal, quantity:qty, child: true});
						currentOrder.get_selected_orderline().set_cross_sell_id(product.base_product);
						list_ids.push(currentOrder.get_selected_orderline());
					}
				}
			});
			product = self.pos.db.get_product_by_id(product.base_product);
			currentOrder.add_product(product,{'ac_allow':'No', parent: true});
			currentOrder.get_selected_orderline().child_ids = list_ids;
			currentOrder.mirror_image_data();
	        this.gui.close_popup();
	    },
	    click_cancel: function(){
	    	var self = this;
	    	var product = this.product_list[0];
			var currentOrder = self.pos.get_order();
			product = self.pos.db.get_product_by_id(product.base_product);
			currentOrder.add_product(product,{'ac_allow':'No'});
			this.gui.close_popup();
	    },
	    get_product_image_url: function(product_id){
    		return window.location.origin + '/web/image?model=product.product&field=image_medium&id='+product_id;
    	},
	});
	gui.define_popup({name:'cross_selling', widget: ProductSelectionPopupWidget});

	var ProductQtyPopupWidget = PopupWidget.extend({
	    template: 'ProductQtyPopupWidget',
	    show: function(options){
	        options = options || {};
	        this.prod_info_data = options.prod_info_data || false;
	        this.total_qty = options.total_qty || '';
	        this.product = options.product || false;
	        this.from_selected_line = options.from_selected_line || false;
	        this._super(options);
	        this.renderElement();
	    },
	    click_confirm: function(){
	    	var self = this;
            var order = self.pos.get_order();
	        for(var i in this.prod_info_data){
	        	var loc_id = this.prod_info_data[i][2];
	        	var loc_name = this.prod_info_data[i][0];
	        	if($("#"+loc_id).val() && Number($("#"+loc_id).val()) > 0){
	        		order.add_product(this.product,{quantity:$("#"+loc_id).val(),force_allow:true})
					order.get_selected_orderline().set_location_id(loc_id);
	        	}
	        }
	        self.pos.gui.screen_instances.products.order_widget.renderElement()
	        this.gui.close_popup();
	    },
	});
	gui.define_popup({name:'product_qty_popup', widget: ProductQtyPopupWidget});


//	var PosReturnOrder = PopupWidget.extend({
//	    template: 'PosReturnOrder',
//	    init: function(parent, args) {
//	    	var self = this;
//	        this._super(parent, args);
//	        this.options = {};
//	        this.line = [];
//	        this.return_method_choice = self.pos.cashregisters;
//	        this.update_qty = function(ev){
//	        	ev.preventDefault();
//	            var $link = $(ev.currentTarget);
//	            var $input = $link.parent().parent().find("input");
//	            var min = parseFloat($input.data("min") || 0);
//	            var max = parseFloat($input.data("max") || Infinity);
//	            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
//	            $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
//	            $('input[name="'+$input.attr("name")+'"]').val(quantity > min ? (quantity < max ? quantity : max) : min);
//	            $input.change();
//	            return false;
//	        };
//	        this.keypress_order_number = function(e){
//	        	if(e.which === 13){
//	        		var selectedOrder = self.pos.get_order();
//	        		var ret_o_ref = $("input#return_order_number").val();
//	        		if (ret_o_ref.indexOf('Order') == -1) {
//	                    var ret_o_ref_order = _t('Order ') + ret_o_ref.toString();
//	                }
//	        		if (ret_o_ref.length > 0) {
//	        			new Model("pos.order").get_func("search_read")
//                        ([['pos_reference', '=', ret_o_ref_order]], 
//                        ['id', 'pos_reference', 'partner_id',
//                        ]).then(
//                        function(result) {
//                        	if (result && result.length > 0) {
//                        		selectedOrder.set_ret_o_id(result[0].id);
//                                selectedOrder.set_ret_o_ref(result[0].pos_reference);
//                                if(result[0].partner_id.length > 0){
//                                	selectedOrder.set_client(self.pos.db.get_partner_by_id(result[0].partner_id[0]));
//                                }
//                        		new Model("pos.order.line").get_func("search_read")
//                                ([['order_id', '=', result[0].id],['return_qty', '>', 0]]).pipe(
//                                function(res) {
//                                	if(res && res.length > 0){
//	                                	var lines = [];
//	                                    _.each(res,function(r) {
//	                                    	if(!selectedOrder.is_ignore_prod(r.product_id[0])){
//	                                    		lines.push(r);
//		                                    	self.line[r.id] = r;
//	                                    	}
//	                                    });
//	                                    self.lines = lines;
//		                                    self.renderElement();
//		                                    $('#return_method_choice').show();
//		                                    $('#return_whole_order').prop('disabled',false);
//                                	} else {
//                                		alert(_t("No item found"));
//                                	}
//                                });
//                        	} else {
//                        	    $('input#return_order_number').val('');
//                        	    $('.ac_return_product_list').empty();
//                        		alert(_t("No result found"));
//                        	}
//                        });
//	        		}
//	        	}
//	        };
//	        this.keydown_qty = function(e){
//	        	if($(this).val() > $(this).data('max')){
//	        		$(this).val($(this).data('max'))
//	        	}
//	        	if($(this).val() < $(this).data('min')){
//	        		$(this).val($(this).data('min'))
//	        	}
//	        };
//	        this.selected_product = function(e){
//	        	$('.ac_selected_product').change(function(e){
//	        		if($('.ac_selected_product:checked').length === $('.ac_selected_product').length){
//		            	$('#return_whole_order').prop('checked', true);
//		        	} else{
//		        		$('#return_whole_order').prop('checked', false);
//		        	}
//	        	});
//	        },
//	        this.return_whole_order = function(e){
//
//	        	if($('.ac_selected_product').prop('checked')){
//	        		$('.ac_selected_product').prop('checked', false);
//	        	}else{
//	        		$('.ac_selected_product').prop('checked', true);
//	        	}
//	        	
//	        	_.each($('.product_content'), function(box){
//	        		if($(box).find('.js_quantity').data('max')){
//	        			$(box).find('.js_quantity').val($(box).find('.js_quantity').data('max'));
//	        		}
//	        	});
//	        };
//	    },
//	    show: function(options){
//	    	var self = this;
//	        options = options || {};
//	        this._super(options);
//	        $("span#sale_mode").css('background', '');
//	        $("span#return_order").css('background', 'blue');
//	        $("span#missing_return_order").css('background', '');
//	        this.renderElement();
//	        
//	        $('#return_method_choice').hide();
//	        $("input#return_order_number").focus();
//	        $('.ac_return_product_list').empty();
//	    },
//	    click_confirm: function(){
//	    	var self = this;
//	    	var ret_o_ref = $("input#return_order_number").val();
//	    	var selectedOrder = this.pos.get_order();
//	    	selectedOrder.empty_cart();
//	    	if($('#return_whole_order').prop('checked') && self.pos.config.enable_allow_return_coupon_order){
//            	selectedOrder.set_whole_order(true);
//            }
//	    	if(selectedOrder.get_ret_o_id()){
//	            var flag = $('#return_method_choice').find(':selected').data('journal');
//	            if(flag){
//	            	self.return_products();
//	            	var journal_id = Number($('#return_method_choice').val());
//	            	self.pos.gui.screen_instances.payment.click_paymentmethods(journal_id);
//	            	selectedOrder.selected_paymentline.set_amount(selectedOrder.get_total_with_tax());
//	            	selectedOrder.set_return_via_wallet(true);
//	            	$('#return_order_ref').html(selectedOrder.get_ret_o_ref());
//	            	self.pos.gui.screen_instances.payment.validate_order();
//	            } else{
//	            	var operation = $('#return_method_choice').val();
//	            	if(operation == "select_option"){
//	            		self.return_products();
//	            		this.gui.close_popup();
//	            	} else if(operation == "create_giftcard"){
//	            		var res = self.return_products();
//	            		if(res.count > 0){
//	            			self.gui.show_popup('create_card_popup',{'data':res,'flag':"ret_create_card"});
//	            		} else{
//	            			alert("please select products");
//	            			return
//	            		}
//	            	} else if(operation == "recharge_giftcard"){
//	            		var res = self.return_products();
//	            		if(res.count > 0){
//	            			self.gui.show_popup('recharge_card_popup',{'data':res,'flag':"ret_recharge_card"});
//	            		} else{
//	            			alert("please select products");
//	            			return
//	            		}
//	            	} else if(operation == "add_wallet"){
//	            		var res = self.return_products();
//	            		if(res.count > 0){
//	            			if(selectedOrder.get_client()){
//		        	    		if(selectedOrder.get_missing_mode() || selectedOrder.get_ret_o_id()){
//		        	    			selectedOrder.set_type_for_wallet('return');
//		        	    		}else{
//		        	    			selectedOrder.set_type_for_wallet('change');
//		        	    		}
//		        	    		selectedOrder.set_change_amount_for_wallet(selectedOrder.get_change());
//		        	    		var currentOrder = selectedOrder;
//		        		    	self.pos.push_order(selectedOrder).then(function(){
//		        	        		setTimeout(function(){
//		        	        			self.gui.show_screen('receipt');
//		        	        		},1000)
//		        	        	});
//		        	    	} else {
//		        	    		if(confirm("To add money into wallet you have to select a customer or create a new customer \n Press OK for go to customer screen \n Press Cancel to Discard.")){
//		        	    			self.gui.show_screen('clientlist');
//		        	    		}
//		        	    	}
//	            		} else{
//	            			alert("please select products");
//	            			return
//	            		}
//	            	}
//	            }
//	    	}else{
//		    	$("input#return_order_number").focus();
//		    	alert(_t('Please press enter to view order'));
//	    	}
//	    },
//	    return_products: function(){
//	    	var self = this;
//	    	var ret_o_ref = $("input#return_order_number").val();
//	    	var selectedOrder = this.pos.get_order();
//	    	var total = 0;
//	    	var count = 0;
//	    	_.each($('.ac_selected_product'), function(item){
//            	if($(item).prop('checked')){
//            		var orderline = self.line[$(item).data('name')];
//            		if (orderline){
//	            		var product = self.pos.db.get_product_by_id(orderline.product_id[0]);
//	            		var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
//	                    line.set_quantity($('input[name="'+orderline.id+'"').val() * -1);
//	                    line.set_unit_price(orderline.price_unit);
//	                    line.set_oid(orderline.order_id);
//	                    line.set_back_order(selectedOrder.get_ret_o_ref());
//	                    selectedOrder.add_orderline(line);
//	                    if(orderline.discount){
//	                    	line.set_discount(orderline.discount);
//	                    }
//	                    total += Math.abs(line.get_price_with_tax());
//	                    count++;
//            		}
//            	}
//            });
//	    	return {
//	    		'total': total,
//	    		'count': count,
//	    		'client':selectedOrder.get_client() ? selectedOrder.get_client(): false,
//	    	};
//	    },
//	    click_cancel: function(){
//	    	$('div#menu a#sale_mode').parent().trigger('click');
//	    	this.gui.close_popup();
//	    },
//	    get_product_image_url: function(product_id){
//    		return window.location.origin + '/web/image?model=product.product&field=image_medium&id='+product_id;
//    	},
//    	renderElement: function(){
//            this._super();
//            this.$('.input-group-addon').delegate('a.js_qty','click', this.update_qty);
//            this.$('div.content').delegate('#return_order_number','keypress', this.keypress_order_number);
//            this.$('div.input-group').delegate('.js_quantity','input', this.keydown_qty);
//            this.$('div.whole_order').delegate('#return_whole_order','change', this.return_whole_order); // open if use bonus
//            this.$('span.check_box_tag').delegate('.ac_selected_product','click', this.selected_product);
//    	},
//	});
//	gui.define_popup({name:'pos_return_order', widget: PosReturnOrder});
	var PosReturnOrder = PopupWidget.extend({
	    template: 'PosReturnOrder',
	    init: function(parent, args) {
	    	var self = this;
	        this._super(parent, args);
	        this.options = {};
	        this.line = [];
	        this.result = [];
	        this.return_method_choice = self.pos.cashregisters;
	        this.update_return_product_qty = function(ev){
	        	ev.preventDefault();
	            var $link = $(ev.currentTarget);
	            var $input = $link.parent().parent().find("input");
	            var product_elem = $('.product_content[data-line-id="'+$input.attr("name")+'"]')
	            if(!product_elem.hasClass('select_item')){
	            	product_elem.addClass('select_item')
	            }
	            var min = parseFloat($input.data("min") || 0);
	            var max = parseFloat($input.data("max") || $input.val());
	            var total_qty = parseFloat($input.data("total-qty") || 0);
	            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
	            $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
	            var $scrap_input = $('input.scrap_product_qty[name="'+$input.attr("name")+'"]');
	            $scrap_input.data('max', total_qty - $input.val());
	            $scrap_input.change();
	            $input.change();
	            return false;
	        };
	        this.update_scrap_product_qty = function(ev){
	        	ev.preventDefault();
	            var $link = $(ev.currentTarget);
	            var $input = $link.parent().parent().find("input");
	            var product_elem = $('.product_content[data-line-id="'+$input.attr("name")+'"]')
	            if(!product_elem.hasClass('select_item')){
	            	product_elem.addClass('select_item')
	            }
	            var min = parseFloat($input.data("min") || 0);
	            var max = parseFloat($input.data("max") || $input.val());
	            var total_qty = parseFloat($input.data("total-qty") || 0);
	            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
	            $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
	            var $return_input = $('input.return_product_qty[name="'+$input.attr("name")+'"]');
	            $return_input.data('max', total_qty - $input.val());
	            $return_input.change();
	            $input.change();
	            return false;
	        };
	        this.select_item = function(e){
	        	self.selected_item($(this).parent());
	        };
	        this.keypress_order_number = function(e){
	        	if(e.which === 13){
	        		var selectedOrder = self.pos.get_order();
	        		var ret_o_ref = $("input#return_order_number").val();
	        		if (ret_o_ref.indexOf('Order') == -1) {
	                    var ret_o_ref_order = _t('Order ') + ret_o_ref.toString();
	                }
	        		if (ret_o_ref.length > 0) {
	        			new Model("pos.order").get_func("search_read")
                        ([['pos_reference', '=', ret_o_ref_order]], 
                        ['id', 'pos_reference', 'partner_id']).then(
                        function(result) {
                        	if (result && result.length > 0) {
                        		self.result = result;
                        		selectedOrder.set_ret_o_id(result[0].id);
                                selectedOrder.set_ret_o_ref(result[0].pos_reference);
                        		new Model("pos.order.line").get_func("search_read")
                                ([['order_id', '=', result[0].id],['return_qty', '>', 0]]).pipe(
                                function(res) {
                                	if(res && res.length > 0){
	                                	var lines = [];
	                                    _.each(res,function(r) {
	                                    	lines.push(r);
	                                    	self.line[r.id] = r;
	                                    });
	                                    self.lines = lines;
	                                    self.renderElement();
                                	} else {
                                		alert(_t("No item found"));
                                	}
                                });
                        	} else {
                        		alert(_t("No result found"));
                        	}
                        });
	        		}
	        	}
	        };
	        this.keydown_qty = function(e){
	        	var opp_elem;
	        	var product_elem = $('.product_content[data-line-id="'+$(e.currentTarget).attr("name")+'"]')
	            if(!product_elem.hasClass('select_item')){
	            	product_elem.addClass('select_item')
	            }
	        	if($(e.currentTarget).hasClass('return_product_qty')){
	        		opp_elem = $('.scrap_product_qty[name="'+ $(e.currentTarget).attr('name') +'"]');
	        	} else if($(e.currentTarget).hasClass('scrap_product_qty')){
	        		opp_elem = $('.return_product_qty[name="'+ $(e.currentTarget).attr('name') +'"]');
	        	}
	        	var total_qty = $(e.currentTarget).data('total-qty');
	        	$(opp_elem).data('max', total_qty - $(e.currentTarget).val());
	        	if((!$.isNumeric($(e.currentTarget).val())) || ($(e.currentTarget).val() > $(e.currentTarget).data('max'))){
	        		$(e.currentTarget).val('');
	        		$('.product[data-line-id="'+ $(e.currentTarget).attr('name') +'"]').find('.item_remain_qty').effect( "bounce", {times:3}, 300 );;
	        	}
	        };
	    },
	    selected_item: function($elem){
	    	var self = this;
	    	if($elem.hasClass('select_item')){
	    		$elem.removeClass('select_item')
	    	} else {
	    		$elem.addClass('select_item')
	    	}
	    	
	    },
	    show: function(options){
	    	var self = this;
	        options = options || {};
	        this._super(options);
	        $("span#sale_mode").css('background', '');
	        $("span#return_order").css('background', 'blue');
	        this.renderElement();
	        $("input#return_order_number").focus();
	        $('.ac_product_list').empty();
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var selectedOrder = this.pos.get_order();
	    	if(selectedOrder.get_ret_o_id()){
	    		var flag = $('#return_method_choice').find(':selected').data('journal');
	            if(flag){
	            	self.return_products();
	            	var journal_id = Number($('#return_method_choice').val());
	            	self.pos.gui.screen_instances.payment.click_paymentmethods(journal_id);
	            	selectedOrder.selected_paymentline.set_amount(selectedOrder.get_total_with_tax());
	            	selectedOrder.set_return_via_wallet(true);
	            	$('#return_order_ref').html(selectedOrder.get_ret_o_ref());
	            	self.pos.gui.screen_instances.payment.validate_order();
	            } else{
	            	var operation = $('#return_method_choice').val();
	            	if(operation == "create_giftcard"){
	            		var res = self.return_products();
	            		if(res.count > 0){
	            			self.gui.show_popup('create_card_popup',{'data':res,'flag':"ret_create_card"});
	            		} else{
	            			alert("please select products");
	            			return
	            		}
	            	} else if(operation == "recharge_giftcard"){
	            		var res = self.return_products();
	            		if(res.count > 0){
	            			self.gui.show_popup('recharge_card_popup',{'data':res,'flag':"ret_recharge_card"});
	            		} else{
	            			alert("please select products");
	            			return
	            		}
	            	} else if(operation == "add_wallet"){
	            		var res = self.return_products();
	            		if(res.count > 0){
	            			if(selectedOrder.get_client()){
		        	    		if(selectedOrder.get_missing_mode() || selectedOrder.get_ret_o_id()){
		        	    			selectedOrder.set_type_for_wallet('return');
		        	    		}else{
		        	    			selectedOrder.set_type_for_wallet('change');
		        	    		}
		        	    		selectedOrder.set_change_amount_for_wallet(selectedOrder.get_change());
		        	    		var currentOrder = selectedOrder;
		        		    	self.pos.push_order(selectedOrder).then(function(){
		        	        		setTimeout(function(){
		        	        			self.gui.show_screen('receipt');
		        	        		},1000)
		        	        	});
		        	    	} else {
		        	    		if(confirm("To add money into wallet you have to select a customer or create a new customer \n Press OK for go to customer screen \n Press Cancel to Discard.")){
		        	    			self.gui.show_screen('clientlist');
		        	    		}
		        	    	}
	            		} else{
	            			alert("please select products");
	            			return
	            		}
	            	} else {
	            		self.return_products();
	            		self.gui.close_popup();
	            	}
	            }
//	    		if($('.select_item').length > 0){
//		            _.each($('.select_item'), function(item){
//	            		var orderline = self.line[$(item).data('line-id')];
//	            		var input_val = $(item).find('input.return_product_qty[name='+orderline.id+']').val()
//	            		if(input_val > 0 && input_val <= orderline.return_qty){
//	            			var product = self.pos.db.get_product_by_id(orderline.product_id[0]);
//		            		var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
//		                    line.set_quantity($('input[name="'+orderline.id+'"').val() * -1);
//		                    line.set_unit_price(orderline.price_unit);
//		                    line.set_oid(orderline.order_id);
//		                    if(orderline.discount){
//		                    	line.set_discount(orderline.discount);
//		                    }
//		                    line.set_back_order(selectedOrder.get_ret_o_ref());
//		                    selectedOrder.add_orderline(line);
//	            		}
//		            });
//		            _.each($('.select_item'), function(item){
//	            		var orderline = self.line[$(item).data('line-id')];
//	            		var input_val = $(item).find('input.scrap_product_qty[name='+orderline.id+']').val()
//	            		if(input_val > 0 && input_val <= orderline.return_qty){
//	            			var product = self.pos.db.get_product_by_id(orderline.product_id[0]);
//		            		var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
//		                    line.set_quantity(input_val * -1);
//		                    line.set_unit_price(orderline.price_unit);
//		                    line.set_oid(orderline.order_id);
//		                    line.set_back_order(selectedOrder.get_ret_o_ref());
//		                    if(orderline.discount){
//		                    	line.set_discount(orderline.discount);
//		                    }
//		                    line.set_scrap_item(true);
//		                    selectedOrder.add_orderline(line);
//	            		}
//		            });
//		            $('#return_order_ref').html(selectedOrder.get_ret_o_ref());
//		            this.gui.close_popup();
//	    		}else{
//	    			alert(_t('Please select any product to return'));
//	    		}
	    	}else{
		    	$("input#return_order_number").focus();
		    	alert(_t('Please press enter to view order'));
	    	}
	    },
	    return_products: function(){
	    	var self = this;
	    	var ret_o_ref = $("input#return_order_number").val();
	    	var selectedOrder = this.pos.get_order();
	    	var total = 0;
	    	var count = 0;
	    	if($('.select_item').length > 0){
	    		  var pack_lot_ids = []
	    		  var line_prod_serial = {}
	            _.each($('.select_item'), function(item){
            		var orderline = self.line[$(item).data('line-id')];
            		var input_val = $(item).find('input.return_product_qty[name='+orderline.id+']').val()
            		if(input_val > 0 && input_val <= orderline.return_qty){
            			var product = self.pos.db.get_product_by_id(orderline.product_id[0]);
	            		var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
	                    var return_qty = $('input[name="'+orderline.id+'"').val() * -1;
	                    if(orderline.pack_lot_ids.length != 0){
	                    	$.merge( pack_lot_ids, orderline.pack_lot_ids)
	                    	if(line_prod_serial[orderline.id]){
	                    		$.merge(line_prod_serial[orderline.id],orderline.pack_lot_ids)
	                    	} else {
	                    		line_prod_serial[orderline.id] = orderline.pack_lot_ids
	                    	}
	                    }
//	                    Discount while return order Back here
	                    line.set_quantity(return_qty);
	                    line.set_unit_price(orderline.price_unit);
	                    line.set_oid(orderline.order_id);
	                    line.set_orderline_id(orderline.id);
	                    if(orderline.discount){
	                    	line.set_discount(orderline.discount);
	                    }
	                    var unit_discounted_price,previous_disc_amount;
	                    if (Math.abs(orderline.qty) > 1){
	                    	unit_discounted_price = orderline.item_discount_share / orderline.qty;
	                    } else{
	                    	unit_discounted_price = orderline.item_discount_share;
	                    }
	                    line.set_unit_discounted_price(Math.abs(unit_discounted_price));
	                    line.set_share_discount(orderline.discount_share_per);
	                    if (Math.abs(line.qty) > 1){
	                    	previous_disc_amount = line.get_unit_discounted_price() * line.qty;
	                    }
	                    else{
	                    	previous_disc_amount = line.get_unit_discounted_price()
	                    }
						line.set_share_discount_amount(Math.abs(previous_disc_amount));
						line.set_globle_discount_amount(Math.abs(previous_disc_amount));

						line.set_back_order(selectedOrder.get_ret_o_ref());
	                    selectedOrder.add_orderline(line);
	                    total += Math.abs(line.get_unit_price());
	                    count++;
            		}
	            });
	            _.each($('.select_item'), function(item){
            		var orderline = self.line[$(item).data('line-id')];
            		var input_val = $(item).find('input.scrap_product_qty[name='+orderline.id+']').val()
            		if(input_val > 0 && input_val <= orderline.return_qty){
            			var product = self.pos.db.get_product_by_id(orderline.product_id[0]);
	            		var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
	            		if(orderline.pack_lot_ids.length != 0){
	                    	$.merge( pack_lot_ids, orderline.pack_lot_ids)
	                    	if(line_prod_serial[orderline.id]){
	                    		$.merge(line_prod_serial[orderline.id],orderline.pack_lot_ids)
	                    	} else {
	                    		line_prod_serial[orderline.id] = orderline.pack_lot_ids
	                    	}
	                    }
	            		line.set_quantity(input_val * -1);
	                    line.set_unit_price(orderline.price_unit);
	                    line.set_oid(orderline.order_id);
	                    line.set_orderline_id(orderline.id);
	                    line.set_back_order(selectedOrder.get_ret_o_ref());
	                    line.set_orderline_id(orderline.id);
	                    if(orderline.discount){
	                    	line.set_discount(orderline.discount);
	                    }
	                    var unit_discounted_price,previous_disc_amount;
	                    if (Math.abs(orderline.qty) > 1){
	                    	unit_discounted_price = orderline.item_discount_share / orderline.qty;
	                    } else{
	                    	unit_discounted_price = orderline.item_discount_share;
	                    }
	                    line.set_unit_discounted_price(Math.abs(unit_discounted_price));
	                    line.set_share_discount(orderline.discount_share_per);
	                    if (Math.abs(line.qty) > 1){
	                    	previous_disc_amount = line.get_unit_discounted_price() * line.qty;
	                    }
	                    else{
	                    	previous_disc_amount = line.get_unit_discounted_price()
	                    }
						line.set_share_discount_amount(Math.abs(previous_disc_amount));
						line.set_globle_discount_amount(Math.abs(previous_disc_amount));

	                    line.set_scrap_item(true);
	                    selectedOrder.add_orderline(line);
	                    total += Math.abs(line.get_price_with_tax());
	                    count++;
            		}
	            });
	            //for parent product serial
	            if(pack_lot_ids.length != 0){
	            	new Model('pos.pack.operation.lot').call('search_read', [[['id', 'in', pack_lot_ids]]], {}, {async: false}).then(
	                function(res) {
	                	for(var i in line_prod_serial){
	                		var lot_data = []
	                		for (var j in line_prod_serial[i]){
	                			var prod_lot_id = line_prod_serial[i][j];
	                			for(var k in res){
	                				if(res[k].id == prod_lot_id){
	                					lot_data.push(res[k]);
	                				}
	                			}
	                		}
	                		line_prod_serial[i] = lot_data
	                	}
	                	selectedOrder.set_return_product_lots(line_prod_serial);
	                });
	            }
	            $('#return_order_ref').html(selectedOrder.get_ret_o_ref());
	            var orderlines = selectedOrder.get_orderlines();
	            _.each(orderlines, function(line){
	            	var lot_data = selectedOrder.get_return_product_lots_by_line_id(line.get_orderline_id());
	            	var prod = line.get_product();
	            	if(lot_data && lot_data[0]){
	            		line.set_input_lot_serial(lot_data,1)
//	            		if(prod.tracking == 'lot'){
//	            			line.set_input_lot_serial(lot_data[0].lot_name,line.quantity,'lot')
//	            		} else if(prod.tracking == 'serial') {
//	            			_.each(lot_data, function(lot){
//	            				line.set_input_lot_serial(lot.lot_name,1,'unique_serial')
//	            			});
//	            		}
	            	}
	            });
	            this.gui.close_popup();
    		}else{
    			alert(_t('Please select any product to return'));
    		}
	    	return {
	    		'total': total,
	    		'count': count,
	    		'client':selectedOrder.get_client() ? selectedOrder.get_client(): false,
	    	};
	    },
	    click_cancel: function(){
	    	$("span#sale_mode").css('background', 'blue');
	        $("span#return_order").css('background', '');
	        $("span#missing_return_order").css('background', '');
	        $("span#sale_mode").trigger('click');
	    	this.gui.close_popup();
	    },
	    get_product_image_url: function(product_id){
    		return window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id='+product_id;
    	},
    	renderElement: function(){
            this._super();
            this.$('.return_scrap .input-group-addon').delegate('a.js_scrap_qty','click', this.update_scrap_product_qty);
            this.$('.return_product .input-group-addon').delegate('a.js_return_qty','click', this.update_return_product_qty);
            this.$('div.content').delegate('#return_order_number','keypress', this.keypress_order_number);
            this.$('div.input-group').delegate('.js_quantity','input', this.keydown_qty);
            this.$('.ac_product_list').delegate('.product-img','click', this.select_item);
    	}
	});
	gui.define_popup({name:'pos_return_order', widget: PosReturnOrder});

	screens.ReceiptScreenWidget.include({
		show: function(){
			var self = this;
	        var order = self.pos.get_order();
	        var vouchers = order.get_voucher();
	        var counter = []
			if(self.pos.config.enable_gift_voucher){
                if(order.get_voucher().length > 0){
                    var voucher_use = _.countBy(vouchers, 'voucher_code');
                    _.each(vouchers, function(voucher){
                        if(_.where(counter, {voucher_code: voucher.voucher_code}).length < 1){
                            counter.push({
                                voucher_name : voucher.display_name,
                                voucher_code: voucher.voucher_code,
                                remaining_redeemption: voucher.redemption_customer - (voucher.already_redeemed > 0 ? voucher.already_redeemed + voucher_use[voucher.voucher_code] : voucher_use[voucher.voucher_code]),
                            });
                        }
                    });
                    order.set_remaining_redeemption(counter);
                }
            }
	        if(self.pos.config.enable_print_valid_days){
                var order_category_list = [];
                var order = this.pos.get_order();
                var orderlines = order.get_orderlines();
                _.each(orderlines, function(orderline){
                    if(orderline.get_product().pos_categ_id){
                        var category = self.pos.db.get_category_by_id(orderline.get_product().pos_categ_id[0]);
                        if (category && category.return_valid_days > 0){
                            order_category_list.push({
                                "id": category.id,
                                "name": category.name,
                                "return_valid_days": category.return_valid_days || self.pos.config.default_return_valid_days,
                            });
                        } else if(category && category.return_valid_days < 1){
                            var temp = self.find_parent_category(category);
                            order_category_list.push(temp);
                        }
                    } else {
                        order_category_list.push({
                            "id": self.pos.db.root_category_id,
                            "name": "others",
                            "return_valid_days": self.pos.config.default_return_valid_days,
                        });
                    }
                });
                this.final_order_category_list = _.uniq(order_category_list, function(item){
                    return item.id;
                });
            }
			
            this._super();

            var next = self.pos.company.pos_next;
            this.handler_new_order = function(e){
                if(String.fromCharCode(e.which) === next){ // for ASCII of 'n' character
                    self.click_next();
                }
            };
            $('body').on('keypress', this.handler_new_order);
        },
        find_parent_category: function(category){
            var self = this;
            if (category){
                if(!category.parent_id){
                    return {
                        "id": category.id,
                        "name": category.name,
                        "return_valid_days": category.return_valid_days || self.pos.config.default_return_valid_days,
                    };
                }
                if(category.return_valid_days > 0){
                    return {
                        "id": category.id,
                        "name": category.name,
                        "return_valid_days": category.return_valid_days || self.pos.config.default_return_valid_days,
                    };
                } else {
                    category = self.pos.db.get_category_by_id(category.parent_id[0]);
                    return self.find_parent_category(category)
                }
            }
        },
        click_next: function() {
        	var self = this;
 	        this.pos.get_order().set_delivery(false);
 	        this.pos.get_order().set_delivery_date(false);
 	        this.pos.get_order().set_delivery_time(false);
// 	        this.pos.get_order().finalize();
 	        $('#delivery_mode').removeClass('deliver_on');
            this.pos.get('selectedOrder').set_ret_o_id('');
            this.pos.get('selectedOrder').destroy();
            this.pos.get('selectedOrder').set_sale_mode(false);
            this.pos.get('selectedOrder').set_missing_mode(false);
            $("span#sale_mode").css('background', 'blue');
            $("span#return_order").css('background', '');
            $("span#missing_return_order").css('background', '');
            $('#return_order_ref').html('');
            $('#return_order_number').text('');
            $('#ref_customer_name').text('');
            $("span.remaining-qty-tag").css('display', 'none');
        },
        wait: function( callback, seconds){
            return window.setTimeout( callback, seconds * 1000 );
         },
//         print: function() {
//             this.pos.get_order()._printed = true;
//             this.wait( function(){ window.print(); }, 2);
//         },
         print_xml: function() {
        	 var order = this.pos.get_order();
        	 var env = {
                 widget:  this,
                 pos:     this.pos,
                 order:   this.pos.get_order(),
                 receipt: this.pos.get_order().export_for_printing(),
                 paymentlines: this.pos.get_order().get_paymentlines()
             };
             if(order.get_free_data()){
                 var receipt = QWeb.render('XmlFreeTicket',env);
             } else{
                 var receipt = QWeb.render('XmlReceipt',env);
             }
             this.pos.proxy.print_receipt(receipt);
             this.pos.get_order()._printed = true;
         },
         renderElement: function() {
             var self = this;
             this._super();
             this.$('.next').click(function(){
                self.pos.get('selectedOrder').mirror_image_data();
             });
         },
         render_receipt: function() {
             var order = this.pos.get_order();
             
             if (order.get_free_data()){
                 this.$('.pos-receipt-container').html(QWeb.render('FreeTicket',{
                     widget:this,
                     order: order,
                 }));
             }else if(order.get_print_stock_data()){
            	this.$('.pos-receipt-container').html(QWeb.render('InternalTransferTicket',{
                     widget:this,
                     order: order,
                     receipt: order.export_for_printing(),
                     stock_data:order.get_print_stock_data() || false,
                 }));
             } else{
                 this.$('.pos-receipt-container').html(QWeb.render('PosTicket',{
                     widget:this,
                     order: order,
                     receipt: order.export_for_printing(),
                     orderlines: order.get_orderlines(),
                     paymentlines: order.get_paymentlines(),
                 }));
                 var gift_receipt_lines = _.filter(order.get_orderlines(), function(line){
                     return line.get_line_for_gift_receipt()
                 })
                 this.$('.pos-receipt-container').html(QWeb.render('PosTicket',{
                     widget:this,
                     order: order,
                     receipt: order.export_for_printing(),
                     orderlines: order.get_orderlines(),
                     paymentlines: order.get_paymentlines(),
                 }));
                 var gift_receipt_data = order.get_gift_receipt_data();
                 if(gift_receipt_data && gift_receipt_data.length > 0){
                     for (var key in gift_receipt_data) {
                         this.$('.pos-receipt-container').append(QWeb.render('PosGiftTicket',{
                             widget:this,
                             order: order,
                             data:gift_receipt_data[key],
                             receipt: order.export_for_printing(),
                             orderlines: gift_receipt_lines,
                             all_gift_receipt: order.get_gift_receipt_data(),
                         }));
                     }
                 } else if(order.get_gift_receipt_mode() && !gift_receipt_data) {
                	order.set_gift_receipt_data(order.get_orderlines());
                	this.$('.pos-receipt-container').append(QWeb.render('PosGiftTicket',{
                         widget:this,
                         order: order,
                         receipt: order.export_for_printing(),
                         orderlines: order.get_orderlines(),
                     }));
                 } 
             }
             var barcode_val = this.pos.get_order().get_pos_reference() || this.pos.get_order().get_name();
             if (barcode_val.indexOf(_t("Order ")) != -1) {
                 var vals = barcode_val.split(_t("Order "));
                 if (vals) {
                     var barcode = vals[1];
                     $("tr#barcode1").html($("<td text-align:center;><div class='" + barcode + "' /></td>"));
                     $("." + barcode.toString()).barcode(barcode.toString(), "code128");
                     $("td#barcode_val").html(barcode);
                 }
             }

             var bar_val = order.get_giftcard();
             if( bar_val && bar_val[0]){
                 var barcode = bar_val[0].giftcard_card_no;
                 $("tr#barcode_giftcard").html($("<td style='padding:2px 2px 2px 38px; text-align:center;'><div class='" + barcode + "' width='150' height='50' /></td>"));
                 $("." + barcode.toString()).barcode(barcode.toString(), "code128");
                 $("td#barcode_val_giftcard").html(barcode);
             }

             var barcode_recharge_val = this.pos.get('selectedOrder').get_recharge_giftcard();
             if( barcode_recharge_val && barcode_recharge_val[0]){
                 var barcode = barcode_recharge_val[0].recharge_card_no;
                 $("tr#barcode_recharge").html($("<td style='padding:2px 2px 2px 38px; text-align:center;'><div class='" + barcode + "' width='150' height='50' /></td>"));
                 $("." + barcode.toString()).barcode(barcode.toString(), "code128");
                 $("td#barcode_val_recharge").html(barcode);
             }

             var barcode_free_val = this.pos.get('selectedOrder').get_free_data();
             if( barcode_free_val){
                 var barcode = barcode_free_val.giftcard_card_no;
                 $("tr#barcode_free").html($("<td style='padding:2px 2px 2px 38px; text-align:center;'><div class='" + barcode + "' width='150' height='50' /></td>"));
                 $("." + barcode.toString()).barcode(barcode.toString(), "code128");
                 $("td#barcode_val_free").html(barcode);
             }

             var barcode_redeem_val = this.pos.get('selectedOrder').get_redeem_giftcard();
             if( barcode_redeem_val && barcode_redeem_val[0]){
                 var barcode = barcode_redeem_val[0].redeem_card;
                 $("tr#barcode_redeem").html($("<td style='padding:2px 2px 2px 38px; text-align:center;'><div class='" + barcode + "' width='150' height='50' /></td>"));
                 $("." + barcode.toString()).barcode(barcode.toString(), "code128");
                 $("td#barcode_val_redeem").html(barcode);
             }
         },
    });
	screens.OrderWidget.include({
		init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.line_dblclick_handler = function(event){
            	self.gui.show_popup('add_note_popup');
            };
        },
        set_value: function(val) {
        	var self = this;
            var order = this.pos.get_order();
            this.numpad_state = this.numpad_state;
            var mode = this.numpad_state.get('mode');
            if (order.get_selected_orderline()) {
                var ret_o_id = order.get_ret_o_id();
                if (ret_o_id) {
                    var prod_id = order.get_selected_orderline().get_product().id;
                    if (order.get_orderlines().length !== 0) {
                        if( mode === 'quantity'){
                            var ret_o_id = order.get_ret_o_id();
                            if (ret_o_id && ret_o_id.toString() != 'Missing Receipt' && val != 'remove') {
                                var self = this;
                                var pids = [];
                                new Model("pos.order.line").get_func("search_read")
                                                    ([['order_id', '=', ret_o_id],['product_id', '=', prod_id],['return_qty', '>', 0]], 
                                                    ['return_qty', 'id']).pipe(
                                    function(result) {
                                        if (result && result.length > 0) {
                                            if (result[0].return_qty > 0) {
                                                var add_prod = true;
                                                _.each(order.get_orderlines(),function(item) {
                                                    if (prod_id == item.get_product().id && 
                                                        result[0].return_qty < parseInt(val)) {
                                                    	alert(_t("Can not return more products !"));
                                                        add_prod = false;
                                                    }
                                                });
                                            }
                                            if (add_prod) {
                                                if (val != 'remove') {
	                                                order.get_selected_orderline().set_quantity(parseInt(val) * -1);
	                                            } else {
	                                                order.get_selected_orderline().set_quantity(val)
	                                            }
                                            }
                                        }
                                    }
                                );
                            } else {
                                order.get_selected_orderline().set_quantity(val);
                            }
                        }else if( mode === 'discount'){
                            order.get_selected_orderline().set_discount(val);
                            var disc_amount = order.get_selected_orderline().price * val / 100;
    						disc_amount = round_di(disc_amount,3);
    						order.get_selected_orderline().set_item_discount_amount(disc_amount * order.get_selected_orderline().quantity);
                        }else if( mode === 'price'){
                        	if(order.get_selected_orderline().get_discount_amount_printing()){
         	                	if(self.pos.config.discount_print_receipt == "public_price"){
         	                		order.get_selected_orderline().set_discount_amount_printing(0);
         	                	}
                            }
         	                if(order.get_selected_orderline().get_discount_amount_storing()){
         	                	if(self.pos.config.store_discount_based_on == "public_price"){
	                        		order.get_selected_orderline().set_discount_amount_storing(0);
	                        	}
         	                }
                            order.get_selected_orderline().set_unit_price(val);
                            order.get_selected_orderline().set_manual_price(true);
                        }
                    } else {
                        this.pos.get('selectedOrder').destroy();
                    }
                } else {
                	 var mode = this.numpad_state.get('mode');
                	 if(self.pos.config.use_discount_rules){
	                     if( mode === 'quantity'){
	                    	if(!order.get_selected_orderline().get_delivery_charges_flag()){
	                    	    if (self._check_qty_stock(mode, val)){
	                                order.get_selected_orderline().set_quantity(val);
	                                self.apply_pricelist(val);
	                            }
	                    	}
	                     }else if( mode === 'discount'){
	                    	if(self.pos.get_cashier().can_give_discount){
	                    		if(self.pos.get_cashier().user_discount > 0){
	                    			if(val <= self.pos.get_cashier().user_discount){
	                        			order.get_selected_orderline().set_discount(val);
	                        			var disc_amount = order.get_selected_orderline().price * val / 100;
	            						disc_amount = round_di(disc_amount,3);
	            						order.get_selected_orderline().set_item_discount_amount(disc_amount * order.get_selected_orderline().quantity);
	                        		}else{
	                        			self.gui.show_popup('scan_barcode_for_discount',{val:val});
	                        		}
	                    		}else{
	                    			order.get_selected_orderline().set_discount(val);
	                    		}
	                    	}else{
	                    		alert(_t("You are not authorised to give discount"));
	                    	}
	                     }else if( mode === 'price'){
	                        if(order.get_selected_orderline().get_discount_amount()){
                                order.get_selected_orderline().set_discount_amount(0);
                            }
	                    	if(self.pos.get_cashier().can_change_price){
	                    		order.get_selected_orderline().set_unit_price(val);
	                    		order.get_selected_orderline().set_manual_price(true);
	                    	}else{
	                    		alert(_t("You are not authorised to change price"));
	                    	}
	                     }
                	 }else{
                		var order = this.pos.get_order();
             	    	if (order.get_selected_orderline()) {
             	            var mode = this.numpad_state.get('mode');
             	            if( mode === 'quantity'){
             	            	if(!order.get_selected_orderline().get_delivery_charges_flag()){
             	            		if (self._check_qty_stock(mode, val)){
	                                    order.get_selected_orderline().set_quantity(val);
	                                    self.apply_pricelist(val);
	                                }
             	            	}
             	            }else if( mode === 'discount'){
             	            	if(!order.get_selected_orderline().get_delivery_charges_flag()){
             	            		order.get_selected_orderline().set_discount(val);
             	            		var disc_amount = order.get_selected_orderline().price * val / 100;
            						disc_amount = round_di(disc_amount,3);
            						order.get_selected_orderline().set_item_discount_amount(disc_amount * order.get_selected_orderline().quantity);
             	            	}
             	            }else if( mode === 'price'){
             	                if(order.get_selected_orderline().get_discount_amount()){
                                    order.get_selected_orderline().set_discount_amount(0);
                                }
             	                order.get_selected_orderline().set_unit_price(val);
             	                order.get_selected_orderline().set_manual_price(true);
             	            }
             	    	}
                	 }
                }
            }
            var selected_line = order.get_selected_orderline();
            if (selected_line && selected_line.get_line_for_gift_receipt()) {
                order.set_gift_receipt_mode(true);
                $('.gift_receipt_btn').addClass('highlight');
            } else if(!selected_line || !selected_line.get_line_for_gift_receipt()){
                order.set_gift_receipt_mode(false);
                $('.gift_receipt_btn').removeClass('highlight');
            }
        },
        apply_pricelist: function(val){
            var self = this;
            var order = this.pos.get_order();
            var select_orderline = order.get_selected_orderline();
            var pricelist_id = parseInt($('#price_list').val()) || order.get_pricelist();
            if (pricelist_id && order.get_selected_orderline() && (val != 'remove') && !order.get_giftcard()) {
                var qty = order.get_selected_orderline().get_quantity();
                var p_id = order.get_selected_orderline().get_product().id;
                if (! val) {
                    val = 1;
                }
                new Model("product.pricelist").get_func('price_get')([pricelist_id], p_id, qty).pipe(
                function(res){
                    if (res[pricelist_id]) {
                        var pricelist_value = parseFloat(res[pricelist_id].toFixed(3));
                        if (pricelist_value) {
                            var old_price = select_orderline.get_product().price;
                            select_orderline.set_unit_price(pricelist_value);
                            select_orderline.set_discount_amount(old_price - select_orderline.get_unit_price());
                            select_orderline.set_is_pricelist_apply(true);
                        }
                    }
                });
            }
        },
        _check_qty_stock: function(mode, val){
             var self = this;
             var order = self.pos.get_order();
             var orderline = order.get_selected_orderline();
             if (order.get_selected_orderline()) {
                var mode = this.numpad_state.get('mode');
                if( mode === 'quantity' && orderline.product.type != "service"){
                	var order_line_qnty = order.cart_product_qnty(orderline.product.id);
                	if(val != 'remove' || val != ''){
	                	var total_quantity = parseInt(order_line_qnty) + parseInt(val);
	                	var product = self.pos.db.get_product_by_id(orderline.product.id);
	                	if(self.pos.config.restrict_order){
				        	if(self.pos.config.prod_qty_limit){
				        		var product_qty_available = product.qty_available - total_quantity
				        		var remain = product.qty_available-self.pos.config.prod_qty_limit
				        		if(total_quantity > remain){
				        			if(self.pos.config.custom_msg){
				        				alert(self.pos.config.custom_msg);
				        				this.numpad_state.reset();
					        		} else{
					        			alert("Product Out of Stock");
					        			this.numpad_state.reset();
					        		}
			        				return false
					        	}
				        	}
				        	if(total_quantity > product.qty_available && !self.pos.config.prod_qty_limit){
				        		if(self.pos.config.custom_msg){
				        			alert(self.pos.config.custom_msg);
				        			this.numpad_state.reset();
				        		} else{
				        			alert("Product Out of Stock");
				        			this.numpad_state.reset();
				        		}
			        			return false
				        	}
		        		}
		        		return true
                	}
                }
                return true;
            }
        },
        click_line: function(orderline, event) {
	    	this._super(orderline, event);
	    	var self = this;
	    	var order = self.pos.get_order();
	    	var lines = order.get_orderlines();
	    	var selected_orderline = order.get_selected_orderline() || false;
	    	if(selected_orderline && selected_orderline.get_delivery_charges_flag()){
	    		$('#delivery_mode').prop('disabled',true);
	    	}else{
	    		if(selected_orderline && selected_orderline.get_deliver_info()){
		    		$('#delivery_mode').addClass('deliver_on');
		    	}else{
		    		$('#delivery_mode').removeClass('deliver_on');
		    	}
	    	}
	    	if(selected_orderline && selected_orderline.get_line_for_gift_receipt()){
                $('#gift_receipt').addClass('gift_mode_on');
            } else {
                $('#gift_receipt').removeClass('gift_mode_on');
            }
            order.set_gift_receipt_mode(selected_orderline.get_line_for_gift_receipt());
	    },
	    render_orderline: function(orderline){
    		var el_node = this._super(orderline);
    		var self = this;
    		if (this.pos.config.enable_product_note) {
    			el_node.addEventListener('dblclick',this.line_dblclick_handler);
            }
            var oe_del = el_node.querySelector('.oe_del');
            if(oe_del){
            	oe_del.addEventListener('click', (function() {
            		if(!confirm(_t("Are you sure you want to unassign lot/serial number(s) ?"))){
        	    		return
        	    	}
            		var pack_lot_lines = orderline.pack_lot_lines;
            		var len = pack_lot_lines.length;
            		var cids = [];
            		for(var i=0; i<len; i++){
            			var lot_line = pack_lot_lines.models[i];
            			cids.push(lot_line.cid);
            		}
            		for(var j in cids){
            			var lot_model = pack_lot_lines.get({cid: cids[j]});
            			lot_model.remove();
            		}
            		self.renderElement();
            	}.bind(this)));
            }
            return el_node
    	},
    });
//	var Bags = screens.ActionButtonWidget.extend({
//	    template : 'Bags',
//	    button_click : function() {
//	    	var self = this;
//	    	self.gui.show_popup('bags_popup');
//	    },
//	});
//	screens.define_action_button({
//	    'name' : 'Bags',
//	    'widget' : Bags,
//	    'condition': function(){
//            return this.pos.config.enable_bag_charges;
//        },
//	});
	var BagSelectionPopupWidget = PopupWidget.extend({
	    template: 'BagSelectionPopupWidget',
	    show: function(options){
	        options = options || {};
	        this._super(options);
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var order    = this.pos.get_order();

	    	if($('#chk_bag_charges').prop('checked')){
		    	$('.ac_selected_prod').each(function(index,el){
	    			if($(this).prop('checked')){
	    				var input_qty = $(".product_qty"+el.name).val();
	    				var product = self.pos.db.get_product_by_id(el.name);
	    				if(input_qty > 0){
		    				if(product){
		    					var line = new models.Orderline({}, {pos: self.pos, order: order, product: product});
		                        line.set_quantity(input_qty);
		                        line.set_unit_price(product.price);
		                        line.set_bag_color(true);
		                        line.set_is_bag(true);
		                        order.add_orderline(line);
		    				}
	    				}
	    			}
	    		});
	    	}else{
	    		$('.ac_selected_prod').each(function(index,el){
	    			if($(this).prop('checked')){
	    				var input_qty = $(".product_qty"+el.name).val();
	    				var product = self.pos.db.get_product_by_id(el.name);
	    				if(input_qty > 0){
		    				if(product){
		    					var line = new models.Orderline({}, {pos: self.pos, order: order, product: product});
		                        line.set_quantity(input_qty);
		                        line.set_unit_price(0);
		                        line.set_bag_color(true);
		                        line.set_is_bag(true);
		                        order.add_orderline(line);
		    				}
	    				}
	    			}
	    		});
	    	}
	        this.gui.close_popup();
	    },
	    renderElement: function() {
            var self = this;
            this._super();
            $('.check_box_tag .ac_selected_prod').change(function(){
            	 if(!$(this).is(':checked')){
            		 self.count_bag_total();
            		 $('.product[data-product-id="'+ $(this).attr('name') +'"]').find('#product_qty_cs').val('')
            	 }else{
            		 $('.product[data-product-id="'+ $(this).attr('name') +'"]').find('#product_qty_cs').val(1)
            		 self.count_bag_total();
            	 }
            });
            $('.product-name input#product_qty_cs').keypress(function(e){
            	if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57)) {
                	return false;
            	}
//            	if(e.which === 13){
            	$('.product-name input#product_qty_cs').change(function(){
            		if($.isNumeric($(this).val()) && parseInt($(this).val()) >= 0){
            			self.count_bag_total();
            		}else if($(this).val() == ""){
            			$(this).val(1);
            			self.count_bag_total();
            		}
            	});
//            	}
            });
    	},
    	count_bag_total: function(){
    		var self = this;
    		$('table.total .bag_value').text("");
    		var total = 0;
    		$('.ac_selected_prod').each(function(index,el){
    			if($(this).prop('checked')){
    				self.input_qty = $(".product_qty"+el.name).val();
    				var val = $(".product_price"+el.name).val().replace('price','');
    				if(self.input_qty && val){
    					total += self.input_qty*val;
    				}
    			}
    		});
    		$('table.total .bag_value').text(total);
    	},
    	get_product_image_url: function(product_id){
    		return window.location.origin + '/web/image?model=product.product&field=image_medium&id='+product_id;
    	},
	});
	gui.define_popup({name:'bags_popup', widget: BagSelectionPopupWidget});
//	var DeliveryMode = screens.ActionButtonWidget.extend({
//	    template : 'DeliveryMode',
//	    button_click : function() {
//	    	var self = this;
//	    	var order = self.pos.get_order();
//	    	var lines = order.get_orderlines();
//	    	var selected_orderline = order.get_selected_orderline();
//
//	    	if(order.get_delivery_time() && order.get_delivery_date()){
//		    	var selected_orderline = order.get_selected_orderline();
//		    	if(selected_orderline){
//			    	if(selected_orderline && !$('.delivery_mode').hasClass('deliver_on')){
//			    		if(!selected_orderline.get_delivery_charges_flag()){
//			    			selected_orderline.set_deliver_info(true);
//			    		}else{
//			    			$('.delivery_mode').removeClass('deliver_on');
//			    		}
//			    		var deliver_product_id = this.pos.config.delivery_product_id[0];
//			    		var product = this.pos.db.get_product_by_id(deliver_product_id);
//			    		if(!order.get_is_delivery()){
//			        		var line_deliver_charges = new models.Orderline({}, {pos: self.pos, order:order, product: product});
//			        		line_deliver_charges.set_quantity(1);
//			        		line_deliver_charges.set_unit_price(0);
//			        		line_deliver_charges.set_delivery_charges_color(true);
//			        		line_deliver_charges.set_delivery_charges_flag(true);
//			                order.add_orderline(line_deliver_charges);
//			                order.set_is_delivery(true);
//			    		}
//		                order.set_delivery(true);
//		                $('.delivery_mode').addClass('deliver_on');
//			    	}else if(selected_orderline && selected_orderline.get_deliver_info()){
//			    		selected_orderline.set_deliver_info(false);
//			    		order.count_to_be_deliver();
//			    		$('.delivery_mode').removeClass('deliver_on');
//			    	}else if(selected_orderline && !selected_orderline.get_deliver_info()){
//			    		if(!selected_orderline.get_delivery_charges_flag()){
//			    			selected_orderline.set_deliver_info(true);
//			    		}else{
//			    			$('.delivery_mode').removeClass('deliver_on');
//			    		}
//			    	}else{
//			    		$('.delivery_mode').removeClass('deliver_on');
//			    		selected_orderline.set_deliver_info(false);
//			    		order.count_to_be_deliver();
//			    	}
//		    	}else{
//		    		alert("Please select product to deliver.");
//		    	}
//	    	}else{
//	    		if(selected_orderline && selected_orderline.get_deliver_info()){
//	    			selected_orderline.set_deliver_info(false);
//	    			order.count_to_be_deliver();
//	    			$('.delivery_mode').removeClass('deliver_on');
//	    		}else{
//	    			alert("Please Select Date and Time to Deliver Product.");
//	    		}
//	    	}
//	    },
//	});
//	screens.define_action_button({
//	    'name' : 'DeliveryMode',
//	    'widget' : DeliveryMode,
//	    'condition': function(){
//            return this.pos.config.enable_delivery_charges;
//        },
//	});
//	var DeliveryPopup = screens.ActionButtonWidget.extend({
//	    template : 'DeliveryPopup',
//	    button_click : function() {
//	    	var self = this;
//	    	self.gui.show_popup('delivery_popup');
//	    },
//	});
//	screens.define_action_button({
//	    'name' : 'DeliveryPopup',
//	    'widget' : DeliveryPopup,
//	    'condition': function(){
//            return this.pos.config.enable_delivery_charges;
//        },
//	});
	var DeliveryPopupWidget = PopupWidget.extend({
	    template: 'DeliveryPopupWidget',
	    show: function(options){
	        options = options || {};
	        this._super(options);
	        this.from = options.from_delivery_mode || false;
	        this.renderElement();
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	var txt_date = $('#txt_date').val();
	    	var txt_time = $('#txt_time').val();
	    	if(txt_date == '' || txt_time == ''){

               if(txt_date != '' && txt_time == ''){ $('#txt_time').css('border', 'thin solid red'); }
               else if(txt_date == '' && txt_time != ''){ $('#txt_date').css('border', 'thin solid red'); }
               else if(txt_date == '' && txt_time == ''){
                    order.set_delivery_date(false);
                    order.set_delivery_time(false);
                    $('#open_calendar').css({'background-color':''});
                    $('#delivery_mode').removeClass('deliver_on');
                    this.gui.close_popup();
               }
	    	}else{
	    		order.set_delivery_date(txt_date);
	    		order.set_delivery_time(txt_time);
	    		$('#open_calendar').css({'background':'#6EC89B'});
                if(self.from){
	    		    $('#delivery_mode').click();
	    		}
	    		this.gui.close_popup();
	    	}

	    },
	    renderElement: function() {
            var self = this;
            this._super();
            var order = self.pos.get_order();
            var date = order.get_delivery_date();
            var time = order.get_delivery_time();
            if(date && time){
            	$('#txt_date').val(date);
            	$('#txt_time').val(time);
            }
            self.$(".emptybox_date").click(function(){ $('#txt_date').val('') });
            self.$(".emptybox_time").click(function(){ $('#txt_time').val('') });
	        self.$("#txt_date").datepicker({minDate: 0});
	        self.$("#txt_time").timepicker({
	        	'timeFormat': 'h:i A',
	        });
    	},
	});
	gui.define_popup({name:'delivery_popup', widget: DeliveryPopupWidget});
	screens.NumpadWidget.include({
		start: function() {
            var self = this;
            this._super(); 
            this.$(".input-button").click(function(){
                self.pos.get('selectedOrder').mirror_image_data(); 
            });
        },
		clickDeleteLastChar: function() {
			var order = this.pos.get_order();
			var lines = order.get_orderlines();
			var selected_orderline = order.get_selected_orderline() || '';
			if(selected_orderline && selected_orderline.get_delivery_charges_flag()){
				if(!selected_orderline.product.quantity == 1){
					$('#delivery_mode').removeClass('deliver_on');
					order.set_delivery(false);
					this.state.set({order: order});
					return this.state.deleteLastChar();
				}
			}else{
				$('#delivery_mode').removeClass('deliver_on');
				order.set_delivery(false);
				this.state.set({order: order});
				return this.state.deleteLastChar();
			}
		},
	});

	/* Scan Barcode POPUP */
	var ScanBarcodeForDiscount = PopupWidget.extend({
	    template: 'ScanBarcodeForDiscount',
	    show: function(options){
	    	var self = this;
			this._super();
			this.val = options.val || 0;
			this.renderElement();
			var order = self.pos.get_order();
			$('#manager_barcode').focus();
			$('#discount_value').text(this.val);
			$('div.dis_auth_confirm').prop('disabled', true);
			$('div.dis_auth_confirm').css('color','#CCC');
			order.set_barcode_for_manager(true);
	    },
	    renderElement: function() {
            var self = this;
            this._super();
			var order = self.pos.get_order();
    	},
	    click_confirm: function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	order.get_selected_orderline().set_discount(this.val);
	    	self.pos.get_order().set_barcode_for_manager(false);
	        this.gui.close_popup();
	    },
    	click_cancel: function(){
    		var self = this;
    		self.pos.get_order().set_barcode_for_manager(false);
    		this.gui.close_popup();
    	}
	});
	gui.define_popup({name:'scan_barcode_for_discount', widget: ScanBarcodeForDiscount});
	var SuperNumpadState = models.NumpadState.prototype;
	models.NumpadState = models.NumpadState.extend({
		defaults: {
	        buffer: "0",
	        mode: "quantity",
	        order:undefined
	    },
	    deleteLastChar: function() {
	        if(this.get('buffer') === ""){
	            if(this.get('mode') === 'quantity'){
	            	var order = this.get('order');
	    			var lines = order.get_orderlines();
	    			var count = 0;
	    	    	var selected_orderline = order.get_selected_orderline() || false;
	    	    	if(selected_orderline && selected_orderline.get_deliver_info()){
		    	    	for(var i=0;i<lines.length;i++){
		    				if(lines[i].get_deliver_info()){
		    					count = count + 1;
		    				}
		    			}
		    			if(count == 1 && !selected_orderline.product.is_packaging){
		    				for(var j=0; j<lines.length;j++){
		    					if(lines[j].get_delivery_charges_flag()){
		    						order.remove_orderline(lines[j]);
		    						order.set_is_delivery(false);
		    						break;	
		    					}
		    				}
		    			}
	    	    	}
	                this.trigger('set_value','remove');
	            }else{
	                this.trigger('set_value',this.get('buffer'));
	            }
	        }else{
	            var newBuffer = this.get('buffer').slice(0,-1) || "";
	            this.set({ buffer: newBuffer });
	            this.trigger('set_value',this.get('buffer'));
	        }
	    },
	});
	var ComformDeliveryPopupWidget = PopupWidget.extend({
	    template: 'ComformDeliveryPopupWidget',
	    show: function(options){
	        options = options || {};
	        this._super(options);
	        this.renderElement();
	    },
	    click_confirm: function(){
	        var order = this.pos.get_order();
	        var lines = order.get_orderlines();
	        var list = []
	        for(var i=0;i<lines.length;i++){
	        	lines[i].set_deliver_info(false);
	        	if(lines[i].get_delivery_charges_flag()){
	        		list.push(lines[i]);
	        	}
	        }
	        for(var j=0;j<list.length;j++){
	        	order.remove_orderline(list[j]);
				order.set_is_delivery(false);
	        }
	        $('#delivery_mode').removeClass('deliver_on');
	        this.gui.close_popup();
	        this.gui.show_screen('payment');
	    },
	    renderElement: function() {
            var self = this;
            this._super();
            
	    	this.$('.cancel').click(function(){
	    		self.gui.show_screen('products');
	        });
    	},
	});
	gui.define_popup({name:'conf_delivery', widget: ComformDeliveryPopupWidget});

 	/* REDEEMPOINT POPUP */
    var RedeemPointPopup = PopupWidget.extend({
        template: 'RedeemPointPopup',
        show: function(options){
            var self = this;
            this._super();
            window.document.body.removeEventListener('keypress',self.pos.chrome.screens.payment.keyboard_handler);
            window.document.body.removeEventListener('keydown',self.pos.chrome.screens.payment.keyboard_keydown_handler);
            var currentOrder = self.pos.get_order();
            this.renderElement();
            var client_id = currentOrder.get_client();
            var due_total = currentOrder.get_total_with_tax();
            this.to_amounts = 0;
            this.points = 0;
            this.remain_amt = 0;
            var result = options.result || false;

            if (result && result[0]) {
               self.points = Number(result[0].single_point);
               self.to_amounts = Number(result[0].per_point_amount);
               self.remain_amt = result[0].remaining_points;
               var cpn_amt = currentOrder.get_total_redeem_point() ? (self.remain_amt - currentOrder.get_total_redeem_point()) * (self.to_amounts / self.points) : (result[0].remaining_points) * (self.to_amounts / self.points)
               var remain_amount = currentOrder.get_total_redeem_point() ?  (Math.abs(self.remain_amt - currentOrder.get_total_redeem_point()).toFixed(3)) + ' [' + self.format_currency(cpn_amt).toString() +']' : result[0].remaining_points.toFixed(3) + ' [' + self.format_currency(cpn_amt).toString() +']';
               $('.remain_redeem_input').text(remain_amount);
            }
            $('#redeem_barcode_amt').focus();
            currentOrder.set_popup_open(true);
        },
        hide: function(){
     	   var self = this;
     	   self._super();
     	   var currentOrder = self.pos.get_order();
     	   currentOrder.set_popup_open(false);
        },
        click_confirm: function(){
            var self = this;
            var currentOrder = self.pos.get_order();
            var use_redeem_point = Number($("input#redeem_barcode_amt").val());
            if(use_redeem_point){
            	var remaining_point = currentOrder.get_total_redeem_point() ? (self.remain_amt).toFixed(3) - currentOrder.get_total_redeem_point() : (self.remain_amt).toFixed(3) ;
                var remaining_amt = remaining_point * (self.to_amounts/self.points);
                if (use_redeem_point > remaining_point) {
                    alert (_t('You can not use more than available points.'));
                    window.document.body.addEventListener('keypress',self.pos.chrome.screens.payment.keyboard_handler);
                    window.document.body.addEventListener('keydown',self.pos.chrome.screens.payment.keyboard_keydown_handler);
                    return;
                } else{
                	var rate = self.to_amounts / self.points;
                	var converted_redeem_amt = use_redeem_point * rate;
                	for ( var i = 0; i < self.pos.cashregisters.length; i++ ) {
                		if ( self.pos.cashregisters[i].journal.id === self.pos.config.loyalty_journal[0] ){
                			currentOrder.set_redeem_amt(converted_redeem_amt);
	                		currentOrder.set_order_redeem_point(use_redeem_point);
	                		var total_redeem_point = currentOrder.get_total_redeem_point() ? currentOrder.get_total_redeem_point()+use_redeem_point : use_redeem_point;
	                		var total_redeem_amt = currentOrder.get_total_redeem_amt() ? currentOrder.get_total_redeem_amt()+converted_redeem_amt : converted_redeem_amt;
	                		currentOrder.set_total_redeem_point(total_redeem_point);
	                		currentOrder.set_total_redeem_amt(total_redeem_amt);
	                		self.pos.chrome.screens.payment.click_paymentmethods(self.pos.cashregisters[i].journal_id[0])
                		}
                	}
                }
        	}
            window.document.body.addEventListener('keypress',self.pos.chrome.screens.payment.keyboard_handler);
            window.document.body.addEventListener('keydown',self.pos.chrome.screens.payment.keyboard_keydown_handler);
            this.gui.close_popup();
        },
       click_cancel: function(){
            var self = this;
            window.document.body.addEventListener('keypress',self.pos.chrome.screens.payment.keyboard_handler);
            window.document.body.addEventListener('keydown',self.pos.chrome.screens.payment.keyboard_keydown_handler);
            this.gui.close_popup();
        },
    });
    gui.define_popup({name:'redeem_point_popup', widget: RedeemPointPopup});

//    DEBIT
    screens.ClientListScreenWidget.include({
    	init: function(parent, options){
			var self = this;
			this._super(parent, options);
			$.ajax({
	            type: "GET",
	            url: '/web/dataset/load_customers',
	            data: {
                    model: 'res.partner',
                    fields: JSON.stringify(self.pos.partner_fields),
                    domain: JSON.stringify(self.pos.partner_domain),
                    context: JSON.stringify(self.pos.partner_context),
                },
	            success: function(res) {
	                self.pos.partners = JSON.parse(res);
	                self.pos.partners_load = true;
	                self.pos.db.add_partners(JSON.parse(res));
	                self.render_list(self.pos.db.get_partners_sorted(1000));
	            },
	            error: function() {
	                console.log('Partner Qa-run failed.');
	            },
	        });
		},
    	toggle_save_button: function(){
            this._super();
            var $button = this.$('.button.set-customer-pay-full-debt');
            if (this.editing_client) {
                $button.addClass('oe_hidden');
                return;
            } else if (this.new_client){
                if (this.new_client.debt > 0){
                    $button.toggleClass('oe_hidden',!this.has_client_changed());
                }else{
                	$button.addClass('oe_hidden');
                }
            }
        },
        show: function(){
            this._super();
            var self = this;
            var search_timeout = null;
            this.$('.searchbox input').off('keypress').on('keypress',function(event){
                clearTimeout(search_timeout);
                var query = this.value;
                var partner_name_list = self.pos.db.get_partners_name();
                $(this).autocomplete({
                    source:partner_name_list,
                    select: function(event, ui) {
                        if(ui && event.which === 13){
                            self.perform_search(ui.item.value, event.which === 13);
                        }
                    },
                });
                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });
            this.$('.button.set-customer-pay-full-debt').click(function(){
                self.save_changes();
                self.gui.back();
                if (self.new_client && self.new_client.debt <= 0) {
                    self.gui.show_popup('error',{
                    'message':_t('Error: No Debt'),
                    'comment':_t("The selected customer has no debt."),
                    });
                    return;
                }
                // if the order is empty, add a dummy product with price = 0
                var order = self.pos.get_order();
                var dummy_product;
                if (order) {
                    var lastorderline = order.get_last_orderline();
                    if (lastorderline == null &&
                            self.pos.config.debt_dummy_product_id){
                        dummy_product = self.pos.db.get_product_by_id(
                            self.pos.config.debt_dummy_product_id[0]);
                        order.add_product(dummy_product, {'price': 0});
                        }
                }

                // select debt journal
                var debtjournal = false;
                _.each(self.pos.cashregisters, function(cashregister) {
                    if (cashregister.journal.debt) {
                        debtjournal = cashregister;
                    }
                });

                // add payment line with amount = debt *-1
                var paymentLines = order.get_paymentlines();
                if (paymentLines.length) {
                    /* Delete existing debt line
                    Usefull for the scenario where a customer comes to
                    pay his debt and the user clicks on the "Debt journal"
                    which opens the partner list and then selects partner
                    and clicks on "Select Customer and Pay Full Debt" */
                    _.each(paymentLines.models, function(paymentLine) {
                        if (paymentLine.cashregister.journal.debt){
                            paymentLine.destroy();
                        }
                    });
                }
                var newPaymentline = new models.Paymentline({},{order: order, cashregister:debtjournal, pos: self.pos});
                newPaymentline.set_amount(order.get_client().debt * -1);
                self.gui.show_screen('payment');
                order.paymentlines.add(newPaymentline);
                order.select_paymentline(newPaymentline);
                self.pos.chrome.screens.payment.reset_input();
                self.pos.chrome.screens.payment.render_paymentlines();
				$("#pay_register").show();
                $(".gotopay").hide();
                $('#more_features').hide();
            });
        },
        save_changes: function(){
             this._super();
             if (this.pos.config.enable_ereceipt && this.has_client_changed()) {
                var prefer_ereceipt = this.new_client ? this.new_client.prefer_ereceipt : false;
                var customer_email = this.new_client ? this.new_client.email : false;
                if (prefer_ereceipt) {
                    $('#is_ereciept')[0].checked = true;
                    $('#email_id').show();
                    if(order.get_client()){
                    	$('.update_email').show();
                    }
                    if(customer_email) {
                        $('#email_id').val(customer_email);
                    };
                } else {
                    $('#is_ereciept')[0].checked = false;
                    $('#email_id').hide();
                    $('.update_email').hide();
                    $('#email_id').val('');
                }
            }
        },
        edit_client_details: function(partner){
	        var self = this;
	        this._super(partner);
	        var pricelist_list = this.pos.prod_pricelists;
	        var order = self.pos.get_order();
	        var new_options_cust = [];
	        new_options_cust.push('<option value="">Select Pricelist</option>\n');
	        if(pricelist_list.length > 0){
	            for(var i = 0, len = pricelist_list.length; i < len; i++){
	                new_options_cust.push('<option value="' + pricelist_list[i].id + '">' + pricelist_list[i].display_name + '</option>\n');
	            }
	            $('#cust_detail_price_list').html(new_options_cust);
	            $('#cust_detail_price_list').val(partner.property_product_pricelist[0]);
	        }
	    },
	    display_client_details: function(visibility,partner,clickpos){
	        var self = this;
	        self._super(visibility,partner,clickpos);
	        if(partner && partner.property_product_pricelist){
	            $('#readonly_pricelist').text(partner.property_product_pricelist[1]);
	        }
	        if (visibility === 'edit') {
            	self.pricelist_list = this.pos.prod_pricelists;
                var order = self.pos.get_order();
                var new_options_cust = [];
                new_options_cust.push('<option value="">Select Pricelist</option>\n');
                if(self.pricelist_list.length > 0){
                    for(var i = 0, len = self.pricelist_list.length; i < len; i++){
                        new_options_cust.push('<option value="' + self.pricelist_list[i].id + '">' + self.pricelist_list[i].display_name + '</option>\n');
                    }
                    $('#cust_detail_price_list').html(new_options_cust);
                    if(partner && partner.property_product_pricelist && partner.property_product_pricelist[0]){
                    	$('#cust_detail_price_list').val(partner.property_product_pricelist[0]);
                    }
                }
            }
	    },
    });

//    product variant code
    screens.ProductListWidget.include({
//	    init: function(parent, options) {
//	        this._super(parent,options);
//	        var self = this;
//	        // OVERWRITE 'click_product_handler' function to do
//	        // a different behaviour if template with one or many variants
//	        // are selected.
//	        this.click_product_handler = function(event){
//	            var product = self.pos.db.get_product_by_id(this.dataset['productId']);
//	            if(self.pos.config.enable_product_variant){
//		            if (product.product_variant_count == 1) {
//		                // Normal behaviour, The template has only one variant
//		                options.click_product_action(product);
//		            } else{
//		                // Display for selection all the variants of a template
//		            	self.gui.show_screen('select_variant_screen',{product_tmpl_id:product.product_tmpl_id});
//		//                     self.pos.pos_widget.screen_selector.show_popup('select-variant-popup', product.product_tmpl_id);
//		            }
//	            }else{
//	            	options.click_product_action(product);
//	            }
//	        };
//	    },
	    set_product_list: function(product_list){
	    	var self = this;
	    	var new_product_list = [];

	    	var delivery_product_id = self.pos.config.delivery_product_id[0] || false;
	    	var payment_product_id = self.pos.config.payment_product_id[0] || false;
	    	var wallet_product_id = self.pos.config.wallet_product[0] || false;
	    	var debt_dummy_product_id = self.pos.config.debt_dummy_product_id[0] || false;
	    	var gift_card_id = self.pos.config.gift_card_product_id[0] || false;

	    	product_list.map(function(product){
	    		if(
	    			product.id != delivery_product_id && 
	    			product.id != payment_product_id && 
	    			product.id != wallet_product_id &&
	    			product.id != debt_dummy_product_id &&
	    			product.id != gift_card_id &&
	    			!product.is_packaging){
	    			new_product_list.push(product);
	    		}
	    	});

	    	this.product_list = new_product_list;
	        this.renderElement();
	        new_product_list = [];
//            for (var i = product_list.length - 1; i >= 0; i--){
//                if (!product_list[i].is_primary_variant){
//                    product_list.splice(i, 1);
//                }
//            }
//            this._super(product_list);
        },
	    render_product: function(product){
	        self = this;
	        if (product.product_variant_count == 1){
	            // Normal Display
	            return this._super(product);
	        }
	        else{
	            var cached = this.product_cache.get_node(product.id);
	            if(!cached){
	                var image_url = this.get_product_image_url(product);
	                var product_html = QWeb.render('Product',{ 
	                        widget:  this, 
	                        product: product, 
	                        image_url: this.get_product_image_url(product),
	                    });
	                var product_node = document.createElement('div');
	                product_node.innerHTML = product_html;
	                product_node = product_node.childNodes[1];
	                this.product_cache.cache_node(product.id,product_node);
	                return product_node;
	            }
	            return cached;
	        }
	    },
	    init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.model = options.model;
            this.productwidgets = [];
            this.weight = options.weight || 0;
            this.show_scale = options.show_scale || false;
            this.next_screen = options.next_screen || false;

            this.click_product_handler = function(e){
                var product = self.pos.db.get_product_by_id(this.dataset.productId);
                if($(e.target).attr('class') === "product-qty-low" || $(e.target).attr('class') === "product-qty"){
                	var prod = product;
    	        	var prod_info = [];
                    var total_qty = 0;
                    var total_qty = 0;
                    new Model('stock.warehouse').call('disp_prod_stock',[prod.id,self.pos.shop.id]).then(function(result){
                    if(result){
                    	prod_info = result[0];
                        total_qty = result[1];
                        self.gui.show_popup('product_qty_popup',{prod_info_data:prod_info,total_qty: total_qty,product: product});
                    }
    		    	}).fail(function (error, event){
    			        if(error.code === -32098) {
    			        	alert("Server Down...");
    			        	event.preventDefault();
    		           }
    		    	});
//                    self.gui.show_popup('show_image_popup',{'productnm':product.display_name,'product_id':this.dataset.productId});
                }else{
                    options.click_product_action(product);
                }
            };

            this.product_list = options.product_list || [];
            this.product_cache = new screens.DomCache();
        },
	});
    /* ********************************************************
    Overload: point_of_sale.PosWidget

    - Add a new PopUp 'SelectVariantPopupWidget';
    *********************************************************** */
//        module.PosWidget = module.PosWidget.extend({
    //
//            /* Overload Section */
//            build_widgets: function(){
//                this._super();
//                this.select_variant_popup = new module.SelectVariantPopupWidget(this, {});
//                this.select_variant_popup.appendTo($(this.$el));
//                this.screen_selector.popup_set['select-variant-popup'] = this.select_variant_popup;
//                // Hide the popup because all pop up are displayed at the
//                // beginning by default
//                this.select_variant_popup.hide();
//            },
//        });

    /* ********************************************************
    Define : pos_product_template.SelectVariantPopupWidget
        
    - This widget that display a pop up to select a variant of a Template;
    *********************************************************** */
//    var SelectVariantScreen = screens.ScreenWidget.extend({
//        template:'SelectVariantScreen',
//        init: function(parent, options){
//            this._super(parent, options);
//        },
//        start: function(){
//        	this._super();
//            var self = this;
//            // Define Variant Widget
//            this.variant_list_widget = new VariantListWidget(this,{});
//            this.variant_list_widget.replace(this.$('.placeholder-VariantListWidget'));
//
//            // Define Attribute Widget
//            this.attribute_list_widget = new AttributeListWidget(this,{});
//            this.attribute_list_widget.replace(this.$('.placeholder-AttributeListWidget'));
//
//            // Add behaviour on Cancel Button
//            this.$('#variant-popup-cancel').off('click').click(function(){
//            	self.gui.back();
//            });
//        },
//
//        show: function(options){
//        	this._super();
//            var self = this;
//            var product_tmpl_id = self.gui.get_current_screen_param('product_tmpl_id');
//            var template = this.pos.db.template_by_id[product_tmpl_id];
//            // Display Name of Template
//            this.$('#variant-title-name').html(template.name);
//
//            // Render Variants
//            var variant_ids  = this.pos.db.template_by_id[product_tmpl_id].product_variant_ids;
//            var variant_list = [];
//            for (var i = 0, len = variant_ids.length; i < len; i++) {
//                variant_list.push(this.pos.db.get_product_by_id(variant_ids[i]));
//            }
//            this.variant_list_widget.filters = {}
//            this.variant_list_widget.set_variant_list(variant_list);
//
//            // Render Attributes
//            var attribute_ids  = this.pos.db.attribute_by_template_id(template.id);
//            var attribute_list = [];
//            for (var i = 0, len = attribute_ids.length; i < len; i++) {
//                attribute_list.push(this.pos.db.get_product_attribute_by_id(attribute_ids[i]));
//            }
//            this.attribute_list_widget.set_attribute_list(attribute_list, template);
//            this._super();
//        },
//    });
//	gui.define_screen({name:'select_variant_screen', widget: SelectVariantScreen});
//	/* ********************************************************
//	Define: pos_product_template.VariantListWidget
//
//	- This widget will display a list of Variants;
//	- This widget has some part of code that come from point_of_sale.ProductListWidget;
//	*********************************************************** */
//    var VariantListWidget = PosBaseWidget.extend({
//        template:'VariantListWidget',
//
//        init: function(parent, options) {
//            var self = this;
//            this._super(parent, options);
//            this.variant_list = [];
//            this.filter_variant_list = [];
//            this.filters = {};
//            this.click_variant_handler = function(event){
//                var variant = self.pos.db.get_product_by_id(this.dataset['variantId']);
//                if(variant.to_weight && self.pos.config.iface_electronic_scale){
//                    self.__parentedParent.hide();
//                    self.pos_widget.screen_selector.set_current_screen('scale',{product: variant});
//                }else{
//                    self.pos.get_order().add_product(variant);
//                    self.gui.show_screen('products');
//                }
//            };
//        },
//
//        replace: function($target){
//            this.renderElement();
//            var target = $target[0];
//            target.parentNode.replaceChild(this.el,target);
//        },
//
//        set_filter: function(attribute_id, value_id){
//            this.filters[attribute_id] = value_id;
//            this.filter_variant();
//        },
//
//        reset_filter: function(attribute_id){
//            if (attribute_id in this.filters){
//                delete this.filters[attribute_id];
//            }
//            this.filter_variant();
//        },
//
//        filter_variant: function(){
//            var value_list = []
//            for (var item in this.filters){
//                value_list.push(parseInt(this.filters[item]));
//            }
//            this.filter_variant_list = [];
//            for (var index in this.variant_list){
//                var variant = this.variant_list[index];
//                var found = true;
//                for (var i = 0; i < value_list.length; i++){
//                    found = found && (variant.attribute_value_ids.indexOf(value_list[i]) != -1);
//                }
//                if (found){
//                    this.filter_variant_list.push(variant);
//                }
//            }
//            this.renderElement();
//        },
//
//        set_variant_list: function(variant_list){
//            this.variant_list = variant_list;
//            this.filter_variant_list = variant_list;
//            this.renderElement();
//        },
//
//        render_variant: function(variant){
//        	var image_url = this.get_product_image_url(variant);
//            var variant_html = QWeb.render('VariantWidget', {
//                    widget:  this,
//                    variant: variant,
//                    image_url: image_url
//                });
//            var variant_node = document.createElement('div');
//            variant_node.innerHTML = variant_html;
//            variant_node = variant_node.childNodes[1];
//            return variant_node;
//        },
//
//        get_product_image_url: function(product){
//            return window.location.origin + '/web/image?model=product.product&field=image_medium&id='+product.id;
//        },
//
//        renderElement: function() {
//            var self = this;
//            var el_html  = openerp.qweb.render(this.template, {widget: this});
//            var el_node = document.createElement('div');
//            el_node.innerHTML = el_html;
//            el_node = el_node.childNodes[1];
//            if(this.el && this.el.parentNode){
//                this.el.parentNode.replaceChild(el_node,this.el);
//            }
//            this.el = el_node;
//            var list_container = el_node.querySelector('.variant-list');
//            for(var i = 0, len = this.filter_variant_list.length; i < len; i++){
//                var variant_node = this.render_variant(this.filter_variant_list[i]);
//                variant_node.addEventListener('click',this.click_variant_handler);
//                list_container.appendChild(variant_node);
//            }
//        },
//    });
//    /* ********************************************************
//    Define: pos_product_template.AttributeListWidget
//
//        - This widget will display a list of Attribute;
//    *********************************************************** */
//    var AttributeListWidget = PosBaseWidget.extend({
//        template:'AttributeListWidget',
//
//        init: function(parent, options) {
//            var self = this;
//            this.attribute_list = [];
//            this.product_template = null;
//            this.click_set_attribute_handler = function(event){
//                /*TODO: Refactor this function with elegant DOM manipulation */
//                // remove selected item
//                var parent = this.parentElement.parentElement.parentElement;
//                parent.children[0].classList.remove('selected');
//                for (var i = 0 ; i < parent.children[1].children[0].children.length; i ++){
//                    var elem = parent.children[1].children[0].children[i];
//                    elem.children[0].classList.remove('selected');
//                }
//                // add selected item
//                this.children[0].classList.add('selected');
//                self.__parentedParent.variant_list_widget.set_filter(this.dataset['attributeId'], this.dataset['attributeValueId']);
//            };
//            this.click_reset_attribute_handler = function(event){
//                /*TODO: Refactor this function with elegant DOM manipulation */
//                // remove selected item
//                var parent = this.parentElement;
//                parent.children[0].classList.remove('selected');
//                for (var i = 0 ; i < parent.children[1].children[0].children.length; i ++){
//                    var elem = parent.children[1].children[0].children[i];
//                    elem.children[0].classList.remove('selected');
//                }
//                // add selected item
//                this.classList.add('selected');
//                self.__parentedParent.variant_list_widget.reset_filter(this.dataset['attributeId']);
//            };
//            this._super(parent, options);
//        },
//
//        replace: function($target){
//            this.renderElement();
//            var target = $target[0];
//            target.parentNode.replaceChild(this.el,target);
//        },
//
//        set_attribute_list: function(attribute_list, product_template){
//            this.attribute_list = attribute_list;
//            this.product_template = product_template;
//            this.renderElement();
//        },
//
//        render_attribute: function(attribute){
//            var attribute_html = QWeb.render('AttributeWidget',{
//                    widget:  this,
//                    attribute: attribute,
//                });
//            var attribute_node = document.createElement('div');
//            attribute_node.innerHTML = attribute_html;
//            attribute_node = attribute_node.childNodes[1];
//            
//            var list_container = attribute_node.querySelector('.value-list');
//            for(var i = 0, len = attribute.value_ids.length; i < len; i++){
//                var value = this.pos.db.get_product_attribute_value_by_id(attribute.value_ids[i]);
//                var product_list = this.pos.db.get_product_by_ids(this.product_template.product_variant_ids);
//                var subproduct_list = this.pos.db.get_product_by_value_and_products(value.id, product_list);
//                var variant_qty = subproduct_list.length;
//                // Hide product attribute value if there is no product associated to it
//                if (variant_qty != 0) {
//                    var value_node = this.render_value(value, variant_qty);
//                    value_node.addEventListener('click', this.click_set_attribute_handler);
//                    list_container.appendChild(value_node);
//                }
//            };
//            return attribute_node;
//        },
//
//        render_value: function(value, variant_qty){
//            var value_html = QWeb.render('AttributeValueWidget',{
//                    widget:  this,
//                    value: value,
//                    variant_qty: variant_qty,
//                });
//            var value_node = document.createElement('div');
//            value_node.innerHTML = value_html;
//            value_node = value_node.childNodes[1];
//            return value_node;
//        },
//
//
//        renderElement: function() {
//            var self = this;
//            var el_html  = openerp.qweb.render(this.template, {widget: this});
//            var el_node = document.createElement('div');
//            el_node.innerHTML = el_html;
//            el_node = el_node.childNodes[1];
//            if(this.el && this.el.parentNode){
//                this.el.parentNode.replaceChild(el_node,this.el);
//            }
//            this.el = el_node;
//
//            var list_container = el_node.querySelector('.attribute-list');
//            for(var i = 0, len = this.attribute_list.length; i < len; i++){
//                var attribute_node = this.render_attribute(this.attribute_list[i]);
//                attribute_node.querySelector('.attribute-name').addEventListener('click', this.click_reset_attribute_handler);
////                    attribute_node.addEventListener('click', this.click_reset_attribute_handler);
//                list_container.appendChild(attribute_node);
//            };
//        },
//
//    });

//    Graph Screen
    var GraphScreenWidget = screens.ScreenWidget.extend({
	    template: 'GraphScreenWidget',
	    init: function(parent, options){
	    	var self = this;
	        this._super(parent, options);
	        var list_ids = [];
	        var del_prod_id = self.pos.config.delivery_product_id ? list_ids.push(self.pos.config.delivery_product_id[0]) : false;
	        var pmt_prod_id = self.pos.config.payment_product_id ? list_ids.push(self.pos.config.payment_product_id[0]) : false;
	        var wlt_prod_id = self.pos.config.wallet_product ? list_ids.push(self.pos.config.wallet_product[0]) : false;
	        this.bar_chart = function(){
	        	var order = self.pos.get_order();
	        	var data = order.get_result();
	        	var dps = [];
        		if(data){
	        		for(var i=0;i<data.length;i++){
	        			if($.inArray(data[i][2],list_ids) == -1){
	        				dps.push({label: data[i][0], y: data[i][1]});
	        			}
		        	}
	        	}
	    		var chart = new CanvasJS.Chart("chartContainer",{
	    			width: data && data.length > 10 ? 1200 : 0,
	    			dataPointMaxWidth:25,
	    			zoomEnabled:true,
	    			exportFileName: $('a.menu_selected').text(),
	    			exportEnabled: true,
	    			theme: "theme3",
	    			title: {
	    				text: $('a.menu_selected').text()
	    			},
	    			axisY: {
	    				suffix: ""
	    			},		
	    			legend :{
	    				verticalAlign: 'bottom',
	    				horizontalAlign: "center"
	    			},
	    			data: [{
	    				type: "column",
	    				bevelEnabled: true,
	    				indexLabel:'{y}',
	    				indexLabelOrientation: "vertical", //horizontal
	    				dataPoints: dps
	    			}]
	    		});
	    		chart.render();
	        };
	        this.pie_chart = function(){
	        	var order = this.pos.get_order();
	        	var data = order.get_result();
	        	var dps = [];
	        	for(var i=0;i<data.length;i++){
	        		if($.inArray(data[i][2],list_ids) == -1){
	        			dps.push({y: data[i][1], indexLabel: data[i][0]});
	        		}
	        	}
	        	var chart = new CanvasJS.Chart("chartContainer",
    			{
	        		exportFileName: $('a.menu_selected').text(),
	    			exportEnabled: true,
	    			zoomEnabled:true,
    				theme: "theme2",
    				title:{
    					text: $('a.menu_selected').text()
    				},
    				data: [{
    					type: "pie",
    					showInLegend: true,
    					toolTipContent: "{y} - #percent %",
    					yValueFormatString: "",
    					legendText: "{indexLabel}",
    					dataPoints: dps
    				}]
    			});
    			chart.render();
	        };
	    },
        show: function(){
        	var self = this;
        	this._super();
        	$('#duration_selection').prop('selectedIndex',0);
        	var from = moment(new Date()).format('YYYY-MM-DD')+" 00:00:00";
    		var to = moment(new Date()).format('YYYY-MM-DD HH:mm:ss');
        	var active_chart = $('span.selected_chart').attr('id');
        	var category = $('a.menu_selected').attr('id');
        	var limit = $('#limit_selection').val() || 10;
        	self.graph_data(from, to, active_chart="bar_chart", category, limit);
        	self.bar_chart();
        },
	    start: function(){
	    	var self = this;
            this._super();
            var active_chart = $('span.selected_chart').attr('id');
        	var category = $('a.menu_selected').attr('id');
            var from = moment(new Date()).format('YYYY-MM-DD')+" 00:00:00";
    		var to = moment(new Date()).format('YYYY-MM-DD HH:mm:ss');
    		var limit = $('#limit_selection').val() || 10;
            this.graph_data(from,to, active_chart, category, limit);
            this.$('.back').click(function(){
                self.gui.back();
            });

            this.$('#duration_selection, #limit_selection').on('change',function(){
            	self.get_graph_information();
            });

            this.$('#top_customer').click(function(){
            	if(!$('#top_customer').hasClass('menu_selected')){
            		$('#top_customer').addClass('menu_selected');
            		if(self.$('#top_products').hasClass('menu_selected')){
            			self.$('#top_products').removeClass('menu_selected');
            		}
            		if(self.$('#cashiers').hasClass('menu_selected')){
            			self.$('#cashiers').removeClass('menu_selected');
            		}
            		if(self.$('#sales_by_location').hasClass('menu_selected')){
            			self.$('#sales_by_location').removeClass('menu_selected');
            		}
        			if(self.$('#income_by_journals').hasClass('menu_selected')){
            			self.$('#income_by_journals').removeClass('menu_selected');
            		}
        			if(self.$('#top_category').hasClass('menu_selected')){
            			self.$('#top_category').removeClass('menu_selected');
            		}
            	}
            	self.get_graph_information();
            });
            this.$('#top_products').click(function(){
            	if(!$('#top_products').hasClass('menu_selected')){
            		$('#top_products').addClass('menu_selected');
            		if(self.$('#top_customer').hasClass('menu_selected')){
            			self.$('#top_customer').removeClass('menu_selected');
            		}
            		if(self.$('#cashiers').hasClass('menu_selected')){
            			self.$('#cashiers').removeClass('menu_selected');
            		}
            		if(self.$('#sales_by_location').hasClass('menu_selected')){
            			self.$('#sales_by_location').removeClass('menu_selected');
            		}
        			if(self.$('#income_by_journals').hasClass('menu_selected')){
            			self.$('#income_by_journals').removeClass('menu_selected');
            		}
        			if(self.$('#top_category').hasClass('menu_selected')){
            			self.$('#top_category').removeClass('menu_selected');
            		}
            	}
            	self.get_graph_information();
            });
            this.$('#cashiers').click(function(){
            	if(!$('#cashiers').hasClass('menu_selected')){
            		$('#cashiers').addClass('menu_selected');
            		if(self.$('#top_customer').hasClass('menu_selected')){
            			self.$('#top_customer').removeClass('menu_selected');
            		}
            		if(self.$('#top_products').hasClass('menu_selected')){
            			self.$('#top_products').removeClass('menu_selected');
            		}
            		if(self.$('#sales_by_location').hasClass('menu_selected')){
            			self.$('#sales_by_location').removeClass('menu_selected');
            		}
        			if(self.$('#income_by_journals').hasClass('menu_selected')){
            			self.$('#income_by_journals').removeClass('menu_selected');
            		}
        			if(self.$('#top_category').hasClass('menu_selected')){
            			self.$('#top_category').removeClass('menu_selected');
            		}
            	}
            	self.get_graph_information();
            });
            this.$('#sales_by_location').click(function(){
            	if(!$('#sales_by_location').hasClass('menu_selected')){
            		$('#sales_by_location').addClass('menu_selected');
            		if(self.$('#top_customer').hasClass('menu_selected')){
            			self.$('#top_customer').removeClass('menu_selected');
            		}
            		if(self.$('#top_products').hasClass('menu_selected')){
            			self.$('#top_products').removeClass('menu_selected');
            		}
            		if(self.$('#cashiers').hasClass('menu_selected')){
            			self.$('#cashiers').removeClass('menu_selected');
            		}
        			if(self.$('#income_by_journals').hasClass('menu_selected')){
            			self.$('#income_by_journals').removeClass('menu_selected');
            		}
        			if(self.$('#top_category').hasClass('menu_selected')){
            			self.$('#top_category').removeClass('menu_selected');
            		}
            	}
            	self.get_graph_information();
            });
            this.$('#income_by_journals').click(function(){
            	if(!$('#income_by_journals').hasClass('menu_selected')){
            		$('#income_by_journals').addClass('menu_selected');
            		if(self.$('#top_customer').hasClass('menu_selected')){
            			self.$('#top_customer').removeClass('menu_selected');
            		}
            		if(self.$('#top_products').hasClass('menu_selected')){
            			self.$('#top_products').removeClass('menu_selected');
            		}
            		if(self.$('#cashiers').hasClass('menu_selected')){
            			self.$('#cashiers').removeClass('menu_selected');
            		}
        			if(self.$('#sales_by_location').hasClass('menu_selected')){
            			self.$('#sales_by_location').removeClass('menu_selected');
            		}
        			if(self.$('#top_category').hasClass('menu_selected')){
            			self.$('#top_category').removeClass('menu_selected');
            		}
            	}
            	self.get_graph_information();
            });
            this.$('#top_category').click(function(){
            	if(!$('#top_category').hasClass('menu_selected')){
            		$('#top_category').addClass('menu_selected');
            		if(self.$('#top_customer').hasClass('menu_selected')){
            			self.$('#top_customer').removeClass('menu_selected');
            		}
            		if(self.$('#top_products').hasClass('menu_selected')){
            			self.$('#top_products').removeClass('menu_selected');
            		}
            		if(self.$('#cashiers').hasClass('menu_selected')){
            			self.$('#cashiers').removeClass('menu_selected');
            		}
        			if(self.$('#sales_by_location').hasClass('menu_selected')){
            			self.$('#sales_by_location').removeClass('menu_selected');
            		}
            	}
            	self.get_graph_information();
            });

            /*Bar Chart*/
            this.$('#bar_chart').click(function(){
            	var order = self.pos.get_order();
            	if($('#bar_chart').hasClass('selected_chart')){
//            		$('#bar_chart').removeClass('selected_chart');
//            		$('#chartContainer').html('');
            	}else{
            		$('#bar_chart').addClass('selected_chart');
        			if(self.$('#pie_chart').hasClass('selected_chart')){
            			self.$('#pie_chart').removeClass('selected_chart');
            		}
        			self.get_graph_information();
                	self.bar_chart();
            	}
            });
            /*Pie Chart*/
            this.$('#pie_chart').click(function(){
            	if(!$('#pie_chart').hasClass('selected_chart')){
            		$('#pie_chart').addClass('selected_chart');
        			if(self.$('#bar_chart').hasClass('selected_chart')){
            			self.$('#bar_chart').removeClass('selected_chart');
            		}
        			self.get_graph_information();
        			self.pie_chart();
            	}
            });
	    },
	    graph_data: function(from, to, active_chart, category, limit){
	    	var self = this;
	    	new Model('pos.order').call('graph_data', [from, to, category, limit]).then(
					function(result) {
						var order = self.pos.get_order();
						if(result){
							if(result.length > 0){
								order.set_result(result);
							}else{
								order.set_result(0);
							}
						}else{
							order.set_result(0);
						}
						if(active_chart == "bar_chart"){
		            		self.bar_chart();
		            	}
						if(active_chart == "pie_chart"){
		            		self.pie_chart();
		            	}
					}).fail(function(error, event) {
				if (error.code === -32098) {
					alert(_t("Server closed..."));
					event.preventDefault();
				}
			});
	    },
	    get_graph_information: function(){
	    	var self = this;
	    	var time_period = $('#duration_selection').val() || 'today';
    		var active_chart = $('span.selected_chart').attr('id');
        	var category = $('a.menu_selected').attr('id');
        	var limit = $('#limit_selection').val() || 10;
        	if(time_period == "today"){
        		var from = moment(new Date()).format('YYYY-MM-DD')+" 00:00:00";
        		var to = moment(new Date()).format('YYYY-MM-DD HH:mm:ss');
        		self.graph_data(from, to, active_chart, category, limit);
        	}else if(time_period == "week"){
        		var from = moment(moment().startOf('week').toDate()).format('YYYY-MM-DD')+" 00:00:00";
        		var to   = moment(moment().endOf('week').toDate()).format('YYYY-MM-DD')+" 23:59:59";
        		self.graph_data(from, to, active_chart, category, limit);
        	}else if(time_period == "month"){
        		var from = moment(moment().startOf('month').toDate()).format('YYYY-MM-DD')+" 00:00:00";
        		var to   = moment(moment().endOf('month').toDate()).format('YYYY-MM-DD')+" 23:59:59";
        		self.graph_data(from, to, active_chart, category, limit);
        	}
	    },
	});
	gui.define_screen({name:'graph_view', widget: GraphScreenWidget});

	chrome.Chrome.include({
        build_widgets: function(){
            var self = this;
            var cashregisters = self.pos.cashregisters;
            var flag_is_cashjournal = false;
            if(cashregisters){
            	_.each(cashregisters, function(cashregister){
            		if(cashregister.journal.is_cashdrawer){
            			flag_is_cashjournal = true;
            		}
            	})
            }
            this._super();
            if(!flag_is_cashjournal && cashregisters){
            	alert("Please enable 'Is Cashdrawer' from any one of available payment method.");
            	self.gui.close();
            }
            if(self.pos.config.require_cashier){
	            this.gui.set_startup_screen('login');
	            this.gui.set_default_screen('login');
            }
            if(self.pos.config.enable_chat){
            	$('div.pos_chat').show();
            }else{
            	$('div.pos_chat').hide();
            }
            if(self.pos.config.enable_product_sync){
            	$('div.sync_products').show();
            }else{
            	$('div.sync_products').hide();
            }
            this.el.querySelector('.searchbox input').addEventListener('keypress',self.chrome.screens.products.product_categories_widget.search_handler);
            this.el.querySelector('.searchbox input').addEventListener('keydown',self.chrome.screens.products.product_categories_widget.search_handler);
            this.el.querySelector('.search-clear').addEventListener('click',self.chrome.screens.products.product_categories_widget.clear_search_handler);
	    	var delivery_product_id = self.pos.config.delivery_product_id[1] || false;
	    	var payment_product_id = self.pos.config.payment_product_id[1] || false;
	    	var wallet_product_id = self.pos.config.wallet_product[1] || false;
	    	var debt_dummy_product_id = self.pos.config.debt_dummy_product_id[1] || false;

            var new_prod_list = [];
            $('body.ui-autocomplete').css('font-size','200px');
            $('.searchbox.products input', this.el).keypress(function(e){
                if (new_prod_list.length <= 0){
                    var prod_list = self.pos.db.get_all_products_name();
                    var demo_prod_list = [
                                       delivery_product_id, payment_product_id,
                                       wallet_product_id,debt_dummy_product_id ];

                    prod_list.map(function(prod_name){
                        if ( prod_name && $.inArray(prod_name,demo_prod_list) == -1) {
                            new_prod_list.push(prod_name);
                        }
                    });
                }
                $('.searchbox.products input').autocomplete({
                    source:new_prod_list,
                    select: function(event, ui) {
                        if(ui){
                            var category = self.pos.db.get_category_by_id(self.pos.db.root_category_id);
                            self.pos.gui.screen_instances.products.product_categories_widget.perform_search(category, ui.item.value, true);
                        }
                        this.value = "";
                        return false
                    },
                });
                e.stopPropagation();
            });
            $('.search-clear', this.el).click(function(e){
            	self.clear_prod_search();
            });
            $('.category_searchbox.search_categories input', this.el).keypress(function(e){
                if($(this).val() == ""){
                   var cat = self.pos.db.get_category_by_id(self.pos.db.root_category_id);
                   self.pos.gui.screen_instances.products.product_categories_widget.set_category(cat);
                   self.pos.gui.screen_instances.products.product_categories_widget.renderElement();
                }
                $('.category_searchbox.search_categories input').autocomplete({
                    source:self.pos.db.get_category_search_list(),
                    select: function(event, select_category){
                        if(select_category.item && select_category.item.id){
                        	var cat = self.pos.db.get_category_by_id(select_category.item.id);
                            self.pos.gui.screen_instances.products.product_categories_widget.set_category(cat);
                            self.pos.gui.screen_instances.products.product_categories_widget.renderElement();
                        }
                    },
                });
                e.stopPropagation();
            });
            $('.category-clear', this.el).click(function(e){
            	self.clear_cat_search();
            });
            $('.sync_products').click(function(){
                $('.sync_products .fa-refresh').toggleClass('rotate', 'rotate-reset');
                if(self.pos.product_list.length > 0 && self.pos.db.get_is_product_load()){
                    var context = {
                            pricelist: self.pos.pricelist.id,
                            display_default_code: false,
                        }
                    var fields = ['display_name', 'list_price','price','pos_categ_id', 'taxes_id', 'barcode', 'default_code',
                             'to_weight', 'uom_id', 'description_sale', 'description',
                             'product_tmpl_id','tracking','write_date','type'];
                    var offset;
                    var domain = [['write_date','>',self.pos.db.get_partner_write_date()],['available_in_pos','=',true]];
                    new Model('product.product').call("search_read", [domain=domain, fields=fields, offset=0, false, false, context=context]).then(
                    function(products) {
                        if(products && products[0]){
                            self.pos.db.add_products(products);
                            products.map(function(product){
                                product.price = product.list_price;
                                $("[data-product-id='"+product.id+"']").find('.price-tag').html(self.format_currency(product.price));
                            });
                        }
                    });
                }else{
                    alert("Please wait, Products are still loading...");
                }
            });
            this.$('.control-buttons').removeClass('oe_hidden');
            var config_var = self.pos.config;
            
            setTimeout(function(){
            $('.pos-topheader').css("background",config_var.pos_topheader_bar);
            $('.product-list-container .product-list-scroller').css("background",config_var.product_background);
            $('.order-container').css("background",config_var.order_line_background);
            $('.category-simple-button').css("background",config_var.category_list_background);
            $('.rightpane-header').css("background",config_var.category_menu_background);
            $('.paymentmethods .button:hover').css("background",config_var.product_payment_selected, 'important');
            $('.pos .paymentline').css({"background":config_var.product_payment_line,"color":config_var.product_payment_line_text});
            $('.pos-actionbar .pos-actionbar-button-list').css("background",config_var.bottom_button_bar);
            $('.pos-actionbar .pos-actionbar-button-list .button').css("background",config_var.bottom_bar_button);
            $('.pos .leftpane .pads').css("background",config_var.product_left_down);

            $('.paymentmethods .button:hover').css("background",config_var.product_payment_selected, 'important');
            $('.numpad button, .actionpad .button').css({"background":config_var.product_numpad_background,"color":config_var.product_numpad_text});
            $('.numpad button:active').css("background",config_var.product_numpad_selected);

            $('#sidebar-wrapper').css("background",config_var.sidebar_background);
            $('#sidebar-wrapper #menu').css("background",config_var.sidebar_button);

            $('.subwindow-container-fix .receipt-screen').css("background",config_var.receipt_screen_background);
            $('.subwindow-container-fix .payment-screen').css("background",config_var.payment_screen_background);
            $('.subwindow-container-fix .clientlist-screen').css("background",config_var.customer_view_background);
            $('.client-list-contents tr').css("background",config_var.customer_list_view_nothighlight);
            $('.client-list-contents tr:nth-child(2n)').css("background",config_var.customer_list_view_highlight);
            $(".client-list thead tr").css("background",config_var.customer_list_view_head);
            $('.pos .clientlist-screen .screen-content .top-content .button').css("background",config_var.customer_screen_buttons);

            $('.popup').find('.title').css('background',config_var.popup_title_background);
            $('.popup').find('.title').css('color', config_var.popup_title_font_color);
            $('.popup').css('background', config_var.popup_content_background);
            $('.popup').css('color', config_var.popup_content_font_color);
            $('.popup').find('.footer').css('background', config_var.popup_footer_background);
            $('.popup').find('.footer').css('color', config_var.popup_footer_font_color);

            $('.screen').css('background',config_var.screen_background);
            $('.top-content').css('background',config_var.screen_title_background);
            $('.top-content').css('color',config_var.screen_title_font_color);
            $('.full-content').css('background',config_var.screen_content_background);
            $('.full-content').css('color',config_var.screen_content_font_color);

            }, 100);

        },
		clear_cat_search: function(){
			if(self.pos){
				var products = self.pos.db.get_product_by_category(0);
		        self.pos.gui.screen_instances.products.product_list_widget.set_product_list(products);
			}
		    var input = $('.category_searchbox input');
		    input.val('');
		    input.focus();
		},
		clear_prod_search: function(){
	        var products = this.pos.db.get_product_by_category(0);
	        self.pos.gui.screen_instances.products.product_list_widget.set_product_list(products);
	        var input = $('.searchbox input');
	            input.val('');
	            input.focus();
	    },
        renderElement:function(){
            var self = this;
            this._super();

            this.$el.click(function(){
                var config_var = self.pos.config;
                $('.pos-topheader').css("background",config_var.pos_topheader_bar);
                $('.product-list-container .product-list-scroller').css("background",config_var.product_background);
                $('.order-container').css("background",config_var.order_line_background);
                $('.category-simple-button').css("background",config_var.category_list_background);
                $('.rightpane-header').css("background",config_var.category_menu_background);
                $('.pos .paymentline').css({"background":config_var.product_payment_line,"color":config_var.product_payment_line_text});
                $('.pos-actionbar .pos-actionbar-button-list').css("background",config_var.bottom_button_bar);
                $('.pos-actionbar .pos-actionbar-button-list .button').css("background",config_var.bottom_bar_button);
                $('.pos .leftpane .pads').css("background",config_var.product_left_down);
                $('.paymentmethods .button').css("background",config_var.product_payment_selected, 'important');
                $('.numpad button, .actionpad .button').css({"background":config_var.product_numpad_background,"color":config_var.product_numpad_text});
                $('.numpad button:hover, .actionpad .button:hover').css("background",config_var.product_numpad_selected);

                $('#sidebar-wrapper').css("background",config_var.sidebar_background);
                $('#sidebar-wrapper #menu').css("background",config_var.sidebar_botton);

                $('.subwindow-container-fix .receipt-screen').css("background",config_var.receipt_screen_background);
                $('.subwindow-container-fix .payment-screen').css("background",config_var.payment_screen_background);
                $('.subwindow-container-fix .clientlist-screen').css("background",config_var.customer_view_background);
                $('.client-list-contents tr').css("background",config_var.customer_list_view_nothighlight);
                $('.client-list-contents tr:nth-child(2n)').css("background",config_var.customer_list_view_highlight);
                $(".client-list thead tr").css("background",config_var.customer_list_view_head);
                $('.pos .clientlist-screen .screen-content .top-content .button').css("background",config_var.customer_screen_buttons);

                $('.popup').find('.title').css('background',config_var.popup_title_background, 'important');
                $('.popup').find('.title').css('color', config_var.popup_title_font_color, 'important');
                $('.popup').css('background', config_var.popup_content_background);
                $('.popup').css('color', config_var.popup_content_font_color);
                $('.popup').find('.footer').css('background', config_var.popup_footer_background);
                $('.popup').find('.footer').css('color', config_var.popup_footer_font_color);

                $('.screen').css('background',config_var.screen_background);
                $('.top-content').css('background',config_var.screen_title_background);
                $('.top-content').css('color',config_var.screen_title_font_color);
                $('.full-content').css('background',config_var.screen_content_background);
                $('.full-content').css('color',config_var.screen_content_font_color);

            });
        },

    });

	var PosReturnOrderOption = PopupWidget.extend({
	    template: 'PosReturnOrderOption',
	    show: function(options){
	    	var self = this;
	        options = options || {};
	        this._super(options);
	        this.renderElement();
	        $('.close_btn').click(function(){
	        	$("div#menu a#sale_mode").parent().css({'background':'#6EC89B'});
	 	       	$("div#menu a#return_order").parent().css({'background':''});
	            $('#return_order_ref').html('');
	            $('#return_order_number').text('');
	        	self.gui.close_popup(); 
	        });
	        $('#choice_without_receipt').click(function(event){
	        		var selectedOrder = self.pos.get_order();
	        		var cashregisters = self.pos.cashregisters;
	        		var is_cashdrawer = false;
	        		_.each(cashregisters, function(cashregister){
				        if(cashregister.journal.is_cashdrawer && cashregister.journal.type === _t("cash")){
	                        is_cashdrawer = true;
	                        return
				        }
				    });
	        		if(selectedOrder){
	        			selectedOrder.set_sale_mode(false);
		                selectedOrder.set_missing_mode(true);
		                $("div#menu a#sale_mode").parent().css({'background':'','color':'#000'});
		                $("div#menu a#return_order").parent().css({'background':'#6EC89B','color':'#FFF'});
		                selectedOrder.set_ret_o_ref('Missing Receipt');
		                $('#return_order_ref').html('Missing Receipt');
		                $("span.remaining-qty-tag").css('display', 'none');
		                self.gui.close_popup();
	        		}else{
	        			alert("Order not found...");
	        		}
	        });
	        $('#choice_with_receipt').click(function(){
	        	self.gui.close_popup();
	        	var selectedOrder = self.pos.get_order();
                selectedOrder.set_sale_mode(false);
                selectedOrder.set_missing_mode(false);
                $("div#menu a#sale_mode").parent().css({'background':'','color':'#000'});
                $("div#menu a#return_order").parent().css({'background':'#6EC89B','color':'#FFF'});
                $('#return_order_ref').html();
	        	self.gui.show_popup('pos_return_order');
	        });
	    },
	});
	gui.define_popup({name:'PosReturnOrderOption', widget: PosReturnOrderOption});

	var AddToWalletPopup = PopupWidget.extend({
	    template: 'AddToWalletPopup',
	    show: function(options){
	    	var self = this;
	    	var order = self.pos.get_order();
	        options = options || {};
	        this.change = order.get_change() || false;
	        this._super(options);
	        this.renderElement();
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	if(!self.pos.config.cash_control){
	    		return alert("Please enable cash control from point of sale settings.");
	    	}
	    	if(order.get_client()){
	    		if(order.get_missing_mode() || order.get_ret_o_id()){
	    			order.set_type_for_wallet('return');
	    		}else{
	    			order.set_type_for_wallet('change');
	    		}
	    		order.set_change_amount_for_wallet(order.get_change());
	    		this.validate();
	    	} else {
	    		if(confirm("To add money into wallet you have to select a customer or create a new customer \n Press OK for go to customer screen \n Press Cancel to Discard.")){
	    			self.gui.show_screen('clientlist');
	    		}else{
	    			this.gui.close_popup();
	    		}
	    	}
	    },
	    click_cancel: function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	self.validate();
	        this.gui.close_popup();
	    },
	    validate: function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	var currentOrder = order;
	    	self.pos.push_order(order).then(function(){
        		setTimeout(function(){
        			self.gui.show_screen('receipt');
        		},1000)
        	});
	        this.gui.close_popup();
	    }
	});
	gui.define_popup({name:'AddToWalletPopup', widget: AddToWalletPopup});

//	var SyncProduct = screens.ActionButtonWidget.extend({
//        template: 'SyncProduct',
//        button_click: function(){
//
//        },
//    });
//	screens.define_action_button({
//        'name': 'SyncProduct',
//        'widget': SyncProduct,
//    });

    var ReferralCustomerScreenWidget = screens.ScreenWidget.extend({
	    template: 'ReferralCustomerScreenWidget',

//	    init: function(parent, options){
//	    	var self = this;
//	        this._super(parent, options);
//	        this.reload_btn = function(){
//	        	$('.fa-refresh').toggleClass('rotate', 'rotate-reset');
//	        	self.reloading_orders();
//	        };
//	    },

//	    filter:"all",
//
//        date: "all",

	    show: function(){
            var self = this;
            this._super();

            this.renderElement();
            var order = self.pos.get_order();

            this.$('.back').click(function(){
                self.gui.back();
            });
            var partners = self.pos.db.get_partners_sorted(1000);
            self.render_list(partners);
          //search box
            var search_timeout = null;
            if(this.pos.config.iface_vkeyboard && self.chrome.widget.keyboard){
            	self.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }
            this.$('.searchbox input').on('keyup',function(event){
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });

            this.$('.referral-customer-list-contents').delegate('.client-line','click',function(event){
                var partner = self.pos.db.get_partner_by_id($(this).data('id'));
                if (order.get_client()) {
                    if (order.get_client().id != partner.id){
                        order.set_ref_cust(partner.id);
                        order.set_ref_cust_label(partner.name);
                        $('#ref_customer_name').html('Reference of: ' + order.get_ref_cust_label());
                        self.gui.show_screen('products');
                    } else {
                        alert (_t('Customer and Reference can not be same !'));
                        return;
                    }
                } else {
                    order.set_ref_cust(partner.id);
                    order.set_ref_cust_label(partner.name);
                    $('#ref_customer_name').html('Reference of: ' + order.get_ref_cust_label());
                    self.gui.show_screen('products');
                }
            });
        },
        perform_search: function(query, associate_result){
            var partners;
            if(query){
            	partners = this.pos.db.search_partner(query);
            	this.render_list(partners);
                if ( associate_result && partners.length === 1){
                    this.new_client = partners[0];
                    var order = this.pos.get_order();
                    if (order.get_client()) {
                        if (order.get_client().id != partners[0].id){
                            order.set_ref_cust(partners[0].id);
                            order.set_ref_cust_label(partners[0].name);
                            $('#ref_customer_name').html('Reference of: ' + order.get_ref_cust_label());
                            this.gui.show_screen('products');
                        } else {
                            alert (_t('Customer and Reference can not be same !'));
                            return;
                        }
                    } else {
                        order.set_ref_cust(partners[0].id);
                        order.set_ref_cust_label(partners[0].name);
                        $('#ref_customer_name').html('Reference of: ' + order.get_ref_cust_label());
                        this.gui.show_screen('products');
                    }
                }
            }else{
            	partners = this.pos.db.get_partners_sorted();
                this.render_list(partners);
            }
        },
        clear_search: function(){
            var partners = this.pos.db.get_partners_sorted(1000);
            this.render_list(partners);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
	    render_list: function(partners){
        	var self = this;
            var contents = this.$el[0].querySelector('.referral-customer-list-contents');
            contents.innerHTML = "";

            for(var i = 0, len = Math.min(partners.length,1000); i < len; i++){
                var partner    = partners[i];
            	var clientline_html = QWeb.render('ReferralCustomerLine',{widget: this, partner:partner});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                contents.appendChild(clientline);
            }
            $("table.referral-customer-list").simplePagination({
				previousButtonClass: "btn btn-danger",
				nextButtonClass: "btn btn-danger",
				previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
				nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
				perPage: 10
			});
        },
	});
	gui.define_screen({name:'referral_customer', widget: ReferralCustomerScreenWidget});

	PosBaseWidget.include({
		format_currency: function(amount,precision){
			var self = this;
	        var currency = (this.pos && this.pos.currency) ? this.pos.currency : {symbol:'$', position: 'after', rounding: 0.01, decimals: 2};
	        amount = this.format_currency_no_symbol(amount,precision);
	        currency.decimals = this.pos.dp['Product Price'];
	        currency.rounding = 0.001;
	        if (currency.position === 'after') {
	            return amount + ' ' + (currency.symbol || '');
	        } else {
	            return (currency.symbol || '') + ' ' + amount;
	        }
	    },
	})
	var ProxyScreenDisplay = PosBaseWidget.extend({
        template: 'ProxyScreenDisplay',
        start: function(){
            $(".customer_display_icon").click(function(){
                var status_code = new Model('screen.notification.msg');
                function createRequest(){
                    status_code.call('check_status',[]).then(
                        function(result) {
                            if(result){
                                $(".customer_display_icon").css('color','green');
                            }
                            else{
                                $(".customer_display_icon").css('color','red');
                            } 
                    });
                }
            });
            var status_code = new Model('screen.notification.msg');
            function createRequest(){
                status_code.call('check_status',[]).then(
                    function(result) {
                        if(result){
                            $(".customer_display_icon").css('color','green');
                        }
                        else{
                            $(".customer_display_icon").css('color','red');
                        } 
                     setTimeout(function(){ createRequest(); }, 10000);
                 });
            }
            createRequest();
        },

    });
    var chrome_obj = chrome.Chrome.prototype
    chrome_obj.widgets.push({
            'name':   'ProxyScreenDisplay',
            'widget': ProxyScreenDisplay,
            'append':  '.pos-rightheader',
    });

    chrome.OrderSelectorWidget.include({
        renderElement: function(){
            var self = this;
            this._super();
            this.$('.order-button.select-order').click(function(event){
                self.pos.get('selectedOrder').mirror_image_data();
            });
            this.$('.neworder-button').click(function(event){
                self.pos.get('selectedOrder').mirror_image_data();
            });
            this.$('.deleteorder-button').click(function(event){
                self.pos.get('selectedOrder').mirror_image_data();
            });
        },
        deleteorder_click_handler: function(event, $el) {
            var self  = this;
            var order = this.pos.get_order(); 
            if (!order) {
                return;
            } else if ( !order.is_empty() ){
                this.gui.show_popup('confirm',{
                    'title': _t('Destroy Current Order ?'),
                    'body': _t('You will lose any data associated with the current order'),
                    confirm: function(){
                        self.pos.delete_current_order();
                        self.pos.get('selectedOrder').mirror_image_data();
                        $('.set-customer').html("Customer");
                    },
                });
            } else {
                this.pos.delete_current_order();
                self.pos.get('selectedOrder').mirror_image_data();
                $('.set-customer').html("Customer");
            }
        },
        order_click_handler: function(event,$el) {
            this._super(event,$el);
            var order = this.pos.get_order();
            if(order.get_gift_receipt_mode()){
		        $('.gift_receipt_btn').addClass('highlight');
		    } else {
		        $('.gift_receipt_btn').removeClass('highlight');
		    }
        },
    });

    var RedeemGiftVoucherPopup = PopupWidget.extend({
		template: 'RedeemGiftVoucherPopup',
		show: function(options){
            var self = this;
            this.payment_self = options.payment_self || false;
            this._super();
            var order = self.pos.get_order();
    		var total_pay = order.get_total_with_tax();
    		self.self_voucher = false ;
            window.document.body.removeEventListener('keypress',self.payment_self.keyboard_handler);
        	window.document.body.removeEventListener('keydown',self.payment_self.keyboard_keydown_handler);
            this.renderElement();
            $('#gift_voucher_text').focus();
            $('#gift_voucher_text').keypress(function(e) {
            	if (e.which == 13 && $(this).val()) {
            		var today = moment().format('YYYY-MM-DD');
            		var code = $(this).val();
        			new Model('aspl.gift.voucher').get_func('search_read')([['voucher_code', '=', code], ['expiry_date', '>=', today]])
        			.then(function(res){
        				if(res.length > 0){
        					var due = order.get_total_with_tax() - order.get_total_paid();
	        				if (res[0].minimum_purchase <= total_pay && res[0].voucher_amount <= due){
		        					self.self_voucher = res[0]
		        					$('#barcode').html("Amount: "+ self.format_currency(res[0].voucher_amount))
		        			}else{
		        				alert(_t("Due amount should be equal or above to "+self.format_currency(res[0].minimum_purchase)));
		        			}
		        		}else{
		        			$('#barcode').html("")
		        			self.self_voucher = false ;	
		        			alert(_t("Voucher not found or voucher has been expired"));
		        		}
        			});
	        	}
        	});
        },
        click_confirm: function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	var vouchers = order.get_voucher();
	    	var paymentlines = order.get_paymentlines();
	    	var cashregister = false;
	    	var code = $(gift_voucher_text).val();
	    	if (paymentlines.length > 0){
	    		self.chrome.screens.payment.click_delete_paymentline(paymentlines.cid)
	    	}
	    	if (self.self_voucher){
	    		var pid = Math.floor(Math.random() * 90000) + 10000;
	    		self.self_voucher['pid'] = pid
	    		if (self.pos.config.gift_voucher_journal_id.length > 0){
			        for ( var i = 0; i < self.pos.cashregisters.length; i++ ) {
			            if ( self.pos.cashregisters[i].journal_id[0] === self.pos.config.gift_voucher_journal_id[0] ){
			               cashregister = self.pos.cashregisters[i]
			            }
    				}
    				if (cashregister){
    					if(!vouchers){
    						self.check_redemption_customer().then(function(redeem_count){
								if (redeem_count == 0 || redeem_count < self.self_voucher.redemption_customer){
									order.add_paymentline(cashregister);
			    					order.selected_paymentline.set_amount( Math.max(self.self_voucher.voucher_amount, 0) );
								    order.selected_paymentline.set_gift_voucher_line_code(code);
								    order.selected_paymentline.set_pid(pid);
								    self.chrome.screens.payment.reset_input();
								    self.chrome.screens.payment.render_paymentlines();
								    order.set_voucher(self.self_voucher);
								    self.gui.close_popup();
								    window.document.body.addEventListener('keypress',self.payment_self.keyboard_handler);
        							window.document.body.addEventListener('keydown',self.payment_self.keyboard_keydown_handler);
								} else {
									alert(_t("Your voucher use's limit has been expired"));
								}
							});
						} else {
							if (self.self_voucher.voucher_code == code){
								var voucher_use = _.countBy(vouchers, 'voucher_code');
								if (voucher_use[code]){
									if((self.self_voucher.redemption_order > voucher_use[code]) || (self.self_voucher.redemption_order == 0)){
										self.check_redemption_customer().then(function(redeem_count){
                                            redeem_count += voucher_use[code];
											if (redeem_count == 0 || redeem_count < self.self_voucher.redemption_customer){
												order.add_paymentline(cashregister);
						    					order.selected_paymentline.set_amount( Math.max(self.self_voucher.voucher_amount, 0) );
						    					order.selected_paymentline.set_gift_voucher_line_code(code);
												order.selected_paymentline.set_pid(pid);
											    self.chrome.screens.payment.reset_input();
											    self.chrome.screens.payment.render_paymentlines();
											    order.set_voucher(self.self_voucher);
											    self.gui.close_popup();
											    window.document.body.addEventListener('keypress',self.payment_self.keyboard_handler);
        										window.document.body.addEventListener('keydown',self.payment_self.keyboard_keydown_handler);
											} else {
												alert(_t("Your voucher use's limit has been expired"));
											}
										});
									} else {
										alert(_t("Voucher limit has been expired for this order"));
										$('#barcode').html("")
										$('#gift_voucher_text').focus();
									}
								} else {
	                                self.check_redemption_customer().then(function(redeem_count){
										if (redeem_count == 0 || redeem_count < self.self_voucher.redemption_customer){
										    self.self_voucher['already_redeemed'] = redeem_count;
											order.add_paymentline(cashregister);
					    					order.selected_paymentline.set_amount(Math.max(self.self_voucher.voucher_amount, 0) );
										    order.selected_paymentline.set_gift_voucher_line_code(code);
										    order.selected_paymentline.set_pid(pid);
										    self.chrome.screens.payment.reset_input();
										    self.chrome.screens.payment.render_paymentlines();
										    order.set_voucher(self.self_voucher);
											self.gui.close_popup();
											window.document.body.addEventListener('keypress',self.payment_self.keyboard_handler);
        									window.document.body.addEventListener('keydown',self.payment_self.keyboard_keydown_handler);
										} else {
											alert(_t("Your voucher use's limit has been expired"));
										}
									});
								}
							} else {
								alert(_t("Voucher barcode is invalid"))
							}
						}
					} 
				} else {
					alert(_t("Please set Journal for gift voucher in POS Configuration"));
				}
			} else {
				alert(_t("Press enter to get voucher amount"));
				$('#gift_voucher_text').focus();
			}
		},
        click_cancel: function(){
        	var self = this;
        	self._super()
        	window.document.body.addEventListener('keypress',self.payment_self.keyboard_handler);
        	window.document.body.addEventListener('keydown',self.payment_self.keyboard_keydown_handler);
        },
        check_redemption_customer: function(){
        	var self = this;
        	var order = self.pos.get_order();
	        	return new Model('aspl.gift.voucher.redeem').get_func('search_count')([['voucher_id', '=', self.self_voucher.id], ['customer_id', '=', order.get_client() ? order.get_client().id : 0]])
    	},
	});
	gui.define_popup({name:'redeem_gift_voucher_popup', widget: RedeemGiftVoucherPopup});

	screens.ActionpadWidget.include({
        renderElement: function() {
            var self = this;
            this._super();
            if(self.pos.config.enable_gift_voucher){
                this.$('.set-customer').unbind('click').click(function(){
                    var temp = true;
                    var lines = self.pos.get_order().get_paymentlines();
                    _.each(lines, function(line){
                        if(line.get_gift_voucher_line_code()){
                            temp = false;
                        }
                    });
                    if(temp){
                        self.gui.show_screen('clientlist');
                    }
                });
            }
            this.$('#delivery_mode').click(function(){
		    	var order = self.pos.get_order();
		    	var lines = order.get_orderlines();
		    	var selected_orderline = order.get_selected_orderline();

		    	if(order.get_delivery_time() && order.get_delivery_date()){
			    	var selected_orderline = order.get_selected_orderline();
			    	if(selected_orderline){
				    	if(selected_orderline && !$('#delivery_mode').hasClass('deliver_on')){
				    		if(!selected_orderline.get_delivery_charges_flag()){
				    			selected_orderline.set_deliver_info(true);
				    		}else{
				    			$('#delivery_mode').removeClass('deliver_on');
				    		}
				    		var deliver_product_id = self.pos.config.delivery_product_id[0];
				    		var product = self.pos.db.get_product_by_id(deliver_product_id);
				    		if(!order.get_is_delivery()){
				        		var line_deliver_charges = new models.Orderline({}, {pos: self.pos, order:order, product: product});
				        		line_deliver_charges.set_quantity(1);
				        		line_deliver_charges.set_unit_price(0);
				        		line_deliver_charges.set_delivery_charges_color(true);
				        		line_deliver_charges.set_delivery_charges_flag(true);
				                order.add_orderline(line_deliver_charges);
				                order.set_is_delivery(true);
				    		}
			                order.set_delivery(true);
			                $('#delivery_mode').addClass('deliver_on');
				    	}else if(selected_orderline && selected_orderline.get_deliver_info()){
				    		selected_orderline.set_deliver_info(false);
				    		order.count_to_be_deliver();
				    		$('#delivery_mode').removeClass('deliver_on');
				    	}else if(selected_orderline && !selected_orderline.get_deliver_info()){
				    		if(!selected_orderline.get_delivery_charges_flag()){
				    			selected_orderline.set_deliver_info(true);
				    		}else{
				    			$('#delivery_mode').removeClass('deliver_on');
				    		}
				    	}else{
				    		$('#delivery_mode').removeClass('deliver_on');
				    		selected_orderline.set_deliver_info(false);
				    		order.count_to_be_deliver();
				    	}
			    	}else{
			    		alert(_t("Please select product to deliver."));
			    	}
		    	}else{
		    		if(selected_orderline && selected_orderline.get_deliver_info()){
		    			selected_orderline.set_deliver_info(false);
		    			order.count_to_be_deliver();
		    			$('#delivery_mode').removeClass('deliver_on');
		    		}else{
//		    			alert(_t("Please Select Date and Time to Deliver Product."));
		    			self.gui.show_popup('delivery_popup', {'from_delivery_mode': true});
		    		}
		    	}
			});
            
            this.$('button.clear_order').click(function(){
                var order = self.pos.get_order();
		        var lines = order.get_orderlines();
		        var customer_id = self.pos.get_client() && self.pos.get_client().id || '';
		        if(lines.length>0){
		        	var r = confirm("Are you sure you want to remove products from cart?");
		        	if(r){
			        	for(var i=0; i<= lines.length + 1; i++){
			        		_.each(lines,function(item){
			        			order.remove_orderline(item);
			        		});
			        	}
			        	for(var i=0; i<= lines.length + 1; i++){
			        		_.each(lines,function(item){
			        			order.remove_orderline(item);
			        		});
			        	}
		        	}
		        }else{
		            alert(_t("Your shopping cart is empty."))
		        }
            });
        },
    });

	var GiftCardListScreenWidget = screens.ScreenWidget.extend({
        template: 'GiftCardListScreenWidget',

        init: function(parent, options){
            var self = this;
            this._super(parent, options);
            this.reload_btn = function(){
                $('.fa-refresh').toggleClass('rotate', 'rotate-reset');
                self.reloading_gift_cards();
            };
        },

        filter:"all",

        date: "all",

        start: function(){
            var self = this;
            this._super();
            var gift_cards = self.pos.get('gift_card_order_list');
            this.render_list(gift_cards);
            this.$('.back').click(function(){
                self.gui.back();
            });

            this.$('.search_date').datepicker({
            	dateFormat:'yy-mm-dd',
            	onSelect: function(dateText) {
            		var temp = self.$('.search_date').val();
                    if(temp){
                       if(temp === ""){
                            self.date = "all"
                        }else if(jQuery.type(new Date(temp)) == "date"){
                            self.date = temp;
                            $('.search_date').val(temp);
                        }else{
                            self.$('.search_date').focusout();
                            alert("Please input a valid date...");
                            self.$('.search_date').val('');
                        }
                        self.render_list(gift_cards);
                    }else{
                        if($(this).val() == ""){
                            self.date = "all";
                            self.render_list(gift_cards);
                        }
                    }
            	},
            });
            // create button
            this.$('.button.create').click(function(){
                self.gui.show_popup('create_card_popup');
            });

            //recharge card
            this.$('.giftcard-list-contents').delegate('#recharge','click',function(event){
                var card_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_card_by_id(card_id);
                var order = self.pos.get_order();
                var client = order.get_client();
                self.gui.show_popup('recharge_card_popup',{'card_id':result.id,'card_no':result.card_no,'card_value':result.card_value,'customer_id':result.customer_id});
            });

            //edit exipre date
            this.$('.giftcard-list-contents').delegate('#edit','click',function(event){
                var card_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_card_by_id(card_id);
                if (result) {
                    self.gui.show_popup('edit_card_popup',{'card_id':card_id,'card_no':result.card_no,'expire_date':result.expire_date});
                }
            });

             //exchange barcode
            this.$('.giftcard-list-contents').delegate('#exchange','click',function(event){
                var card_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_card_by_id(card_id);
                if (result) {
                    self.gui.show_popup('exchange_card_popup',{'card_id':card_id,'card_no':result.card_no});
                } 
            });

            //searchbox
            var search_timeout = null;
            if(this.pos.config.iface_vkeyboard && self.chrome.widget.keyboard){
                self.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }
            this.$('.searchbox input').on('keyup',function(event){
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });
            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            }); 
        },

        show: function(){
            this._super();
            this.reload_gift_cards();
            this.reloading_gift_cards();
        },

        perform_search: function(query, associate_result){
            if(query){
                var gift_cards = self.pos.db.search_gift_card(query);
                if ( associate_result && gift_cards.length === 1){
                    this.gui.back();
                }
                this.render_list(gift_cards);
            }else{
                var gift_cards = self.pos.get('gift_card_order_list');
                this.render_list(gift_cards);
            }
        },

        clear_search: function(){
            var gift_cards = this.pos.get('gift_card_order_list');
            this.render_list(gift_cards);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },

        render_list: function(gift_cards){
    		var self = this;
            var contents = this.$el[0].querySelector('.giftcard-list-contents');
            contents.innerHTML = "";
            var temp = [];
            if(self.filter !== "" && self.filter !== "all"){
                gift_cards = $.grep(gift_cards,function(order){
                    return gift_card.state === self.filter;
                });
            }
            if(self.date !== "" && self.date !== "all"){
                var x = [];
                for (var i=0; i<gift_cards.length;i++){
                    var date_expiry = gift_cards[i].expire_date;
                    var date_issue = gift_cards[i].issue_date;
                    if(self.date === date_expiry || self.date == date_issue){
                        x.push(gift_cards[i]);
                    }
                }
                gift_cards = x;
            }
            for(var i = 0, len = Math.min(gift_cards.length,1000); i < len; i++){
                var gift_card    = gift_cards[i];
                gift_card.amount = parseFloat(gift_card.amount).toFixed(3); 
                var clientline_html = QWeb.render('GiftCardlistLine',{widget: this, gift_card:gift_card});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                contents.appendChild(clientline);
            }
            $("table.card-table").simplePagination({
                previousButtonClass: "btn btn-danger",
                nextButtonClass: "btn btn-danger",
                previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
                nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
                perPage: 10
            });
        },

        reload_gift_cards: function(){
            var self = this;
            var gift_cards = self.pos.get('gift_card_order_list');
            this.render_list(gift_cards);
        },

        reloading_gift_cards: function(){
            var self = this;
            return new Model('aspl.gift.card').get_func('search_read')([['is_active', '=', true]],[]).then(function(result){
                self.pos.db.add_giftcard(result);
                self.pos.set({'gift_card_order_list' : result});
                self.date = 'all';
                self.reload_gift_cards();
                return self.pos.get('gift_card_order_list');
            }).fail(function (error, event){
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                    self.gui.show_popup('error-traceback',{
                        message: error.data.message,
                        comment: error.data.debug
                    });
                }
                event.preventDefault();
                var gift_cards = self.pos.get('gift_card_order_list');
                console.error('Failed to send orders:', gift_cards);
                self.reload_gift_cards();
                return gift_cards
            });
        },

        renderElement: function(){
            var self = this;
            self._super();
            self.el.querySelector('.button.reload').addEventListener('click',this.reload_btn);
        },
    });

    gui.define_screen({name:'giftcardlistscreen', widget: GiftCardListScreenWidget});

//    var CreateCardPopupWidget = PopupWidget.extend({
//        template: 'CreateCardPopupWidget',
//        
//        show: function(options){
//            var self = this;
//            self.partner_id = '';
//            options = options || {};
//            this.opt_context = options; 
//            this._super(options);
//            this.renderElement();
//            var timestamp = new Date().getTime()/1000;
//            var partners = this.pos.partners;
//            var partners_list = [];
//            if(options && options.data){
//            	if(options.data){
//            		$('#text_expire_date').focus();
//            		$('#checkbox_paid').prop('checked',true);
//            		$('#checkbox_paid').prop('disabled',true);
//            		if(options.data.total){
//            			$("#text_amount").val(options.data.total);
//                		$("#text_amount").prop('disabled',true);
//            		}
//            		if(options.data.client){
//            			$('#select_customer').val(options.data.client.name);
//            		}
//            	}
//            }
//            if(partners && partners[0]){
//            	partners.map(function(partner){
//            		partners_list.push({
//            			'id':partner.id,
//            			'value':partner.name,
//            			'label':partner.name,
//            		});
//            	});
//            	$('#select_customer').keypress(function(e){
//	            	$('#select_customer').autocomplete({
//	                    source:partners_list,
//	                    select: function(event, ui) {
//	                    	self.partner_id = ui.item.id;
//	                    },
//	                });
//            	});
//            }
//            $("#text_amount").keypress(function (e) {
//                if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
//                    return false;
//               }
//            });
//            $('#card_no').html(window.parseInt(timestamp));
//            var partner = null;
//            for ( var j = 0; j < self.pos.partners.length; j++ ) {
//                partner = self.pos.partners[j];
//                self.partner=this.partner
//            }
//        },
//
//        click_confirm: function(){
//            var self = this;
//            var order = self.pos.get_order();
//            var checkbox_paid = document.getElementById("checkbox_paid");
//            var select_customer;
//            var expire_date = this.$('#text_expire_date').val();
//            if(self.opt_context && self.opt_context.data){
//            	if(!self.partner_id){
//                	self.partner_id = self.opt_context.data.client.id;
//                	select_customer = self.partner_id;
//                }else{
//                	select_customer = self.partner_id;
//                }
//            } else{
//            	select_customer = self.partner_id;
//            }
//            var select_card_type = $('#select_card_type').val();
//        	if(self.partner_id){
//        		var client = self.pos.db.get_partner_by_id(self.partner_id);
//        	}
//    		if(expire_date){
//                if(checkbox_paid.checked){
//                    $('#text_amount').focus();
//                    var input_amount =this.$('#text_amount').val();
//                    if(input_amount){
//                        var product = self.pos.db.get_product_by_id(self.pos.config.gift_card_product_id[0]);
//                        var gift_order = {'giftcard_card_no': $('#card_no').html(),
//                                'giftcard_customer': select_customer ? select_customer : false,
//                                'giftcard_expire_date': $('#text_expire_date').val(),
//                                'giftcard_amount': $('#text_amount').val(),
//                                'giftcard_customer_name': $("#select_customer").val() ? $("#select_customer").val() : "",
//                                'card_type': $('#select_card_type').val(),
//                            }
//                        order.set_giftcard(gift_order);
//                        if(self.pos.config.gift_card_product_id[0]){
//                            var orderlines=order.get_orderlines();
//                            if(self.opt_context.flag != "ret_create_card"){
//                            	for(var i = 0, len = orderlines.length; i < len; i++){
//                                    order.remove_orderline(orderlines);
//                                }
//                            }
//                            order.add_product(product, {price: input_amount});
//                        }
//                        $("#card_back").hide();
//                        $("div.js_set_customer").off("click");
//                        $("div#card_invoice").off("click");
//                        if(self.opt_context.flag != "ret_create_card"){
//                        	self.gui.show_screen('payment');
//                        } else{
//                        	self.pos.gui.screen_instances.payment.validate_order();
//                        }
//                        this.gui.close_popup(); 
//                    } else {
//                        alert("Please enter card value.")
//                        $('#text_amount').focus();
//                    }
//                }else{
//                    var input_amount =this.$('#text_amount').val();
//                    if(input_amount){
////                    	if(self.partner_id){
////                    		order.set_client(self.pos.db.get_partner_by_id(self.partner_id));
////                    	}
//                        order.set_free_data({
//                            'giftcard_card_no': $('#card_no').html(),
//                            'giftcard_customer': select_customer ? select_customer : '',
//                            'giftcard_expire_date': $('#text_expire_date').val(),
//                            'giftcard_amount': $('#text_amount').val(),
//                            'giftcard_customer_name': $("#select_customer").val() ? $("#select_customer").val() : '',
//                            'card_type': $('#select_card_type').val(),
//                        })
//                    	new Model("aspl.gift.card").get_func("create")({
//                    		'card_no': Number($('#card_no').html()),
//                    		'card_value':  Number($('#text_amount').val()),
//                    		'customer_id':self.partner_id ? Number(self.partner_id) : false,
//                    		'expire_date':$('#text_expire_date').val(),
//                    		'card_type': Number($('#select_card_type').val()),
//                    	});
//                        self.gui.show_screen('receipt');
//                        this.gui.close_popup();
//                    }else{
//                        alert("Please enter card value.")
//                        $('#text_amount').focus();
//                    }
//                }
//            }else{
//                alert("Please select expire date.")
//                $('#text_expire_date').focus();
//            }
//        },
//        click_cancel: function() {
//        	var self = this;
//        	if(self.opt_context.flag == "ret_create_card"){
//        		var r = confirm("Are you sure ? Press ok to destroy order!");
//        		if(r == true) {
//        			var order = self.pos.get_order();
//            		order.destroy();
//        		} 
//        	} else{
//        		self.gui.close_popup();
//        	}
//        },
//        renderElement: function() {
//            var self = this;
//            this._super();
//            $('.datetime').datepicker({
//            	minDate: 0,
//            	dateFormat:'yy/mm/dd',
//            });
//        },
//    });
//    gui.define_popup({name:'create_card_popup', widget: CreateCardPopupWidget});
    var CreateCardPopupWidget = PopupWidget.extend({
        template: 'CreateCardPopupWidget',
        
        show: function(options){
            var self = this;
            self.partner_id = '';
            options = options || {};
            this.opt_context = options;
            self.panding_card = options.card_data || false;
            this._super(options);
            this.renderElement();
            $('#card_no').focus();
            $('#checkbox_paid').prop('checked',true);
            var timestamp = new Date().getTime()/1000;
            var partners = this.pos.partners;
            var partners_list = [];
            if(self.pos.config.default_exp_date && !self.panding_card){
            	var date = new Date();
            	date.setMonth(date.getMonth() + self.pos.config.default_exp_date);
            	var new_date = date.getFullYear()+ "/" +(date.getMonth() + 1)+ "/" +date.getDate();
            	self.$('#text_expire_date').val(new_date);
            }
            if(options && options.data){
            	if(options.data){
            		$('#text_expire_date').focus();
            		$('#checkbox_paid').prop('checked',true);
            		$('#checkbox_paid').prop('disabled',true);
            		if(options.data.total){
            			$("#text_amount").val(options.data.total);
                		$("#text_amount").prop('disabled',true);
            		}
            		if(options.data.client){
            			$('#select_customer').val(options.data.client.name);
            		}
            	}
            }
            if(partners && partners[0]){
            	partners.map(function(partner){
            		partners_list.push({
            			'id':partner.id,
            			'value':partner.name,
            			'label':partner.name,
            		});
            	});
            	$('#select_customer').keypress(function(e){
	            	$('#select_customer').autocomplete({
	                    source:partners_list,
	                    select: function(event, ui) {
	                    	self.partner_id = ui.item.id;
	                    },
	                });
            	});
            	if(self.panding_card){
            		self.partner_id = self.panding_card.giftcard_customer;
            		$('#checkbox_paid').prop('checked',true);
            	}
            }
            $("#text_amount").keypress(function (e) {
                if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                    return false;
               }
            });
            if(self.pos.config.manual_card_number && !self.panding_card){
            	$('#card_no').removeAttr("readonly");
            	$("#card_no").keypress(function (e) {
                    if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                        return false;
                   }
                });
            } else if(!self.panding_card){
            	$('#card_no').val(window.parseInt(timestamp));
            	$('#card_no').attr("readonly", "readonly");
            }
            var partner = null;
            for ( var j = 0; j < self.pos.partners.length; j++ ) {
                partner = self.pos.partners[j];
                self.partner=this.partner
            }
        },

        click_confirm: function(){
            var self = this;
            var move = true;
            var order = self.pos.get_order();
            var checkbox_paid = document.getElementById("checkbox_paid");
            var select_customer;
            var expire_date = this.$('#text_expire_date').val();
            if(self.opt_context && self.opt_context.data){
            	if(!self.partner_id){
                	self.partner_id = self.opt_context.data.client.id;
                	select_customer = self.partner_id;
                }else{
                	select_customer = self.partner_id;
                }
            } else{
            	select_customer = self.partner_id;
            }
            var select_card_type = $('#select_card_type').val();
            var card_number = $('#card_no').val();
            if(!card_number){
        		alert("Enter gift card number");
        		return;
        	} else{
        		new Model('aspl.gift.card').call('search_count', [[['card_no', '=', card_number]]], {}, {async: false})
                .then(function(gift_count){
                    if(gift_count > 0){
                        $('#card_no').css('border', 'thin solid red');
                        move = false;
                    } else{
                    	$('#card_no').css('border', '0px');
                    }
                });
        	}
        	if(!move){
        		alert("Card already exist");
        		return
        	}
        	if(self.partner_id){
        		var client = self.pos.db.get_partner_by_id(self.partner_id);
        	}
    		if(expire_date){
                if(checkbox_paid.checked){
                    $('#text_amount').focus();
                    var input_amount =this.$('#text_amount').val();
                    if(input_amount){
                    	order.set_client(client);
                        var product = self.pos.db.get_product_by_id(self.pos.config.gift_card_product_id[0]);
                        if(!product){
                        	alert("Product may not loaded yet!");
                        	return
                        }
                        var gift_order = {'giftcard_card_no': $('#card_no').val(),
                                'giftcard_customer': select_customer ? select_customer : false,
                                'giftcard_expire_date': $('#text_expire_date').val(),
                                'giftcard_amount': $('#text_amount').val(),
                                'giftcard_customer_name': $("#select_customer").val() ? $("#select_customer").val() : "",
                                'card_type': $('#select_card_type').val(),
                            }
                        if(self.pos.config.gift_card_product_id[0]){
                            var orderlines=order.get_orderlines();
                            if(self.opt_context.flag != "ret_create_card"){
                            	for(var i = 0, len = orderlines.length; i < len; i++){
                                    order.remove_orderline(orderlines);
                                }
                            }
                            var line = new models.Orderline({}, {pos: self.pos, order: order, product: product});
                            line.set_unit_price(input_amount);
                            order.add_orderline(line);
                            order.select_orderline(order.get_last_orderline());
                        }
                        if(self.pos.config.msg_before_card_pay) {
                        	self.gui.show_popup('confirmation_card_payment',{'card_data':gift_order});
                        } else{
                        	order.set_giftcard(gift_order);
                        	self.gui.show_screen('payment');
                        	$("#card_back").hide();
                            $( "div.js_set_customer" ).off("click");
                            $( "div#card_invoice" ).off("click");
                            if(self.opt_context.flag != "ret_create_card"){
                            	self.gui.show_screen('payment');
                            } else{
                            	self.pos.gui.screen_instances.payment.validate_order();
                            }
                            this.gui.close_popup(); 
                        }
                    } else {
                        alert("Please enter card value.")
                        $('#text_amount').focus();
                    }
                }else{
                    var input_amount =this.$('#text_amount').val();
                    if(input_amount){
                        order.set_free_data({
                            'giftcard_card_no': $('#card_no').val(),
                            'giftcard_customer': select_customer ? select_customer : '',
                            'giftcard_expire_date': $('#text_expire_date').val(),
                            'giftcard_amount': $('#text_amount').val(),
                            'giftcard_customer_name': $("#select_customer").val() ? $("#select_customer").val() : '',
                            'card_type': $('#select_card_type').val(),
                        })
                    	new Model("aspl.gift.card").get_func("create")({
                    		'card_no': Number($('#card_no').val()),
                    		'card_value':  Number($('#text_amount').val()),
                    		'customer_id':self.partner_id ? Number(self.partner_id) : false,
                    		'expire_date':$('#text_expire_date').val(),
                    		'card_type': Number($('#select_card_type').val()),
                    	});
                        self.gui.show_screen('receipt');
                        this.gui.close_popup();
                    }else{
                        alert("Please enter card value.")
                        $('#text_amount').focus();
                    }
                }
            }else{
                alert("Please select expire date.")
                $('#text_expire_date').focus();
            }
        },
        click_cancel: function() {
        	var self = this;
        	if(self.opt_context.flag == "ret_create_card"){
        		var r = confirm("Are you sure ? Press ok to destroy order!");
        		if(r == true) {
        			var order = self.pos.get_order();
            		order.destroy();
        		} 
        	} else{
        		self.gui.close_popup();
        	}
        },
        renderElement: function() {
            var self = this;
            this._super();
            $('.datetime').datepicker({
            	minDate: 0,
            	dateFormat:'yy/mm/dd',
            });
        },
    });
    gui.define_popup({name:'create_card_popup', widget: CreateCardPopupWidget});

//    var RedeemCardPopupWidget = PopupWidget.extend({
//        template: 'RedeemCardPopupWidget',
//
//        show: function(options){
//           self = this;
//           this.payment_self = options.payment_self || false;
//           this._super();
//           self.redeem = false;
//           var order = self.pos.get_order();
//           window.document.body.removeEventListener('keypress',self.payment_self.keyboard_handler);
//           window.document.body.removeEventListener('keydown',self.payment_self.keyboard_keydown_handler);
//           this.renderElement();
//           $("#text_redeem_amount").keypress(function (e) {
//               if(e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
//                    return false;
//               }
//            });
//           $('#text_gift_card_no').focus();
//           $('#redeem_amount_row').hide();
//           $('#in_balance').hide();
//           $('#text_gift_card_no').keypress(function(e) {
//               if (e.which == 13 && $(this).val()) {
//                    var today = moment().format('YYYY-MM-DD');
//                    var code = $(this).val();
//                    var get_redeems = order.get_redeem_giftcard();
//                    var existing_card = _.where(get_redeems, {'redeem_card': code });   
//                    new Model('aspl.gift.card').get_func('search_read')([['card_no', '=', code], ['expire_date', '>=', today]])
//                    .then(function(res){
//                        if(res.length > 0){
//                            if (res[0]){
//                                if(existing_card.length > 0){
//                                    res[0]['card_value'] = existing_card[existing_card.length - 1]['redeem_remaining']
//                                }
//                                self.redeem = res[0];
//                                $('#lbl_card_no').html("Amount: "+ self.format_currency(res[0].card_value));
//                                if(res[0].customer_id[1]){
//                                	$('#lbl_set_customer').html("Hello  "+ res[0].customer_id[1]);
//                                } else{
//                                	$('#lbl_set_customer').html("Hello");
//                                }
//                                if(res[0].card_value <= 0){
//                                    $('#redeem_amount_row').hide();
//                                    $('#in_balance').show();
//                                }else{
//                                    $('#redeem_amount_row').fadeIn('fast');
//                                    $('#text_redeem_amount').focus();
//                                }
//                            }
//                        }else{
//                            alert("Barcode not found Or Gift card has been expired.")
//                            $('#text_gift_card_no').focus();
//                            $('#lbl_card_no').html('');
//                            $('#lbl_set_customer').html('');
//                            $('#in_balance').html('');
//                        }
//                    });
//                }
//            });
//        },
//  
//        click_cancel: function(){
//            var self = this;
//            self._super();  
//            window.document.body.addEventListener('keypress',self.payment_self.keyboard_handler);
//            window.document.body.addEventListener('keydown',self.payment_self.keyboard_keydown_handler);
//        },
//
//        click_confirm: function(){
//            var order = self.pos.get_order();
//            var client = order.get_client();
//            var redeem_amount = this.$('#text_redeem_amount').val();
//            var code = $('#text_gift_card_no').val();
//            if(self.redeem.card_no){ 
//                if(code == self.redeem.card_no){
//                    if(!self.redeem.card_value == 0){
//                        if(redeem_amount){
//                            if (redeem_amount<=order.get_total_with_tax()){
//                                if(!client){
//                                    order.set_client(self.pos.db.get_partner_by_id(self.redeem.customer_id[0]));
//                                }
//                                if( 0 < Number(redeem_amount)){
//                                    if(self.redeem && self.redeem.card_value >= Number(redeem_amount) ){
//                                        var vals = {
//                                            'redeem_card_no':self.redeem.id,
//                                            'redeem_card':$('#text_gift_card_no').val(),
//                                            'redeem_card_amount':$('#text_redeem_amount').val(),
//                                            'redeem_remaining':self.redeem.card_value - $('#text_redeem_amount').val(),
//                                            'card_customer_id': self.redeem.customer_id[0] || false,
//                                            'customer_name': self.redeem.customer_id[1],
//                                        };
//                                        var get_redeem = order.get_redeem_giftcard();
//                                        if(get_redeem){
//                                            var product=self.pos.db.get_product_by_id(self.pos.config.enable_journal_id)
//                                            if(self.pos.config.enable_journal_id[0]){
//                                               var cashregisters = null;
//                                               for ( var j = 0; j < self.pos.cashregisters.length; j++ ) {
//                                                    if(self.pos.cashregisters[j].journal_id[0] === self.pos.config.enable_journal_id[0]){
//                                                        cashregisters = self.pos.cashregisters[j];
//                                                    }
//                                                }
//                                            }
//                                            if (vals){
//                                                window.document.body.addEventListener('keypress',self.payment_self.keyboard_handler);
//                                                window.document.body.addEventListener('keydown',self.payment_self.keyboard_keydown_handler);
//                                                if (cashregisters){
//                                                    order.add_paymentline(cashregisters);
//                                                    order.selected_paymentline.set_amount( Math.max(redeem_amount),0 );
//                                                    order.selected_paymentline.set_giftcard_line_code(code);
//                                                    self.chrome.screens.payment.reset_input();
//                                                    self.chrome.screens.payment.render_paymentlines();
//                                                    order.set_redeem_giftcard(vals);
//                                                } 
//                                            }
//                                            this.gui.close_popup();
//                                        }
//                                    }else{
//                                        alert("Please enter amount below card value.");
//                                        $('#text_redeem_amount').focus();
//                                    }
//                                }else{
//                                    alert("Please enter valid amount.");
//                                    $('#text_redeem_amount').focus();
//                                }
//                            }else{
//                                alert("Card amount should be less than or equal to order total amount");
//                            } 
//                            
//                        }else{
//                            alert("Please enter amount.");
//                            $('#text_redeem_amount').focus();
//                        }
//                    }
//                }else{
//                    alert("Invalid barcode.");
//                    $('#text_gift_card_no').focus();
//                }
//            }else{
//                alert("Press Enter key.");
//                $('#text_gift_card_no').focus();
//            }
//        },
//    });
//    gui.define_popup({name:'redeem_card_popup', widget: RedeemCardPopupWidget});

    var RedeemCardPopupWidget = PopupWidget.extend({
        template: 'RedeemCardPopupWidget',

        show: function(options){
           self = this;
           this.payment_self = options.payment_self || false;
           this._super();
           self.redeem = false;
           var order = self.pos.get_order();
           window.document.body.removeEventListener('keypress',self.payment_self.keyboard_handler);
           window.document.body.removeEventListener('keydown',self.payment_self.keyboard_keydown_handler);
           this.renderElement();
           $("#text_redeem_amount").keypress(function (e) {
               if(e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                    return false;
               }
            });
           $('#text_gift_card_no').focus();
           $('#redeem_amount_row').hide();
           $('#in_balance').hide();
           $('#text_gift_card_no').keypress(function(e) {
        	   if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                   return false;
                }
    	    	if (e.which == 13 && $(this).val()) {
                    var today = moment().format('YYYY-MM-DD');
                    var code = $(this).val();
                    var get_redeems = order.get_redeem_giftcard();
                    var existing_card = _.where(get_redeems, {'redeem_card': code });   
                    new Model('aspl.gift.card').get_func('search_read')([['card_no', '=', code], ['expire_date', '>=', today]])
                    .then(function(res){
                        if(res.length > 0){
                            if (res[0]){
                                if(existing_card.length > 0){
                                    res[0]['card_value'] = existing_card[existing_card.length - 1]['redeem_remaining']
                                }
                                self.redeem = res[0];
                                $('#lbl_card_no').html("Amount: "+ self.format_currency(res[0].card_value));
                                if(res[0].customer_id[1]){
                                	$('#lbl_set_customer').html("Hello  "+ res[0].customer_id[1]);
                                } else{
                                	$('#lbl_set_customer').html("Hello");
                                }
                                if(res[0].card_value <= 0){
                                    $('#redeem_amount_row').hide();
                                    $('#in_balance').show();
                                }else{
                                    $('#redeem_amount_row').fadeIn('fast');
                                    $('#text_redeem_amount').focus();
                                }
                            }
                        }else{
                            alert("Barcode not found Or Gift card has been expired.")
                            $('#text_gift_card_no').focus();
                            $('#lbl_card_no').html('');
                            $('#lbl_set_customer').html('');
                            $('#in_balance').html('');
                        }
                    });
                }
            });
        },
  
        click_cancel: function(){
            var self = this;
            self._super();  
            window.document.body.addEventListener('keypress',self.payment_self.keyboard_handler);
            window.document.body.addEventListener('keydown',self.payment_self.keyboard_keydown_handler);
        },

        click_confirm: function(){
            var order = self.pos.get_order();
            var client = order.get_client();
            var redeem_amount = this.$('#text_redeem_amount').val();
            var code = $('#text_gift_card_no').val();
            if(self.redeem.card_no){ 
                if(code == self.redeem.card_no){
                    if(!self.redeem.card_value == 0){
                        if(redeem_amount){
                            if (redeem_amount<=order.get_total_with_tax()){
                                if(!client){
                                    order.set_client(self.pos.db.get_partner_by_id(self.redeem.customer_id[0]));
                                }
                                if( 0 < Number(redeem_amount)){
                                    if(self.redeem && self.redeem.card_value >= Number(redeem_amount) ){
                                        var vals = {
                                            'redeem_card_no':self.redeem.id,
                                            'redeem_card':$('#text_gift_card_no').val(),
                                            'redeem_card_amount':$('#text_redeem_amount').val(),
                                            'redeem_remaining':self.redeem.card_value - $('#text_redeem_amount').val(),
                                            'card_customer_id': self.redeem.customer_id[0] || false,
                                            'customer_name': self.redeem.customer_id[1],
                                        };
                                        var get_redeem = order.get_redeem_giftcard();
                                        if(get_redeem){
                                            var product=self.pos.db.get_product_by_id(self.pos.config.enable_journal_id)
                                            if(self.pos.config.enable_journal_id[0]){
                                               var cashregisters = null;
                                               for ( var j = 0; j < self.pos.cashregisters.length; j++ ) {
                                                    if(self.pos.cashregisters[j].journal_id[0] === self.pos.config.enable_journal_id[0]){
                                                        cashregisters = self.pos.cashregisters[j];
                                                    }
                                                }
                                            }
                                            if (vals){
                                                window.document.body.addEventListener('keypress',self.payment_self.keyboard_handler);
                                                window.document.body.addEventListener('keydown',self.payment_self.keyboard_keydown_handler);
                                                if (cashregisters){
                                                    order.add_paymentline(cashregisters);
                                                    order.selected_paymentline.set_amount( Math.max(redeem_amount),0 );
                                                    order.selected_paymentline.set_giftcard_line_code(code);
                                                    self.chrome.screens.payment.reset_input();
                                                    self.chrome.screens.payment.render_paymentlines();
                                                    order.set_redeem_giftcard(vals);
                                                } 
                                            }
                                            this.gui.close_popup();
                                        }
                                    }else{
                                        alert("Please enter amount below card value.");
                                        $('#text_redeem_amount').focus();
                                    }
                                }else{
                                    alert("Please enter valid amount.");
                                    $('#text_redeem_amount').focus();
                                }
                            }else{
                                alert("Card amount should be less than or equal to order total amount");
                            } 
                            
                        }else{
                            alert("Please enter amount.");
                            $('#text_redeem_amount').focus();
                        }
                    }
                }else{
                    alert("Invalid barcode.");
                    $('#text_gift_card_no').focus();
                }
            }else{
                alert("Press Enter key.");
                $('#text_gift_card_no').focus();
            }
        },
    });
    gui.define_popup({name:'redeem_card_popup', widget: RedeemCardPopupWidget});

    var ConfirmationCardPayment = PopupWidget.extend({
        template: 'ConfirmationCardPayment',

        show: function(options){
            self = this;
            this._super();
            self.options = options.card_data || false;
            self.recharge_card = options.rechage_card_data || false;
            self.renderElement();
        },
        click_confirm: function(){
            var self = this;
            var order = self.pos.get_order();
            if(self.recharge_card){
            	var vals = {
                    'recharge_card_id':self.recharge_card.recharge_card_id,
                    'recharge_card_no':self.recharge_card.recharge_card_no,
                    'recharge_card_amount':self.recharge_card.recharge_card_amount,
                    'card_customer_id': self.recharge_card.card_customer_id || false,
                    'customer_name': self.recharge_card.customer_name,
                    'total_card_amount':self.recharge_card.total_card_amount,
                }
            	order.set_recharge_giftcard(vals);
            	if(!order.get_ret_o_id()){
            		self.gui.show_screen('payment');
            	} else{
            		self.pos.gui.screen_instances.payment.validate_order();
            	}
            	$("#card_back").hide();
                $( "div.js_set_customer" ).off("click");
                $( "div#card_invoice" ).off("click");
                this.gui.close_popup();
            } else if(self.options){
            	var gift_order = {'giftcard_card_no': self.options.giftcard_card_no,
                        'giftcard_customer': self.options.giftcard_customer ? Number(self.options.giftcard_customer) : false,
                        'giftcard_expire_date': self.options.giftcard_expire_date,
                        'giftcard_amount': self.options.giftcard_amount,
                        'giftcard_customer_name': self.options.giftcard_customer_name,
                        'card_type': self.options.card_type,
                }
                order.set_giftcard(gift_order);
            	if(!order.get_ret_o_id()){
            		self.gui.show_screen('payment');
            	} else{
            		self.pos.gui.screen_instances.payment.validate_order();
            	}
                
            	$("#card_back").hide();
                $( "div.js_set_customer" ).off("click");
                $( "div#card_invoice" ).off("click");
                this.gui.close_popup();
            }
        },
        click_cancel: function(){
        	var self = this;
        	var order = self.pos.get_order();
        	if(self.recharge_card && !order.get_ret_o_id()){
        		self.gui.show_popup('recharge_card_popup',{'recharge_card_data':self.recharge_card})
        	}else if(self.options && !order.get_ret_o_id()){
        		self.gui.show_popup('create_card_popup',{'card_data':self.options});
        	} else {
        		if (confirm("Are you sure you want to cancel process!") == true) {
        			order.destroy();
        		}
        	}
        }
    });

    gui.define_popup({name:'confirmation_card_payment', widget: ConfirmationCardPayment});
    var RechargeCardPopupWidget = PopupWidget.extend({
        template: 'RechargeCardPopupWidget',

        show: function(options){
            self = this;
            var new_options = [];
            this._super();
            self.pending_card = options.recharge_card_data;
            if(!self.pending_card){
            	this.card_no = options.card_no || "";
                this.card_id = options.card_id || "";
                this.card_value = options.card_value || 0 ;
                this.customer_id = options.customer_id || "";
                var partner = _.find(self.pos.partners, function(obj) { return obj.id == self.customer_id[0]});
                this.renderElement();
                if(partner){
                	$(' tr td select#set_customers').html("<option value="+partner.id+">"+partner.name+"</option/>");
                }
                this.opt_context = options;
                $('#set_customers').val("");
                $('#text_card_num').val(this.card_no);
                $('#text_card_num').prop('disabled',true);
                $('#bal_amount').val(this.card_value);
            }else{
            	if(self.pending_card){
            		if(self.pending_card.card_customer_id){
                		$(' tr td select#set_customers').html("<option value="+self.pending_card.card_customer_id+">"+self.pending_card.customer_name+"</option/>");
                	}
                	$('#text_card_num').val(self.pending_card.recharge_card_no);
                	$('#text_recharge_amount').val(self.pending_card.recharge_card_amount);
            	}
            }
            $('#text_recharge_amount').focus();
            $("#text_recharge_amount").keypress(function (e) {
                if(e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                	return false;
                }
            });
            if(options.data && options.flag && options.flag == "ret_recharge_card"){
            	if(options.data.total){
            		$('#text_recharge_amount').val(options.data.total);
            		$('#text_recharge_amount').prop('disabled',true);
            	}
            	$('#text_card_num').prop('disabled',false);
            	$('#text_card_num').focus();
            	$('#text_card_num').keypress(function (e) {
            		if(e.which === 13){
            			var iscard = $('#text_card_num').val();
                        var res = self.pos.db.get_card_by_no(iscard);
                        if(res){
                        	self.card_id = res.id
                        	if(res.customer_id){
                        		self.customer_id = res.customer_id;
                        		$(' tr td select#set_customers').html("<option value="+self.customer_id[0]+">"+self.customer_id[1]+"</option/>");
                        		$('#set_customers').val(self.customer_id[0]);
                        	}
                        	$('#text_card_num').val(res.card_no);
                        	if(res.card_value){
                        		$('#bal_amount').text(res.card_value);
                        	}
                        	if(options.data.total){
                        		$('#text_recharge_amount').val(options.data.total);
                        		$('#text_recharge_amount').prop('disabled',true);
                        	}
                        } else{
                        	new Model('aspl.gift.card').get_func('search_read')([['is_active', '=', true],['card_no','=',iscard]],[]).then(function(res){
            	                if(res && res[0]){
            	                	self.result = res;
            	                	self.card_id = res[0].id
                                	if(res[0].customer_id){
                                		self.customer_id = res[0].customer_id;
                                		$('#set_customers').val(self.customer_id[0]);
                                	}
                                	if(res[0].card_value){
                                		self.card_value = res[0].card_value
                                		$('#bal_amount').text(res[0].card_value);
                                	}
                                	if(options.data.total){
                                		$('#text_recharge_amount').val(options.data.total);
                                		$('#text_recharge_amount').prop('disabled',true);
                                	}
            	                }else{
            	                	alert("Card not found!");
                                	$('#set_customers').val("");
                                	$('#bal_amount').text("");
                                	$('#text_recharge_amount').val("");
            	                }
                        	});
                        }
                    }
            		if(e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                    	return false;
                    }
                });
            } else{
            	$('#set_customers').val(self.customer_id[0]);
            	$('#bal_amount').text(self.card_value);
            }
        },

        click_confirm: function(){
            var self = this;
            var order = self.pos.get_order();
            if(self.opt_context.data && self.opt_context.flag && self.opt_context.flag == "ret_recharge_card"){
	            var iscard = $('#text_card_num').val();
	            var res = self.pos.db.get_card_by_no(iscard);
	            if(!res && !self.result ){
	            	$('#set_customers').val("");
	            	$('#bal_amount').text("");
	            	$('#text_recharge_amount').val("");
	            	alert("Card Not Found!");
	            	return
	            }
            }
            var client = order.get_client();
            var card_no= $('#text_card_num').val();
            var set_customer = $('#set_customers').val();
            self.card_value = Number($('#bal_amount').text());
            if(!client){
                order.set_client(self.pos.db.get_partner_by_id(set_customer));
            }
            if(!card_no){
            	alert("please enter card number and press enter.");
            	return
            }
            var recharge_amount = this.$('#text_recharge_amount').val();
            if (Number(recharge_amount)>0){
                var vals = {
                'recharge_card_id':self.card_id,
                'recharge_card_no':card_no,
                'recharge_card_amount':Number(recharge_amount),
                'card_customer_id': self.customer_id[0] || false,
                'customer_name': self.customer_id[1],
                'total_card_amount':Number(recharge_amount)+self.card_value,
                }
                var get_recharge = order.get_recharge_giftcard();
                if(get_recharge){
                    var product = self.pos.db.get_product_by_id(self.pos.config.gift_card_product_id[0]);
                    if(!product){
                    	alert("Product which you are going to use is not loaded properly.");
                    	return 
                    }
                    if (self.pos.config.gift_card_product_id[0]){
                        var orderlines=order.get_orderlines();
                        if(self.opt_context.flag != "ret_recharge_card"){
                            for(var i = 0, len = orderlines.length; i < len; i++){
                                order.remove_orderline(orderlines);
                            }
                        }
                        var line = new models.Orderline({}, {pos: self.pos, order: order, product: product});
                        line.set_unit_price(recharge_amount);
                        order.add_orderline(line);
                        order.select_orderline(order.get_last_orderline());
                    }
                    if(self.pos.config.msg_before_card_pay){
                    	self.gui.show_popup('confirmation_card_payment',{'rechage_card_data':vals})
                    } else {
                    	order.set_recharge_giftcard(vals);
                        self.gui.show_screen('payment');
                       	$("#card_back").hide();
                        $( "div.js_set_customer" ).off("click");
                        $( "div#card_invoice" ).off("click");
                        this.gui.close_popup();
                    }
                }
            }else{
               alert("Please enter valid amount.");
               $('#text_recharge_amount').focus();
            }
        },
        click_cancel: function() {
        	var self = this;
        	if(self.opt_context.flag == "ret_recharge_card"){
        		var r = confirm("Are you sure ? Press ok to destroy order!");
        		if(r == true) {
        			var order = self.pos.get_order();
            		order.destroy();
        		} 
        	} else{
        		this.gui.close_popup(); 
        	}
        },
    });
    gui.define_popup({name:'recharge_card_popup', widget: RechargeCardPopupWidget});

    var EditCardPopupWidget = PopupWidget.extend({
        template: 'EditCardPopupWidget',

        show: function(options){
            self = this;
            this._super();
            this.card_no = options.card_no || "";
            this.card_id = options.card_id || "";
            this.expire_date = options.expire_date || "";
            this.renderElement();
            $('#new_expire_date').focus();
            $('#new_expire_date').keypress(function(e){
                if( e.which == 8 || e.keyCode == 46 ) return true;
                return false;
            });
        },

        click_confirm: function(){
            var self = this;
            var new_expire_date = this.$('#new_expire_date').val();
            if(new_expire_date){
                if(self.card_no){
                    new Model("aspl.gift.card").get_func("write")(self.card_id,{'expire_date':new_expire_date})
                    .then(function(res){
                    	if(res){
                    		self.pos.gui.chrome.screens.giftcardlistscreen.reloading_gift_cards();
                    	}
                    });
                    this.gui.close_popup();
                }else{
                    alert(" Invalid card no.");
                }
            }else{
                alert(" Please select date.");
                $('#new_expire_date').focus();
            }
        },

        renderElement: function() {
            var self = this;
            this._super();
            $('.date').datepicker({
            	minDate: 0,
            	dateFormat:'yy/mm/dd',
            });
            self.$(".emptybox_time").click(function(){ $('#new_expire_date').val('') });
        },
    });

    gui.define_popup({name:'edit_card_popup', widget: EditCardPopupWidget});
    
    var ExchangeCardPopupWidget = PopupWidget.extend({
        template: 'ExchangeCardPopupWidget',

        show: function(options){
            self = this;
            this._super();
            this.card_no = options.card_no || "";
            this.card_id = options.card_id || "";
            this.renderElement();
            if(self.pos.config.manual_card_number){
            	$("#new_card_no").keypress(function (e) {
                    if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57) && e.which != 46) {
                        return false;
                   }
                });
            	$('#new_card_no').focus();
            } else{
            	$('#new_card_no').prop('disabled',true);
                var timestamp = new Date().getTime()/1000;
                $('#new_card_no').val(window.parseInt(timestamp));
            }
            
        },

        click_confirm: function(){
	        var self = this;
	        var move = true;
	        var new_card_no = $('#new_card_no').val();
	        if(new_card_no == self.card_no){
	        	alert("Card number can not be same");
	        	return;
	        }
	        if(new_card_no){
	        	new Model('aspl.gift.card').call('search_count', [[['card_no', '=', new_card_no]]], {}, {async: false})
                .then(function(gift_count){
                    if(gift_count > 0){
                        $('#new_card_no').css('border', 'thin solid red');
                        move = false;
                    } else{
                    	$('#new_card_no').css('border', '0px');
                    }
                });
	        	if(!move){
	        		alert("Card already exist");
	        		return
	        	} else{
	        		var exchange_card_no = confirm("Are you sure you want to change card number?");
				    if( exchange_card_no == true ){
				      new Model("aspl.gift.card").get_func("write")(self.card_id,{'card_no':new_card_no})
				      .then(function(res){
				    	   if(res){
				    		  self.pos.gui.chrome.screens.giftcardlistscreen.reloading_gift_cards();
				    	  }
				       });
				    }
	        	}
	        } else{
	        	alert("Invalid card number.");
	        }
		   this.gui.close_popup();
        },
    });
    gui.define_popup({name:'exchange_card_popup', widget: ExchangeCardPopupWidget});

    var MessageWidget = PosBaseWidget.extend({
        template:'MessageWidget',
        events: {
            "click .o_mail_channel_preview": "on_click_message_item",
            "click .pos-new_message": "on_click_new_message",
            "click .pos-filter": "on_click_filter",
        },
        renderElement: function(){
            var self = this;
            return this._super();
        },
        show: function(options){
            options = options || {};
            var self = this;
            this._super(options);
            this.list    = options.list    || [];
            this.renderElement();
        },
        on_click_new_message: function () {
	        this.gui.close_popup();
	        chat_manager.bus.trigger('open_chat');
        },
        on_click_filter: function (event) {
            event.stopPropagation();
            this.$(".pos-filter").removeClass('pos-selected');
            var $target = $(event.currentTarget);
            $target.addClass('pos-selected');
            this.filter = $target.data('filter');
            this.update_channels_preview();
        },
        update_channels_preview: function () {
            var self = this;
            this.$('.o_mail_navbar_dropdown_channels').html(QWeb.render('Spinner'));
             chat_manager.is_ready.then(function () {
                var channels = _.filter(chat_manager.get_channels(), function (channel) {
                    if (self.filter === 'chat') {
                        return channel.is_chat;
                    } else if (self.filter === 'channels') {
                        return !channel.is_chat && channel.type !== 'static';
                    } else {
                        return channel.type !== 'static';
                    }
                });
                chat_manager.get_channels_preview(channels).then(self._render_channels_preview.bind(self));
            });
        },
        _render_channels_preview: function (channels_preview) {
	        channels_preview.sort(function (c1, c2) {
	            return Math.min(1, c2.unread_counter) - Math.min(1, c1.unread_counter) ||
	                   c2.is_chat - c1.is_chat ||
	                   c2.last_message.date.diff(c1.last_message.date);
	        });
	        _.each(channels_preview, function (channel) {
	            channel.last_message_preview = chat_manager.get_message_body_preview(channel.last_message.body);
	            if (channel.last_message.date.isSame(new Date(), 'd')) {  // today
	                channel.last_message_date = channel.last_message.date.format('LT');
	            } else {
	                channel.last_message_date = channel.last_message.date.format('lll');
	            }
	        });
	        this.$('.o_mail_navbar_dropdown_channels').html(QWeb.render('mail.chat.ChannelsPreview', {
                channels: channels_preview,
            }));
	    },
        close: function(){
            if (this.$el) {
                this.$el.addClass('oe_hidden');
            }
        },
        on_click_message_item: function(event){
            event.stopPropagation();
            var $target = $(event.currentTarget);
            var channel_id = $target.data('channel_id');
            var channel = chat_manager.get_channel(channel_id);
                if (channel) {
                    this.gui.close_popup();
                    chat_manager.open_channel(channel);
                }
        },
    });
    gui.define_popup({name:'message', widget: MessageWidget});

    var GiftVoucherListScreenWidget = screens.ScreenWidget.extend({
        template: 'GiftVoucherListScreenWidget',

        init: function(parent, options){
            var self = this;
            this._super(parent, options);
            this.reload_btn = function(){
                $('.fa-refresh').toggleClass('rotate', 'rotate-reset');
                self.reloading_gift_vouchers();
            };
        },

        filter:"all",

        date: "all",

        start: function(){
            var self = this;
            this._super();
            var gift_vouchers = self.pos.get('gift_voucher_list');
            this.render_list(gift_vouchers);
            this.$('.back').click(function(){
                self.gui.back();
            });
            this.$('.button.create').click(function(){
                self.gui.show_popup('create_gift_voucher');
            });
            $('input#search_voucher_expiry_date').datepicker({
           		'dateFormat': 'yy-mm-dd',
               'autoclose': true,
               onSelect: function(dateText) {
                    if(dateText === ""){
	            		self.date = "all"
	            	}else {
	            		self.date = dateText;
	            	}
	            	self.render_list(gift_vouchers);
                },
            });

            //searchbox
            var search_timeout = null;
            if(this.pos.config.iface_vkeyboard && self.chrome.widget.keyboard){
                self.chrome.widget.keyboard.connect(this.$('.searchbox.voucher_search input'));
            }
            this.$('.searchbox.voucher_search input').on('keyup',function(event){
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });
            this.$('.searchbox.voucher_search .search-clear').click(function(){
                self.clear_search();
            });
        },

        show: function(){
            this._super();
            this.reload_gift_vouchers();
        },

        perform_search: function(query, associate_result){
            if(query){
                var gift_vouchers = self.pos.db.search_gift_vouchers(query);
                if ( associate_result && gift_vouchers.length === 1){
                    this.gui.back();
                }
                this.render_list(gift_vouchers);
            }else{
                var gift_vouchers = self.pos.get('gift_voucher_list');
                this.render_list(gift_vouchers);
            }
        },

        clear_search: function(){
            var gift_cards = this.pos.get('gift_voucher_list');
            this.render_list(gift_cards);
            this.$('.searchbox.voucher_search input')[0].value = '';
            this.$('.searchbox.voucher_search input').focus();
        },

        render_list: function(gift_vouchers){

    		var self = this;
            var contents = this.$el[0].querySelector('.giftvoucher-list-contents');
            contents.innerHTML = "";
            var temp = [];
            if(self.filter !== "" && self.filter !== "all"){
                gift_vouchers = $.grep(gift_vouchers,function(gift_voucher){
                    return gift_vouchers.state === self.filter;
                });
            }
            if(self.date !== "" && self.date !== "all"){
                var x = [];
                for (var i=0; i<gift_vouchers.length;i++){
                    var date_expiry = gift_vouchers[i].expiry_date;
                    if(self.date === date_expiry){
                        x.push(gift_vouchers[i]);
                    }
                }
                gift_vouchers = x;
            }
            for(var i = 0, len = Math.min(gift_vouchers.length,1000); i < len; i++){
                var gift_voucher    = gift_vouchers[i];
                gift_voucher.amount = parseFloat(gift_voucher.amount).toFixed(3);
                var clientline_html = QWeb.render('GiftVoucherlistLine',{widget: this, gift_voucher:gift_voucher});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                contents.appendChild(clientline);
            }
            $("table.giftvoucher-list").simplePagination({
                previousButtonClass: "btn btn-danger",
                nextButtonClass: "btn btn-danger",
                previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
                nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
                perPage: 10
            });
        },

        reload_gift_vouchers: function(){
            var self = this;
            var gift_vouchers = self.pos.get('gift_voucher_list');
            this.render_list(gift_vouchers);
        },

        reloading_gift_vouchers: function(){
            var self = this;
            return new Model('aspl.gift.voucher').get_func('search_read')()
            .then(function(result){
                self.pos.db.add_gift_vouchers(result);
                self.pos.set({'gift_voucher_list' : result});
                self.date = 'all';
                self.reload_gift_vouchers();
                return self.pos.get('gift_card_order_list');
            }).fail(function (error, event){
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                    self.gui.show_popup('error-traceback',{
                        message: error.data.message,
                        comment: error.data.debug
                    });
                }
                event.preventDefault();
                var gift_vouchers = self.pos.get('gift_voucher_list');
                console.error('Failed to send orders:', gift_cards);
                self.reload_gift_vouchers();
                return gift_vouchers
            });
        },

        renderElement: function(){
            var self = this;
            self._super();
            self.el.querySelector('.button.reload').addEventListener('click',this.reload_btn);
        },
    });

    gui.define_screen({name:'giftvoucherlistscreen', widget: GiftVoucherListScreenWidget});

	var LoginScreenWidget = screens.ScreenWidget.extend({
	    template: 'LoginScreenWidget',
	    init: function(parent, options){
	    	var self = this;
	        this._super(parent, options);
	        self.company_logo_src = $(self.pos.company_logo).attr('src');
	    },
	    start: function(){
	        var self = this;
	        this._super();
	        this.show_keyboard();
	        $('.button.login').click(function(){
	           var username = $("input.username").val();
	           var password = $("input.password").val();
	           var user;
	           if(username && password){
	                user = _.find(self.pos.users, function(obj) { return obj.login == username && obj.pos_security_pin == password })
	                if(user){
	                	self.pos.set_cashier(user);
	                	self.chrome.widget.username.renderElement()
	                    self.gui.show_screen("products");
	                    self.gui.set_default_screen('products');
	                }else{
	                	self.pos.db.notification('danger','Invalid Username or Pin!!!');
	                }
	           }
	        });
	        $('#close_login').click(function(){
	        	self.gui.show_popup('POS_session_config');
	        });
	        $('.password').keypress(function(e){
	        	if(e.keyCode == 13){
	        		$('.button.login').click();
	        	}
	        });
	    },
	    show: function(){
	    	var self = this;
	    	this._super();
	    	$('.pos').css('background','#E5E2CA');
	    	$('.pos .pos-topheader, #searchHeader').hide();
	    	$('.username').focus();
	    },
	    close: function(){
	        var self = this;
	    	this._super();
//	    	$('.pos').css({'background:#f0eeee'});
            $('.pos').css('background','#f0eeee');
	    	$('.pos .pos-topheader, #searchHeader').show();
	    },
	    show_keyboard : function() {
		    var selected_input;
		    if($("input.username").is(":focus")){
		        selected_input = $("input#usernametxt");
		    }

		    if($("input.password").is(":focus")){
		       selected_input = $("input#pwdtxt");
		    }

		    $( "input" ).focus(function() {
		        selected_input = $(this);
		    });

		    $('.number_pad_button').click(function(){
		    	var pres_char = $(this).html();
		    	if(!selected_input){
		    		return
		    	}
		        if($(this).hasClass("ac-clear-data")){
		            selected_input.val("");
		        }
		        else if($(this).hasClass( "back-button" )){
		            selected_input.val(selected_input.val().slice(0, -1));
		        }
		        else if($(this).hasClass("ac-submit-button")){

		        }
		        else if($(this).hasClass("login_space")){
		            selected_input.val(selected_input.val()+" ");
		        }
		        else{
		            selected_input.val(selected_input.val()+""+pres_char);
		        }
		    });
		    $(".change_char").click(function(){
		    	if(!selected_input){
		    		return
		    	}
		        $(".is_numpad").addClass("display_none");
		        $(".is_charpad").removeClass("display_none");
		        $(".is_smallcharpad").addClass("display_none")
		        $(".change_num").removeClass("display_none");
		        $(".change_char").addClass("display_none");
		        $(".change_smallChar").removeClass("display_none");
		    });
		    $(".change_num").click(function(){
		    	if(!selected_input){
		    		return
		    	}
		        $(".is_numpad").removeClass("display_none");
		        $(".is_charpad").addClass("display_none");
		        $(".is_smallcharpad").addClass("display_none")
		        $(".change_num").addClass("display_none")
		        $(".change_smallChar").addClass("display_none");
		        $(".change_char").removeClass("display_none");
		    });
		    $(".change_smallChar").click(function(){
		    	if(!selected_input){
		    		return
		    	}
		        if($( ".is_smallcharpad" ).hasClass( "display_none" )){
		            $(".is_numpad").addClass("display_none");
		            $(".is_charpad").addClass("display_none");
		            $(".is_smallcharpad").removeClass("display_none");
		            $(".change_smallChar").removeClass("display_none");

		        }else{
		            $(".is_charpad").removeClass("display_none");
		            $(".is_smallcharpad").addClass("display_none");
		        }
		    });
		},
    });
    gui.define_screen({name:'login', widget: LoginScreenWidget});

    var InternalTransferPopupWidget = PopupWidget.extend({
        template: 'InternalTransferPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this.picking_types = options.stock_pick_types || [];
            this.location = options.location || [];
            this._super(options);
            this.renderElement();
            var new_picking_types = [];
            var user_picking_ids = [];
            user_picking_ids = self.pos.get_cashier().allowed_picking_type_ids;
	        if(self.picking_types.length > 0){
	        	_.each(self.picking_types, function(picking_type){
	        		if($.inArray(picking_type.id, user_picking_ids) !== -1){
	        			new_picking_types.push('<option value="' + picking_type.id + '">' + picking_type.display_name + '</option>\n');
	        		}
	        	});
	            $('#pick_type').html(new_picking_types);
	        }
            var pick_type = Number($('#pick_type').val());
            var selected_pick_type = self.pos.db.get_picking_type_by_id(pick_type);
            if(selected_pick_type && selected_pick_type.default_location_src_id[0]){
            	$('#src_loc').val(selected_pick_type.default_location_src_id[0]);
            }
//            if(selected_pick_type && selected_pick_type.default_location_dest_id[0]){
//            	$('#dest_loc').val(selected_pick_type.default_location_dest_id[0]);
//            }
            $('#pick_type').change(function(){
            	var pick_type = Number($(this).val());
            	var selected_pick_type = self.pos.db.get_picking_type_by_id(pick_type);
            	if(selected_pick_type && selected_pick_type.default_location_src_id[0]){
                	$('#src_loc').val(selected_pick_type.default_location_src_id[0]);
                }
//            	if(selected_pick_type && selected_pick_type.default_location_dest_id[0]){
//                	$('#dest_loc').val(selected_pick_type.default_location_dest_id[0]);
//                }
            });
        },
        click_confirm: function(){
        	var self = this;
        	var selectedOrder = this.pos.get_order();
            var currentOrderLines = selectedOrder.get_orderlines();
            var moveLines = [];
            _.each(currentOrderLines,function(item) {
               var data = {}
               var lot_ids = [];
               _.each(item.pack_lot_lines.models, function(lot_line){
            	   if(lot_line.get('lot_id')){
            		   lot_ids.push(Number(lot_line.get('lot_id')));
            	   }
               });
               var nm = item.product.default_code ? "["+ item.product.default_code +"]"+ item.product.display_name  : "";
               data['product_id'] = item.product.id;
               data['name'] = nm || item.product.display_name;
               data['product_uom_qty'] = item.get_quantity();
               data['location_id'] =  Number($('#src_loc').val());;
               data['location_dest_id'] = self.pos.config.stock_location_id[0];
               data['product_uom'] = item.product.uom_id[0];
               moveLines.push(data);
            });
            var data = {}
            data['moveLines'] = moveLines;
            data['picking_type_id'] = Number($('#pick_type').val());
            data['location_src_id'] =  Number($('#src_loc').val());
            data['location_dest_id'] = self.pos.config.stock_location_id[0];
            data['state'] = $('#state').val();
        	new Model('stock.picking').call('do_detailed_internal_transfer',[[],{data:data}]).then(function(result){
        		if(result && result[0] && result[0]){
        			var url = window.location.origin + '#id=' + result[0].id + '&view_type=form&model=stock.picking';
        			self.pos.gui.show_popup('stock_pick', {'url':url, 'stock_data':result[0]});
        		}
        	});
        },
    });
    gui.define_popup({name:'int_trans_popup', widget: InternalTransferPopupWidget});

    var StockPickPopupWidget = PopupWidget.extend({
        template: 'StockPickPopupWidget',
        click_confirm: function(){
        	var self = this;
        	var order = self.pos.get_order();
            var lines = order.get_orderlines();
            if(lines.length>0){
            	for(var i=0; i<= lines.length + 1; i++){
            		_.each(lines,function(item){
            			order.remove_orderline(item);
            		});
            	}
            	for(var i=0; i<= lines.length + 1; i++){
            		_.each(lines,function(item){
            			order.remove_orderline(item);
            		});
            	}
            }
            this.gui.close_popup();
        },
        click_cancel: function(){
        	var self = this;
        	var order = self.pos.get_order();
        	var stock_data = self.options.stock_data
        	var print_stock_data = {};
        	if(stock_data){
        		new Model("stock.move").get_func("search_read")([['id', 'in', stock_data.move_lines]], []).then(
                function(movelines) {
                	if(movelines){
                		print_stock_data = {
            				'source_location_name':stock_data.location_id[1],
            				'dest_location_name':stock_data.location_dest_id[1],
            				'schedule_date':stock_data.max_date,
            				'ref':stock_data.display_name,
            				'movelines':movelines
                		}
                		order.set_print_stock_data(print_stock_data);
                		self.gui.show_screen('receipt');
                	}
                });
        	}
        }
    });
    gui.define_popup({name:'stock_pick', widget: StockPickPopupWidget});

    /* Split Product POPUP */
	var SplitProductPopup = PopupWidget.extend({
	    template: 'SplitProductPopup',
	    show: function(options){
	    	var self = this;
			this._super();
			var order    = self.pos.get_order();
            var lines    = order.get_orderlines();
			self.line_list = [];
            if(lines.length > 0) {
            	lines.map(function(line){
            		if(line && line.get_line_for_gift_receipt()){
            			self.line_list.push(line);
            		}
            	});
                order.set_num_of_line(self.line_list.length);
            }
			this.renderElement();
	    },
	    click_confirm: function(){
	    	var self = this;
	        this.gui.close_popup();
	    },
	    renderElement: function() {
            var self = this;
            this._super();
            var dict_data = {};
            var order = self.pos.get_order();
            if(order.get_gift_receipt_data()){
                $('#total_receipt').text("Total Gift Receipt: "+order.get_gift_receipt_data().length);
            } else{
                $('#total_receipt').text("Total Gift Receipt: "+'0');
            }
            $('.rand_number_text').keyup(function(){
            	$('div.split').trigger('click');
            });
            $('div.split').click(function(){
                dict_data = {};
            	var rand_number = Math.floor(Math.random() * 1000);
            	$.each($("input[class='select_chkbox']"), function(key,value){
                    if(!value){
                        return
                    }
                    var id = $(value).data('id');
                    var row = $('.popup-product-list-contents tr[data-id="'+ id +'"]');
                    if(value.checked){
                        if($(row).find("input.rand_number_text").val() == ""){
                            $(row).find("input.rand_number_text").val(rand_number);
                            var random_num = row.find("input.rand_number_text").val();
                        }
            		} else{
                        $(row).find("input.rand_number_text").val('');
                    }
         
    	    	});
                $.each($("input[class='select_chkbox']"), function(key,value){
                    if(value && value.checked){
                        var id = $(value).data('id');
                        var row = $('.popup-product-list-contents tr[data-id="'+ id +'"]');
                        var random_num = row.find("input.rand_number_text").val();
                        var orderline = order.get_orderline(id);
                        !dict_data.hasOwnProperty(random_num) ? dict_data[random_num]=[orderline] : dict_data[random_num].push(orderline);
                        orderline.set_line_random_number(random_num);
                    } else{
                        var id = $(value).data('id');
                        var row = $('.popup-product-list-contents tr[data-id="'+ id +'"]');
                        var random_num = row.find("input.rand_number_text").val();
                        var orderline = order.get_orderline(id);
                        orderline.set_line_random_number(random_num);
                    }

                    $('#total_receipt').text("Total Gift Receipt: "+Object.keys(dict_data).length);
                });
                var parent_list = [];
                var temp_data_list = [];
                $.each(dict_data, function(key,value){
                    var temp_line_list = [];
                    $.each(value, function(key,line){
                        var temp_data_list = []
                        temp_data_list.push(line.product.display_name);
                        if(line.product.uom_id[1] !== "Unit(s)"){
                            temp_data_list.push(line.quantityStr+' '+line.product.uom_id[1]);
                        } else{
                            temp_data_list.push(line.quantityStr);
                        }
                        temp_data_list.push(line.quantityStr);
                        temp_line_list.push(temp_data_list);
                    });
                    parent_list.push(temp_line_list);
                });
                order.set_gift_receipt_data(parent_list);
        	});
    	},
    	click_cancel: function(){
    		this.gui.close_popup();
    	},
	});
	gui.define_popup({name:'split_product_popup', widget: SplitProductPopup});

	var PackLotLinePopupWidget = PopupWidget.extend({
	    template: 'PackLotLinePopupWidget',
	    events: _.extend({}, PopupWidget.prototype.events, {
	        'click .remove-lot': 'remove_lot',
	        'click .select-lot': 'select_lot',
	        'keydown .popup-input': 'add_lot',
	        'blur .packlot-line-input': 'lose_input_focus',
	        'keyup .popup-search': 'seach_lot',
	    }),

	    show: function(options){
	        this._super(options);
	        this.focus();
	        var self = this;
	        var order = this.pos.get_order();
	        var serials = self.options.serials;
	        _.each(order.get_orderlines(),function(item) {
		        for(var i=0; i < item.pack_lot_lines.length; i++){
		        	var lot_line = item.pack_lot_lines.models[i];
	                if(serials.length != 0){
		                for(var j=0 ; j < serials.length ; j++){
		                	if(serials[j].name == lot_line.get('lot_name')){
		                		serials[j]['remaining_qty'] = serials[j]['remaining_qty'] - 1;
		                	}
		                }
	                }
		        }
            });
	        this.renderElement();
	    },

	    click_confirm: function(){
	        var pack_lot_lines = this.options.pack_lot_lines;
	        this.$('.packlot-line-input').each(function(index, el){
	            var cid = $(el).attr('cid'),
	                lot_name = $(el).val(),
	                lot_id = $(el).attr("lot_id");
	            var pack_line = pack_lot_lines.get({cid: cid});
	            	pack_line.set_lot_name(lot_name);
		            pack_line.set_lot_id(lot_id);
	        });
	        pack_lot_lines.remove_empty_model();
	        pack_lot_lines.set_quantity_by_lot();
	        this.options.order.save_to_db();
	        this.gui.close_popup();
	    },
	    click_cancel: function(){
	    	if(!this.pos.config.enable_pos_serial){
	    		this.gui.close_popup();
	    		return
	    	}
	    	var pack_lot_lines = this.options.pack_lot_lines;
	    	if(pack_lot_lines.length > 0){
	    		if(!confirm(_t("Are you sure you want to unassign lot/serial number(s) ?"))){
		    		return
		    	}
	    	}
	    	var self = this;
	        this.$('.packlot-line-input').each(function(index, el){
	            var cid = $(el).attr('cid'),
	                lot_name = $(el).val();
	            var lot_model = pack_lot_lines.get({cid: cid});
		        lot_model.remove();
		        var serials = self.options.serials;
	            for(var i=0 ; i < serials.length ; i++){
	            	if(serials[i].name == lot_name){
	            		serials[i]['remaining_qty'] = serials[i]['remaining_qty'] + 1;
	            		break
	            	}
	            }
	        });
	        var order = this.pos.get_order();
	        var order_line = order.get_selected_orderline();
	        self.renderElement()
	        this.gui.close_popup();
	    },
	    select_lot: function(ev) {
	    	var $i = $(ev.target);
            var data = $i.attr('data');
            var lot_id = $i.attr('lot_id');
            var add_qty = $(ev.currentTarget).find("input").val();
            var order = this.pos.get_order();
            var order_line = order.get_selected_orderline();
            if(data && add_qty){
            	for(var i=0; i< add_qty;i++){
                	this.focus();
        	    	this.$("input[autofocus]").val(data);
        	    	this.$("input[autofocus]").attr('lot_id', lot_id );
        	    	this.add_lot(false,true,lot_id);
                }
            }
	    },
	    add_lot: function(ev,val,lot_id) {
	        if ((ev && ev.keyCode === $.ui.keyCode.ENTER)|| val){
	            var pack_lot_lines = this.options.pack_lot_lines,
	                $input = ev ? $(ev.target) : this.$("input[autofocus]"),
	                cid = $input.attr('cid'),
	                lot_name = $input.val();
                var serials = this.options.serials;
                if(serials.length != 0){
                	var flag = true
	                for(var i=0 ; i < serials.length ; i++){
	                	if(serials[i].name == lot_name){
	                		if((serials[i]['remaining_qty'] - 1) < 0){
	                			flag = true;
	                		} else {
	                			if(serials[i].life_date){
	                				if(moment(new moment().add(this.pos.config.product_exp_days, 'd').format('YYYY-MM-DD HH:mm:mm')).format('DD/MM/YYYY') < moment(serials[i].life_date).format('DD/MM/YYYY')){
		                				serials[i]['remaining_qty'] = serials[i]['remaining_qty'] - 1;
			                			flag = false;
		                			}
	                			}else{
	                				serials[i]['remaining_qty'] = serials[i]['remaining_qty'] - 1;
		                			flag = false;
	                			}
	                		}
	                		break
	                	}
	                }
	                if(flag){
	                	$input.css('border','5px solid red');
	                	$input.val('');
	                	return
	                }
                }
	            var lot_model = pack_lot_lines.get({cid: cid});
	            lot_model.set_lot_name(lot_name);  // First set current model then add new one
	            if(lot_id){
	            	lot_model.set_lot_id(lot_id);
	            }
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
	            cid = $input.attr('cid'),
	        	lot_name = $input.val();
	        if(lot_name){
	        	var lot_model = pack_lot_lines.get({cid: cid});
		        lot_model.remove();
		        pack_lot_lines.set_quantity_by_lot();
		        var serials = this.options.serials;
	            for(var i=0 ; i < serials.length ; i++){
	            	if(serials[i].name == lot_name){
	            		serials[i]['remaining_qty'] = serials[i]['remaining_qty'] + 1;
	            		break
	            	}
	            }
		        this.renderElement();
	        }
	    },
	    seach_lot: function(ev){
	    	var self = this;
	    	var valThis = $(ev.target).val().toLowerCase();
	    	var sr_list = [];
	        $('.select-lot').each(function(){
	        	var text = $(this).attr('data');
		        (text.indexOf(valThis) == 0) ? sr_list.push(text) : "";
		    });
	        var serials = this.options.serials;
	        var sr = [];
	        var all_sr = [];
            for(var i=0 ; i < serials.length ; i++){
            	if($.inArray(serials[i].name, sr_list) !== -1 && serials[i].remaining_qty > 0){
            		sr.push(serials[i]);
            	}
            	if(serials[i].remaining_qty > 0){
            		all_sr.push(serials[i])
            	}
            }
            if(sr.length != 0 && valThis != ""){
            	this.render_list(sr);
            } else {
            	this.render_list(all_sr);
            }
	    },
	    render_list: function(orders){
	    	if(!orders){
	    		return
	    	}
        	var self = this;
            var contents = $('.serial-list-contents');
            contents.html('');
            var temp = [];
            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
                var serial    = orders[i];
            	var clientline_html = QWeb.render('listLine',{widget: this, serial:serial});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                contents.append(clientline);
            }
            $("#lot_list").simplePagination({
				previousButtonClass: "btn btn-danger",
				nextButtonClass: "btn btn-danger",
				previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
				nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
				perPage:10
			});
        },
	    lose_input_focus: function(ev){
	        var $input = $(ev.target),
	            cid = $input.attr('cid');
	        var lot_model = this.options.pack_lot_lines.get({cid: cid});
	        lot_model.set_lot_name($input.val());
	    },
	    
	    renderElement: function(){
	    	this._super();
	    	var serials = this.options.serials;
	    	var serials_lst = []
	    	if(serials){
	    		for(var i=0 ; i < serials.length ; i++){
	            	if(serials[i].remaining_qty > 0){
	            		serials_lst.push(serials[i])
	            	}
	            }
		    	this.render_list(serials_lst);
	    	}
	    },
	    focus: function(){
	        this.$("input[autofocus]").focus();
	        this.focus_model = false;   // after focus clear focus_model on widget
	    }
	});
	gui.define_popup({name:'packlotline', widget:PackLotLinePopupWidget});

	var CustomDiscountPopup = PopupWidget.extend({
		template: 'CustomDiscountPopup',
		show: function(){
			var self = this;
			this._super();
			$('#discount_fix').focus();
			$('#custom_discount_type').on('change',function(e){
				if($(this).val() == 'percent'){
					$('#discount_fix').hide();
					$('#discount_fix').val('')
					$('#discount').show();
					$('#discount').focus();
				}
				if($(this).val() == 'fixed'){
					$('#discount').hide();
					$('#discount').val('')
					$('#discount_fix').show();
					$('#discount_fix').focus();
				}
			})
		},
		click_confirm: function(){
			var self = this;
			var per = parseFloat($('#discount').val());
			var fix = parseFloat($('#discount_fix').val());
			var order = self.pos.get_order();
			var orderlines = order.get_orderlines();
			if(!per && !fix || per > 100  || (per <= 0 || fix <= 0)){
				alert("Input valid discount percentage!")
			} else{
				if($('#custom_discount_type').val() == 'percent'){
					_.each(orderlines, function(orderline){
						if(orderline.get_discount()){
							var unit_discounted_price = orderline.get_base_price() / orderline.quantity;
							orderline.set_unit_discounted_price(unit_discounted_price);
							orderline.set_previous_discount(orderline.get_discount());
							orderline.set_discount(0);
						}
						orderline.set_share_discount(per);
						var disc_amount = orderline.get_unit_price() * per / 100;
						disc_amount = round_di(disc_amount,3);
//						orderline.set_unit_price(orderline.get_unit_price()-disc_amount);
						if(orderline.get_unit_discounted_price()){
							var previous_disc_amount = orderline.get_unit_discounted_price() * per / 100;
							orderline.set_share_discount_amount(previous_disc_amount);
							orderline.set_globle_discount_amount(previous_disc_amount);
						} else{
							orderline.set_share_discount_amount(disc_amount);
							orderline.set_globle_discount_amount(disc_amount);
						}
						if(orderline.get_previous_discount()){
							orderline.set_discount(orderline.get_previous_discount());
						}
					});
				} else {
					var fix_frm_per = fix / order.get_total_without_tax() * 100;
					fix_frm_per = round_di(fix_frm_per,3);
					var without_discount_total = order.get_total_with_tax() - fix;
					var total_line_discount = 0;
					var unbalanced_disc = 0;
					if(orderlines.length > 1){
						for (var i=0;i<orderlines.length-1;i++){
							if(orderlines[i].get_discount()){
								var unit_discounted_price = orderlines[i].get_base_price() / orderlines[i].quantity;
								orderlines[i].set_unit_discounted_price(unit_discounted_price);
								orderlines[i].set_previous_discount(orderlines[i].get_discount());
								orderlines[i].set_discount(0);
							}
							orderlines[i].set_share_discount(fix_frm_per);
							var disc_amount = orderlines[i].get_unit_price() * fix_frm_per / 100;
							disc_amount = round_di(disc_amount,3);
							if(orderlines[i].get_unit_discounted_price()){
								var previous_disc_amount = orderlines[i].get_unit_discounted_price() * fix_frm_per / 100;
								orderlines[i].set_share_discount_amount(previous_disc_amount);
								orderlines[i].set_globle_discount_amount(previous_disc_amount);
							} else{
								orderlines[i].set_share_discount_amount(disc_amount);
								orderlines[i].set_globle_discount_amount(disc_amount);
							}
							if(orderlines[i].get_previous_discount()){
								orderlines[i].set_discount(orderlines[i].get_previous_discount());
							}
							var line_discount = orderlines[i].get_share_discount_amount() * orderlines[i].quantity;
							total_line_discount = total_line_discount + round_di(line_discount,3)
						}
						var last_orderline = order.get_last_orderline();
						if(last_orderline.get_discount()){
							var unit_discounted_price = last_orderline.get_base_price() / last_orderline.quantity;
							last_orderline.set_unit_discounted_price(unit_discounted_price);
							last_orderline.set_previous_discount(last_orderline.get_discount());
							last_orderline.set_discount(0);
						}
						if(fix > total_line_discount){
							var remaining_discount = round_di(fix - total_line_discount,3);
							if(last_orderline.quantity > 1){
								remaining_discount = remaining_discount/last_orderline.quantity;
							}
							last_orderline.set_share_discount(fix_frm_per);
							last_orderline.set_share_discount_amount(remaining_discount);
						} else if(fix < total_line_discount){
							var remaining_discount = round_di(total_line_discount - fix,3);
							if(last_orderline.quantity > 1){
								remaining_discount = remaining_discount/last_orderline.quantity;
							}
							last_orderline.set_share_discount_amount(remaining_discount);
							last_orderline.set_share_discount(fix_frm_per);
						}
						if(last_orderline.get_previous_discount()){
							last_orderline.set_discount(last_orderline.get_previous_discount());
						}
					} else {
						var selected_line = order.get_selected_orderline();
						var fix_frm_per = fix / order.get_total_without_tax() * 100;
						if(selected_line && selected_line.get_discount()){
							var unit_discounted_price = selected_line.get_base_price() / selected_line.quantity;
							selected_line.set_unit_discounted_price(unit_discounted_price);
							selected_line.set_previous_discount(selected_line.get_discount());
							selected_line.set_discount(0);
						}
						var disc_amount = selected_line.get_unit_price() * fix_frm_per / 100;
//						disc_amount = round_di(disc_amount,3);
						selected_line.set_share_discount(fix_frm_per);
						selected_line.set_share_discount_amount(disc_amount);
						if(selected_line.get_previous_discount()){
							selected_line.set_discount(selected_line.get_previous_discount());
						}
					}
				}
			}
			self.gui.close_popup();
		},
		click_cancel: function(){
			var self = this;
			self._super();
			self.gui.current_screen.order_widget.numpad_state.reset();
		}
	});
	gui.define_popup({name:'custom_discount_popup',widget:CustomDiscountPopup });

	device.ProxyDevice.include({
	    print_receipt: function(receipt) {
	        this._super(receipt);
	        this.pos.old_receipt = receipt || this.pos.old_receipt;
	    },
	});
});
