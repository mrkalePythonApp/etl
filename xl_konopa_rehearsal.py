# -*- coding: utf-8 -*-
"""Plugin module for definition of MS Excel workbook Konopa_rehearsal.xlsx."""
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
            Column('Dátum', 'd', 'date_on'),
            Column('Akcia', 's', 'title'),
            Column('Miesto', desc=True),
            Column('Čas', 'n', 'duration', desc=True),
            Column('Hráčov', 'n', desc=True),
            Column('Poznámka', desc=True),
        ]

    @property
    def excel(self):
        return 'Konopa_rehearsal.xlsx'

    @property
    def agenda(self):
        return 'events'

    def store_cell(self, cell: object, colnum: int) -> Column:
        """Additional specific actions at storing a workbook cell."""
        coldef = super().store_cell(cell, colnum)
        if coldef and coldef.value is not None:
            if coldef.title == 'Čas':
                format_time = '%H:%M'
                times = coldef.value.split('-')
                start = datetime.datetime.strptime(
                    times[0].strip(), format_time)
                stop = datetime.datetime.strptime(
                    times[1].strip(), format_time)
                # Convert duration to quarters of an hour
                coldef.value = (stop - start).total_seconds() // 900 * 0.25
        return coldef
