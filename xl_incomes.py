# -*- coding: utf-8 -*-
"""Script for migrating incomes from MS Excel to Family Chronicle."""
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


class Source:
    """Status parameters of the data source."""

    (
        file, juser, wbook, wsheet,
    ) = ('Mimoriadne príjmy.xlsx', 820, None, None,)


class Target:
    """Status parameters of the data target."""

    (
        conn, query, cursor, table, database, root, register,
    ) = (None, None, None, None, None, None, None,)


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

    def reset(self):
        self.valid = False


class Agenda(object):
    """MS Excel agenda column set."""

    def __init__(self):
        self._columns: [Column] = []

    @property
    def coldefs(self):
        return self._columns
    
    @property
    def comments(self):
        l = [c.comment.content for c in self.coldefs if c.comment]
        return '\n'.join(l)

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
    def get_columns(self):
        """Calculate number of active columns in MS Excel sheet."""
        cols = 0
        for col in self.coldefs:
            if col.index:
                cols += 1
        return cols

    def store_cell(self, cell, colnum):
        coldef = self.get_column_by_index(colnum)
        coldef.value = None
        coldef.comment = None
        if not cell.value:
            return
        if cell.data_type == coldef.datatype:
            coldef.value = cell.value
            coldef.comment = cell.comment
            return coldef
        else:
            logger.warning(
                'Ignored cell "%s!%s%s" ' \
                'with unexpected data type "%s" ' \
                'for column "%s"',
                Source.wsheet.title,
                cell.column_letter,
                cell.row,
                cell.data_type,
                coldef.title
            )


###############################################################################
# Agenda definitions
###############################################################################
class Income(Agenda):
    """MS Excel agenda column set."""

    def __init__(self):
        self._columns = [
            Column('Dátum', 'd', 'date_on'),
            Column('Príjem', 's', 'title'),
            Column('Suma €', 'n', 'price', optional=True),
            Column('Suma Sk', 'n', 'price_orig', optional=True),
        ]
    
    def store_cell(self, cell, colnum):
        coldef = super().store_cell(cell, colnum)
        if coldef and coldef.value and coldef.dbfield == 'price_orig':
            pricedef = self.get_column_by_dbfield('price')
            pricedef.value = coldef.value / 30.126
        return coldef

    def check_row(self):
        coldef = self.get_column_by_dbfield('date_on')
        return coldef.value and coldef.datatype == 'd'


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


def detect_agenda():
    """Determine the target agenda from the first row of a worksheet.

    Returns
    -------
    boolean
        Flag about successful processing.

    """
    income = Income()
    # Header row
    for cn, cell in enumerate(list(Source.wsheet)[0]):
        income.set_column_index(cell.value, cn)
    if not income.check_agenda():
        msg = 'Uknown agenda structure'
        logger.error(msg)
        return False
    # Data rows
    for row in Source.wsheet.iter_rows(
        min_row=2,
        max_col=income.get_columns() + 1):
        # Process columns of a row
        for cn, cell in enumerate(row):
            income.store_cell(cell, cn)
        # Ignore row with empty date column
        if not income.check_row():
            continue
        # Migrate row
        for cn, coldef in enumerate(income.coldefs):
            msg = f'{cn}. {coldef.value}'
            logger.debug(msg)


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
        logger.debug('Database %s connected', config['database'])
        return conn
    except mysql.Error as err:
        if err.errno == mysql.errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error('Bad database %s credentials', config['database'])
        elif err.errno == mysql.errorcode.ER_BAD_DB_ERROR:
            logger.error('Database %s does not exist', config['database'])
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
    if Target.conn is None:
        try:
            Target.conn = connect_db(db.target_config)
        except Exception:
            logger.error(
                'Cannot connect to the target database %s',
                Target.database
                )
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
        description='Migration the agenda "incomes" from MS Excel, version '
        + __version__
    )
    # Position arguments
    parser.add_argument(
        'workbook',
        nargs='?',
        default=Source.file,
        help='MS Excel workbook file, default: ' + Source.file
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
        default=Source.juser,
        help='Joomla! user id for migration, default: ' + str(Source.juser)
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
    # Process sheets
    # for Source.wsheet in list(Source.wbook):
    Source.wsheet = Source.wbook['2006']
    detect_agenda()
    Source.wsheet = Source.wbook['2003']
    detect_agenda()
        # break

    # Connect to target database
    # Target.database = db.target_config['database']
    # if not target_open():
    #     return
    # Close databases
    target_close()
    logger.info('Migration finished')


if __name__ == '__main__':
    main()
