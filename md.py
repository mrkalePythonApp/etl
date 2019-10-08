# -*- coding: utf-8 -*-
"""Script for showing modification datetime of migrated tables.

Notes
-----
- For each source and target table the latest modification datime is displayed.
- If some source table has latest modification datetime younger than the target
  one, it is flagged.
"""
__version__ = '0.3.0'
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
import datetime

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


class Source:
    """Status parameters of the data source."""

    (
        conn, query, cursor, table, database,
    ) = (None, None, None, None, None,)


class Target:
    """Status parameters of the data target."""

    (
        conn, query, cursor, table, database,
    ) = (None, None, None, None, None,)


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


def source_open():
    """Connect to a source database.

    Returns
    -------
    boolean
        Flag about successful processing.

    """
    if Source.conn is None:
        try:
            Source.conn = connect_db(db.source_config)
        except Exception:
            logger.error(
                'Cannot connect to the source database %s',
                Source.database
            )
            return False
    return True


def source_close():
    """Close cursor and connection to a source database."""
    # Close cursor
    if Source.cursor is not None:
        Source.cursor.close()
    # Close connection to database
    if Source.conn is not None:
        Source.conn.close()
    Source.conn = None
    Source.query = None
    Source.cursor = None
    Source.table = None


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
    desc = \
        f'Recent modification datetimes for code lists and agendas, ' \
        f'version {__version__}'
    parser = argparse.ArgumentParser(description=desc)
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
        help='Show codelist tables.'
    )
    parser.add_argument(
        '-a', '--agendas',
        action='store_true',
        help='Show agenda tables.'
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
    """List of source and target tables with modification datetimes.

    Arguments
    ---------
    table_prefix : str
        Prefix of tables.

    Returns
    -------
    list : dict
        List of source-target records for codelists or agendas according to
        to provided table prefix.

    """
    format = '%d.%m.%Y %H:%M:%S'
    format_db = '%Y-%m-%d %H:%M:%S'
    tables = [{
                'source_table': source_table,
                'source_datetime': None,
                'source_timestamp': None,
                'source_count': None,
                'target_table': target['table_target'],
                'target_datetime': None,
                'target_timestamp': None,
                'target_count': None,
              }
              for source_table, target
              in sql.source.items()
              if source_table.startswith(table_prefix)
              ]
    for i, table in enumerate(tables):
        # Source datetime
        Source.query = sql.compose_select(
            table['source_table'],
            'MAX(GREATEST(modified, created)), COUNT(*)'
        )
        Source.cursor = Source.conn.cursor()
        try:
            Source.cursor.execute(Source.query)
            record = Source.cursor.fetchone()
            timestamp = record[0]
            if isinstance(timestamp, str):
                timestamp = datetime.datetime.strptime(timestamp, format_db)
            tables[i]['source_timestamp'] = timestamp
            tables[i]['source_count'] = record[1]
            try:
                tables[i]['source_datetime'] = timestamp.strftime(format)
            except AttributeError as err:
                tables[i]['source_datetime'] = 'N/A'
                errmsg = \
                    f"{table['source_table']}" \
                    f".modified" \
                    f" - {err}"
                # logger.error(errmsg)
        except mysql.Error as err:
            logger.error(err)
        finally:
            Source.cursor.close()
        # Target datetime
        Target.query = sql.compose_select(
            table['target_table'],
            'MAX(GREATEST(modified, created)), COUNT(*)'
        )
        Target.cursor = Target.conn.cursor()
        try:
            Target.cursor.execute(Target.query)
            record = Target.cursor.fetchone()
            timestamp = record[0]
            if isinstance(timestamp, str):
                timestamp = datetime.datetime.strptime(timestamp, format_db)
            tables[i]['target_timestamp'] = timestamp
            tables[i]['target_count'] = record[1]
            try:
                tables[i]['target_datetime'] = timestamp.strftime(format)
            except AttributeError as err:
                tables[i]['target_datetime'] = 'N/A'
                errmsg = \
                    f"{table['target_table']}" \
                    f".modified" \
                    f" - {err}"
                # logger.error(errmsg)
        except mysql.Error as err:
            logger.error(err)
        finally:
            Target.cursor.close()
    return tables


def main():
    """Fundamental control function."""
    def esc(code):
        """ANSI Escape Codes."""
        return f'\033[{code}m'
    setup_params()
    setup_cmdline()
    setup_logger()
    if cmdline.codelists or cmdline.agendas:
        # Connect to source database
        Source.database = db.source_config['database']
        if not source_open():
            return
        # Connect to target database
        Target.database = db.target_config['database']
        if not target_open():
            return
        # Migrated tables
        sources = {
            'codelists': sql.source_table_prefix_codelist,
            'agendas': sql.source_table_prefix_agenda,
        }
        for source, prefix in sources.items():
            if not eval(f'cmdline.{source}'):
                continue
            tables = tablelist(prefix)
            print()
            print(f'{source.capitalize()}:')
            for table in tables:
                ansi = esc(0)
                if table['source_timestamp'] is None \
                or table['target_timestamp'] is None:
                    prefix = '???'
                    ansi = esc(96)  # Cyan
                elif table['source_timestamp'] > table['target_timestamp']:
                    prefix = '!!!'
                    ansi = esc(31)  # Red
                elif table['source_timestamp'] < table['target_timestamp']:
                    prefix = '<'
                    ansi = esc(93)  # Yellow
                elif table['source_timestamp'] == table['target_timestamp']:
                    prefix = '='
                else:
                    prefix = ''
                msg = \
                    f"{prefix.ljust(4)}" \
                    f"{table['source_table']} (" \
                    f"{table['source_datetime']}" \
                    f", {table['source_count']}" \
                    f") -> " \
                    f"{table['target_table']} (" \
                    f"{table['target_datetime']}" \
                    f", {table['target_count']}" \
                    f")"
                print(ansi + msg)
        print(esc(0))
        source_close()
        target_close()
    else:
        logger.warning('Nothing to show, see --help')


if __name__ == '__main__':
    main()
