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
    },
    'jos_familylist_expense': {
        'table_target': 'lgbj_gbjfamily_expenses',
        'fields': source_table_fields_agenda + (
            ', item_name AS title'
            ', item_units AS quantity'
            ', item_price_euro AS price'
            ', item_price_orig AS price_orig'
            ', item_domain_id AS id_domain'
            ', item_commodity_id AS id_commodity'
            ', item_type_id AS id_type'
            ', item_unit_id AS id_unit'
            ', item_currency_id AS id_currency'
        )
    },
    'jos_familylist_fuel': {
        'table_target': 'lgbj_gbjfamily_fuels',
        'fields': source_table_fields_agenda + (
            ', item_volume AS quantity'
            ', item_tacho AS tacho'
            ', item_period AS period'
            ', item_distance AS distance'
            ', item_consumption AS consumption'
            ', item_domain_id AS id_domain'
        )
    },
    'jos_familylist_income': {
        'table_target': 'lgbj_gbjfamily_incomes',
        'fields': source_table_fields_agenda + (
            ', item_name AS title'
            ', item_price_euro AS price'
            ', item_price_orig AS price_orig'
            ', item_domain_id AS id_domain'
            ', item_currency_id AS id_currency'
            ', item_asset_id AS id_asset'
        )
    },
    'jos_familylist_vacation': {
        'table_target': 'lgbj_gbjfamily_vacations',
        'fields': source_table_fields_agenda + (
            ', item_name AS title'
            ', item_date1 AS date_off'
            ', item_stay_id AS id_stay'
            ', item_staff_id AS id_staff'
        )
    },
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
target_table_fields_agenda = (
    'params, metakey, metadesc, metadata'
    ', id, created, state, description'
    ', modified'
    ', date_on'
    )
target_table_values_agenda = (
    '"", "", "", ""'
    ', %(id)s, %(created)s, %(state)s, %(description)s'
    ', IFNULL(%(modified)s, %(created)s)'
    ', %(date_on)s'
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
    'lgbj_gbjfamily_assets': {
        'fields': target_table_fields_agenda + (
            ', title, value, price'
            ', price_orig'
            ', id_domain, id_currency, id_asset'
        ),
        'values': target_table_values_agenda + (
            ', %(title)s, %(value)s, %(price)s'
            ', IF(%(price_orig)s, %(price_orig)s, NULL)'
            ', %(id_domain)s, %(id_currency)s, %(id_asset)s'
        ),
    },
    'lgbj_gbjfamily_events': {
        'fields': target_table_fields_agenda + (
            ', title'
            ', id_domain, id_activity'
        ),
        'values': target_table_values_agenda + (
            ', %(title)s'
            ', %(id_domain)s, %(id_activity)s'
        ),
    },
    'lgbj_gbjfamily_expenses': {
        'fields': target_table_fields_agenda + (
            ', title, quantity, price'
            ', price_unit'
            ', price_orig'
            ', id_domain, id_currency, id_commodity'
            ', id_type, id_unit'
        ),
        'values': target_table_values_agenda + (
            ', %(title)s, %(quantity)s, %(price)s'
            ', IF(%(quantity)s IN (0, 1), NULL, %(price)s / %(quantity)s)'
            ', IF(%(price_orig)s, %(price_orig)s, NULL)'
            ', %(id_domain)s, %(id_currency)s, %(id_commodity)s'
            ', %(id_type)s, %(id_unit)s'
        ),
    },
    'lgbj_gbjfamily_fuels': {
        'fields': target_table_fields_agenda + (
            ', quantity, tacho, period'
            ', distance, consumption'
            ', id_domain'
        ),
        'values': target_table_values_agenda + (
            ', %(quantity)s, %(tacho)s, %(period)s'
            ', %(distance)s, %(consumption)s'
            ', %(id_domain)s'
        ),
    },
    'lgbj_gbjfamily_incomes': {
        'fields': target_table_fields_agenda + (
            ', title, price'
            ', price_orig'
            ', id_domain, id_currency, id_asset'
        ),
        'values': target_table_values_agenda + (
            ', %(title)s, %(price)s'
            ', IF(%(price_orig)s, %(price_orig)s, NULL)'
            ', %(id_domain)s, %(id_currency)s, %(id_asset)s'
        ),
    },
    'lgbj_gbjfamily_vacations': {
        'fields': target_table_fields_agenda + (
            ', title, date_off'
            ', period'
            ', id_stay, id_staff'
        ),
        'values': target_table_values_agenda + (
            ', %(title)s, %(date_off)s'
            ', datediff(%(date_off)s, %(date_on)s) + 1'
            ', %(id_stay)s, %(id_staff)s'
        ),
    },
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
