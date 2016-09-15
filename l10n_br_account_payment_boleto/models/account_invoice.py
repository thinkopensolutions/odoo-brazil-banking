# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
#    @author Danimar Ribeiro <danimaribeiro@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp import models, api, _
from openerp.exceptions import Warning

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        # set transaction_id in invoice before calling super
        # because finalize_invoice_move_lines() tries to read it and
        # set on move lines if it is 
        # called after super finalize_invoice_move_lines()
        # will never set transaction_ref in move lines
        for invoice in self:
            own_number_type = self.company_id.own_number_type
            sequence = False
            if own_number_type == '0':
                sequence = self.env['ir.sequence'].next_by_id(
                    self.company_id.own_number_sequence.id)
            elif own_number_type == '1':
                sequence = self.env['ir.sequence'].next_by_id(
                    self.company_id.transaction_id_sequence.id)
            if sequence:
                invoice.transaction_id = sequence
            value = super(AccountInvoice, invoice).action_move_create()
            if own_number_type == '2':
                for move_line in invoice.move_id.line_id:
                    if invoice.account_id.id == move_line.account_id.id:
                        sequence = self.env['ir.sequence'].next_by_id(
                            self.payment_mode_id.internal_sequence_id.id)
                        move_line.transaction_ref = sequence

        return value

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ Propagate the transaction_id from the invoice to the move lines.

        The transaction id is written on the move lines only if the account is
        the same than the invoice's one.
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        for invoice in self:
            if invoice.transaction_id:
                invoice_account_id = invoice.account_id.id
                index = 1
                for line in move_lines:
                    # line is a tuple (0, 0, {values})
                    if invoice_account_id == line[2]['account_id']:
                        line[2]['transaction_ref'] = u'{0}/{1:02d}'.format(
                            invoice.transaction_id, index)
                        index += 1
        return move_lines
