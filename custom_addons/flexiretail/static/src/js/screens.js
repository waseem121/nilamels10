odoo.define('flexiretail.screens', function (require) {
	var screens = require('point_of_sale.screens');
	var gui = require('point_of_sale.gui');
	var Model = require('web.Model');
	var utils = require('web.utils');
	var PopupWidget = require('point_of_sale.popups');
	var models = require('point_of_sale.models');
    var basewidget = require('point_of_sale.BaseWidget');
    var core = require('web.core');
    var formats = require('web.formats');

    var round_pr = utils.round_precision;
    var round_di = utils.round_decimals;
    var QWeb = core.qweb;
    var _t = core._t;

//    var SaveDraftButton = screens.ActionButtonWidget.extend({
//	    template : 'SaveDraftButton',
//	    button_click : function() {
//	        var self = this;
//            var selectedOrder = this.pos.get_order();
//            selectedOrder.initialize_validation_date();
//            var currentOrderLines = selectedOrder.get_orderlines();
//            var orderLines = [];
//            var client = selectedOrder.get_client();
//            _.each(currentOrderLines,function(item) {
//                return orderLines.push(item.export_as_JSON());
//            });
//            if (orderLines.length === 0) {
//                return alert ('Please select product !');
//            } else {
//            	if(!selectedOrder.get_client()){
//            		self.gui.show_screen('clientlist');
//            		return
//            	}
//                var credit = selectedOrder.get_total_with_tax() - selectedOrder.get_total_paid();
//        		if (client && credit > client.remaining_credit_limit){
//                    self.gui.show_popup('max_limit',{
//                        remaining_credit_limit: client.remaining_credit_limit,
//                        draft_order: true,
//                    });
//                    return
//        	    } else {
//                    this.pos.push_order(selectedOrder);
//                    self.gui.show_screen('receipt');
//                }
//            }
//	    },
//	});

//    screens.define_action_button({
//	    'name' : 'savedraftbutton',
//	    'widget' : SaveDraftButton,
//	    'condition': function(){
//	        return this.pos.config.allow_reservation_with_no_amount;
//	    },
//	});

	/* Order list screen */
	var ReservedOrderListScreenWidget = screens.ScreenWidget.extend({
	    template: 'ReservedOrderListScreenWidget',

	    init: function(parent, options){
	    	var self = this;
	        this._super(parent, options);
	        this._filter_reserved_orders();
	        this.reload_btn = function(){
	        	$('.fa-refresh').toggleClass('rotate', 'rotate-reset');
	        	self.reloading_orders();
	        };
	    },
        _filter_reserved_orders: function(){
            var self = this;
            self.reserved_orders = []
            _.each(self.pos.get('pos_order_list'), function(order){
                if(order && (order.reserved || order.partial_pay)){
                    self.reserved_orders.push(order)
                }
            });
        },
        _get_reserved_orders: function(){
            if(this.reserved_orders.length > 0){
                return this.reserved_orders
            }
            return false
        },
        date: "all",

	    start: function(){
	    	var self = this;
            this._super();
            
            this.$('.back').click(function(){
                self.gui.show_screen('products');
            });

            var orders = self._get_reserved_orders()
            this.render_list(orders);

            $('input#datepicker').datepicker({
           	    dateFormat: 'yy-mm-dd',
                autoclose: true,
                closeText: 'Clear',
                showButtonPanel: true,
                onSelect: function (dateText, inst) {
                	var date = $(this).val();
					if (date){
					    self.date = date;
					    self.render_list(self._get_reserved_orders());
					}
				},
				onClose: function(dateText, inst){
                    if( !dateText ){
                        self.date = "all";
                        self.render_list(self._get_reserved_orders());
                    }
                }
            }).focus(function(){
                var thisCalendar = $(this);
                $('.ui-datepicker-close').click(function() {
                    thisCalendar.val('');
                    self.date = "all";
                    self.render_list(self._get_reserved_orders());
                });
            });

			this.$('.reserved-order-list-contents').delegate('.order-line td:not(.order_history_button)','click', function(event){
                var order_id = parseInt($(this).parent().data('id'));
                self.gui.show_screen('orderdetail', {'order_id': order_id});
			});

            //Pay due Amount
            this.$('.reserved-order-list-contents').delegate('#pay_due_amt','click',function(event){
            	var order_id = parseInt($(this).data('id'));
            	self.pay_order_due(order_id);

            });

            this.$('.reserved-order-list-contents').delegate('#cancel_order','click', function(event){
                var order = self.pos.get_order();
                var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_order_by_id(order_id);

                self.gui.show_popup("cancel_order_popup", { 'order': result });
            });

            this.$('.reserved-order-list-contents').delegate('#delivery_date','click', function(event){
                var order = self.pos.get_order();
                var order_id = parseInt($(this).data('id'));
                var result = self.pos.db.get_order_by_id(order_id);
                order.set_reserved_delivery_date(result.delivery_date);
                self.gui.show_popup("delivery_date_popup", { 'order': result, 'new_date': false });
            });

          //search box
            var search_timeout = null;
            if(this.pos.config.iface_vkeyboard && self.chrome.widget.keyboard){
            	self.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }
            this.$('.searchbox input').on('keyup',function(event){
                $(this).autocomplete({
                    source: self.search_list,
                    select: function (a, b) {
                        self.perform_search(b.item.value, true);
                    }
                })
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function(){
                    self.perform_search(query, event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
            
	    },
	    pay_order_due: function(order_id){
	        var self = this;
	        var result = self.pos.db.get_order_by_id(order_id);
	        if(!result){
	            new Model('pos.order').call('search_read', [[['id', '=', order_id], ['state', 'not in', ['draft']]]])
	            .then(function(order){
	                if(order && order[0])
	                    result = order[0]
	            });
	        }
            if(result.state == "paid"){
                alert("Sorry, This order is paid State");
                return
            }
            if(result.state == "done"){
                alert("Sorry, This Order is Done State");
                return
            }
            if (result && result.lines.length > 0) {
                var count = 0;
                var selectedOrder = self.pos.get_order();
                var currentOrderLines = selectedOrder.get_orderlines();
                if(currentOrderLines.length > 0) {
                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
                        _.each(currentOrderLines,function(item) {
                            currentOrderLines.remove_orderline(item);
                        });
                    }
                    for (var i=0; i <= currentOrderLines.length + 1; i++) {
                        _.each(currentOrderLines,function(item) {
                            currentOrderLines.remove_orderline(item);
                        });
                    }
                }
                if (result.partner_id && result.partner_id[0]) {
                    var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                }
                if(!result.partial_pay){
                    selectedOrder.set_reservation_mode(true);
                }
                selectedOrder.set_reserved_delivery_date(result.delivery_date);
                selectedOrder.set_client(partner);
                selectedOrder.set_pos_reference(result.pos_reference);
                selectedOrder.set_paying_due(true);
                if (result.lines) {
                        new Model("pos.order.line").get_func("search_read")([['id', 'in', result.lines]], []).then(
                            function(results) {
                             if(results){
                                 _.each(results, function(res) {
                                     var product = self.pos.db.get_product_by_id(Number(res.product_id[0]));
                                     if(product){
                                         var line = new models.Orderline({}, {pos: self.pos, order: selectedOrder, product: product});
                                         line.set_discount(res.discount);
                                         line.set_quantity(res.qty);
                                         line.set_unit_price(res.price_unit);
                                         selectedOrder.add_orderline(line);
                                         selectedOrder.select_orderline(selectedOrder.get_last_orderline());
                                     }
                                 });
                                var prd = self.pos.db.get_product_by_id(self.pos.config.prod_for_payment[0]);
                                if(prd && result.amount_due > 0){
                                    var paid_amt = result.amount_total - result.amount_due;
                                    selectedOrder.set_amount_paid(paid_amt);
                                    selectedOrder.add_product(prd,{'price':-paid_amt});
                                }
                                self.gui.show_screen('payment');
                             }
                        });
                     selectedOrder.set_order_id(order_id);
                }
                selectedOrder.set_sequence(result.name);
            }
	    },
	    show: function(){
	        this._super();
	        this.reload_orders();
	        $('.button.reserved').removeClass('selected').trigger('click');
	    },
	    perform_search: function(query, associate_result){
	        var self = this;
            if(query){
				var orders = this.pos.db.search_order(query);
				self.render_list(orders);
            }else{
                var orders = self._get_reserved_orders()
                this.render_list(orders);
            }
        },
        clear_search: function(){
            var orders = this._get_reserved_orders()
            this.render_list(orders);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
	    render_list: function(orders){
        	var self = this;
            var contents = this.$el[0].querySelector('.reserved-order-list-contents');
            contents.innerHTML = "";
            var temp = [];
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
                order.amount_total = parseFloat(order.amount_total).toFixed(3); 
            	var clientline_html = QWeb.render('ReservedOrderlistLine',{widget: this, order:order});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
                contents.appendChild(clientline);
            }
//            $("table.reserved-order-list").simplePagination({
//				previousButtonClass: "btn btn-danger",
//				nextButtonClass: "btn btn-danger",
//				previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
//				nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
//				perPage:self.pos.config.record_per_page > 0 ? self.pos.config.record_per_page : 10
//			});
        },
        reload_orders: function(){
        	var self = this;
        	self._filter_reserved_orders();
            var orders = self._get_reserved_orders()
            this.search_list = []
            _.each(self.pos.partners, function(partner){
                self.search_list.push(partner.name);
            });
            _.each(orders, function(order){
                self.search_list.push(order.display_name, order.pos_reference)
            });
            this.render_list(orders);
        },
	    reloading_orders: function(){
	    	var self = this;
            self.pos.load_new_orders();
            self.reload_orders();
	    },
	    renderElement: function(){
	    	var self = this;
	    	self._super();
	    	self.el.querySelector('.button.reload').addEventListener('click', this.reload_btn);
	    },
	});
	gui.define_screen({name:'reserved_orderlist', widget: ReservedOrderListScreenWidget});
	
	screens.PaymentScreenWidget.include({
        partial_payment: function() {
            var self = this;
            var currentOrder = this.pos.get_order();
            var client = currentOrder.get_client() || false;

            if(currentOrder.get_total_with_tax() > 0 && currentOrder.get_due() != 0){
                if(!currentOrder.get_reservation_mode()){
            	    currentOrder.set_partial_pay(true);
            	} else {
            	    currentOrder.set_draft_order(true);
            	}
				if(currentOrder.get_total_with_tax() > currentOrder.get_total_paid()
        			&& currentOrder.get_total_paid() != 0){
					var credit = currentOrder.get_total_with_tax() - currentOrder.get_total_paid();
					if (client && credit > client.remaining_credit_limit && !currentOrder.get_paying_due() && !currentOrder.get_cancel_order()){
						self.gui.show_popup('max_limit',{
							remaining_credit_limit: client.remaining_credit_limit,
							payment_obj: self,
						});
						return
					}
        	    }
            	if(currentOrder.get_reservation_mode() && !currentOrder.get_paying_due() && !currentOrder.get_cancel_order() && self.pos.config.enable_pos_welcome_mail){
            		currentOrder.set_fresh_order(true);
            	}

				if(!currentOrder.get_reserved_delivery_date()){
					self.gui.show_popup("delivery_date_popup", { 'payment_obj': self, 'new_date': true });
				} else {
					if(currentOrder.get_total_paid() != 0){
						this.finalize_validation();
					}
					$('.js_reservation_mode').removeClass('highlight');
				}
        	}
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('#partial_pay').click(function(){
            	if(self.pos.get_order().get_client()){
                	self.partial_payment();
                } else {
                	self.gui.show_screen('clientlist');
                }
            });
        },
        order_changes: function(){
            var self = this;
            this._super();
            var order = this.pos.get_order();
            var total = order ? order.get_total_with_tax() : 0;
            if(!order){
            	return
            } else if(order.get_due() == total || order.get_due() == 0){
            	self.$('#partial_pay').removeClass('highlight');
            } else {
            	self.$('#partial_pay').addClass('highlight');
            }
        },
        validate_order: function(force_validation){
        	this.pos.get_order().set_reservation_mode(false);
        	this._super(force_validation);
        },
        show: function(){
            var self = this;
            self._super();
            var order = self.pos.get_order();
            if(order.get_reservation_mode()){
                self.$('#partial_pay').show();
                self.$('#partial_pay').text("Reserve");
            } else {
                self.$('#partial_pay').text("Partial Pay");
            }
            if(order.get_total_with_tax() > 0){
                if((order.get_paying_due() || order.get_cancel_order())){
                    self.$('#partial_pay, .next').show();
                }
            } else {
                self.$('#partial_pay').hide();
                self.$('.next').show();
            }
            if((order.get_paying_due() || order.get_cancel_order())){
                self.$('#partial_pay').text("Pay");
            }
        },
        click_back: function(){
	        var self = this;
	        var order = this.pos.get_order();
	        if(order.get_paying_due() || order.get_cancel_order()){
                this.gui.show_popup('confirm',{
                    title: _t('Discard Sale Order'),
                    body:  _t('Do you want to discard the payment of POS '+ order.get_pos_reference() +' ?'),
                    confirm: function() {
                        order.finalize();
                    },
                });
	        } else {
	            self._super();
	        }
	    },
	    click_invoice: function(){
	        var order = this.pos.get_order();
	        if(order.get_cancel_order() || order.get_paying_due()){
	            return
	        }
	        this._super();
	    },
	    click_set_customer: function(){
	        var order = this.pos.get_order();
	        if(order.get_cancel_order() || order.get_paying_due()){
	            return
	        }
	        this._super();
	    },
    });
	
	screens.OrderWidget.include({
		set_value: function(val) {
			var order = this.pos.get_order();
			var line = order.get_selected_orderline();
	    	if ($.inArray(line && line.get_product().id,
	    	    [this.pos.config.prod_for_payment[0],
	    	    this.pos.config.refund_amount_product_id[0],
	    	    this.pos.config.cancellation_charges_product_id[0]]) == -1) {
	    		this._super(val)
	    	}
		},
	});

    var OrderDetailScreenWidget = screens.ScreenWidget.extend({
	    template: 'OrderDetailScreenWidget',
	     init: function(parent, options){
	        var self = this;
	        self._super(parent, options);
	    },
        show: function(){
            var self = this;
            self._super();

            var order = self.pos.get_order();
            var params = order.get_screen_data('params');
            var order_id = false;
            if(params){
                order_id = params.order_id;
            }
            if(order_id){
                self.clicked_order = self.pos.db.get_order_by_id(order_id)
            }
            this.renderElement();
            this.$('.back').click(function(){
                self.gui.back();
                if(params.previous){
                    self.pos.get_order().set_screen_data('previous-screen', params.previous);
                    if(params.partner_id){
                        $('.client-list-contents').find('.client-line[data-id="'+ params.partner_id +'"]').click();
                        $('#show_client_history').click();
                    }
                }

            });
            if(self.clicked_order){
				this.$('.pay').click(function(){
                    self.pos.gui.screen_instances.reserved_orderlist.pay_order_due(order_id)
                });
				var contents = this.$('.order-details-contents');
				contents.append($(QWeb.render('OrderDetails',{widget:this, order:self.clicked_order})));
				new Model('account.bank.statement.line').call('search_read',
				[[['pos_statement_id', '=', order_id]]], {}, {'async': true})
				.then(function(statements){
					if(statements){
						self.render_list(statements);
					}
				});
            }

        },
        render_list: function(statements){
            var contents = this.$el[0].querySelector('.paymentline-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(statements.length,1000); i < len; i++){
                var statement = statements[i];
                var paymentline_html = QWeb.render('PaymentLines',{widget: this, statement:statement});
                var paymentline = document.createElement('tbody');
                paymentline.innerHTML = paymentline_html;
                paymentline = paymentline.childNodes[1];
                contents.append(paymentline);
            }

        },
	});
	gui.define_screen({name:'orderdetail', widget: OrderDetailScreenWidget});

    screens.ClientListScreenWidget.include({
        show: function(){
            var self = this;
            this._super();
            var $show_customers = $('#show_customers');
            var $show_client_history = $('#show_client_history');
            if (this.pos.get_order().get_client() || this.new_client) {
                $show_client_history.removeClass('oe_hidden');
            }
            $show_customers.off().on('click', function(e){
                $('.client-list').removeClass('oe_hidden');
                $('#customer_history').addClass('oe_hidden')
                $show_customers.addClass('oe_hidden');
                $show_client_history.removeClass('oe_hidden');
            })
        },
        toggle_save_button: function(){
            var self = this;
            this._super();
            var $show_customers = this.$('#show_customers');
            var $show_client_history = this.$('#show_client_history');
            var $customer_history = this.$('#customer_history');
            var client = this.new_client || this.pos.get_order().get_client();
            if (this.editing_client) {
                $show_customers.addClass('oe_hidden');
                $show_client_history.addClass('oe_hidden');
            } else {
                if(client){
                    $show_client_history.removeClass('oe_hidden');
                    $show_client_history.off().on('click', function(e){
                        self.render_client_history(client);
                        $('.client-list').addClass('oe_hidden');
                        $customer_history.removeClass('oe_hidden');
                        $show_client_history.addClass('oe_hidden');
                        $show_customers.removeClass('oe_hidden');
                    });
                } else {
                    $show_client_history.addClass('oe_hidden');
                    $show_client_history.off();
                }
            }
        },
        _get_customer_history: function(partner){
            new Model('pos.order').call('search_read', [[['partner_id', '=', partner.id]]], {}, {async: false})
            .then(function(orders){
                if(orders){
                     var filtered_orders = orders.filter(function(o){return (o.amount_total - o.amount_paid) > 0})
                     partner['history'] = filtered_orders
                }

            })
        },
        render_client_history: function(partner){
            var self = this;
            var contents = this.$el[0].querySelector('#client_history_contents');
            contents.innerHTML = "";
            self._get_customer_history(partner);
            if(partner.history){
                for (var i=0; i < partner.history.length; i++){
                    var history = partner.history[i];
                    var history_line_html = QWeb.render('ClientHistoryLine', {
                        partner: partner,
                        order: history,
                        widget: self,
                    });
                    var history_line = document.createElement('tbody');
                    history_line.innerHTML = history_line_html;
                    history_line = history_line.childNodes[1];
                    history_line.addEventListener('click', function(e){
                        var order_id = $(this).data('id');
                        if(order_id){
                            var previous = self.pos.get_order().get_screen_data('previous-screen');
                            self.gui.show_screen('orderdetail', {
                                order_id: order_id,
                                previous: previous,
                                partner_id: partner.id
                            });
                        }
                    })
                    contents.appendChild(history_line);
                }
            }
        },
        render_payment_history: function(){
            var self = this;
            var $client_details_box = $('.client-details-box');
            $client_details_box.addClass('oe_hidden');
        }
	});
    var ProductManageListScreen = screens.ScreenWidget.extend({
	    template: 'ProductManageListScreen',
	    
	    init: function(parent, options){
	        var self = this;
	        self._super(parent, options);
	        self.pos_categories = self.pos.db.get_all_categories();
	        self.product_cat = self.pos.product_category;
	    },
	    show: function(){
            var self = this;
            self._super();
            this.renderElement();
            $('.next.serial_number_btn').hide();
            this.$('.back').click(function(){
                self.gui.back();
            });
            this.$('.new-product').click(function(){
                self.display_product_details('edit', {});
                $('.next.serial_number_btn').hide();
            });
            var products = this.pos.db.get_products_sorted(1000);
            this.render_list(products);

            this.$('.next.serial_number_btn').click(function(){
        		self.gui.show_popup('assign_serial_lot',{'product':self.new_product});
          	});

            this.$('.product-list-contents').delegate('.product-line','click',function(event){
            	self.line_select(event,$(this),parseInt($(this).data('id')));
            });
            var search_timeout = null;
            
            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }

            this.$('.searchbox input').on('keypress',function(event){
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
	    perform_search: function(query, associate_result){
	        var products;
	        if(query){
	            products = this.pos.db.search_product(query);
	            this.display_product_details('hide');
	            if ( associate_result && products.length === 1){
	                this.new_product = products[0];
	            }
	            this.render_list(products);
	        }else{
	            products = this.pos.db.get_products_sorted();
	            this.render_list(products);
	        }
	    },
	    clear_search: function(){
	        var products = this.pos.db.get_products_sorted(1000);
	        this.render_list(products);
	        this.$('.searchbox input')[0].value = '';
	        this.$('.searchbox input').focus();
	    },
	    render_list: function(products){
	        var contents = this.$el[0].querySelector('.product-list-contents');
	        contents.innerHTML = "";
	        for(var i = 0, len = Math.min(products.length,1000); i < len; i++){
	            var product    = products[i];
                var productline_html = QWeb.render('ProductLine',{widget: this, product:products[i]});
                var productline = document.createElement('tbody');
                productline.innerHTML = productline_html;
                productline = productline.childNodes[1];
	            contents.appendChild(productline);
	        }
	        $("table.product-list").simplePagination({
				previousButtonClass: "btn btn-danger",
				nextButtonClass: "btn btn-danger",
				previousButtonText: '<i class="fa fa-angle-left fa-lg"></i>',
				nextButtonText: '<i class="fa fa-angle-right fa-lg"></i>',
				perPage : 10
			});
	    },
	    line_select: function(event,$line,id){
	        var product = this.pos.db.get_product_by_id(id);
	        this.$('.product-list .lowlight').removeClass('lowlight');
	        if ( $line.hasClass('highlight') ){
//	        	$('.next.serial_number_btn').hide();
	            $line.removeClass('highlight');
	            $line.addClass('lowlight');
	            this.display_product_details('hide',product);
	        }else{
	            this.$('.product-list .highlight').removeClass('highlight');
	            var last_status_inv = self.pos.group_stock_production_lot;
	            $line.addClass('highlight');
	            var y = event.pageY - $line.parent().offset().top;
	            this.display_product_details('show',product,y);
	            if(last_status_inv){
	            	if(last_status_inv.group_stock_production_lot == 1){
	                	if(product.tracking != "none" && product.type != "service"){
	                		$('.next.serial_number_btn').show();
	                	} else{
	                		$('.next.serial_number_btn').hide();
	                	}
	                } else{
	                	$('.next.serial_number_btn').hide();
	                }
	            }
	            this.new_product = product;
	        }
	    },
	    display_product_details: function(visibility, product, clickpos){
	        var self = this;
	        var contents = this.$('.product-details-contents');
	        var parent   = this.$('.product-list').parent();
	        var scroll   = parent.scrollTop();
	        var height   = contents.height();
	        contents.off('click','.button.edit'); 
	        contents.off('click','.button.save'); 
	        contents.off('click','.button.undo'); 
	        contents.on('click','.button.edit',function(){ self.edit_product_details(product); });
	        contents.on('click','.button.save',function(){ self.save_product_details(product); });
	        contents.on('click','.button.undo',function(){ self.undo_product_details(product); });
	        this.editing_product = false;
	        this.uploaded_picture = null;
	        if(visibility === 'show'){
	            contents.empty();
	            contents.append($(QWeb.render('ProductDetails',{widget:this,product:product})));
	            var new_height   = contents.height();
	            if(!this.details_visible){
	                parent.height('-=' + new_height);
	                if(clickpos < scroll + new_height + 20 ){
	                    parent.scrollTop( clickpos - 20 );
	                }else{
	                    parent.scrollTop(parent.scrollTop() + new_height);
	                }
	            }else{
	                parent.scrollTop(parent.scrollTop() - height + new_height);
	            }
	            this.details_visible = true;
	        } else if (visibility === 'edit') {
	            this.editing_product = true;
	            contents.empty();
	            contents.append($(QWeb.render('ProductDetailsEdit',{widget:this,product:product})));
	            contents.find('input').blur(function() {
	                setTimeout(function() {
	                    self.$('.window').scrollTop(0);
	                }, 0);
	            });
	            $('.button.next.serial_number_btn').hide();
	            this.$('.detail.product-type').change(function(event){
	            	var val = $('.detail.product-type').val();
	            	if(val){
	            		if(val == "service"){
	            			$('.product-detail.tracking').hide();
	            		} else{
	            			$('.product-detail.tracking').show();
	            		}
	            	}
	            });
	            contents.find('.image-uploader').on('change',function(event){
	                self.load_image_file(event.target.files[0],function(res){
	                    if (res) {
	                        contents.find('.product-picture img, .product-picture .fa').remove();
	                        contents.find('.product-picture').append("<img src='"+res+"'>");
	                        contents.find('.detail.picture').remove();
	                        self.uploaded_picture = res;
	                    }
	                });
	            });
	        } else if (visibility === 'hide') {
	            contents.empty();
	            parent.height('100%');
	            if( height > scroll ){
	                contents.css({height:height+'px'});
	                contents.animate({height:0},400,function(){
	                    contents.css({height:''});
	                });
	            }else{
	                parent.scrollTop( parent.scrollTop() - height);
	            }
	            this.details_visible = false;
	        }
	    },
	    product_icon_url: function(id){
	        return '/web/image?model=product.template&id='+id+'&field=image_small';
	    },
	    edit_product_details: function(product) {
	        this.display_product_details('edit',product);
	    },
	    resize_image_to_dataurl: function(img, maxwidth, maxheight, callback){
	        img.onload = function(){
	            var canvas = document.createElement('canvas');
	            var ctx    = canvas.getContext('2d');
	            var ratio  = 1;
	            if (img.width > maxwidth) {
	                ratio = maxwidth / img.width;
	            }
	            if (img.height * ratio > maxheight) {
	                ratio = maxheight / img.height;
	            }
	            var width  = Math.floor(img.width * ratio);
	            var height = Math.floor(img.height * ratio);
	            canvas.width  = width;
	            canvas.height = height;
	            ctx.drawImage(img,0,0,width,height);
	            var dataurl = canvas.toDataURL();
	            callback(dataurl);
	        };
	    },
	    load_image_file: function(file, callback){
	        var self = this;
	        if (!file.type.match(/image.*/)) {
	            this.gui.show_popup('error',{
	                title: _t('Unsupported File Format'),
	                body:  _t('Only web-compatible Image formats such as .png or .jpeg are supported'),
	            });
	            return;
	        }
	        var reader = new FileReader();
	        reader.onload = function(event){
	            var dataurl = event.target.result;
	            var img     = new Image();
	            img.src = dataurl;
	            self.resize_image_to_dataurl(img,800,600,callback);
	        };
	        reader.onerror = function(){
	            self.gui.show_popup('error',{
	                title :_t('Could Not Read Image'),
	                body  :_t('The provided file could not be read due to an unknown error'),
	            });
	        };
	        reader.readAsDataURL(file);
	    },
	    save_product_details: function(product) {
	    	var self = this;
	        var fields = {};
	        this.$('.product-details-contents .detail').each(function(idx,el){
	            fields[el.name] = el.value || false;
	        });

	        if (!fields.name) {
	            this.gui.show_popup('error',_t('A Product Name Is Required'));
	            return;
	        }
	        
	        if (this.uploaded_picture) {
	            fields.image = this.uploaded_picture;
	        }
	        fields.id = product.id || false;
	        new Model('product.template').call('create_from_ui',[fields]).then(function(product_id){
	            
	        	self.saved_product_details(product_id);
	        },function(err,event){
	            event.preventDefault();
	            self.gui.show_popup('error',{
	                'title': _t('Error: Could not Save Changes'),
	                'body': _t('Your Internet connection is probably down.'),
	            });
	        });
	        
	    },
	    saved_product_details: function(product_id){
	        var self = this;
	        this.reload_products().then(function(){
	            var product = self.pos.db.get_product_by_id(product_id);
	            if (product) {
	                self.new_product = product;
	                self.display_product_details('show',product);
	                if(product.tracking != "none" && product.type != "service"){
	                	$(".button.next.serial_number_btn").show();
	                }
	            } else {
	            	self.display_product_details('hide');
	            }
	        });
	    },
	    reload_products: function(){
	        var self = this;
	        return this.pos.load_new_products().then(function(){
	        	self.render_list(self.pos.db.get_products_sorted(1000));
	        });
	    },
	    undo_product_details: function(product) {
	        if (!product.id) {
	            this.display_product_details('hide');
	        } else {
	            this.display_product_details('show',product);
	        }
	        if(product.type != "service" && product.tracking != "none"){
	        	$('.button.next.serial_number_btn').show();
	        }
	    },
	    close: function(){
	        this._super();
	    },
	    
	});
	gui.define_screen({name:'product_manage_list', widget: ProductManageListScreen});

//    aspl_pos_product_pack
    var PackListScreenWidget = screens.ScreenWidget.extend({
		template: 'PackListScreenWidget',

		init: function(parent, options){
		    var self = this;
			this._super(parent, options);
			var search_timeout  = null;
            this.search_handler = function(event){
                if(event.type == "keypress" || event.keyCode === 46 || event.keyCode === 8){
                    clearTimeout(search_timeout);

                    var searchbox = this;

                    search_timeout = setTimeout(function(){
                        self.pack_product_list_widget.perform_search(self.category, searchbox.value, event.which === 13);
                    },70);
                }
            };
            this.clear_search_handler = function(event){
                self.clear_search();
            };
		},
		start: function(){
            var self = this;
            this._super();
            self.category = this.pos.db.get_category_by_id(0);
            this.pack_product_list_widget = new PackProductListWidget(this,{
                check_product_action: function(line, operation=false){ self._pack_product(line, operation); },
                pack_product_list: self._get_pack_products(),
                update_qty: function(line){ self._update_pack_product(line) }
            });
            this.pack_product_list_widget.replace(this.$('.placeholder-PackProductListWidget'));
            this.cart_widget = new CartWidget(this,{});
            this.cart_widget.replace(this.$('.placeholder-CartWidget'));
        },
        _pack_product: function(line, operation){
            var self = this;
            if(!line){
                return;
            }
            this.cart_widget.render_line(line, operation);
        },
        _update_pack_product: function(line){
            var self = this;
            if(!line){
                return;
            }
            this.cart_widget.update_line(line);
        },
        _get_pack_products: function(){
            var product_list = this.pos.db.get_product_by_category(0);
            var pack_product_list = [];
            _.each(product_list, function(product){
                if(product.is_product_pack)
                    pack_product_list.push(product)
            });
            return pack_product_list;
        },
		show: function(){
            var self = this;
            this._super();
            this.$('.back').off().on('click', function(){
                self.gui.back();
            });
            this.$('.validate_cart').off().on('click', function(){
                if(!$.isEmptyObject(self.cart_widget.line)){
                    self.add_to_cart(self.cart_widget.line);
                }
            });
	        this.cart_widget.clear_cart();
	        this.pack_product_list_widget.renderElement();
            this.clear_search();
        },
        add_to_cart: function(lines){
            var self = this;
            var order = self.pos.get_order();
            _.each(lines, function(line){
               if(line.pack_products){
                    var product = self.pos.db.get_product_by_id(line.id);
                    if(product){
                        order.add_product(product, {price: line.price, quantity: line.qty, force_allow: true, pack_product:true})
                        order.get_selected_orderline().set_pack_products(line.pack_products);
                    }
               }
            });
            this.cart_widget.clear_cart();
            $('.product').removeClass('selected');
            self.gui.show_screen('products');
        },
        renderElement: function(){
            var self = this;
            this._super();
            this.el.querySelector('.searchbox input').addEventListener('keypress',this.search_handler);
            this.el.querySelector('.searchbox input').addEventListener('keydown',this.search_handler);
            this.el.querySelector('.search-clear').addEventListener('click',this.clear_search_handler);
        },
        clear_search: function(){
            var products = this.pos.db.get_product_by_category(this.category.id);
            var temp_products = [];
            _.each(products, function(product){
                if(product.is_product_pack){
                    temp_products.push(product);
                }
            })
            if(temp_products){
                this.pack_product_list_widget.set_pack_product_list(temp_products);
            }

            var input = this.el.querySelector('.searchbox input');
                input.value = '';
                input.focus();
        },
    });
    gui.define_screen({name:'pack_list', widget: PackListScreenWidget});

    var PackProductListWidget = basewidget.extend({
        template:'PackProductListWidget',
        init: function(parent, options){
            var self = this;
            this._super(parent,options);
            this.parent = parent;
            this.pack_product_list = options.pack_product_list;
            this.change_selection_handler = function(event){
                var parent = $(this).parent('.product')
                var product_id = $(parent).data('product-id');
                if(product_id){
                    var line = self._generate_line(product_id);
                    if(!$(parent).hasClass('selected')){
                        options.check_product_action(line);
                        $(parent).addClass('selected')
                    } else {
                        options.check_product_action(line, "remove");
                        $(parent).removeClass('selected');
                    }
                }
            };
            this.update_qty = function(ev){
	        	ev.preventDefault();
	            var $link = $(ev.currentTarget);
                var $input = $link.parent().parent().find("input");
                var min = parseFloat($input.data("min") || 0);
                var max = parseFloat($input.data("max") || Infinity);
                var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
                $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
                $('input[name="'+$input.attr("name")+'"]').val(quantity > min ? (quantity < max ? quantity : max) : min);
                $input.change();
                var val = $('input[name="'+$input.attr("name")+'"]').val();
                var line = self._generate_line($input.attr("name"))
                options.update_qty(line);
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
                var line = self._generate_line($(this).attr('name'))
                options.update_qty(line);
	        };
        },
        set_pack_product_list: function(product_list=[]){
            this.pack_product_list = product_list;
            this.renderElement();
        },
	    _generate_line: function(product_id){
	        var self = this;
	        var product = self.pos.db.get_product_by_id(product_id);
            if(product){
                var qty = $('.js_quantity[name="'+ product.id +'"]').val();
                var line = {
                    id: product.id,
                    product_name: product.display_name,
                    qty: qty,
                    price: product.price,
                    subtotal: product.price * qty,
                    pack_products: self.pos.pack_products[product.product_tmpl_id],
                };
                return line;
            }
            return false;
	    },

        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },
        get_product_image_url: function(product){
            return window.location.origin + '/web/image?model=product.product&field=image_medium&id='+product.id;
        },
        render_pack_product: function(product){
            var image_url = this.get_product_image_url(product);
            var product_html = QWeb.render('PackProduct',{
                    widget:  this,
                    product: product,
                    image_url: this.get_product_image_url(product),
                });
            var product_node = document.createElement('div');
            product_node.innerHTML = product_html;
            product_node = product_node.childNodes[1];
            return product_node;
        },
        renderElement: function() {
            var self = this;
            var el_str  = QWeb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
                el_node.innerHTML = el_str;
                el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;
            var list_container = el_node.querySelector('.pack-product-list');
            for(var i = 0, len = this.pack_product_list.length; i < len; i++){
                var product_node = this.render_pack_product(this.pack_product_list[i]);
                product_node.querySelector(':not(.input-group)').addEventListener('click',this.change_selection_handler);
                product_node.querySelector('span.input-group-addon .minus').addEventListener('click', this.update_qty);
                product_node.querySelector('span.input-group-addon .plus').addEventListener('click', this.update_qty);
                product_node.querySelector('div.input-group .js_quantity').addEventListener('input', this.keydown_qty);
                list_container.appendChild(product_node);
                if(self.parent.cart_widget && self.parent.cart_widget.line && self.parent.cart_widget.line[this.pack_product_list[i].id]){
                    $(product_node).addClass('selected');
                }
            }
        },
        perform_search: function(category, query, buy_result){
            var products;
            if(query){
                products = this.pos.db.search_product_in_category(category.id,query);
            }else{
                products = this.pos.db.get_product_by_category(category.id);
            }
            var temp_products = [];
            _.each(products, function(product){
                if(product.is_product_pack){
                    temp_products.push(product);
                }
            })
            if(temp_products){
                this.set_pack_product_list(temp_products);
            }
        },
    });
    var CartWidget = basewidget.extend({
        template:'CartWidget',
        init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            self.line = {};
            this.clear_cart_handler = function(){
                _.each(self.line, function(line){
                    self.render_line(line, "remove");
                })
            };
        },
        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },
        rerender_line: function(line){
	        var self = this;
	        var el_str  = QWeb.render('PackOrderLines',{widget:this, line:line});
            var el_ul = document.createElement('ul');
            el_ul.innerHTML = el_str;
            el_ul = el_ul.childNodes[1];
            el_ul.querySelector('.remove_line').addEventListener('click', function(e){
                self.render_line(line, "remove");
            });
            self.line[line.id] = line;
            return el_ul;
	    },
	    clear_cart: function(){
	        var contents = this.$el[0].querySelector('div.product_info ul');
	        $(contents).empty();
	        this.line = {};
	        this.update_summary();
//	        $('.validate_cart').removeClass('highlight');
	        $('.validate_cart').hide();
	    },
        render_line: function(line, operation=false){
            var self = this;
            var contents = this.$el[0].querySelector('div.product_info ul');
            if(operation && operation == "remove"){
                $('span.product[data-product-id="'+ line.id +'"]').removeClass('selected');
                delete self.line[line.id];
                $(contents).find('li[data-id="'+ line.id +'"]').remove();
                var line_count = $(contents).find('ul li').length;
                if(line_count < 1){
//                    $('.validate_cart').removeClass('highlight');
                	$('.validate_cart').hide();
                }
                self.update_summary()
                return
            }
            var el_ul = self.rerender_line(line);
            contents.appendChild(el_ul);
            var line_count = $(contents).find('ul li').length;
            if(line_count > 0){
            	$('.validate_cart').show();
                $('.validate_cart').addClass('highlight');
            }
            self.update_summary()
            this.el.querySelector('.product_info').scrollTop = 100 * line_count;
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
        _get_cart_total: function(){
            var self = this;
            var order_total = 0.00;
            _.each(self.line, function(line){
                order_total += line.subtotal
            })
            return order_total;
        },
        update_summary: function(){
            var self = this;
            var order_total = self._get_cart_total();
            this.el.querySelector('.pack_order_summary .order_total > .value').textContent = this.format_currency(order_total);
        },
        renderElement: function(){
            var self = this;
            this._super();
            this.el.querySelector('.clear_cart').addEventListener('click',this.clear_cart_handler);
        },
    });
});