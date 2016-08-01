# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Fernando Marcato Rodrigues
#    Copyright (C) 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp import api, models, fields


class CnabLines(models.Model):
    """  """
    _name = 'cnab.lines'

    # date, name, type , error showing only 4 columns in tree view
    name = fields.Char(string="Name", required=False, )
    account_no = fields.Char('Account No')
    amount = fields.Float('Amount')
    ref = fields.Char('Reference')
    date = fields.Date('Date')
    error_message = fields.Char("Error Message")
    partner_id = fields.Many2one('res.partner','Partner')
    unique_import_id = fields.Char('Unique Import ID')
    transaction_id = fields.Char('Transaction ID')
    statement_id = fields.Many2one('account.bank.statement', 'Bank Statement')
    servico_codigo_movimento = fields.Char("Servico Codigo Movimento")
