odoo.define('product_multi_barcodes.PosModel', function(require){
"use strict";

    var screens = require('point_of_sale.screens');
    var Model = require('web.DataModel');
    var core = require('web.core');

    screens.ScreenWidget.include({

    play_wav: function() {
        var src = '';
        src = "/product_multi_barcodes/static/src/sounds/zt.wav";
        $('body').append('<audio src="'+src+'" autoplay="true"></audio>');
    },

    barcode_product_action: function(code){
        var self1 = this;
        /////////////////////////////////////////////////////


            if (self1.pos.scan_product(code)) {
               if (self1.barcode_product_screen) {
                  self1.gui.show_screen(self1.barcode_product_screen, null, null, true);
               }
            }
            else {
                //////////////////////////////////////////////////////////////
                   new Model("prod.pri")
                          .query(["id", "amou", "pri", "bar", "pri_id", "br"])
                          .filter([['bar', '=', code.base_code]])
                          .first()
                          .then(function (results){
                               if(results){
                                    var dsc = 0.0;
                                    var disc_per = 0.0;
                                    var product = self1.pos.db.get_product_by_barcode(results.br);
                                    if(!product){ self1.barcode_error_action(code); return false;}

                                    dsc = (results.amou * product.price) - results.pri;
                                    disc_per = (dsc * 100.0) / (results.amou * product.price);
                                    self1.pos.get_order().add_product(product, {quantity: results.amou, discount: disc_per});
                                    if (self1.barcode_product_screen) {
                                         self1.gui.show_screen(self1.barcode_product_screen, null, null, true);
                                     }
                               }
                               else{
                                    self1.play_wav();
                                    self1.barcode_error_action(code);
                                    return false;
                               }

                          });

        /////////////////////////////////////////////////////////////
            }




    },

    });
    ///////////////////////////////////////////////////////////////////////////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////////////////////////////

});
