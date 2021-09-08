odoo.define('quickview.gets_product', function(require) {	
	
	"use strict";	
	var base = require('web_editor.base');	
	var ajax = require('web.ajax');	
	var utils = require('web.utils');	
	var core = require('web.core');	
	var _t = core._t;
	
	
	 // add website_sale & wishlist , compare and rating script for quick view
	 function addScript()
	 { 
	    var script=document.createElement('script');
	    script.type='text/javascript';
	    script.src="/clarico_quick_view/static/src/js/function_add.js";
	    var scriptwish=document.createElement('script');	    
	    scriptwish.type='text/javascript';	    
	    scriptwish.src="/clarico_quick_view/static/src/js/quick_wish_compare.js"; 	   	    
	    $("head").append(script);	    
	    $("head").append(scriptwish);
	  }
		
		function close_quickview()
		{                
			$('.mask').css("display","none");
			$('.mask_cover').css("display","none");
			$("script[src='/clarico_quick_view/static/src/js/function_add.js']").remove()
			$("script[src='/clarico_quick_view/static/src/js/quick_wish_compare.js']").remove()
			
		}
		function get_quickview(pid)
		{
				pid=pid;
				ajax.jsonRpc('/productdata', 'call', {'product_id':pid}).then(function(data) {
					
				$(".mask_cover").append(data)
				$(".mask").fadeIn();
				$('.cus_theme_loader_layout').addClass('hidden');
				$(".mask_cover").css("display","block");
		    	addScript();
		    	$(".close_btn").click(function()
		    	{
		    		close_quickview()
		    		$('.mask_cover').empty(data);
		    	});
		    	$(document).on( 'keydown', function(e)
		    	{
		    		if(e.keyCode === 27) 
		    		{
		    			if(data)
		    			{
		    				close_quickview()
		    				$('.mask_cover').empty(data);
		    			}
		    		}
		    	});
			});
		}
	$(".quick-view-a").click(function(){ 
			$('.cus_theme_loader_layout').removeClass('hidden');
			var pid = $(this).attr('data-id');
			get_quickview(pid)
			
	});
	
	return{
		get_quickview:get_quickview
	};
})
