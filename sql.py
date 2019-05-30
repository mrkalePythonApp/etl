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

source_codelist_read = (
    "SELECT id AS id"
    ", created AS created, modified AS modified, published AS state"
    ", code_desc AS description, code_name AS title, code_abbr AS alias"
    " FROM jos_codelist_%s"
    )

source_agenda_read = (
    "SELECT id AS id"
    ", created AS created, modified AS modified, published AS state"
    ", item_desc AS description, item_name AS title, item_abbr AS alias"
    " FROM jos_familylist_%s"
    )
