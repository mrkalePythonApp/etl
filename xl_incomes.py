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
        file, juser, wbook,
    ) = ('Mimoriadne príjmy.xlsx', 820, None,)


class Target:
    """Status parameters of the data target."""

    (
        conn, query, cursor, table, database, root, register,
    ) = (None, None, None, None, None, None, None,)


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
    # Connect to target database
    # Target.database = db.target_config['database']
    # if not target_open():
    #     return
    # Close databases
    target_close()
    logger.info('Migration finished')


if __name__ == '__main__':
    main()
