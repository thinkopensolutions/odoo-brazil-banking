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


class AccountBankStatement(models.Model):
    """  """
    _inherit = 'account.bank.statement'

    statement_type = fields.Selection([('c', 'CNAB Return'), ('b', 'Bank Statement')],
                                      default='b', required=True, string="Type")

    cnab_lines = fields.One2many('cnab.lines', 'statement_id', 'CNAB Lines')
    
class AccountBankStatementLine(models.Model):
    """  """
    _inherit = 'account.bank.statement.line'
    
    def _domain_reconciliation_proposition(self, cr, uid, st_line, excluded_ids=None, context=None):
        # if statement is canb return statement then 
        # chnage domain with transaction_ref
        if st_line.statement_id.statement_type == 'c':
            if excluded_ids is None:
                excluded_ids = []
            domain = [('transaction_ref', '=', st_line.ref),
                      ('reconcile_id', '=', False),
                      ('state', '=', 'valid'),
                      ('account_id.reconcile', '=', True),
                      ('id', 'not in', excluded_ids),]
            if st_line.partner_id:
                domain.append(('partner_id', '=', st_line.partner_id.id))
            return domain
        else:
            return super(AccountBankStatementLine,self)._domain_reconciliation_proposition(cr, uid, st_line, excluded_ids=excluded_ids, context=context)
