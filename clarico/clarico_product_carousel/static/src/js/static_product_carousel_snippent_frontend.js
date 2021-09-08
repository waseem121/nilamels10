odoo.define('website.snippets.animation', function (require) 
{
'use strict';
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

animation.registry.js_get_static_objects = animation.Class.extend
({
    selector : ".js_get_static_objects",
    start: function()
    {
      this.redrow();
    },
    stop: function(){
      this.clean();
    },

    redrow: function(debug)
    {
      this.clean(debug);
      this.build(debug);
    },

    clean:function(debug){
      this.$target.empty();
    },
    
    build: function(debug)
    {
		//$('.cus_theme_loader_layout').removeClass('hidden');
    	var self = this,
    	filter_id  = self.$target.data("filter_static_by_filter_id"),
        sale_label = self.$target.data("sale_label"),
        get_rating = self.$target.data("get_rating"),
    	template = self.$target.data("template");
    	$("#wait").css("display", "block");
        if(!template) template = 'clarico_product_carousel.clarico_product_carousel_static_carousel_snippet_heading';
        if(!sale_label)sale_label = 0;
        if(!get_rating)get_rating = 0;
        if(!filter_id)filter_id = false;
        var rpc_end_point = '/ecommerce_static_product_carousel_snippets/render';
        
        function optionEnable()
        {

      	  	if(get_rating==0)
  				self.$target.find('.rating-block').css("display","none")
  			else
  				self.$target.find('.rating-block').css("display","block")
  			
  			if(sale_label==0)
  				self.$target.find('.ribbon-wrapper').css("display","none")
  			else
  				self.$target.find('.ribbon-wrapper').css("display","block")
        }
        function getCommonfunction()
        {
        		optionEnable()

        		rate.get_stars();	
			
        		$(".add2quick").click(function(){
        			$('.cus_theme_loader_layout').removeClass('hidden');
	   				var pid = $(this).attr('data-id');
	   				quickview.get_quickview(pid)
        		})	
 				
        		wish.getwishproduct()
				
        		var MCW=self.$target.find(".add2wish_MC")
        		MCW.click(function()
        		{
        			$('.cus_theme_loader_layout').removeClass('hidden');
        			var pid = $(this).attr('data-id');
        			wish.getwish(pid)
        		});
		     
        		compare.getcompareproduct();
		
        		$(".add2compare").change(function() 
        		{	
        			var chk_status="";
        			if(this.checked)
        				chk_status=true
        			var pid = $(this).attr('data-id');
        			compare.getcompare(pid,chk_status)
        		});	
        }
        ajax.jsonRpc(rpc_end_point, 'call', {'template': template,'filter_id': filter_id,}).then(function(objects) 
        {
        	$(objects).appendTo(self.$target);
        	//$('.cus_theme_loader_layout').removeClass('hidden');
        	self.$target.find(".filter_static_title:first").addClass("active_tab")
        	var temp_id=self.$target.find(".filter_static_title:first").attr("data-id")
        	if(!temp_id)temp_id = false;
        	ajax.jsonRpc('/static_product_data', 'call', {'template': template,'temp_filter_id': temp_id,}).then(function(data) 
    		{	
        		var cont_tab=(self.$target).find(".contenttab")
        		$(cont_tab).html(data);
        		$('.cus_theme_loader_layout').addClass('hidden');
    			self.$target.find("div[class='fun_slide_class']").removeClass("fun_slide_class").addClass('non')
    			getCommonfunction()
     	  })
     	  $(".filter_static_title").click(function()
    	  {
				$('.cus_theme_loader_layout').removeClass('hidden');
    			var curr_tag=$(this);
    			var curr_tag_id=curr_tag.attr("data-id");
    			$(".filter_static_title").removeClass("active_tab")
    			curr_tag.addClass("active_tab")
    			ajax.jsonRpc('/static_product_data', 'call', {'template': template,'temp_filter_id': curr_tag_id}).then(function(data) 
    			{
    				var cont_tab=(self.$target).find(".contenttab")
    				$(cont_tab).html(data);
    				self.$target.find("div[class='fun_slide_class']").removeClass("fun_slide_class").addClass('non');
        			$(".non").addClass("zoom-animation");
    				setTimeout(function(){
    					$(".non").removeClass("zoom-animation");
    				},500);
    				getCommonfunction()		
    		  })
    	})	  	    
    }).then(function(){
  	  self.loading(debug);
    }).fail(function(e) {
      
    });
    },
    loading: function(debug){
    	//function to hook things up after build    	
    }
    
	});
});
