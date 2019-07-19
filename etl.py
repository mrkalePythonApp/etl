# -*- coding: utf-8 -*-
"""Script for migrating individual code list or agenda table."""
__version__ = '0.5.0'
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


class Source:
    """Status parameters of the data source."""

    (
        conn, query, cursor, table, database, root, ALL,
    ) = (None, None, None, None, None, None, '*')


class Target:
    """Status parameters of the data target."""

    (
        conn, query, cursor, table, database, root, register,
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
    Target.conn = None
    Target.query = None
    Target.cursor = None
    Target.table = None


def migrate():
    """Migrate content of a source table to target one.

    Returns
    -------
    boolean
        Flag about successful processing.

    """
    # Check source table
    if Source.table not in sql.source:
        logger.warning(
            'Unexpected source table %s.%s ignored',
            Source.database, Source.table
            )
        return False
    # Read source table
    Source.query = sql.compose_select(
        table=Source.table,
        fields=sql.source[Source.table]['fields'],
        )
    Source.cursor = Source.conn.cursor(dictionary=True)
    try:
        Source.cursor.execute(Source.query)
        records = Source.cursor.fetchall()
        logger.debug(
            'Read %d records from table %s.%s',
            Source.cursor.rowcount,
            Source.database,
            Source.table
            )
    except mysql.Error as err:
        logger.error(err)
        return False
    # Truncate target table
    Target.table = sql.source[Source.table]['table_target']
    Target.query = sql.compose_truncate(Target.table)
    Target.cursor = Target.conn.cursor()
    try:
        Target.cursor.execute(Target.query)
        logger.debug(
            'Table %s.%s truncated',
            Target.database,
            Target.table
            )
    except mysql.Error as err:
        logger.error(err)
        return False
    # Insert to target table
    Target.query = sql.compose_insert(
        table=Target.table,
        fields=sql.target[Target.table]['fields'],
        values=sql.target[Target.table]['values'],
        )
    Target.cursor = Target.conn.cursor()
    try:
        Target.cursor.executemany(Target.query, records)
        logger.debug(
            'Inserted %d records to table %s.%s',
            Target.cursor.rowcount,
            Target.database,
            Target.table
            )
    except mysql.Error as err:
        logger.error(err)
        # return False
    # Update user in target table
    Target.query = sql.compose_update(
        table=Target.table,
        fields=sql.target_users,
        )
    Target.cursor = Target.conn.cursor()
    try:
        Target.cursor.execute(Target.query, {'user': cmdline.user})
        logger.debug(
            'Updated %d records in table %s.%s',
            Target.cursor.rowcount,
            Target.database,
            Target.table
            )
    except mysql.Error as err:
        logger.error(err)
        return False
    # Update user in registration table
    if Target.register:
        Target.query = sql.compose_update_register(
            register=Target.register,
            table=Target.table,
            fields=sql.target_users,
            )
        Target.cursor = Target.conn.cursor()
        try:
            Target.cursor.execute(Target.query, {'user': cmdline.user})
            logger.debug(
                'Updated %d records in table %s.%s',
                Target.cursor.rowcount,
                Target.database,
                Target.register
                )
        except mysql.Error as err:
            logger.error(err)
            return False
    # Success
    logger.info(
        'Table %s.%s migrated to %s.%s with %d records under user %d',
        Source.database,
        Source.table,
        Target.database,
        Target.table,
        Source.cursor.rowcount,
        cmdline.user,
        )
    return True


###############################################################################
# Setup functions
###############################################################################
def setup_params():
    """Determine script operational parameters."""
    global service_flag
    Script.fullname = os.path.splitext(os.path.abspath(__file__))[0]
    Script.basename = os.path.basename(__file__)
    Script.name = os.path.splitext(Script.basename)[0]


def setup_cmdline():
    """Define command line arguments."""
    parser = argparse.ArgumentParser(
        description='Migration individual code lists and agendas, version '
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
        '-c', '--codelist',
        help='Codelist, comma separated list of them,'
             ' or asterisk for all supported.'
    )
    parser.add_argument(
        '-a', '--agenda',
        help='Agenda, comma separated list of them,'
             ' or asterisk for all supported.'
    )
    parser.add_argument(
        '-u', '--user',
        type=int,
        default=0,
        help='Joomla! user id for migrated records.'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List of migrated codelists and agendas.'
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
    # Print list of migrated sources
    if cmdline.list:
        sources = {
            'codelists': sql.source_table_prefix_codelist,
            'agendas': sql.source_table_prefix_agenda,
        }
        for source, prefix in sources.items():
            tables = {
                k: v for k, v in sql.source.items()
                if k.startswith(prefix)
                }.keys()
            roots = ', '.join([k.replace(prefix, '', 1) for k in tables])
            print('Migrated {}: {}'.format(source, roots))
        return
    logger.info('Migration started')
    # Connect to source database
    Source.database = db.source_config['database']
    if not source_open():
        return
    # Connect to target database
    Target.database = db.target_config['database']
    if not target_open():
        return
    # Migrate codelists
    if cmdline.codelist is not None:
        Target.register = sql.compose_table(
            sql.target_table_prefix_codelist,
            sql.target_table_register_codelist,
        )
        if cmdline.codelist == Source.ALL:
            tables = [
                k for k, v in sql.source.items()
                if k.startswith(sql.source_table_prefix_codelist)
                ]
            for table in tables:
                Source.table = table
                migrate()
        else:
            for codelist in cmdline.codelist.split(','):
                Source.table = sql.compose_table(
                    sql.source_table_prefix_codelist,
                    codelist,
                )
                migrate()
        Target.register = None
    # Migrate agendas
    if cmdline.agenda is not None:
        if cmdline.agenda == Source.ALL:
            tables = [
                k for k, v in sql.source.items()
                if k.startswith(sql.source_table_prefix_agenda)
                ]
            for table in tables:
                Source.table = table
                migrate()
        else:
            for agenda in cmdline.agenda.split(','):
                Source.table = sql.compose_table(
                    sql.source_table_prefix_agenda,
                    agenda,
                )
                migrate()
    # Close all databases
    source_close()
    target_close()
    logger.info('Migration finished')


if __name__ == '__main__':
    main()
