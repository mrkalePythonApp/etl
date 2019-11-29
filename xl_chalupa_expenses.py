# -*- coding: utf-8 -*-
"""Plugin module for definition of MS Excel workbook Chalupa_expenses.xlsx."""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = [__author__]
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'

# Custom library modules
from xl_agenda import Agenda, Column, Params


class workbook(Agenda):
    """MS Excel import workbook column set."""

    def __init__(self):
        super().__init__()
        self._columns = [
            Column('Dátum', 'd', 'date_on'),
            Column('Popis', 's', 'title'),
            Column('Výdavky €', 'n', 'price', optional=True, rounding=2),
            Column('Výdavky Sk', 'n', 'price_orig', optional=True, rounding=2),
            Column('Currency', 'n', 'id_currency', optional=True),
        ]

    @property
    def excel(self):
        return 'Chalupa_expenses.xlsx'

    @property
    def agenda(self):
        return 'expenses'
