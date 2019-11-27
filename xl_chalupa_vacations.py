# -*- coding: utf-8 -*-
"""Plugin module for definition of MS Excel workbook Chalupa_vacations.xlsx."""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = [__author__]
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


# Standard library modules
import datetime

# Custom library modules
from xl_agenda import Agenda, Column, Params


class workbook(Agenda):
    """MS Excel import workbook column set."""

    def __init__(self):
        super().__init__()
        self._columns = [
            Column('Dátum od', 'd', 'date_on'),
            Column('Dátum do', 'd', 'date_off'),
            Column('Účel', 's', 'title'),
            Column('Period', 'n', 'period', optional=True),
        ]

    @property
    def excel(self):
        return 'Chalupa_vacations.xlsx'

    @property
    def agenda(self):
        return 'vacations'

    def store_cell(self, cell: object, colnum: int) -> Column:
        """Additional specific actions at storing a workbook cell."""
        coldef = super().store_cell(cell, colnum)
        if coldef and coldef.value is not None:
            if coldef.dbfield in ['date_on', 'date_off']:
                start = self.get_column_by_dbfield('date_on')
                stop = self.get_column_by_dbfield('date_off')
                if start and stop \
                    and start.value is not None \
                    and stop.value is not None:
                    days = (stop.value - start.value).days + 1
                    period = self.get_column_by_dbfield('period')
                    period.value = days
        return coldef
