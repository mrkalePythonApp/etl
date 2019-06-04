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
import credential

###############################################################################
# Source database resources
###############################################################################
source_config = {
  'user': credential.source_db_user,
  'password': credential.source_db_password,
  'host': 'localhost',
  'database': 'gabajovci',
  'raise_on_warnings': True
}

target_config = {
  'user': credential.target_db_user,
  'password': credential.target_db_password,
  'host': 'localhost',
  'database': 'rodina',
  'raise_on_warnings': True
}
