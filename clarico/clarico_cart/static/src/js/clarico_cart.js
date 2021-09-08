odoo.define('website_sale.cart', function (require) {
    "use strict";
    var base = require('web_editor.base');
    var core = require('web.core');
    var _t = core._t;

    var shopping_cart_link = $('#header-cart');
    var shopping_cart_link_counter;
    shopping_cart_link.popover({
        trigger: 'manual',
        animation: true,
        html: true,
        title: function () {
            return _t("My Cart");
        },
        container: 'body',
        placement: 'auto',
        template: '<div class="popover mycart-popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title chs_heading"></h3><div class="popover-content"></div></div>'
    }).on("mouseenter",function () {
        var self = this;
        clearTimeout(shopping_cart_link_counter);
        shopping_cart_link.not(self).popover('hide');
        shopping_cart_link_counter = setTimeout(function(){
            if($(self).is(':hover') && !$(".mycart-popover:visible").length)
            {
                $.get("/shop/cart", {'type': 'popover'})
                    .then(function (data) {
                        $(self).data("bs.popover").options.content =  data;
                        $(self).popover("show");
                        $(".popover").on("mouseleave", function () {
                            $(self).trigger('mouseleave');
                        });
                    });
            }
        }, 100);
    }).on("mouseleave", function () {
        var self = this;
        setTimeout(function () {
            if (!$(".popover:hover").length) {
                if(!$(self).is(':hover')) {
                   $(self).popover('hide');
                }
            }
        }, 1000);
    });
});

odoo.define('website_sale.clear_cart', function (require) {
	"use strict";
	var ajax = require('web.ajax');
	
	$( document ).ready(function() {
		$(".clear_shopping_cart").click(function (event) {
			event.preventDefault();
		 	ajax.jsonRpc("/shop/clear_cart", 'call', {})
	            .then(function (data) {
	            	window.location.reload(true);
	        });
	        
		});
		if($('#hiddencount').val() == "0"){
			$("#cart_total, .cart-total-heading").css("display","none");
			$("#right_column").css("display","none");
			$(".wizard-main-ul").css("display","none");
			$('.cart_margin_class').css("margin-top","0px");
		}
		$('#cart_total').removeClass('col-sm-4 col-sm-offset-8 col-xs-12');
		$('button.btn-primary').addClass('common-btn');
		$('button.btn-primary > span').css('font-family','oswald-regular');
		$('#cart_total').removeClass('col-sm-4 col-sm-offset-8 col-xs-12');
		
	});
	
});
odoo.define('website_sale.cart', function (require) {
    "use strict";
    var base = require('web_editor.base');
    var core = require('web.core');
    var _t = core._t;

    var shopping_cart_link = $('#header-cart');
    var shopping_cart_link_counter;
    shopping_cart_link.popover({
        trigger: 'manual',
        animation: true,
        html: true,
        title: function () {
            return _t("My Cart");
        },
        container: 'body',
        placement: 'auto',
        template: '<div class="popover mycart-popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title chs_heading"></h3><div class="popover-content"></div></div>'
    }).on("mouseenter",function () {
        var self = this;
        clearTimeout(shopping_cart_link_counter);
        shopping_cart_link.not(self).popover('hide');
        shopping_cart_link_counter = setTimeout(function(){
            if($(self).is(':hover') && !$(".mycart-popover:visible").length)
            {
                $.get("/shop/cart", {'type': 'popover'})
                    .then(function (data) {
                        $(self).data("bs.popover").options.content =  data;
                        $(self).popover("show");
                        $(".popover").on("mouseleave", function () {
                            $(self).trigger('mouseleave');
                        });
                    });
            }
        }, 100);
    }).on("mouseleave", function () {
        var self = this;
        setTimeout(function () {
            if (!$(".popover:hover").length) {
                if(!$(self).is(':hover')) {
                   $(self).popover('hide');
                }
            }
        }, 1000);
    });
});

odoo.define('website_sale.clear_cart', function (require) {
	"use strict";
	var ajax = require('web.ajax');
	
	$( document ).ready(function() {
		$(".clear_shopping_cart").click(function (event) {
			event.preventDefault();
		 	ajax.jsonRpc("/shop/clear_cart", 'call', {})
	            .then(function (data) {
	            	window.location.reload(true);
	        });
	        
		});
		if($('#hiddencount').val() == "0"){
			$("#cart_total").css("display","none");
			$("#right_column").css("display","none");
			$('.cart_margin_class').css("margin-top","0px");
		}
		$('#cart_total').removeClass('col-sm-4 col-sm-offset-8 col-xs-12');
		$('button.btn-primary').addClass('common-btn');
		$('button.btn-primary > span').css('font-family','oswald-regular');
	});
	
});
