*************************
Purpose of the repository
*************************

The repository contains a set of Python scripts for migrating custom code lists
and agendas from previous version of family chronicle based on system
Joomla! 1.5 to current version based on system Joomla! 3.


Scripts
=======
Each script provides help information by command line option ``-h``.

**etl.py** (*Extract, Transform, Load*)
  Migrating code lists and agendas including showing list of their
  source tables.

**uu.py** (*Update Users*)
  Updating user ids (``created_by``, ``modiefied_by``) in all target code list and
  agenda tables including showing list of them with provided user id.
  It is useful because on each database (old, new, test one) the `webmaster`
  user id is usually different.

Other files
===========

**dbconfig.py.sample**
  Source and target storage (db servers) configurations with placeholders for
  credentials and database names. This file should be copied to ``dbconfig.py``
  with updated credentials for particular storage(s).

**sql.py**
  Library with SQL statement string (queries) and list and parameters of
  migrated code list and agenda tables.
