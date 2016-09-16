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
import logging
import StringIO
from decimal import Decimal
from openerp import api, models, fields
from .file_cnab240_parser import Cnab240Parser as cnabparser
from cnab_explicit_errors import service_codigo_message, table_1, table_2, table_3, table_4, table_5

_logger = logging.getLogger(__name__)

MODOS_IMPORTACAO_CNAB = [
    ('bradesco_pag_for', u'Bradesco PagFor 500'),
    ('bradesco_cobranca_240', u'Bradesco Cobrança 240'),
    ('itau_cobranca_240', u'Itaú Cobrança 240'),
    ('cef_cobranca_240', u'CEF Cobrança 240'),
    ('sicoob_240', u'Sicoob Cobrança 240'),
]


class AccountBankStatementImport(models.TransientModel):
    """  """
    _inherit = 'account.bank.statement.import'

    import_modes = fields.Selection(
        MODOS_IMPORTACAO_CNAB,
        string=u'Opções de importação', select=True, required=False)
    import_cnab = fields.Boolean(string="Import Cnab", )

    @api.model
    def _check_cnab(self, data_file):
        if cnabparser is None:
            return False
        try:
            cnab_file = cnabparser.parse(StringIO.StringIO(data_file))
        except:
            return False
        return cnab_file

    @api.model
    def _find_bank_account_id(self, account_number):
        """ Get res.partner.bank ID """
        bank_account_id = None
        if account_number:
            bank_account_ids = self.env['res.partner.bank'].search(
                [('acc_number', '=', str(account_number))], limit=1)
            if bank_account_ids:
                bank_account_id = bank_account_ids[0].id
        return bank_account_id

    @api.model
    def create_cnab_lines(self, line_vals, statement_id):
        line_vals.update({'statement_id': statement_id})
        cnab_line = self.env['cnab.lines'].create(line_vals)
        return cnab_line

    def get_explicit_error_message(self, message_dict, code, error):
        message = error_message = ''
        if code in message_dict.keys():
            message = message_dict.get(code)
        errors = [error[0:2], error[2:4], error[4:6], error[6:8]]
        for error in errors:
            error = int(error)
            # Table 1
            if code == 3 and table_1.get(error):
                error_message += str(error) + ' - ' + table_1.get(error) + '\n'
            # Table 2
            if code == 17 and table_2.get(error):
                error_message += str(error) + ' - ' + table_2.get(error) + '\n'
            # Table 3
            if code == 16 and table_3.get(error):
                error_message += str(error) + ' - ' + table_3.get(error) + '\n'
            # Table 4
            if code == 15 and table_4.get(error):
                error_message += str(error) + ' - ' + table_4.get(error) + '\n'
            # Table 5
            if code == 18 and table_5.get(error):
                error_message += str(error) + ' - ' + table_5.get(error) + '\n'
        return message, error_message

    @api.model
    def _create_bank_statement(self, stmt_vals):
        transactions = stmt_vals['transactions']
        # omit trnasactions with servico_codigo_movimento != 6 for itau_cobranca_240
        if self.import_modes == 'itau_cobranca_240':
            transation_ids = []
            for stmt in stmt_vals['transactions']:
                if stmt.get('servico_codigo_movimento') == 6:
                    transation_ids.append(stmt)
            stmt_vals['transactions'] = transation_ids
        statement_id, notifications = super(
            AccountBankStatementImport, self)._create_bank_statement(stmt_vals)

        if stmt_vals.get('statement_type') == 'c' and stmt_vals.get(
                'line_ids') and self.import_modes == 'itau_cobranca_240':
            for line in transactions:
                # get service codigo message

                servico_codigo_movimento = line.get('servico_codigo_movimento')
                error = str(line.get('errors'))
                # remove unwnanted keys from dict 
                line.pop('errors', None)
                line.pop('label', None)
                line.pop('sequence', None)

                message, error_message = self.get_explicit_error_message(service_codigo_message,
                                                                         servico_codigo_movimento, error)
                if message:
                    line.update({'servico_codigo_movimento':
                                     str(line['servico_codigo_movimento']) + ' - ' + message,
                                 'error_message': error_message,
                                 })
                self.create_cnab_lines(line, statement_id)
        return statement_id, notifications

    @api.model
    def _complete_statement(self, stmt_vals, journal_id, account_number):
        """Complete statement from information passed.
            unique_import_id is assumed to already be unique at the moment of
            CNAB exportation."""
        stmt_vals['journal_id'] = journal_id
        journal = self.env['account.journal'].browse(journal_id)
        if journal.with_last_closing_balance:
            start = self.env['account.bank.statement'] \
                ._compute_balance_end_real(journal_id)
            stmt_vals['balance_start'] = Decimal("%.4g" % start)
            stmt_vals['balance_end_real'] += Decimal("%.4g" % start)

        for line_vals in stmt_vals['transactions']:
            unique_import_id = line_vals.get('unique_import_id', False)
            if unique_import_id:
                line_vals['unique_import_id'] = unique_import_id
                payment = self.env['payment.line'].search(
                    [('name', '=', line_vals['unique_import_id'])])
                line_vals['partner_id'] = payment.partner_id.id
        if self.import_cnab:
            stmt_vals.update({'statement_type': 'c'})
        return stmt_vals

    @api.multi
    def _parse_file(self, data_file):
        """Parse a CNAB file."""
        self.ensure_one()
        parser = cnabparser()

        _logger.debug("Try parsing with CNAB.")
        return parser.parse(data_file, self.import_modes)

        # Not a CNAB file, returning super will call next candidate:
        _logger.debug("Statement file was not a CNAB  file.",
                      exc_info=True)
        return super(AccountBankStatementImport, self)._parse_file(
            data_file)
