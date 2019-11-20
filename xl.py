# -*- coding: utf-8 -*-
"""Script for migrating agendas from MS Excel to Family Chronicle."""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = [__author__]
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'

# Standard library modules
import os
import argparse
import logging
import mysql.connector as mysql
import openpyxl
import datetime
import dataclasses
from abc import ABC, abstractmethod

# Custom library modules
import dbconfig as db
import sql


###############################################################################
# Script global variables
###############################################################################
cmdline = None  # Object with command line arguments
logger = None  # Object with standard logging


###############################################################################
# Enumeration and parameter classes
###############################################################################
class Script:
    """Script parameters."""

    (
        fullname, basename, name,
    ) = ('', '', '',)


class Params:
    """Global business parameters."""

    (
        juser, jskccy
    ) = (820, 1)

class Source:
    """Status parameters of the data source."""

    (
        file, wbook, wsheet, agenda,
    ) = (None, None, None, None)


class Target:
    """Status parameters of the data target."""

    (
        conn, query, cursor, table, database, root, register,
    ) = (None, None, None, None, None, None, None,)


@dataclasses.dataclass
class Column:
    """MS Excel column definition of an agenda.

    - 'desc' determines that the column value is appended to the 'description'
       as comment and 'dbfield' is ignored.
    
    """
    title: str
    datatype: str = 's'
    dbfield: str = ''
    index: int = None
    optional: bool = False
    value: any = None
    comment: str = None
    rounding: int = None
    desc: bool = False

    def reset(self):
        self.index = None
        self.value = None
        self.comment = None


class Agenda(ABC):
    """MS Excel agenda column set."""

    def __init__(self):
        self._columns: [Column] = []

    @property
    @abstractmethod
    def agenda(self):
        ...

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
            'description': self.comments,
        }
        fields = {col.dbfield: col.value \
            for col in self.coldefs \
            if col.value and not col.desc
            }
        fields.update(common_fields)
        return fields

    @property
    def ins_fields(self):
        return ','.join(self.dbfields.keys())

    @property
    def ins_values(self):
        return ','.join([f'%({k})s' for k in self.dbfields.keys()])

    @property
    def header_row(self):
        return self._row_header

    @header_row.setter
    def header_row(self, colnum):
        self._row_header = colnum

    @property
    def coldefs(self):
        return self._columns

    @property
    def columns(self):
        """Calculate number of active columns in MS Excel sheet."""
        cols = 0
        for col in self.coldefs:
            if col.index is not None:
                cols += 1
        return cols

    @property
    def comments(self):
        l = [c.comment.content for c in self.coldefs if c.comment]
        return '\n'.join(l)

    def reset(self):
        for col in self.coldefs:
            col.reset()

    def set_column_index(self, title, colnum):
        """Find column and set it column index."""
        result = None
        title = title.replace('\n', ' ')
        for cn, col in enumerate(self.coldefs):
            if col.title == title:
                col.index = colnum
                result = cn
                break
        return result

    def check_row(self) -> bool:
        for col in self.coldefs:
            if not (col.optional or col.value):
                return False
        return True

    def check_agenda(self) -> bool:
        """Check presence of all mandatory columns
        and at least one optional one.
        
        """
        flag_mandatory_fields = True
        flag_optional_fields = False
        for col in self.coldefs:
            if not col.optional and col.index is None:
                flag_mandatory_fields = False
            if col.optional and col.index is not None:
                flag_optional_fields = True
        return flag_mandatory_fields and flag_optional_fields

    def get_column_by_dbfield(self, dbfield):
        """Find column object by database field in the target db."""
        for col in self.coldefs:
            if col.dbfield == dbfield:
                return col

    def get_column_by_index(self, index):
        """Find column object by column index in MS Excel."""
        for col in self.coldefs:
            if col.index == index:
                return col

    def store_cell(self, cell, colnum):
        coldef = self.get_column_by_index(colnum)
        coldef.value = None
        coldef.comment = None
        if coldef.desc:
            coldef.comment = cell.comment
            if cell.value:
                coldef.comment.content = f'{coldef.title}: {cell.value}'
                coldef.comment.content += ' ' + coldef.comment.content
                print('A.', coldef.comment.content)
            return
        print(coldef.title, cell.value)
        if not cell.value:
            return
        if cell.data_type == coldef.datatype:
            coldef.value = cell.value
            coldef.comment = cell.comment
            return self.round_column(coldef)
        else:
            logger.error(
                'Ignored cell "%s!%s%s" ' \
                'with unexpected data type "%s" ' \
                'for column "%s"',
                Source.wsheet.title,
                cell.column_letter,
                cell.row,
                cell.data_type,
                coldef.title
            )
        
    def round_column(self, coldef):
        if coldef.rounding and coldef.datatype in ['n', 'f']:
            coldef.value = round(coldef.value, coldef.rounding)
        return coldef


