odoo.define('theme_clarico.editor_js',function(require) {
'use strict';

    var ajax = require('web.ajax');
    var core = require('web.core');
    var web_editor = require('web_editor.editor');
    var options = require('web_editor.snippets.options');
    var website = require('website.website');
    var qweb = core.qweb;
    var _t = core._t;
    
    var set_timer = options.Class.extend({
        popup_template_id: "editor_new_product_slider_template",
        popup_title: _t("Modify Time"),
        date_configure: function(type,value) {
            var self = this;
            if (type !== "click") return;
            var def = website.prompt({
                'id': this.popup_template_id,
                'window_title': this.popup_title,
                 'input': _t("Date"),
                 'init': function (date) {
                	 var $group = this.$dialog.find('div.form-group');
                	 $group.find('input').attr("placeholder","Time Format Ex. Oct 01, 2017 13:00:00")
                }
            });            
            def.then(function (date,$dialog) {
            	var dt = new Date(date);
            	var dts=(dt.toString());
            	if(dts == 'Invalid Date')
            		{
            			alert("Invalid Time Format. Please enter correct format of Time")
            			self.$target.attr("data-date","nan");
            			self.date_configure('click')
            		}
            	else
            		{
            			self.$target.attr("data-date", date);
            			$dialog.find('.btn-primary').trigger('click');
            		}
                
            });
            return def;
        },
        drop_and_build_snippet: function(){
  	      var self = this;
  	      this.date_configure('click').fail(function () {
			self.editor.on_remove($.Event( "click" ));
                      
  	      });
  	    },
  	    clean_for_save:function(){
  		      this.$target.empty();
  	    }
    });
    options.registry.js_timer = set_timer.extend({        
        cleanForSave: function(){
        	this.$target.empty();
        }
    });
});
    