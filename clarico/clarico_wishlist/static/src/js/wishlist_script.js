odoo.define('wishlist.wish', function(require) {
	"use strict";
	var base = require('web_editor.base');
	var ajax = require('web.ajax');
	var utils = require('web.utils');
	var core = require('web.core');
	var _t = core._t;
	var url=""
	
	function getwish(pid)
	{
		var pid = pid;
		ajax.jsonRpc('/wishlist_products', 'call',{'product_id' : pid}).then(function(data) 
				{
							
							if(data.user==false)
							{
								$('.login_modle').fadeIn();
								$('.cus_theme_loader_layout').addClass('hidden');
								$('.btnsubmit').click(function()
								{
											
											url =document.URL;
											var userid=$('.email-textbox').val();
											var pwd=$('.password-textbox').val();
											ajax.jsonRpc('/login_web', 'call', {'userid' :userid,'passwd':pwd}).then(function(data) 
											{
														if(data.loginstatus==true)
														{
															$('.login_modle').css("display","none")
															ajax.jsonRpc('/wishlist_products', 'call', {'product_id' : pid}).then(function(data) 
															{
																	window.location.href = url;
															})
														}
														else
														{
															$('.error').css("display","block")
															$('.error').html("Invalid email or Password.")
														}
											})
											
								})
							}
							else
							{
								var last_product=data.wish_product[data.wish_product.length-1];
								ajax.jsonRpc('/wish_product_alert', 'call', {'last_product_id' :last_product}).then(function(data) 
								{
									$('.boxalert').html(data)
									$(".boxalert").animate({
										//right : '250px',
										right : '0px',
									});
									setTimeout(function(){
											$(".boxalert").animate({
												right : '-250px'
											});
										},2000)
								});
								wishcount(data)
								$('.cus_theme_loader_layout').addClass('hidden');
							}
						})
						.fail(function(e)
						{
						$(".comparelist_error").html("Something has gone wrong. Please Try after Sometime");
						$(".comparelist_error").css("display","block");
						setTimeout(function(){
							$(".comparelist_error").css("display","None");
							},2000)
						$('.cus_theme_loader_layout').addClass('hidden')
						});
	}
	
	function getwishproduct()
	{
			ajax.jsonRpc('/wishlist_products', 'call', {}).then(
			function(data) 
			{
				
				if(data.user!=false)
				{
				wishcount(data)
				}
				if(data.user==false)
				{
					$(".apply-wishlist").css("display","none")
				}
				$('.cus_theme_loader_layout').addClass('hidden');
			});
	}
	
	function wishcount(data)
	{
		if(data.wishcount==0)
		{
			$(".wish_count").css("display","none")
			$(".apply-wishlist").css("display","none")
		}
		else
		{
			$(".wish_count").css("display","inline-block")
			$(".apply-wishlist").css("display","block")
		}
		$('.wish_count').html(data.wishcount)
		$(".product").css("display","none");
		for (var j = 0; j < data.wish_product.length; j++) 
		{
			var wish_pid = data.wish_product[j]
			$(".add2wish[data-id='" + wish_pid + "']").css("display","none")
			$(".add2wish_SC[data-id='" + wish_pid + "']").css("display","none")
			$(".add2wish_MC[data-id='" + wish_pid + "']").css("display","none")
			$(".in2wish[data-id='" + wish_pid + "']").css("display","block")
			$(".product[data-id='" + wish_pid + "']").css("display","block")
		}
	}	
	getwishproduct()
	
	$(".add2wish").click(function() 
	{
			
			$('.cus_theme_loader_layout').removeClass('hidden');
			var pid = $(this).attr('data-id');
			getwish(pid)
	});
	
	$(".apply-wishlist").click(function()
	{
		$('.cus_theme_loader_layout').removeClass('hidden');
		ajax.jsonRpc('/wishlist_products_popout', 'call', {}).then(function(data)
		{
			$(".common-continer").html(data);
			$(".common-main-div").css("display","block").addClass("zoom-fadein");
			$('.cus_theme_loader_layout').addClass('hidden');	
		})
		
	});
	
	$(".common-close-btn").click(function(){
		$(".common-continer").html("");
		$(".common-main-div").css("display","none");
	})
	
	$(document).on( 'keydown', function(e){
		if(e.keyCode === 27) {
			$(".common-continer").html("");
			$(".common-main-div").css("display","none");
		}
	});
	$(document).on( 'keydown', function(e){
		if(e.keyCode === 27) {
			$('.login_modle').css("display","none");
		}
	});
	$(".close-btn").click(function(){
		$('.login_modle').css("display","none");
	});
	
	return {
		getwish:getwish,
		getwishproduct:getwishproduct
	};
})