###############################################################################
# Sources definitions
###############################################################################
class Mimoriadne_prijmy(Agenda):
    """MS Excel workbook 'Mimoriadne príjmy.xlsx' column set."""

    def __init__(self):
        self._columns = [
            Column('Dátum', 'd', 'date_on'),
            Column('Príjem', 's', 'title'),
            Column('Suma €', 'n', 'price', optional=True, rounding=2),
            Column('Suma Sk', 'n', 'price_orig', optional=True, rounding=2),
            Column('Currency', 'n', 'id_currency', optional=True),
        ]

    @property
    def agenda(self):
        return 'incomes'

    def store_cell(self, cell, colnum):
        coldef = super().store_cell(cell, colnum)
        if coldef and coldef.value:
            if coldef.dbfield == 'price_orig':
                pricedef = self.get_column_by_dbfield('price')
                pricedef.value = coldef.value / 30.126
                self.round_column(pricedef)
                ccydef = self.get_column_by_dbfield('id_currency')
                ccydef.value = Params.jskccy
        return coldef


class Konopa_income(Agenda):
    """MS Excel workbook 'Konopa_income.xlsx' column set."""

    def __init__(self):
        self._columns = [
            Column('Dátum', 'd', 'date_on'),
            Column('Akcia', 's', 'title'),
            Column('Miesto', desc=True),
            Column('Čas', desc=True),
            Column('Hráčov', 'n', desc=True),
            Column('Môj honorár €', 'n', 'price', optional=True, rounding=2),
            Column('Môj honorár Sk', 'n', 'price_orig', optional=True, rounding=2),
            Column('Poznámka', desc=True),
            Column('Currency', 'n', 'id_currency', optional=True),
        ]

    @property
    def agenda(self):
        return 'incomes'

    def store_cell(self, cell, colnum):
        coldef = super().store_cell(cell, colnum)
        if coldef and coldef.value:
            if coldef.dbfield == 'price_orig':
                pricedef = self.get_column_by_dbfield('price')
                pricedef.value = coldef.value / 30.126
                self.round_column(pricedef)
                ccydef = self.get_column_by_dbfield('id_currency')
                ccydef.value = Params.jskccy
        return coldef


###############################################################################
# MS Excel actions
###############################################################################
def source_open():
    """Open a source MS Excel spreadsheet file.

    Returns
    -------
    boolean
        Flag about successful processing.

    """
    try:
        Source.wbook = openpyxl.load_workbook(cmdline.workbook)
    except Exception:
        logger.error(
            'Cannot open the MS Excel workbook %s',
            cmdline.workbook
        )
        return False
    return True


def migrate_sheet():
    """Migrate worksheet to target agenda.

    Returns
    -------
    boolean
        Flag about successful processing.

    """
    a = Source.agenda
    a.reset()
    # Header row - First one with non-empty first column
    for row in Source.wsheet.iter_rows(min_row=1):
        cell = row[0]
        if cell.value:
            a.header_row = cell.row
            for cn, cell in enumerate(row):
                a.set_column_index(cell.value, cn)
            if not a.check_agenda():
                msg = 'Uknown agenda structure'
                logger.error(msg)
                return False
            break
    if not a.header_row:
        msg = 'No header row detected.'
        logger.error(msg)
        return False
    # Data rows
    rows = 0
    for row in Source.wsheet.iter_rows(
        min_row=a.header_row + 1,
        max_col=a.columns
    ):
        # Process columns of a row
        for cn, cell in enumerate(row):
            a.store_cell(cell, cn)
        # Ignore row with empty date column
        if not a.check_row():
            continue
        # Insert row to target table
        Target.query = sql.compose_insert(
            table=Target.table,
            fields=a.ins_fields,
            values=a.ins_values,
            )
        print(Target.query)
        Target.cursor = Target.conn.cursor()
        try:
            Target.cursor.execute(Target.query, a.dbfields)
            rows += 1
        except mysql.Error as err:
            logger.error(err)
            # return False
    logger.info(
        'Migrated %d rows from sheet "%s"',
        rows,
        Source.wsheet.title,
    )


