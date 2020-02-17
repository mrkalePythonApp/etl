# -*- coding: utf-8 -*-
"""Module with general agenda definition."""
__version__ = '0.3.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019-2020, ' + __author__
__credits__ = [__author__]
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


# Standard library modules
import datetime

# Custom modules
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum


class Params:
    """Global business parameters."""

    (
        juser, jskccy, skeu,
    ) = (820, 1, 30.126)


class Source:
    """Parameters of the data source."""

    (
        file, wbook, wsheet, agenda,
    ) = (None, None, None, None)


@dataclass
class Column:
    """MS Excel column definition of an agenda.

    - 'desc' determines that the column value is appended to the 'description'
       as comment and 'dbfield' is ignored.

    """
    title: str
    datatype: str = 's'
    dbfield: str = None
    index: int = None
    optional: bool = False
    value: any = None
    comment: str = None
    rounding: int = None
    desc: bool = False

    def reset(self, values_only=False):
        """Initialize dynamic fields of a data record."""
        self.value = None
        self.comment = None
        if not values_only:
            self.index = None


class Agenda(ABC):
    """MS Excel agenda column set."""

    def __init__(self):
        """Create the class instance - constructor."""
        self._logger = None
        self._columns: [Column] = []
        self._comments: [str] = []

    @property
    @abstractmethod
    def excel(self):
        ...

    @property
    @abstractmethod
    def agenda(self):
        ...

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    @property
    def dbfields(self):
        now = datetime.datetime.now()
        common_fields = {
            'params': '',
            'metakey': '',
            'metadesc': '',
            'metadata': '',
            'created': now,
            'created_by': Params.juser,
            'modified': now,
            'modified_by': Params.juser,
            'description': self.comment,
        }
        fields = {col.dbfield: col.value
                  for col in self.coldefs
                  if col.value and col.dbfield
                  }
        fields.update(common_fields)
        return fields

    @property
    def ins_fields(self) -> str:
        """Comma separated list of table fields for insert SQL query."""
        fields = ','.join(self.dbfields.keys())
        return fields

    @property
    def ins_values(self) -> str:
        """Comma separated list of values placeholders for insert SQL."""
        values = ','.join([f'%({k})s' for k in self.dbfields.keys()])
        return values

    @property
    def header_row(self) -> int:
        """Number of a header row in a workbook."""
        return self._row_header

    @header_row.setter
    def header_row(self, colnum: int):
        """Storing number of a header row in a workbook."""
        self._row_header = colnum

    @property
    def coldefs(self) -> int:
        """Number of used columns in a workbook."""
        return self._columns

    @property
    def comment(self) -> [str]:
        """Compose a row comment from all workbook cells."""
        return '<br>'.join(self._comments)

    @comment.setter
    def comment(self, text: str):
        if text:
            self._comments.append(text)

    def reset(self, values_only=False):
        """Reset all dynamic properties of all data fields of an agenda."""
        self._comments: [str] = []
        for col in self.coldefs:
            col.reset(values_only)

    def set_column_index(self, title: str, colnum: int) -> int:
        """Set index of a workbook column in an agenda record.

        Arguments
        ---------
        title : string
            Column header taken usually from the first workbook row.
        colnum : int
            Sequence number of a workbook column counting from 1.

        Returns
        -------
        int
            Index of a column determined by the input title in an agenda's
            data record counting from 0 or None, if column is not found.

        Notes
        -----
        - The method sanitizes the input title by substituting all new line
          characters with space.

        """
        title = title.replace('\n', ' ')
        for cn, col in enumerate(self.coldefs):
            if col.title == title:
                col.index = colnum
                return cn

    def check_row(self) -> bool:
        """Test for all mandatory data fields on determined value."""
        for col in self.coldefs:
            if not (col.optional or col.desc or col.value is not None):
                return False
        return True

    def check_agenda(self) -> bool:
        """Check presence of all mandatory data fields
        and at least one optional one in a data record.

        """
        flag_mandatory_fields = True
        flag_optional_fields = False
        for col in self.coldefs:
            if not col.optional and col.index is None:
                flag_mandatory_fields = False
            if col.optional and col.index is not None:
                flag_optional_fields = True
        return flag_mandatory_fields or flag_optional_fields

    def get_column_by_dbfield(self, dbfield: str) -> Column:
        """Find column object by database field name in the data record."""
        for col in self.coldefs:
            if col.dbfield == dbfield:
                return col

    def get_column_by_index(self, index: int) -> Column:
        """Find column object by column index in a workbook."""
        for col in self.coldefs:
            if col.index == index:
                return col

    def sanitize_comment(self, text: str) -> str:
        """Cleanup cell comment."""
        if text:
            text = text.replace('Libor Gabaj:\n', '')
        return text

    def round_column(self, coldef: Column) -> Column:
        """Round a data field value in a column definition, if it is of some
        numeric type and rounding is declared in the column definition.

        """
        if coldef.rounding and coldef.datatype in ['n', 'f']:
            coldef.value = round(coldef.value, coldef.rounding)
        return coldef

    def store_cell(self, cell: object, colnum: int) -> Column:
        """Store value and comment from a workbook cell in a column
        and return that column object for chaining.

        """
        coldef = self.get_column_by_index(colnum)
        # Ignore unexpected column
        if coldef is None:
            return
        coldef.value = None
        if coldef.desc:
            c = []
            if cell.value:
                coldef.value = cell.value
                c.append(str(cell.value))
            if cell.comment and cell.comment.content is not None:
                c.append(self.sanitize_comment(cell.comment.content))
            if len(c):
                self.comment = f'{coldef.title}: {"; ".join(c)}'
            return coldef
        if not cell.value:
            return coldef
        if cell.data_type == coldef.datatype:
            coldef.value = cell.value
            if cell.comment and cell.comment.content is not None:
                self.comment = self.sanitize_comment(cell.comment.content)
            if coldef.dbfield == 'price_orig':
                pricedef = self.get_column_by_dbfield('price')
                pricedef.value = coldef.value / Params.skeu
                self.round_column(pricedef)
                ccydef = self.get_column_by_dbfield('id_currency')
                ccydef.value = Params.jskccy
            return coldef
        else:
            self._logger.error(
                'Ignored cell "%s!%s%s" '
                'with unexpected data type "%s" '
                'for column "%s"',
                Source.wsheet.title,
                cell.column_letter,
                cell.row,
                cell.data_type,
                coldef.title
            )
            return coldef
