odoo.define('flexiretail.web', function (require) {
"use strict";

var from_widget = require('web.form_widgets');
var Session = require('web.Session');
var Model = require('web.DataModel');
var ActionManager = require('web.ActionManager');

from_widget.WidgetButton.include({
	on_confirmed: function() {
		var self = this;
		var context = this.build_context();
		var form_values = context.__eval_context.__contexts[1]
		//pos sales details
		if (form_values['active_model'] == 'wizard.sales.details' && this.$el.hasClass('print_sales_details')){
			if (form_values['report_type'] == 'thermal' && form_values['proxy_ip']) {
				self.connection = new Session(undefined,form_values['proxy_ip'], { use_cors: true});
				new Model("report").call('get_html', [form_values['active_ids'], 'flexiretail.sales_details_template']).done(
					function(report_html) {
						// WORKING  CODE FOR PRINTING VIA PROXY
						self.connection.rpc('/hw_proxy/print_xml_receipt',{receipt: report_html},{timeout: 8000})
                            .then(function(){
//                                        send_printing_job();
                            },function(){
//                                        self.receipt_queue.unshift(r);
                            });
					});
			} else {
				var print = {'context': {'active_id': form_values['active_id'],
					'active_ids': form_values['active_ids']},
					'report_file': 'flexiretail.sales_details_pdf_template',
					'report_name': 'flexiretail.sales_details_pdf_template',
					'report_type': "qweb-pdf",
					'type': "ir.actions.report.xml"};
				var options = {};
				var action_manager = new ActionManager();
				action_manager.ir_actions_report_xml(print);
			}
		}
		//pos session sales details
		if (form_values['active_model'] == 'wizard.pos.sale.report' && this.$el.hasClass('main_print_button')){
			if (form_values['report_type'] == 'thermal') {
				var posSessionModel = new Model('pos.session');
				posSessionModel.call('get_proxy_ip', [form_values['session_ids'][0][2][0]])
				.then(function (res){
					if(res && res.ip) {
						var url = res.ip;
						self.connection = new Session(undefined,url, { use_cors: true});
						new Model("report").call('get_html', [form_values['session_ids'][0][2], 'flexiretail.pos_sales_report_template']).done(
							function(report_html) {
								// WORKING  CODE FOR PRINTING VIA PROXY
								self.connection.rpc('/hw_proxy/print_xml_receipt',{receipt: report_html},{timeout: 8000})
                                    .then(function(){
//                                            send_printing_job();
                                    },function(){
//                                            self.receipt_queue.unshift(r);
                                    });
							});
					}
				}).fail(function (error, event){
					if(error.code === -32098) {
						alert("Odoo server down...");
						event.preventDefault();
					}
			    });
			} else {
				var print = {'context': {'active_id': form_values['session_ids'][0][2][0],
					'active_ids': form_values['session_ids'][0][2]},
					'report_file': 'flexiretail.pos_sales_report_pdf_template',
					'report_name': 'flexiretail.pos_sales_report_pdf_template',
					'report_type': "qweb-pdf",
					'type': "ir.actions.report.xml"};
				var options = {};
				var action_manager = new ActionManager();
				action_manager.ir_actions_report_xml(print);
			}
		}
		if(form_values['active_model'] == 'wizard.pos.x.report' && this.$el.hasClass('print_x_report')){
			if (form_values['report_type'] == 'thermal') {
				var posSessionModel = new Model('pos.session');
				posSessionModel.call('get_proxy_ip', [form_values['session_ids'][0][2][0]])
				.then(function (res){
					if(res && res.ip) {
						var url = res.ip;
						self.connection = new Session(undefined,url, { use_cors: true});
						new Model("report").call('get_html', [form_values['session_ids'][0][2], 'flexiretail.front_sales_thermal_report_template_xreport']).done(
							function(report_html) {
								// WORKING  CODE FOR PRINTING VIA PROXY
								self.connection.rpc('/hw_proxy/print_xml_receipt',{receipt: report_html},{timeout: 8000})
                                    .then(function(){
//                                            send_printing_job();
                                    },function(){
//                                            self.receipt_queue.unshift(r);
                                    });
							});
					}
				}).fail(function (error, event){
					if(error.code === -32098) {
						alert("Odoo server down...");
						event.preventDefault();
					}
			    });
			} else {
				var print = {'context': {'active_id': form_values['session_ids'][0][2][0],
					'active_ids': form_values['session_ids'][0][2]},
					'report_file': 'flexiretail.front_sales_report_pdf_template_xreport',
					'report_name': 'flexiretail.front_sales_report_pdf_template_xreport',
					'report_type': "qweb-pdf",
					'type': "ir.actions.report.xml"};
				var options = {};
				var action_manager = new ActionManager();
				action_manager.ir_actions_report_xml(print);
			}
		}
		return this.view.do_execute_action(
			_.extend({}, this.node.attrs, {context: context}),
			this.view.dataset, this.view.datarecord.id, function (reason) {
				if (!_.isObject(reason)) {
					self.view.recursive_reload();
				}
			});
	},
});

});