###############################################################################
# Database actions
###############################################################################
def connect_db(config):
    """Connect to a database.

    Arguments
    ---------
    config : dict
        Connection configuration to a database.

    Returns
    -------
    connection : object
        Connection object to a database.

    Raises
    -------
    mysql.connector.Error
        Native exception of the database connector.

    """
    try:
        conn = mysql.connect(**config)
        logger.info('Database "%s" connected', config['database'])
        return conn
    except mysql.Error as err:
        if err.errno == mysql.errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error('Bad database "%s" credentials', config['database'])
        elif err.errno == mysql.errorcode.ER_BAD_DB_ERROR:
            logger.error('Database "%s" does not exist', config['database'])
        else:
            logger.error(err)
        raise


def target_open():
    """Connect to a target database.

    Returns
    -------
    boolean
        Flag about successful processing.

    """
    # Connect to database
    Target.database = db.target_config['database']
    if Target.conn is None:
        try:
            Target.conn = connect_db(db.target_config)
        except Exception:
            logger.error(
                'Cannot connect to the target database "%s"',
                Target.database
                )
            return False
    # Truncate target table
    Target.query = sql.compose_truncate(Target.table)
    Target.cursor = Target.conn.cursor()
    try:
        Target.cursor.execute(Target.query)
        logger.info(
            'Table "%s.%s" truncated',
            Target.database,
            Target.table
        )
    except mysql.Error as err:
        logger.error(err)
        return False
    return True


def target_close():
    """Close cursor and connection to a target database."""
    # Close cursor
    if Target.cursor is not None:
        Target.cursor.close()
    # Close connection to database
    if Target.conn is not None:
        Target.conn.close()
    Target.conn = None
    Target.query = None
    Target.cursor = None
    Target.table = None


###############################################################################
# Setup functions
###############################################################################
def setup_params():
    """Determine script operational parameters."""
    Script.fullname = os.path.splitext(os.path.abspath(__file__))[0]
    Script.basename = os.path.basename(__file__)
    Script.name = os.path.splitext(Script.basename)[0]


def setup_cmdline():
    """Define command line arguments."""
    parser = argparse.ArgumentParser(
        description='Migration of an agenda from provided MS Excel, version '
        + __version__
    )
    # Position arguments
    parser.add_argument(
        'workbook',
        choices=[
            'Mimoriadne príjmy.xlsx',
            'Konopa_income.xlsx',
            ],
        help='MS Excel workbook file.'
    )
    # Options
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=__version__,
        help='Current version of the script.'
    )
    parser.add_argument(
        '-v', '--verbose',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='debug',
        help='Level of logging to the console.'
    )
    parser.add_argument(
        '-u', '--user',
        type=int,
        default=Params.juser,
        help='Joomla! user id for migration, default: ' + str(Params.juser)
    )
    # Process command line arguments
    global cmdline
    cmdline = parser.parse_args()


def setup_logger():
    """Configure logging facility."""
    global logger
    logging.basicConfig(
        level=getattr(logging, cmdline.verbose.upper()),
        format='%(levelname)s:%(name)s: %(message)s',
    )
    logger = logging.getLogger(Script.name)


def main():
    """Fundamental control function."""
    setup_params()
    setup_cmdline()
    setup_logger()
    logger.info('Migration started')
    # Connect to MS Excel
    if not source_open():
        return
    if cmdline.workbook == 'Mimoriadne príjmy.xlsx':
        Source.agenda = Mimoriadne_prijmy()
        Target.table = sql.compose_table(
            sql.target_table_prefix_agenda,
            Source.agenda.agenda)
    if cmdline.workbook == 'Konopa_income.xlsx':
        Source.agenda = Konopa_income()
        Target.table = sql.compose_table(
            sql.target_table_prefix_agenda,
            Source.agenda.agenda)
    # Connect to target database
    if target_open():
        # Process sheets
        for Source.wsheet in list(Source.wbook):
            migrate_sheet()
    # Close databases
    target_close()
    logger.info('Migration finished')


if __name__ == '__main__':
    main()
