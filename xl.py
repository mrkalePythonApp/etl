# -*- coding: utf-8 -*-
"""Script for migrating agendas from MS Excel to Family Chronicle."""
__version__ = '0.2.0'
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
from importlib import util as imp

# Custom library modules
import dbconfig as db
import sql
from xl_agenda import Params, Source, Agenda


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


class Target:
    """Parameters of the data target."""

    (
        host, conn, query, cursor, table, database, root, register,
    ) = (None, None, None, None, None, None, None, None,)


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
        Source.wbook = openpyxl.load_workbook(Source.agenda.excel, data_only=True)
    except Exception:
        logger.error(
            'Cannot open the MS Excel workbook "%s"',
            Source.agenda.excel
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
        a.reset(values_only=True)
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
        'Migrated %d rows from sheet "%s"',
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
        help='MS Excel workbook definition module name.'
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
    # Import plugin module
    module_name = cmdline.workbook
    file_path = f'{Script.name}_{module_name}.py'
    try:
        spec = imp.spec_from_file_location(module_name, file_path)
        plugin = imp.module_from_spec(spec)
        spec.loader.exec_module(plugin)
    except Exception:
        logger.error( 'Cannot load module "%s"', file_path)
        return
    # Connect to MS Excel workbook
    Source.agenda = plugin.workbook()
    Source.agenda.logger = logger
    if not source_open():
        return
    # Connect to target database
    Target.table = sql.compose_table(
        sql.target_table_prefix_agenda,
        Source.agenda.agenda)
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
