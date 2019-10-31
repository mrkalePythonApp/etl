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
        juser, jskccy, skeu, rows,
    ) = (820, 1, 30.126, 0)

class Source:
    """Parameters of the data source."""

    (
        file, wbook, wsheet, agenda,
    ) = (None, None, None, None)


class Target:
    """Parameters of the data target."""

    (
        host, conn, query, cursor, table, database, root, register,
    ) = (None, None, None, None, None, None, None, None,)


@dataclasses.dataclass
class Column:
    """MS Excel column definition of an agenda."""
    title: str
    datatype: str
    dbfield: str
    index: int = None
    optional: bool = False
    value: any = None
    comment: str = None
    rounding: int = None

    def reset(self):
        """Initialize dynamic fields of a data record."""
        self.index = None
        self.value = None
        self.comment = None


class Agenda(object):
    """MS Excel workbook of an agenda processing."""

    def __init__(self):
        """Create the class instance - constructor."""
        self._columns: [Column] = []

    @property
    def dbfields(self) -> dict:
        """Common table fields for all target database tables."""
        now = datetime.datetime.now()
        return {
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

    @property
    def ins_fields(self) -> str:
        """Comma separated list of table fields for insert SQL query."""
        return ','.join(self.dbfields.keys())

    @property
    def ins_values(self) -> str:
        """Comma separated list of values placeholders for insert SQL."""
        return ','.join([f'%({k})s' for k in self.dbfields.keys()])

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
    def columns(self) -> int:
        """Calculate number of used columns in a workbook."""
        cols = 0
        for col in self.coldefs:
            if col.index is not None:
                cols += 1
        return cols

    @property
    def comments(self) -> str:
        """Cummulative comment from all workbook cells."""
        l = [c.comment.content for c in self.coldefs if c.comment]
        return '\n'.join(l)

    def reset(self):
        """Reset all dynamic properties of all data fields of an agenda."""
        for col in self.coldefs:
            col.reset()

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
            if not (col.optional or col.value is not None):
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
        return flag_mandatory_fields and flag_optional_fields

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

    def store_cell(self, cell: object, colnum: int) -> Column:
        """Store value and comment from a workbook cell in a column
        and return that column object for chaining.

        """
        coldef = self.get_column_by_index(colnum)
        coldef.value = None
        coldef.comment = None
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

    def round_column(self, coldef: Column) -> Column:
        """Round a data field value in a column definition, if it is of some
        numeric type and rounding is declared in the column definition.

        """
        if coldef.rounding and coldef.datatype in ['n', 'f']:
            coldef.value = round(coldef.value, coldef.rounding)
        return coldef


###############################################################################
# Agenda definitions
###############################################################################
class Income(Agenda):
    """MS Excel agenda column set."""

    def __init__(self):
        """Definition of agenda workbook columns and their relation to target
        database table columns."""
        self._columns = [
            Column('Dátum', 'd', 'date_on'),
            Column('Príjem', 's', 'title'),
            Column('Suma €', 'n', 'price', optional=True, rounding=2),
            Column('Suma Sk', 'n', 'price_orig', optional=True, rounding=2),
            Column('Currency', 'n', 'id_currency', optional=True),
        ]

    @property
    def dbfields(self) -> dict:
        """Adding specific table fields for the agenda to common ones."""
        fields = {col.dbfield: col.value for col in self.coldefs if col.value}
        fields.update(super().dbfields)
        return fields

    def store_cell(self, cell: object, colnum: int) -> Column:
        """Additional specific actions at storing a workbook cell."""
        coldef = super().store_cell(cell, colnum)
        if coldef and coldef.value:
            if coldef.dbfield == 'price_orig':
                pricedef = self.get_column_by_dbfield('price')
                pricedef.value = coldef.value / Params.skeu
                self.round_column(pricedef)
                ccydef = self.get_column_by_dbfield('id_currency')
                ccydef.value = Params.jskccy
        return coldef


###############################################################################
# MS Excel actions
###############################################################################
def source_open() -> bool:
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


def migrate_sheet() -> bool:
    """Migrate workbook to the target agenda.

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
        Target.cursor = Target.conn.cursor()
        try:
            Target.cursor.execute(Target.query, a.dbfields)
            rows += 1
        except mysql.Error as err:
            logger.error(err)
    Params.rows += rows
    logger.info(
        '%d rows from sheet "%s"',
        rows,
        Source.wsheet.title,
    )


###############################################################################
# Database actions
###############################################################################
def connect_db(config: dict) -> object:
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
        logger.debug(
            'Database "%s//%s" connected',
            config['host'],
            config['database'],
            )
        return conn
    except mysql.Error as err:
        if err.errno == mysql.errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error('Bad database "%s" credentials', config['database'])
        elif err.errno == mysql.errorcode.ER_BAD_DB_ERROR:
            logger.error('Database "%s" does not exist', config['database'])
        else:
            logger.error(err)
        raise


def target_open() -> bool:
    """Connect to a target database.

    Returns
    -------
    boolean
        Flag about successful processing.

    """
    # Connect to database
    Target.host = db.target_config['host']
    Target.database = db.target_config['database']
    if Target.conn is None:
        try:
            Target.conn = connect_db(db.target_config)
        except Exception:
            logger.error(
                'Cannot connect to the target database "%s"',
                Target.database,
                )
            return False
    # Truncate target table
    Target.query = sql.compose_truncate(Target.table)
    Target.cursor = Target.conn.cursor()
    try:
        Target.cursor.execute(Target.query)
        logger.debug(
            'Table "%s" truncated',
            Target.table,
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
        'agenda',
        choices=['incomes'],
        help='Migrated agenda.'
    )
    parser.add_argument(
        'workbook',
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
    # Connect to MS Excel workbook
    if not source_open():
        return
    if cmdline.agenda == 'incomes':
        Source.agenda = Income()
    # Store agenda parameters
    Target.table = sql.compose_table(
        sql.target_table_prefix_agenda,
        cmdline.agenda)
    # Migrate sheets of a workbook
    if target_open():
        logger.info(
            'START -- Migration to database table "%s//%s.%s"',
            Target.host,
            Target.database,
            Target.table,
            )
        for Source.wsheet in list(Source.wbook):
            migrate_sheet()
        logger.info(
            'STOP -- Migrated %d rows in total',
            Params.rows,
            )
    # Close databases
    target_close()


if __name__ == '__main__':
    main()
