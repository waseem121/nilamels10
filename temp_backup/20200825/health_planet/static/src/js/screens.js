odoo.define('health_planet.screens', function (require) {
    "use strict";

var screens = require('point_of_sale.screens');
var core = require('web.core');
var QWeb = core.qweb;
var _t  = require('web.core')._t;

screens.ScreenWidget.include({

    barcode_client_action: function(code){
        var partner = this.pos.db.get_partner_by_barcode(code.code);
        if(partner){
            console.log('Partner',partner)
            if(partner.is_instructor==true){
               this.pos.get_order().set_instructor(partner);
//               this.el.querySelector('.order-instructor').textContent = partner.name || '';
               return true;
            }else{
               this.pos.get_order().set_client(partner);
            }
            return true;
        }
        this.barcode_error_action(code);
        return false;
    }
})

screens.ClientListScreenWidget.include({
    render_list: function(partners){
        var contents = this.$el[0].querySelector('.client-list-contents');
        contents.innerHTML = "";
        for(var i = 0, len = Math.min(partners.length,1000); i < len; i++){
            var partner    = partners[i];
            console.log(partner.is_instructor);
            if(partner.is_instructor != true){
                var clientline = this.partner_cache.get_node(partner.id);
                if(!clientline){
                    var clientline_html = QWeb.render('ClientLine',{widget: this, partner:partners[i]});
                    var clientline = document.createElement('tbody');
                    clientline.innerHTML = clientline_html;
                    clientline = clientline.childNodes[1];
                    this.partner_cache.cache_node(partner.id,clientline);
                }
                if( partner === this.old_client ){
                    clientline.classList.add('highlight');
                }else{
                    clientline.classList.remove('highlight');
                }
                contents.appendChild(clientline);
            }
        }
    },

})


})
