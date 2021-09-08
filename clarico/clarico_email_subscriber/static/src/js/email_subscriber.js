odoo.define('clarico_email_subscriber.email_subscriber', function (require) {
	'use strict';
	
var ajax = require('web.ajax');
var utils = require('web.utils');
var core = require('web.core');
var Widget = require('web.Widget');
var base = require('web_editor.base');
var website = require('website.website');

var QWeb = core.qweb;
var session_uid = 0;

ajax.jsonRpc('/web/dataset/call-public', 'call', {
    'model': 'ir.ui.view',
    'method': 'read_template',
    'args': ['clarico_email_subscriber.clarico_email_subscriber_popup', base.get_context()]
}).done(function (data) {
    QWeb.add_template(data);
});

ajax.jsonRpc("/web/session/email_subscriber/get_session_info", "call").then(function (session) {
	session_uid=session.uid;
});

var Email_popup = Widget.extend({
	template: 'clarico_email_subscriber.clarico_email_subscriber_popup',
    events: {
        'click .close': 'close',
    },
    start: function () {
    	var self=  this;

    	setTimeout(function () { self.$el.addClass('in');}, 0);
        
        
        this.keydown_escape = function (event) { 
            if (event.keyCode === 27) {
                self.close();
            }
        };
        $(document).on('keydown', this.keydown_escape);
        
		ajax.jsonRpc('/website_mass_mailing/get_content', 'call', {
            newsletter_id: self.$el.data('list-id')
        }).then(function (data) {
            self.$el.find('input.popup_subscribe_email').val(data.email || "");
            self.redirect_url = data.redirect_url;
            if (!data.is_subscriber) {
                self.$el.find('.popup_subscribe_btn').on('click', function (event) {
                    event.preventDefault(data.email);
                    self.on_click_subscribe();
                });
            }
        });
		
		//Popup-box No Thanks Button
		var $thanks_btn = self.$el.find('#no_thanks');
		if ($thanks_btn.length){
			$thanks_btn.on('click', function(event){
				event.preventDefault();
				self.setEmailCookie('No Thanks Button');
				location.reload();
			});
		}
    },
    on_click_subscribe: function () {
        var self = this;
        var $email = self.$el.find(".popup_subscribe_email:visible");

        if ($email.length && !$email.val().match(/.+@.+/)) {
            self.$el.addClass('has-error');
            return false;
        }
        self.$el.removeClass('has-error');

        ajax.jsonRpc('/website_mass_mailing/subscribe', 'call', {
            'list_id': self.$el.data('list-id'),
            'email': $email.length ? $email.val() : false
        }).then(function (subscribe) {
        	self.$el.find(".popup_subscribe_email, .input-group-btn").addClass("hidden");
        	self.$el.find(".alert").removeClass("hidden");
        
        	self.setEmailCookie($email.length ? $email.val() : 'public@clarico');
            
        	if (self.redirect_url) {
                if (_.contains(self.redirect_url.split('/'), window.location.host) || self.redirect_url.indexOf('/') === 0) {
                    window.location.href = self.redirect_url;
                } else {
                    window.open(self.redirect_url, '_blank');
                }
            }
        });
    },
    setEmailCookie: function (email) {
    	var email_val = email.length ? email : 'public@clarico'
    	var date = new Date();   
    	date.setTime(date.getTime()+(30*24*60*60*1000)); 
    	var expires = "expires=" + date.toGMTString();
    	document.cookie = "subscriber_popup-"+session_uid+"=" + email_val + ";" + expires;
    },
    click: function (event) {
    	if (!$(event.target).closest("#EmailSubscriberModal > *").length){
			this.close();
		}
    },
    close: function () {
    	var self = this;
        setTimeout(function () {self.destroy();}, 500);
    },
});
	
function email_popupError(message) {
    var _t = core._t;

    if (message.indexOf('lessc')) {
        message = '<span class="text-muted">' + message + "</span><br/><br/>" + _t("Please install or update node-less");
    }

    website.error(_t("Theme Error"), message);
}

function email_subscriber() {
    if (Email_popup.open && !Email_popup.open.isDestroyed()) return;
    Email_popup.open = new Email_popup();
    Email_popup.open.appendTo("body");
    
    var error = window.getComputedStyle(document.body, ':before').getPropertyValue('content');
    if (error && error !== 'none') {
    	email_popupError(eval(error));
    }
}


function getCookie(uname) {
    var name = uname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ua = decodedCookie.split(';');
    for(var i = 0; i < ua.length; i++) {
        var u = ua[i];
        while (u.charAt(0) == ' ') {
            u = u.substring(1);
        }
        if (u.indexOf(name) == 0) {
            return u.substring(name.length, u.length);
        }
    }
    return "";
}

function getSessionCookie(uname) {
    var name = uname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ua = decodedCookie.split(';');
    for(var i = 0; i < ua.length; i++) {
        var u = ua[i];
        while (u.charAt(0) == ' ') {
            u = u.substring(1);
        }
        if (u.indexOf(name) == 0) {
            return u.substring(name.length, u.length);
        }
    }
    return "";
}
window.onload = function() {
	setTimeout(function(){
		var visited = getCookie("subscriber_popup-"+session_uid);
		if (! visited){
			ajax.jsonRpc('/website_mass_mailing/is_subscriber', 'call', {
	            list_id: 1,
	        }).always(function (data) {
	        	if(! data.is_subscriber){
	        		email_subscriber()
	        	}
	        });
		}
	},2000);
};	


return Email_popup;

});
