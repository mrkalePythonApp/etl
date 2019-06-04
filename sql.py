# -*- coding: utf-8 -*-
"""Module with SQL DML strings for MySQL databases."""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = []
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'

source_codelist_prefix = 'jos_codelist'
source_agenda_prefix = 'jos_familylist'
#
target_codelist_prefix = 'jos_codelist'
target_agenda_prefix = 'jos_familylist'

source_codelist_read = (
    "SELECT id AS id"
    ", created AS created, modified AS modified, published AS state"
    ", code_desc AS description, code_name AS title, code_abbr AS alias"
    " FROM %(table_prefix)s_%(table_root)s"
    )

source_agenda_read = (
    "SELECT id AS id"
    ", created AS created, modified AS modified, published AS state"
    ", item_desc AS description, item_name AS title, item_abbr AS alias"
    " FROM %(table_prefix)s_%(table_root)s"
    )


def query_compose(query_string, table_prefix, table_root):
    """Compose query string for table name parts.

    Arguments
    ---------
    query_string : str
        Raw query string with parameter placeholders.
    table_prefix : str
        Common part of a table name.
    table_root : str
        Specific part of a table name.

    Returns
    -------
    str
        Query string with real table name. However, it can contain placeholders
        for query parameters.

    """
    query_string = query_string % {
        'table_prefix': table_prefix,
        'table_root': table_root,
        }
    return query_string
