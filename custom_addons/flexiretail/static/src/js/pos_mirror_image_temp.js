$(document).ready(function(){
    function createRequest(){
        $.getJSON("/pos/mirror_data", function(result){
            $(".network_state").css("color","green");
            var product_data="";
            var symbol = result['currency'];
            if(result['name'] !='[]'){
                var obj = result['name'];
                for(var i=0;i<obj.length-1;i++){                                                                                                                     
                    product_data+="<tr><td class='product_name'><b>"+obj[i][0]+"</b><br/><span class='product_price'>"+obj[i][2]+" "+obj[i][3]+" at "+symbol+" "+obj[i][1].toFixed(3)+"/"+obj[i][3]+"</span>";               
                    if(obj[i][4] != 0){
                    product_data+="<br/><span class='product_price'>With a "+obj[i][4]+"% discount</span></td>";
                    }
                    product_data+="<td class='product_name1'><b>"+symbol+" "+((obj[i][1]*obj[i][2])-(obj[i][2]*(obj[i][1]*obj[i][4]*.01))).toFixed(3)+"</b></td></tr>";  
                }
                if(obj.length <= 1){
                    $(".total_amount").html("");
                    $(".total_tax").html("");
                    product_data="<div class='empty'>Your shopping cart is empty</div>"
                }
                else{
                    $(".total_amount").html("Total: "+symbol+" "+obj[obj.length-1][1].toFixed(3));
                    $(".total_tax").html("GST: "+symbol+" "+obj[obj.length-1][0].toFixed(3));
                }
                $(".product_content").html(product_data);
            }
            else{
                $(".total_amount").html("");
                $(".total_tax").html("");
                $(".product_content").html("<div class='empty'>Your shopping cart is empty</div>");
            }
            if(result['payment_line'] !='[]'){
                var obj = result['payment_line'];
                var payment_data ="";
                for(var i=0;i<obj.length-1;i++){ 
                    payment_data+="<tr><td class='payment_name' style='color:#555555;'><b>"+obj[i][0]+"</b><span class='product_name1'>"+symbol+" "+obj[i][1].toFixed(3)+"</span></td></tr>";     
                }
                
                if(obj.length <= 0){
                    payment_data="<div class='empty'>No Paymentline Selected</div>"
                }
                else {
                    if(obj[obj.length-1][0]!= undefined)
                        payment_data+="<tr><td class='payment_amount'><b>Paid</b><span class='product_name1'>"+symbol+" "+obj[obj.length-1][0].toFixed(3)+"</span></td></tr>";
                    if(obj[obj.length-1][1]!= undefined)
                        payment_data+="<tr><td class='payment_amount'><b>Remaining</b><span class='product_name1'>"+symbol+" "+obj[obj.length-1][1].toFixed(3)+"</span></td></tr>";
                    if(obj[obj.length-1][2]!= undefined)
                        payment_data+="<tr><td class='payment_amount'><b>Change</b><span class='product_name1'>"+symbol+" "+obj[obj.length-1][2].toFixed(3)+"</span></td></tr>";
//                    if(obj[obj.length-1][4]!= undefined)
//                        payment_data+="<tr><td class='payment_amount'><b>Coupon Amount</b><span class='product_name1'>"+symbol+" "+obj[obj.length-1][4].toFixed(3)+"</span></td></tr>";
                    if(obj[obj.length-1][3]!= undefined)
                        payment_data+="<tr><td class='payment_amount'><b>Redeem Amount</b><span class='product_name1'>"+symbol+" "+obj[obj.length-1][3].toFixed(3)+"</span></td></tr>";
                    
                }
                $(".payment_content").html(payment_data);
            }
            else{
                $(".payment_content").html("<div class='empty'>No Paymentline Selected</div>");
            }
            $('.product_list').scrollTop(99999999999999999);
            $('.payment_list').scrollTop(99999999999999999);
            setTimeout(function(){ createRequest(); }, 3000);
            
            }).fail(function() {
                $(".network_state").css("color","red");
                setTimeout(function(){ createRequest(); }, 10000);
           
        });
    }
    createRequest();
   var t;
   var start = $('#myCarousel').find('.active').attr('data-interval');
   setTimeout("$('#myCarousel').carousel({interval: 1000});", start-1000);
   $('#myCarousel').on('slid.bs.carousel', function () {
       if($('.item').find('video').length){
           $('.item').find('video')[0].pause();
           if($(this).find('.active').find('video')[0] != undefined){
               if($("#is_mute").data('value')=="True"){
                   $(this).find('.active').find('video').prop('muted', true);
               }
               $(this).find('.active').find('video')[0].play();
           }
       }
//        clearTimeout(t);
       var duration = $(this).find('.active').attr('data-interval');
       $('#myCarousel').carousel('pause');
       setTimeout("$('#myCarousel').carousel();", duration-1000);
   })

$('.carousel-control.right').on('click', function(){
    clearTimeout(t);
});


$('.carousel-control.left').on('click', function(){
    clearTimeout(t);
});
});


