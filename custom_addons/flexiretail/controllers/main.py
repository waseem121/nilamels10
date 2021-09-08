# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import simplejson

from odoo import http
from odoo.http import request
from odoo.tools.translate import _
import logging
import odoo
import re
import time
import datetime
import werkzeug.utils
import hashlib
import json
import werkzeug.utils
import werkzeug.wrappers
from odoo import SUPERUSER_ID
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class DataSet(http.Controller):

    @http.route('/web/dataset/load_products', type='http', auth="user")
    def load_products(self, **kw):
        domain = str(kw.get('domain'))
        domain = domain.replace('true', 'True')
        domain = domain.replace('false', 'False')
        domain = eval(domain)
        temp = int(kw.get('product_limit')) - 1000
        domain += [('id','<=',kw.get('product_limit')),('id','>=',temp)]

        ctx1 = str(kw.get('context'))
        ctx1 = ctx1.replace('true', 'True')
        ctx1 = ctx1.replace('false', 'False')
        ctx1 = eval(ctx1)
        records = []
        fields = eval(kw.get('fields'))
        cr, uid, context = request.cr, request.uid, request.context
        Model = kw.get('model')
        context = dict(context)
        context.update(ctx1)
        try:
            records = request.env[Model].with_context(context).search_read(domain, fields, limit=1000)
        except Exception, e:
            _logger.error('Error .... %s',e)
        return simplejson.dumps(records)

    @http.route('/web/dataset/load_customers', type='http', auth="user")
    def load_customers(self, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        records = []
        fields = [];
        if eval(kw.get('fields')):
            fields = eval(kw.get('fields'))
        domain = [('customer', '=', True)];
        Model = kw.get('model')
        try:
            records = request.env[Model].sudo().search_read(domain, fields)
        except Exception, e:
            print "\n Error......", e
        return simplejson.dumps(records)


    @http.route('/pos/mirror_data', type='http', auth='user',website=True)
    def mirror_data(self,**k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        mirror_img = request.env['mirror.image.order']
        notif_obj = request.env['screen.notification.msg']
        notification_id = notif_obj.search([('create_note','=',uid)])
        if notification_id:
            notification_id[0].write({'msg':True})
        session_name = []
        
        if session.has_key('session_link'):
            session_name = session['session_link']
            try:
                product_name = mirror_img.browse(session_name)
                return json.dumps({'name':eval(product_name.order_line),'currency':product_name.currency,'payment_line':eval(product_name.payment_line)})
            except:
                return werkzeug.utils.redirect("/pos/latest_mirror_url")
        return werkzeug.utils.redirect("/pos/latest_mirror_url")

    @http.route('/pos/latest_mirror_url', type='http', auth='user',website=True)
    def mirror(self, debug=False, **k):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        mirror_img = request.env['mirror.image.order']
        pos_config = request.env['pos.config']
        ad_image = request.env['advertisement.images']
        # website_obj = request.registry['website']
        mirror_img_ids = mirror_img.sudo().search([('session_name', '=', str(uid))])
        if mirror_img_ids:
            session_id = mirror_img_ids[0].session_id
            image_data = []
            first_img = {}
            if session_id:
                pos_config_data = pos_config.sudo().browse(session_id)
                # pos_config_data = ac_config_obj.read(['advertisement_image','marquee_text','marque_color','marque_bg_color','marque_font_size','mute_video_sound','ac_width','ac_height'])
                
                image_ids = pos_config_data.advertisement_image.ids
                # image_duration = pos_config_data['image_duration']*1000
                if image_ids:
                    top_image_id = image_ids[0]
                    del image_ids[0]
                    image_obj = ad_image.browse(top_image_id)
                    first_img['file_type'] = image_obj.file_type
                    first_img['is_youtube_url']=image_obj.is_youtube_url
                    if image_obj.file_type == "image":
                        if(image_obj.image_type == 'url'):
                            first_img['img_link'] = image_obj.url
                        else:
                            first_img['img_link'] = self.image_url(cr, uid, image_obj, 'ad_image')

                    if image_obj.file_type == "video":
                        if(image_obj.video_type == 'url'):
                            first_img['img_link'] = image_obj.video_url
                            url_value = (image_obj.video_url).split('/')
                            name_of_url = url_value[len(url_value)-1]
                            first_img['name_of_url'] = name_of_url
                        else:
                            args = {
                                'id': image_obj.id,
                                'model': image_obj._name,
                                'filename_field': 'ad_video_fname',
                                'field': 'ad_video',
                                }

                            first_img['img_link'] = '/web/content?%s' % werkzeug.url_encode(args)

                    first_img['name'] = image_obj.name
                    first_img['description'] = image_obj.description
                    first_img['image_duration']= image_obj.image_duration*1000
                    for image_id in image_ids:
                        temp_file_dict = {}
                        ad_obj = ad_image.browse(image_id)
                        temp_file_dict['file_type'] = ad_obj.file_type
                        temp_file_dict['is_youtube_url']=ad_obj.is_youtube_url
                        if ad_obj.file_type == "image":
                            if(ad_obj.image_type == 'url'):
                                temp_file_dict['img_link'] = ad_obj.url
                            else:
                                temp_file_dict['img_link'] = self.image_url(cr, uid, ad_obj, 'ad_image')

                        if ad_obj.file_type == "video":
                            if(ad_obj.video_type == 'url'):
                                temp_file_dict['img_link'] = ad_obj.video_url
                                url_value = (ad_obj.video_url).split('/')
                                name_of_url = url_value[len(url_value)-1]
                                temp_file_dict['name_of_url'] = name_of_url
                            else:
                                args = {
                                    'id': ad_obj.id,
                                    'model': ad_obj._name,
                                    'filename_field': 'ad_video_fname',
                                    'field': 'ad_video',
                                    }
                                temp_file_dict['img_link'] = '/web/content?%s' % werkzeug.url_encode(args)


                        temp_file_dict['name'] = ad_obj.name
                        temp_file_dict['description'] = ad_obj.description
                        temp_file_dict['image_duration'] = ad_obj.image_duration*1000
                        image_data.append(temp_file_dict)

            session['session_link'] = mirror_img_ids[0].id
            vals = {
                        "first_img":first_img,"image_link":image_data,
                        "marquee_text": pos_config_data.marquee_text,
                        "marque_color":pos_config_data.marque_color,
                        "marque_bg_color":pos_config_data.marque_bg_color,
                        "marque_font_size":"font-size:"+str(pos_config_data.marque_font_size)+"px",
                        "ac_mute_video":pos_config_data.mute_video_sound,
                        "ac_width":pos_config_data.ac_width,
                        "ac_height":pos_config_data.ac_height,
                        "ac_height_style":"height:"+str(pos_config_data.ac_height)+"px",
                    }
            return request.render('flexiretail.index1', vals)
        else:
            return "<h1>Link is Not valid.....</h1>"

    def image_url(self, cr, uid, record, field, size=None, context=None):
        """Returns a local url that points to the image field of a given browse record."""
        sudo_record = record.sudo()
        sha = hashlib.sha1(getattr(sudo_record, '__last_update')).hexdigest()[0:7]
        size = '' if size is None else '/%s' % size
        return '/web/image/%s/%s/%s%s?unique=%s' % (record._name, record.id, field, size, sha)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: