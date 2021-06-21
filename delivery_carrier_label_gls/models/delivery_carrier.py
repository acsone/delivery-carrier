# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("gls", "Gls")])

    gls_contact_id = fields.Char(
        string="Contact ID", related="company_id.gls_contact_id",
    )
    gls_login = fields.Char(string="Login User", group="base.group_system")
    gls_password = fields.Char(string="Login Password", group="base.group_system")
    gls_url = fields.Char(string="Service Url", group="base.group_system")
    gls_url_test = fields.Char(string="Test Service Url", group="base.group_system")
    gls_url_tracking = fields.Char(
        help="Root URL for parcel tracking. Needs a %s for the tracking reference."
    )
    gls_label_format = fields.Selection(
        string="Label format",
        selection=[
            ("pdf", "PDF"),
            ("zebra", "Zebra"),
            ("intermec", "Intermec"),
            ("datamax", "Datamax"),
            ("toshiba", "Toshiba")
        ],
        default="pdf",
    )

    @api.constrains("delivery_type", "gls_contact_id", "gls_login",
                    "gls_password", "gls_url_tracking", "gls_label_format")
    def _check_gls_fields(self):
        gls_field_names = [
            "gls_contact_id",
            "gls_login",
            "gls_password",
            "gls_url_tracking",
            "gls_label_format"
        ]
        for rec in self.filtered(lambda c: c.delivery_type == "gls"):
            for field_name in gls_field_names:
                value = rec[field_name]
                if not value:
                    field = rec._fields[field_name]
                    description_string = field._description_string(self.env)
                    raise ValidationError(
                        _("The GLS field '%s' is required for carrier %s")
                        % (description_string, rec.name)
                    )

    @api.constrains("delivery_type", "prod_environment", "gls_url", "gls_url_test")
    def _check_fls_url(self):
        for rec in self.filtered(lambda c: c.delivery_type == "gls"):
            if not rec.prod_environment and not rec.gls_url_test:
                raise ValidationError(
                    _("The GLS field 'Test Service Url' is required in "
                      "test mode")
                )
            if rec.prod_environment and not rec.gls_url:
                raise ValidationError(
                    _("The GLS field 'Service Url' is required in "
                      "non test mode")
                )

    def gls_get_shipping_price_from_so(self, order):
        self.ensure_one()
        return [0]  # TODO?

    def gls_send_shipping(self, picking):
        tracking_number = picking.gls_send_shipping(self)
        return [{"exact_price": False, "tracking_number": tracking_number}]

    @api.model
    def gls_tracking_url(self, tracking_number):
        return self.gls_url_tracking % tracking_number

    def gls_get_tracking_link(self, pickings):
        links = []
        for picking in pickings:
            for link in picking.mapped("package_ids.parcel_tracking"):
                if link:
                    links.append(self.gls_tracking_url(link))
        return links

    def gls_cancel_shipment(self, pickings):
        if pickings.mapped("package_ids.report_id"):
            msg = _("Packages cannot be cancelled after the End of Day report.")
            raise ValidationError(msg)
        for picking in pickings:
            picking.gls_cancel_shipment()

    def _get_gls_client(self):
        """Return a GLS connection client using this carrier configuration."""
        # the client checks all parameters, so nothing needed here.
        self.ensure_one()
        return self.env["delivery.client.gls"].create({"carrier_id": self.id})
