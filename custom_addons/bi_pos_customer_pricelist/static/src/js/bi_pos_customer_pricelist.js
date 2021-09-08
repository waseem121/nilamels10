// bi_pos_customer_pricelist js
//console.log("custom callleddddddddddddddddddddd")
odoo.define('bi_pos_customer_pricelist.pos', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var Model = require('web.DataModel');
    var pos_pricelist;

    var _t = core._t;




    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var partner_model = _.find(this.models, function(model){ return model.model === 'res.partner'; });
            partner_model.fields.push('property_product_pricelist');
            //console.log("partner_modellllllllllllllllllllllllllllllllllll",partner_model)
            
            var pricelist_model = _.find(this.models, function(model){ return model.model === 'product.pricelist'; });
            pricelist_model.fields.push('id','name','currency_id','symbol');
            //console.log("pricelist_modellllllllllllllllllllllllll",pricelist_model)
            
            return _super_posmodel.initialize.call(this, session, attributes);
        },
        
    	/*push_order: function(order, opts){
            var self = this;
            var pushed = _super_posmodel.push_order.call(this, order, opts);
            
            var currentOrder = this.get_order();
            console.log("currentOrder   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", currentOrder);
            var client = order && order.get_client();
            console.log("selected_clientttttttttttttttttttttttttttt",client,order);
            if (client){
                var partner_pricelist_id = client.property_product_pricelist[0];
                console.log("222222222222222222222222 partner_pricelist_id", partner_pricelist_id,[currentOrder['sequence_number']]);
                var model1 = new Model('pos.order');
                model1.call('write', [currentOrder['sequence_number'], {'pricelist_id' : partner_pricelist_id}]).then(null);
            }
            return pushed;
        }*/
    });
    

   models.load_models({
        model: 'pos.order',
        fields: ['pricelist_id'],
        domain: null,
        loaded: function(self, pos_order) {
            //console.log("111111111111loadedddddddddddddddddddddddddddddddddddd",models);
            self.pos_order = pos_order;
            //console.log("***************self.pos_orderrrrrrrrrrrrrrrr", self.pos_order);
        },
    });
     
    models.load_models({
        model: 'product.pricelist',
        fields: ['id','name','currency_id'],
        //domain: function(self) { return [ ['currency_id', '=', self.currency.id] ]; },
        domain: null,
        loaded: function(self, pricelists) {
        	
        	var pos_pricelist;
        	var pos_pricelist_id = self.config.pricelist_id[0];
            self.db.get_pricelists_by_id = {};
            pricelists.forEach(function(pricelist) {
                self.db.get_pricelists_by_id[pricelist.id] = pricelist;
                if (pricelist.id == pos_pricelist_id) {
                    self.pricelist = pricelist;
                    pos_pricelist = pricelist;
                    //console.log("pricelist   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", pricelist);
                }
            });

            self.pricelists = pricelists;
            //console.log("222222222222222222222222 self.pos_orderrrrrrrrrrrrrrrr", pricelists);
        
        },
        
        
    });
    
    models.load_models({
        model: 'res.currency',
        //fields: ['id','name','currency_id'],
        domain: null,
        loaded: function(self, currencies) {
            self.currencies = currencies;
        },
    });
    

	models.load_models({
			model:  'product.product',
			fields: ['display_name', 'list_price','price','pos_categ_id', 'taxes_id', 'barcode', 'default_code',
			         'to_weight', 'uom_id', 'description_sale', 'description',
			         'product_tmpl_id','tracking'],
			order:  ['sequence','name'],
			domain: [['sale_ok','=',true],['available_in_pos','=',true]],
			context: function(self){ return { pricelist: self.pricelist.id, display_default_code: false }; },
			loaded: function(self, products){
				
				self.get_products = [];
            	self.get_products_by_id = [];
            	
				//self.db.get_products_by_id = {};
		       // products.forEach(function(product) {
		        //    self.get_products_by_id.push(product.id);
		       // });
		        
		        self.get_products = products;
		        products.forEach(function(product) {
		            self.get_products_by_id.push(product.id);
		        });
			    self.db.add_products(products);
                
			},   
	});
	
	

  //models.Order.extend
	var _super = models.Order.prototype;
    models.Order = models.Order.extend({
        
        // the client related to the current order.
		set_client: function(client){
		    //this.assert_editable();
		    var self = this;
		    var selected_pricelist = self.pos.pricelist;
		    //console.log("selected_pricelistttttttttttttttttttttttttttt",selected_pricelist);
		    _super.set_client.call(this, client);
		    //_super.set_client.call(this, client);
		    if (self.pos.chrome.screens != null) {
				if (client != null) {
		                var partner_pricelist_id = client.property_product_pricelist[0];
		                //console.log("partner_pricelist_id_iddddddddddddddd",partner_pricelist_id);
		                if (selected_pricelist.id != partner_pricelist_id) {
		                    self.get_final_pricelist = self.pos.db.get_pricelists_by_id[partner_pricelist_id]
		                    //console.log("222_clienttttttttttttttttttttttttttt",self.get_final_pricelist);
		                    self.pos.chrome.screens.clientlist.apply_pricelist();
		                } else {
		                	self.get_final_pricelist = self.pos.db.get_pricelists_by_id[partner_pricelist_id]
		                    //console.log("elseeeeeeeeee_clienttttttttttttttttttttttttttt",self.get_final_pricelist);
		                    self.pos.chrome.screens.clientlist.apply_pricelist();
		            }
                }
                _super.set_client.call(this, client);
               }  
		},
	
	});

	gui.Gui.prototype.screen_classes.filter(function(el) { return el.name == 'clientlist'})[0].widget.include({
		
		init: function(parent, options){
		    this._super(parent, options);
			
			
			this.apply_pricelist = function(){
			//apply_pricelist: function() {
		        var self = this;
		        //this._super();
		        var selectedOrder = this.pos.get_order();
		        //console.log("selewcted orderrrrrrrrrrrrrr",selectedOrder)
                
                
                var list_of_product = $('.product');
		        //console.log("##################list_of_product", list_of_product);
		        	
                var entered_partner;
                var partner_id = false
                if (selectedOrder.get_client() != null)
		            partner_id = selectedOrder.get_client();
		            //console.log("parterrrrrrrrrrrrrrrrrrr", partner_id);

		            (new Model('pos.order')).call('apply_customer_pricelist', [ partner_id ? partner_id.id : 0]).fail(function(unused, event) {
		                //alert('Connection Error. Try again later !!!!');
		            }).done(function(output) {
						//console.log("outputttttttttttttttttttttt", output, partner_id)
						
                   		//self.pos.get_products.forEach(function(product) {
                   		$.each(list_of_product, function(index, value) {
                   			//console.log("output[product.id][selectedOrder.get_final_pricelist.id]",output)
                   			
                   			var entered_pricelist_id = selectedOrder.get_final_pricelist.id;
						 	//console.log("entered_pricelist_iddddddddddddddddddddd",entered_pricelist_id)
						    var product = $(value).data('product-id');
						    //console.log("????????????????product????????????????",product, output[i]);
						    
						    
						    for (var i = 0; i < output.length; i++) {
								var new_pricelist = output[i][product][entered_pricelist_id];
								//console.log("##################new_pricelist", new_pricelist)
								
								var currency_sign = self.chrome.widget.order_selector.format_currency(new_pricelist);
								//console.log("currency_sign currency_sign currency_sign currency_sign",currency_sign)
								if (self.pos.db.product_by_id[product].to_weight)
								    currency_sign += '/Kg';
								    
								$(value).find('.price-tag').html(currency_sign);
								//console.log("***************************badhu j callllllllllll",value);
						    
								entered_partner = output;
							}
						});
						//selectedOrder.save_to_db();
						
						
						self.pos.get_products.forEach(function(product) {
						    for (var i = 0; i < entered_partner.length; i++) {
							  //console.log("objettttttttttttttttttttttttttttttttttttt",product)
						    							    
								var entered_pricelist_id = selectedOrder.get_final_pricelist.id;
								product.price = entered_partner[i][product.id][entered_pricelist_id];
						    }
				    	});
				    	
				    	self.pos.currencies.forEach(function(currency) {
				    		//console.log("currencyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",currency)
				    		var entered_currency_id = selectedOrder.get_final_pricelist.currency_id[0];
				    		
						    if (currency.id == entered_currency_id) {
						        self.pos.currency = currency;
						        //console.log("*************************currency",self.pos.currency)
						        self.pos.currency.decimals = currency.decimal_places;
						        //console.log("self.pos.currency.decimals^^^^^^^^^^^^^^^^^^^^^^^",self.pos.currency.decimals);
						        return true;
						    }
						});
				 		selectedOrder.save_to_db();   	
            	});
            	
       		 }
       		 
		},
		
		
		save_client_details: function(partner) {
		    var self = this;

		    var fields = {};
		    this.$('.client-details-contents .detail').each(function(idx,el){
		        fields[el.name] = el.value;
		    });
		    
			fields['property_product_pricelist'] = parseInt($("#entered_pricelist").val());
			//console.log("fffffffffffffffffffffffffffffffffffffffffiledss",fields)
			
		    if (!fields.name) {
		        this.gui.show_popup('error',_t('A Customer Name Is Required'));
		        return;
		    }

		    if (this.uploaded_picture) {
		        fields.image = this.uploaded_picture;
		    }

		    fields.id           = partner.id || false;
		    fields.country_id   = fields.country_id || false;
		    fields.barcode      = fields.barcode || '';

		    new Model('res.partner').call('create_from_ui',[fields]).then(function(partner_id){
		        self.saved_client_details(partner_id);
		    },function(err,event){
		        event.preventDefault();
		        self.gui.show_popup('error',{
		            'title': _t('Error: Could not Save Changes'),
		            'body': _t('Your Internet connection is probably down.'),
		        });
		    });
   		 },
        
        
    
	});
	
	

});
