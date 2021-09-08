# -*- coding: utf-8 -*-
#
# Copyright © Ryan Cole 2017-Present
# 	- https://www.ryanc.me/
# 	- admin@ryanc.me
#
# Please see the LICENSE file for license details


from openerp import api, fields, models


class ResUsers(models.Model):
	_inherit = "res.users"

	# Helper functions to compute the allowed ids for a (single) user. Also used as the default for @allowed_xxx_ids_computed
	@api.multi
	def _get_allowed_warehouses(self):
		if not self or len(self) > 1: return False

		# if the user is restricted, return a list of their allowed warehouses
		if self.restrict_wh_locations:
			return [(6, 0, [wh.id for wh in self.allowed_warehouse_ids])]

		# otherwise, return a list of *all* warehouses (which effectively disables the access-control)
		return [(6, 0, [wh.id for wh in self.env["stock.warehouse"].sudo().search([(1, "=", 1)])])]

	@api.multi
	def _get_allowed_locations(self):
		if not self or len(self) > 1: return False
		
		if self.restrict_wh_locations:
			return [(6, 0, self._recurse_location_children(self.allowed_location_ids))]
		return [(6, 0, [loc.id for loc in self.env["stock.location"].sudo().search([(1, "=", 1)])])]

	@api.multi
	def _get_allowed_picking_types(self):
		if not self or len(self) > 1: return False
		
		if self.restrict_wh_locations:
			return [(6, 0, [pick.id for pick in self.allowed_picking_type_ids])]
		return [(6, 0, [pick.id for pick in self.env["stock.picking.type"].sudo().search([(1, "=", 1)])])]


	# Should the user be restricted to certain warehouses?
	restrict_wh_locations = fields.Boolean(string="Restrict Warehouses/Locations", default=True)

	# Warehouses/Locations/Picking Types that the user *should* have access to. This field is not used directly in the access rules
	allowed_warehouse_ids = fields.Many2many(string="Allowed Warehouses", help="List of warehouses that this user is allowed to access", comodel_name="stock.warehouse")
	allowed_location_ids = fields.Many2many(string="Allowed Locations", help="List of locations that this user is allowed to access", comodel_name="stock.location")
	allowed_picking_type_ids = fields.Many2many(string="Allowed Picking Types", help="List of picking types that this user is allowed to access", comodel_name="stock.picking.type")

	# Ghost fields that contain lists of IDs that are *actually* allowed. For example, @allowed_location_ids_computed will contain all IDs from the above field, but also
	# all sub-locations (see _recurse_location_children). 
	allowed_warehouse_ids_computed = fields.Many2many(comodel_name="stock.warehouse", relation="res_users_allowed_warehouses_comp_rel", column1="res_users_id", column2="stock_warehouse_id", default=_get_allowed_warehouses)
	allowed_location_ids_computed = fields.Many2many(comodel_name="stock.location", relation="res_users_allowed_locations_comp_rel", column1="res_users_id", column2="stock_location_id", default=_get_allowed_locations)
	allowed_picking_type_ids_computed = fields.Many2many(comodel_name="stock.picking.type", relation="res_users_allowed_picking_type_comp_rel", column1="res_users_id", column2="stock_picking_type_id", default=_get_allowed_picking_types)



	@api.model
	def _recurse_location_children(self, locations):
		# Adding a location implies that the user should have access to its sub-locations also
		location_ids = self.env['stock.location'].search([('usage', '!=', 'internal')]).ids
# 		location_ids = []

		for location in locations:
			location_ids.append(location.id)

			if location.child_ids and len(location.child_ids) > 0:
				for child_id in self._recurse_location_children(location.child_ids):
					if child_id not in location_ids:
						location_ids.append(child_id)

		return location_ids


	@api.multi
	@api.onchange('restrict_wh_locations')
	def _onchange_restrict_wh_locations(self):
		for user in self:
			# Update the xxx_ids_computed fields. See the _get_allowed_xxx() functions for more details
			user.allowed_warehouse_ids_computed = user._get_allowed_warehouses()
			user.allowed_location_ids_computed = user._get_allowed_locations()
			user.allowed_picking_type_ids_computed = user._get_allowed_picking_types()
		self.clear_wh_rule_caches()


	@api.multi
	@api.onchange('allowed_warehouse_ids')
	def _onchange_allowed_warehouse_ids(self):
		self.ensure_one()
		self.allowed_warehouse_ids_computed = self._get_allowed_warehouses()
		self.clear_wh_rule_caches()

	@api.multi
	@api.onchange('allowed_location_ids')
	def _onchange_allowed_location_ids(self):
		self.ensure_one()
		self.allowed_location_ids_computed = self._get_allowed_locations()
		self.clear_wh_rule_caches()

	@api.multi
	@api.onchange('allowed_picking_type_ids')
	def _onchange_allowed_picking_type_ids(self):
		self.ensure_one()
		self.allowed_picking_type_ids_computed = self._get_allowed_picking_types()
		self.clear_wh_rule_caches()

	@api.model
	def _recompute_location_restrictions(self):
		# Helper function to recompute the allowed IDs for users who are *not* restricted
		self.search([("restrict_wh_locations", "=", False)])._onchange_restrict_wh_locations()

	@api.multi
	def clear_wh_rule_caches(self):
		# Invalidate the ir.rule cache to ensure that changes take effect immediately
		self.sudo().env["ir.rule"].clear_caches()
ResUsers()


class StockWarehouse(models.Model):
	_inherit = "stock.warehouse"

	@api.model
	def create(self, values):
		res = super(StockWarehouse, self).create(values)

		# If @restrict_wh_locations is un-checked (False), the user should have unrestricted access to all records
		# We can call the _recompute_location_restrictions() method to recompute the @allowed_xxx fields automatically
		self.env["res.users"]._recompute_location_restrictions()

		return res
StockWarehouse()

class StockLocation(models.Model):
	_inherit = "stock.location"

	@api.model
	def create(self, values):
		res = super(StockLocation, self).create(values)
		self.env["res.users"]._recompute_location_restrictions()
		return res
StockLocation()

class StockPickingType(models.Model):
	_inherit = "stock.picking.type"

	@api.model
	def create(self, values):
		res = super(StockPickingType, self).create(values)
		self.env["res.users"]._recompute_location_restrictions()
		return res
StockPickingType()
