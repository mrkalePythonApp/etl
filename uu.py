# -*- coding: utf-8 -*-
"""Script for updating user ids in target codelist and agenda tables."""
__version__ = '0.1.2'
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

# Third party modules
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


class Target:
    """Status parameters of the data target."""

    (
        conn, query, cursor, table, database, codelists, agendas
    ) = (None, None, None, None, None, None, None,)


###############################################################################
# Actions
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
        description='Users update for entire code lists and agendas, version '
        + __version__
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
        default='info',
        help='Level of logging to the console.'
    )
    parser.add_argument(
        '-c', '--codelists',
        action='store_true',
        help='Update all target codelist tables.'
    )
    parser.add_argument(
        '-a', '--agendas',
        action='store_true',
        help='Update all target agenda tables.'
    )
    parser.add_argument(
        '-u', '--user',
        type=int,
        help='Joomla! user id for table records.'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List of target codelist and agenda tables.'
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


def tablelist(table_prefix):
    """List names of target table.

    Arguments
    ---------
    table_prefix : str
        Prefix of tables.

    Returns
    -------
    list : str
        List of full table names.

    """
    Target.query = sql.compose_tablelist(table_prefix)
    Target.cursor = Target.conn.cursor()
    try:
        Target.cursor.execute(Target.query)
        records = Target.cursor.fetchall()
        logger.debug(
            'Read %d tables for prefix %s.%s',
            Target.cursor.rowcount,
            Target.database,
            table_prefix
            )
        return records
    except mysql.Error as err:
        logger.error(err)
        return None


def update_users(table_list):
    """Update user ids in tables from provided list.

    Arguments
    ---------
    table_list : list of str
        Names of tables to be updated.

    Returns
    -------
    int
        Number of updated tables.

    """
    tables = 0
    if not isinstance(table_list, list):
        return tables
    for table in table_list:
        Target.table = table
        Target.query = sql.compose_update(
            table=Target.table,
            fields=sql.target_users,
            )
        Target.cursor = Target.conn.cursor()
        try:
            Target.cursor.execute(Target.query, {'user': cmdline.user})
            tables += 1
            logger.debug(
                'Updated %d records in table %s.%s with user %d',
                Target.cursor.rowcount,
                Target.database,
                Target.table,
                cmdline.user
                )
        except mysql.Error as err:
            logger.error(err)
    return tables


def main():
    """Fundamental control function."""
    setup_params()
    setup_cmdline()
    setup_logger()
    # Is there something to do?
    if not (cmdline.codelists or cmdline.agendas or cmdline.list):
        logger.warning('Nothing to do, see --help')
        return
    # Connect to target database
    Target.database = db.target_config['database']
    if not target_open():
        return
    # Codelist tables
    records = tablelist(sql.target_table_prefix_codelist)
    Target.codelists = [r[0] for r in records]
    # Agenda tables
    records = tablelist(sql.target_table_prefix_agenda)
    Target.agendas = [r[0] for r in records]
    # Print list of updated targets
    if cmdline.list:
        tables = ', '.join(Target.codelists)
        print('Codelists: {}'.format(tables))
        tables = ', '.join(Target.agendas)
        print('Agendas: {}'.format(tables))
    # Updates
    if cmdline.codelists or cmdline.agendas:
        if cmdline.user:
            if cmdline.codelists:
                tables = update_users(Target.codelists)
                logger.info(
                    'Updated %d codelist tables with user %d',
                    tables,
                    cmdline.user,
                    )
            if cmdline.agendas:
                tables = update_users(Target.agendas)
                logger.info(
                    'Updated %d agenda tables with user %d',
                    tables,
                    cmdline.user,
                    )
        else:
            logger.warning('No user id provided, see --help')
    target_close()


if __name__ == '__main__':
    main()
