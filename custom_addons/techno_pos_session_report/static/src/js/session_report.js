odoo.define('aces_pos_x_report.pos', function (require) {
"use strict";

var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var Model = require('web.DataModel');
var ActionManager = require('web.ActionManager');

var QWeb = core.qweb;

var SessionReportPrintButton = screens.ActionButtonWidget.extend({
    template: 'SessionReportPrintButton',
    button_click: function(){
        var self = this;
        var pos_session_id = self.pos.pos_session.id;
        var print = {
                'context': {'active_id': [pos_session_id],
                'active_ids':[pos_session_id]},
                'report_file': 'techno_pos_session_report.report_pos_session_pdf',
                'report_name': 'techno_pos_session_report.report_pos_session_pdf',
                'report_type': "qweb-pdf",
                'type': "ir.actions.report.xml",
            };
        var options = {};
        var action_manager = new ActionManager();
        action_manager.ir_actions_report_xml(print);
    },
});

screens.define_action_button({
    'name': 'session_report_print',
    'widget': SessionReportPrintButton,
    'condition': function(){ 
        return this.pos.config.iface_session_report;
    },
});
});
