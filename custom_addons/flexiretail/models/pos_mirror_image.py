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
from odoo import models, fields, api, _
import re

class mirror_image_order(models.Model):
    _name = "mirror.image.order"

    session_name =  fields.Char(string='Session Id')
    order_id =  fields.Char(string='Order Id')
    order_line =  fields.Char(string='Order Line')
    currency =  fields.Char(string='currency')
    payment_line = fields.Char(string ='Payment Line')
    session_id = fields.Integer(String="POS Session")
    ac_token = fields.Boolean(default=False)

    @api.model
    def create_pos_data(self, order_line, order_id, session_id, currency, ac_session,paymentLines):
        if session_id:
            session_exist_id = self.env['mirror.image.order'].sudo().search([['session_name', '=', session_id]])
            if session_exist_id:
                session_exist_id.write({'order_line': order_line,
                                        'payment_line': paymentLines,
                                        })
            else:
                self.env['mirror.image.order'].create({'order_line': order_line,
                                                       'session_name': session_id,
                                                       'currency': currency,
                                                       'session_id': ac_session,
                                                       'payment_line': paymentLines,
                                                       })
        return True

    @api.model
    def delete_pos_data(self, session_id):
        if session_id:
            session_exist_id = self.env['mirror.image.order'].search([['session_name', '=', session_id]])
            if session_exist_id:
                session_exist_id.unlink()
        return True

class advertisement_images(models.Model):
    _name = "advertisement.images"
    _order = "sequence asc"

    name = fields.Char(string="Name")
    sequence = fields.Integer()
    description = fields.Text(string="Description")
    ad_image = fields.Binary(string="Image",type="binary")
    image_type = fields.Selection(selection=[('image','Image'),
                                             ('url','URL')], string = "Image Type", default='image')
    file_type = fields.Selection(selection=[('image','Image'),
                                             ('video','Video')], string = "File Type", default='image')
    video_type = fields.Selection(selection=[('video','Video'),
                                             ('url','URL')], string = "Video Type", default='video')
    ad_video = fields.Binary(string="Video",type="binary")
    video_url = fields.Char(string="URL")
    ace_video_url = fields.Char(string="URL")
    is_youtube_url = fields.Boolean("Is Youtube URL")
    url = fields.Char(string="URL")
    ad_video_fname = fields.Char()
    image_duration = fields.Integer(string="Image duration(Sec.)" ,default=1)

    @api.model
    def create(self,values):
        if values.has_key('is_youtube_url') and values.has_key('ace_video_url'):
            if values['is_youtube_url'] == True and len(values['ace_video_url']) != 0:
                videoUrl = values['ace_video_url']
                embedUrl = re.sub(r"(?ism).*?=(.*?)$", r"https://www.youtube.com/embed/\1", videoUrl )
                values['video_url'] = embedUrl
        return super(advertisement_images,self).create(values)

    @api.multi
    def write(self,values):
        if values.has_key('is_youtube_url') and values.has_key('ace_video_url'):
            if values['is_youtube_url'] != '' and values['ace_video_url'] == True:
                videoUrl = values['ace_video_url']
                embedUrl = re.sub(r"(?ism).*?=(.*?)$", r"https://www.youtube.com/embed/\1", videoUrl )
                values['video_url'] = embedUrl
        elif values.has_key('ace_video_url') and self.is_youtube_url:
            videoUrl = values['ace_video_url']
            embedUrl = re.sub(r"(?ism).*?=(.*?)$", r"https://www.youtube.com/embed/\1", videoUrl )
            values['video_url'] = embedUrl
        return super(advertisement_images,self).write(values)

class pos_config(models.Model):
    _inherit = 'pos.config'

    advertisement_image = fields.Many2many(comodel_name='advertisement.images',
                                           relation='config_advertisement',
                                           column1='advertisement', column2='config')
    marquee_text = fields.Char(string="Promotional Message")
    marque_color = fields.Char(string="Promotional Message color")
    marque_bg_color = fields.Char(string="Promotional Background color")
    marque_font_size = fields.Integer(string="Promotional Font size",default=1)
    mute_video_sound = fields.Boolean(string="Mute Video sound")
    ac_width = fields.Char(string="Width")
    ac_height = fields.Char(string="Height")

class screen_notification_msg(models.Model):
    _name = 'screen.notification.msg'

    msg = fields.Boolean(String="MSG", default=False)
    create_note= fields.Integer(String="Id")

    @api.model
    def check_status(self):
        msg_id = self.search([('create_note','=',self._uid)])
        if msg_id:
            if msg_id.msg:
                msg_id.msg = False
                return True
            else:
                return False
        else:
            self.create({'msg':True,'create_note':self._uid})
            return True