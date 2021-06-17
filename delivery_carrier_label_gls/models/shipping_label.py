# coding: utf-8
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ShippingLabel(models.Model):

    _inherit = "shipping.label"

    @api.model
    def _get_file_type_selection(self):
        """ To inherit to add file type """
        res = super(ShippingLabel, self)._get_file_type_selection()
        existing = {t[0] for t in res}
        gls_file_formats = self.env["delivery.carrier"]._fields[
            "gls_label_format"
        ].selection
        for key, name in gls_file_formats:
            if key == "PDF":
                continue
            if key in existing:
                continue
            res.append((key, name))
        return res
