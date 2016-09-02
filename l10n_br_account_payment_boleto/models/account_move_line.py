# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
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
from openerp import models, fields, api
from datetime import date
from ..boleto.document import Boleto
from ..boleto.document import BoletoException
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_payment_created = fields.Date(
        u'Data da criação do pagamento', readonly=True)
    boleto_own_number = fields.Char(
        u'Nosso Número', readonly=True)

    # validate config to generate boletos
    @api.multi
    def validate_boleto_config(self):
        for move_line in self:
            if move_line.payment_mode_id.type_payment != '00':
                raise UserError(_(
                    u"In payment mode %s Tipo SPED must be 00 - Duplicata" %
                    move_line.payment_mode_id.name))
            if not move_line.payment_mode_id.internal_sequence_id:
                raise UserError(_(
                    u"Please set sequence in payment mode %s" %
                    move_line.payment_mode_id.name))
            if move_line.company_id.own_number_type != '2':
                raise UserError(_(
                    u"Tipo de nosso número Sequéncial uniquo por modo de pagamento"))
            if not move_line.payment_mode_id.boleto_type:
                raise UserError(_(
                    u"Configure o tipo de boleto no modo de pagamento"))
            if not move_line.payment_mode_id.boleto_carteira:
                raise UserError(_(u"Carteira not set in payment method"))
            if not move_line.payment_mode_id.instrucoes:
                raise UserError(_(u"Instrucoes not set in payment method"))
            else:
                if isinstance(move_line.payment_mode_id.instrucoes, basestring):
                    list_inst = move_line.payment_mode_id.instrucoes.splitlines()
                    # 7 lines allowed but we append last line with multa in the text
                    if len(list_inst) > 6:
                        raise Warning(
                            u'Número de linhas de instruções maior que 6')
                    for line in list_inst:
                        if len(line) > 90:
                            raise Warning(
                                u'Linha de instruções: "%s" possui mais que 90 caracteres' %line)
            return True

    @api.multi
    def send_payment(self):
        boleto_list = []
        self.validate_boleto_config()
        for move_line in self:
            if move_line.payment_mode_id.type_payment == '00':
                # nosso numero must be integer
                nosso_numero =  \
                ''.join(digit for digit in move_line.invoice.transaction_id if digit.isdigit())
                boleto = Boleto.getBoleto(move_line, nosso_numero)
                if boleto:
                    move_line.date_payment_created = date.today()
                    move_line.boleto_own_number = \
                        boleto.boleto.format_nosso_numero()
                    boleto_list.append(boleto.boleto)
        return boleto_list
