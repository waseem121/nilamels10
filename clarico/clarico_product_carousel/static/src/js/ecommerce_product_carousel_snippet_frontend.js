odoo.define('website.snippets.animation', function (require) {
'use strict';
// First Execute
var ajax = require('web.ajax');
var core = require('web.core');
var base = require('web_editor.base');
var animation = require('web_editor.snippets.animation');
var wish = require('wishlist.wish');
var compare = require('compare.compare_product');
var rate= require('rate.getrate');
var quickview = require('quickview.gets_product');
var no_of_product;
var qweb = core.qweb;
/*-------------------------------------------------------------------------*/
animation.registry.js_get_objects = animation.Class.extend({
    selector : ".js_get_objects",

    start: function(){
      this.redrow();
    },
    stop: function(){
      this.clean();
    },

    redrow: function(debug){
      this.clean(debug);
      this.build(debug);
    },

    clean:function(debug){
      this.$target.empty();
    },
    
    
    apply_bxslider:function(debug){
    	var self = this;
    	var bxsliderCount = 0;
    	
    	$(".product_carousel_slider").each(function () {
    		
    			$(this).attr("id", "product_carousel_slider" + bxsliderCount);
    			var current_slider =$(this).parent("div.js_get_objects");
    			
    			var check_slider =(current_slider).hasClass('js_get_objects');
    			if (check_slider){
    				var no_of_carousel_slide=$(current_slider).attr('data-objects_in_slide');
    				if ($(window).width() < 450){
    					no_of_carousel_slide=1;
    			  	  	create_slider(no_of_carousel_slide,"#product_carousel_slider" + bxsliderCount );
    				}
    				else if ($(window).width() < 600) {
    					if (no_of_carousel_slide > 2){
    						no_of_carousel_slide=2;
    					}
    			  	  	create_slider(no_of_carousel_slide,"#product_carousel_slider" + bxsliderCount );
    			  	}
    			  	else if($(window).width() < 1200){
    			  		if (no_of_carousel_slide > 3){
    						no_of_carousel_slide=3;
    					}
    			  	  	create_slider(no_of_carousel_slide,"#product_carousel_slider" + bxsliderCount );
    			  	}
    			  	else{
    			  		create_slider(no_of_carousel_slide,"#product_carousel_slider" + bxsliderCount );
    			  	}
    			}
    			
    			bxsliderCount++;
    	});
    },
    
    build: function(debug)
    {
	  //$('.cus_theme_loader_layout').removeClass('hidden');
      var self = this,
      limit    = self.$target.data("objects_limit"),
      filter_id  = self.$target.data("filter_by_filter_id"),
      objects_in_slide = self.$target.data("objects_in_slide"),
      c_type = self.$target.data("c_type"),
      sale_label = self.$target.data("sale_label"),
      get_rating = self.$target.data("get_rating"),
      object_name = self.$target.data("object_name"),
      custom_controller = self.$target.data("custom_controller"),
      template = self.$target.data("template");
      $("#wait").css("display", "block");
      self.$target.attr("contenteditable","False");
      if(!objects_in_slide)objects_in_slide = 4;
      if(!c_type)c_type = 0;	
      if(!sale_label)sale_label = 0;
      if(!get_rating)get_rating = 0;
      if(!limit)limit = 10;
      if(!filter_id)filter_id = false;
      if(!template) template = 'clarico_product_carousel.clarico_product_carousel_snippet_heading';
	  var rpc_end_point = '/ecommerce_product_carousel_snippets/render';
	  if (custom_controller == '1'){
    	  rpc_end_point='/ecommerce_product_carousel_snippets/render/' + object_name;
      };
      

      function optionEnable()
      {
    	  	// for rating
    	  	if(get_rating==0)
				self.$target.find('.rating-block').css("display","none")
			else
				self.$target.find('.rating-block').css("display","block")
			
  	    	// for label
			if(sale_label==0)
				self.$target.find('.label-block').css("display","none")
			else
				self.$target.find('.label-block').css("display","block")
      }
      ajax.jsonRpc(rpc_end_point, 'call', {
        'template': template,
        'filter_id': filter_id,
        'objects_in_slide' : objects_in_slide,
        'limit': limit,
        'object_name':object_name,
      }).then(function(objects) {
    	  $(objects).appendTo(self.$target);
    	  if(c_type == 1)
    	 {
    		  // For apply bxslider
    		  self.apply_bxslider(objects);
    	    
    		  // For display block as option selection
    		  optionEnable()
    		  
    		  // For rating
    		  rate.get_stars();	
				
    		  // For Quick view	
    		  $(".add2quick").click(function(){
    			  $('.cus_theme_loader_layout').removeClass('hidden');
 	   				var pid = $(this).attr('data-id');
 	   				quickview.get_quickview(pid)
    		  })
     		 
    		  // For Get Product & its count which is in wish list
    		  wish.getwishproduct()
					
    		  //  For Add 2 wishlist click from Multi Cursoul wishlist
    		  var SCW=self.$target.find(".add2wish_SC")
    		  SCW.click(function()
    		{
					// For Loading Icon
					$('.cus_theme_loader_layout').removeClass('hidden');
					var pid = $(this).attr('data-id');
					wish.getwish(pid)
			})
       	     		
			// For Get ProductIds and count which compare
			compare.getcompareproduct();
				
			// For Add product into compare
			$(".add2compare").change(function() 
				{
					var chk_status="";
					if(this.checked)
						chk_status=true
					var pid = $(this).attr('data-id');
					compare.getcompare(pid,chk_status)
				});
    	 }
    	  // For Non - slider = Remove fun_slider_class & add non
    	 if(c_type == 0)
     	 {
    		 // For remove bxSlide class and add non
    		 self.$target.find("div[class='fun_slide_class']").removeClass("fun_slide_class").addClass('non')
    		 
    		// For display block as option selection
   		  optionEnable()
   		  
   		  // For rating
   		  rate.get_stars();	
				
   		  // For Quick view	
   		  $(".add2quick").click(function(){
   			  $('.cus_theme_loader_layout').removeClass('hidden');
	   				var pid = $(this).attr('data-id');
	   				quickview.get_quickview(pid)
   		  })
    		 
   		  // For Get Product & its count which is in wish list
   		  wish.getwishproduct()
					
   		  //  For Add 2 wishlist click from Multi Cursoul wishlist
   		  var SCW=self.$target.find(".add2wish_SC")
   		  SCW.click(function()
   		  {
					// For Loading Icon
					$('.cus_theme_loader_layout').removeClass('hidden');
					var pid = $(this).attr('data-id');
					wish.getwish(pid)
			})
      	     		
			// For Get ProductIds and count which compare
			compare.getcompareproduct();
				
			// For Add product into compare
			$(".add2compare").change(function() 
				{
					var chk_status="";
					if(this.checked)
						chk_status=true
					var pid = $(this).attr('data-id');
					compare.getcompare(pid,chk_status)
				});
    		
     	 }
      }).then(function(){
    	  self.loading(debug);
      }).fail(function(e) {
        return;
      });
    },
    
    loading: function(debug){
    	//function to hook things up after build    	
    }
});
	
});
