$(document).ready(function(){
	$(".o_my_show_more").click(function(){
		$(this).parents('table').find(".to_hide").toggleClass('hidden');
	    $(this).find('span').toggleClass('hidden');
	})
	
})