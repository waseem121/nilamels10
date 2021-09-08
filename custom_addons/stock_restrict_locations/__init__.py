# -*- coding: utf-8 -*-
#
# Copyright © Ryan Cole 2017-Present
# 	- https://www.ryanc.me/
#	- admin@ryanc.me
#
# Please see the LICENSE file for license details


from . import models
from openerp import api, SUPERUSER_ID


# Ensure that the correct locations are set after a fresh install. Default behavior is fully-restrictive
def post_init_hook(cr, registry):
	env = api.Environment(cr, SUPERUSER_ID, {})
	env["res.users"].write({"restrict_wh_locations": True})
	env["res.users"]._recompute_location_restrictions()