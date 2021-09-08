odoo.define('snippet_style_2.front_js',function(require){
'use strict';

  var animation = require('web_editor.snippets.animation');
  var ajax = require("web.ajax");
  
  animation.registry.js_timer = animation.Class.extend({
    selector : ".js_timer",
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
      build: function(debug)
      {
    	  var self = this;
    	  var date = self.$target.data("date");
    	
    	  ajax.jsonRpc("/timer/render", 'call').then(function(objects) {
    		  $(objects).appendTo(self.$target);
        	  //self.$target.html("dsffsdf");
        	  if(date != "nan")
        	  {
    		  var countDownDate = new Date(date).getTime();
    		  var x = setInterval(function() {
    				
    				// Get todays date and time
    				var now = new Date().getTime();
    				
    				// Find the distance between now an the count down date
    				var distance = countDownDate - now;// Time calculations for days, hours, minutes and seconds
    				
    				
    				if (distance > 0) {
    						var days = Math.floor(distance / (1000 * 60 * 60 * 24));
    						var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    						var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    						var seconds = Math.floor((distance % (1000 * 60)) / 1000);
    						
    						if ((seconds+'').length == 1) {
    							seconds = "0" + seconds;
    						}
    						if ((days+'').length == 1) {
    							days = "0" + days;
    						}
    						if ((hours+'').length == 1) {
    							hours = "0" + hours;
    						}
    						if ((minutes+'').length == 1) {
    							minutes = "0" + minutes;
    						}
    				
    				}
    				// If the count down is over, write some text
    				if (distance <= 0) 
    				{
    					clearInterval(x);
    					seconds = "00" ;
    					days = "00";
    					minutes = "00";
    					hours = "00";
    				}
    				 
    				
    				if(self.$target.find(".snippet_right_timer_div"))
    				{
    					self.$target.find(".snippet_right_timer_div").css("display","inline-block")
    					
    					// Output the result in an element with id="date_timer"
    					self.$target.find("#days").html(days);
    					self.$target.find("#d_lbl").html("days");
    					self.$target.find("#hours").html(hours);
    					self.$target.find("#h_lbl").html("hours");
    					self.$target.find("#minutes").html(minutes);
    					self.$target.find("#m_lbl").html("minutes");
    					self.$target.find("#seconds").html(seconds);
    					self.$target.find("#s_lbl").html("seconds");
    				}
    				}, 1000);
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
			
			
