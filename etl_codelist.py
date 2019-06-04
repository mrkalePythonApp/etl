#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script for migrating individual code list table."""
__version__ = "0.1.0"
__status__ = "Alpha"
__author__ = "Libor Gabaj"
__copyright__ = "Copyright 2019, " + __author__
__credits__ = [__author__]
__license__ = "MIT"
__maintainer__ = __author__
__email__ = "libor.gabaj@gmail.com"

# Standard library modules
import os
import os.path
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


script = {
    'fullname': '',  # Name of this script including full path
    'basename': '',  # Name of this script excluding path but with extension
    'name': '',  # Bare name of this script
}

source = {
    'conn': None,
    'query': None,
    'cursor': None,
}


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
        conn, query, cursor,
    ) = (None, None, None)


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
        logger.debug("Database %s connected", config['database'])
        return conn
    except mysql.Error as err:
        if err.errno == mysql.errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Bad database %s credentials", config['database'])
        elif err.errno == mysql.errorcode.ER_BAD_DB_ERROR:
            logger.error("Database %s does not exist", config['database'])
        else:
            logger.error(err)
        raise Exception(mysql.Error)


def source_open():
    """Connect to a source database."""
    if Source.conn is None:
        try:
            Source.conn = connect_db(db.source_config)
        except Exception:
            raise


def source_close():
    """Close cursor and connection to a source database."""
    if Source.cursor is not None:
        Source.cursor.close()
    if Source.conn is not None:
        Source.conn.close()


def codelist_read(codelist):
    """Read content of a code list to a cursor.

    Arguments
    ---------
    codelist : str
        Root name of a code list database table.

    Returns
    -------
    connection : object
        Connection object to a database.

    """
    # Connect to the source database
    try:
        source_open()
    except Exception:
        logger.error(
            'Cannot connect to the source database %s',
            db.source_config['database']
            )
        return
    # Execute query
    Source.query = sql.query_compose(
        query_string=sql.source_codelist_read,
        table_prefix=sql.source_codelist_prefix,
        table_root=codelist,
        )
    Source.cursor = Source.conn.cursor(dictionary=True)
    Source.cursor.execute(Source.query)
    # Process records one by one
    for record in Source.cursor:
        print('{id}: {modified}'.format(**record))
    logger.debug(
        'Read %d records from database %s',
        Source.cursor.rowcount,
        db.source_config['database']
        )
    # Close cursor and connection to a databases
    source_close()


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
        description="ETL for individual code list, version "
        + __version__
    )
    # Options
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=__version__,
        help="Current version of the script."
    )
    parser.add_argument(
        "-v", "--verbose",
        choices=["debug", "info", "warning", "error", "critical"],
        default="debug",
        help="Level of logging to the console."
    )
    # Process command line arguments
    global cmdline
    cmdline = parser.parse_args()


def setup_logger():
    """Configure logging facility."""
    global logger
    logging.basicConfig(
        level=getattr(logging, cmdline.verbose.upper()),
        format="%(levelname)s:%(name)s: %(message)s",
    )
    logger = logging.getLogger(Script.name)
    logger.info("Script started")


def main():
    """Fundamental control function."""
    setup_params()
    setup_cmdline()
    setup_logger()
    # ETL process
    codelist_read('stay')
    logger.info("Script finished")


if __name__ == "__main__":
    main()
