odoo.define('quickview.gets_wishcompare', function(require) {	
	"use strict";	
	var base = require('web_editor.base');	
	var ajax = require('web.ajax');	
	var utils = require('web.utils');	
	var core = require('web.core');	
	var wish = require('wishlist.wish');
	var compare = require('compare.compare_product');
	var rate=require('rate.getrate')
	
	var _t = core._t;
				
				// For Getting ProductIds and count in wishlist
				wish.getwishproduct();
				// For Adding products into wishlist
				$("#wishlist_icon_div_quick_view >.add2wish").click(function()
				{
					 $('.cus_theme_loader_layout').removeClass('hidden');
					 var pid = $(this).attr('data-id');
					 wish.getwish(pid)
				});
				
				// For Getting ProductIds and count in compare
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
				
				// For Rating
				rate.get_stars();
});
