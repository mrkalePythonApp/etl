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

source_table_template_codelist = 'jos_codelist_%(table_root)s'
source_table_template_agenda = 'jos_familylist_%(table_root)s'
target_table_template_codelist = 'lgbj_gbjcodes_%(table_root)s'
target_table_template_agenda = 'lgbj_gbjfamily_%(table_root)s'

# Columns aliases aligned with target column names
source_fields = {
    'codelist': (
        'id, created, modified, published AS state'
        ', code_name AS title, code_abbr AS alias, code_desc AS description'
        ),
    'asset': (
        'id, created, modified, published AS state'
        ', item_date AS date_on, item_name AS title, item_desc AS description'
        ', item_value_euro AS value, item_price_euro AS price'
        ', item_price_orig AS price_orig, item_currency_id AS id_currency'
        ', item_domain_id AS id_domain, item_asset_id AS id_asset'
        ),
}

# Target columns and their values
target_fields = {
    'codelist': {
        'fields': (
            'params, metakey, metadesc, metadata'
            ', id, created, modified, state, description, title, alias'
            ),
        'values': (
            '"", "", "", ""'
            ', %(id)s, %(created)s, %(modified)s, %(state)s'
            ', %(description)s, %(title)s, %(alias)s'
            ),
    },
}

target_users = 'created_by = %(user)s, modified_by = %(user)s'

# Map of source codelist table roots to target ones
map_codelist = {
    'activity': 'activities',
    'asset': 'assets',
    'commodity': 'commodities',
    'currency': 'currencies',
    'domain': 'domains',
    'location': 'locations',
    'staff': 'staffs',
    'stay': 'stays',
    'type': 'types',
    'unit': 'units',
}

# Map of source agenda table roots to target ones
map_agenda = {
    'asset': 'assets',
    'event': 'events',
    'expense': 'expenses',
    'fuel': 'fuels',
    'income': 'incomes',
    'vacation': 'vacations',
}


def compose_table(table_template, table_root):
    """Compose source table name for a codelist.

    Arguments
    ---------
    table_template : str
        Template for a table name.
    table_root : str
        Specific part of a table name.

    Returns
    -------
    str
        Real table name.

    """
    table_name = table_template % {'table_root': table_root}
    return table_name


def compose_select(table, fields):
    """Compose select query string.

    Arguments
    ---------
    table : str
        Real table name.
    fields : str
        List of table fields.

    Returns
    -------
    str
        Query string with real table name. However, it can contain placeholders
        for query parameters.

    """
    query = 'SELECT {} FROM {}'.format(fields, table)
    return query


def compose_insert(table, fields, values):
    """Compose insert command string.

    Arguments
    ---------
    table : str
        Real table name.
    fields : str
        List of table fields.
    values : dict
        Dictionary of table fields and their values.

    Returns
    -------
    str
        Query string with real table name. However, it can contain placeholders
        for query parameters.

    """
    query = 'INSERT INTO {} ({}) VALUES ({})'.format(table, fields, values)
    return query


def compose_update(table, fields):
    """Compose update query string.

    Arguments
    ---------
    table : str
        Real table name.
    fields : str
        List of table fields.

    Returns
    -------
    str
        Query string with real table name. However, it can contain placeholders
        for field values.

    """
    query = 'UPDATE {} SET {}'.format(table, fields)
    return query


def compose_truncate(table):
    """Compose truncate command string.

    Arguments
    ---------
    table : str
        Real table name.

    Returns
    -------
    str
        Query string with real table name.

    """
    query = 'TRUNCATE TABLE {}'.format(table)
    return query


def source_codelist(table_root):
    """Compose source table name for a codelist.

    Arguments
    ---------
    table_root : str
        Specific part of a table name.

    Returns
    -------
    str
        Real table name.

    """
    return compose_table(source_table_template_codelist, table_root)


def source_agenda(table_root):
    """Compose source table name for an agenda.

    Arguments
    ---------
    table_root : str
        Specific part of a table name.

    Returns
    -------
    str
        Real table name.

    """
    return compose_table(source_table_template_agenda, table_root)


def target_codelist(table_root):
    """Compose target table name for a codelist.

    Arguments
    ---------
    table_root : str
        Specific part of a table name.

    Returns
    -------
    str
        Real table name.

    """
    return compose_table(target_table_template_codelist, table_root)


def target_agenda(table_root):
    """Compose target table name for an agenda.

    Arguments
    ---------
    table_root : str
        Specific part of a table name.

    Returns
    -------
    str
        Real table name.

    """
    return compose_table(target_table_template_agenda, table_root)
