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


###############################################################################
# Source database
###############################################################################
source_table_template_agenda = 'jos_familylist_%(table_root)s'
source_table_template_codelist = 'jos_codelist_%(table_root)s'
source_table_fields_codelist = (
    'id, created, modified, published AS state'
    ', code_name AS title'
    ', code_abbr AS alias'
    ', code_desc AS description'
    )
source_table_fields_agenda = (
    'id, created, modified'
    ', published AS state'
    ', item_desc AS description'
    ', item_date AS date_on'
    )
source = {
    'jos_codelist_activity': {
        'table_target': 'lgbj_gbjcodes_activities',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_asset': {
        'table_target': 'lgbj_gbjcodes_assets',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_commodity': {
        'table_target': 'lgbj_gbjcodes_commodities',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_currency': {
        'table_target': 'lgbj_gbjcodes_currencies',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_domain': {
        'table_target': 'lgbj_gbjcodes_domains',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_location': {
        'table_target': 'lgbj_gbjcodes_locations',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_staff': {
        'table_target': 'lgbj_gbjcodes_staffs',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_stay': {
        'table_target': 'lgbj_gbjcodes_stays',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_type': {
        'table_target': 'lgbj_gbjcodes_types',
        'fields': source_table_fields_codelist,
    },
    'jos_codelist_unit': {
        'table_target': 'lgbj_gbjcodes_units',
        'fields': source_table_fields_codelist,
    },
    'jos_familylist_asset': {
        'table_target': 'lgbj_gbjfamily_assets',
        'fields': source_table_fields_agenda + (
            ', item_name AS title'
            ', item_value_euro AS value'
            ', item_price_euro AS price'
            ', item_price_orig AS price_orig'
            ', item_currency_id AS id_currency'
            ', item_domain_id AS id_domain'
            ', item_asset_id AS id_asset'
        )
    },
    'jos_familylist_event': {
        'table_target': 'lgbj_gbjfamily_events',
        'fields': source_table_fields_agenda + (
            ', item_name AS title'
            ', item_domain_id AS id_domain'
            ', item_activity_id AS id_activity'
        )
    }
}


###############################################################################
# Target database
###############################################################################
target_table_template_agenda = 'lgbj_gbjfamily_%(table_root)s'
target_table_template_codelist = 'lgbj_gbjcodes_%(table_root)s'
target_table_fields_codelist = (
    'params, metakey, metadesc, metadata'
    ', id, created, modified, state, description, title, alias'
    )
target_table_values_codelist = (
    '"", "", "", ""'
    ', %(id)s, %(created)s, %(modified)s, %(state)s'
    ', %(description)s, %(title)s, %(alias)s'
    )
target_users = 'created_by = %(user)s, modified_by = %(user)s'
target = {
    'lgbj_gbjcodes_activities': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_assets': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_commodities': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_currencies': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_domains': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_locations': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_staffs': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_stays': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_types': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
    'lgbj_gbjcodes_units': {
        'fields': target_table_fields_codelist,
        'values': target_table_values_codelist,
    },
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
