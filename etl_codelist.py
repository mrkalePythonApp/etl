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

script_pathname = ''  # Name of this script including full path
script_basename = ''  # Name of this script excluding path but with extension
script_name = ''  # Bare name of this script


###############################################################################
# Actions
###############################################################################
def db_connect(dbconfig):
    """Connect to a database.

    Arguments
    ---------
    dbconfig : dict
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
        conn = mysql.connect(**dbconfig)
        return conn
    except mysql.Error as err:
        if err.errno == mysql.errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Bad database %s credentials", dbconfig.database)
        elif err.errno == mysql.errorcode.ER_BAD_DB_ERROR:
            logger.error("Database %s does not exist", dbconfig.database)
        else:
            logger.error(err)
        raise Exception(mysql.Error)
        return None


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
    conn_source = db_connect(db.source)
    if conn_source is None:
        return
    # Execute query
    query = sql.source_codelist_read % {'table_root': codelist}
    cursor = conn_source.cursor(dictionary=True)
    cursor.execute(query)
    # Process records one by one
    for record in cursor:
        print('{id}: {modified}'.format(**record))
    logger.debug(
        'Read %d records from database %s',
        cursor.rowcount,
        db.source['database']
        )
    # Close cursor and connection to a databases
    cursor.close()
    conn_source.close()


###############################################################################
# Setup functions
###############################################################################
def setup_params():
    """Determine script operational parameters."""
    global script_fullname, script_basename, script_name, service_flag
    script_fullname = os.path.splitext(os.path.abspath(__file__))[0]
    script_basename = os.path.basename(__file__)
    script_name = os.path.splitext(script_basename)[0]


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
        default="info",
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
    logger = logging.getLogger(script_name)
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
