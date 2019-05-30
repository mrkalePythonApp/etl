# -*- coding: utf-8 -*-
"""Module with connection strings to MySQL databases."""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = []
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'

# Standard library modules
# import time

# Custom modules
# import gbj_pythonlib_sw.config as modConfig
import credentials as modCredentials

db_config_source = {
  'user': modCredentials.source_db_user,
  'password': modCredentials.source_db_password,
  'host': 'localhost',
  'database': 'gabajovci',
  'raise_on_warnings': True
}

db_config_target = {
  'user': modCredentials.target_db_user,
  'password': modCredentials.target_db_password,
  'host': 'localhost',
  'database': 'rodina',
  'raise_on_warnings': True
}
