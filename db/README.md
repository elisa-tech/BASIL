# <img src="src/app/bgimages/basil.svg" alt= "BASIL" height="85">

# BASIL - Database

This repository folder host the source code of the BASIL Database management.

This project is using SQLAlchemy as Object-relational mapping framework. [SQLAlchemy](https://www.sqlalchemy.org/).

## Init the database

BASIL is configured by default to work with an sqlite database.
It is possible to use a different type of database configuring the SQLAlchemy **create_engine** method used in in the **db/db_orm.py** script.

The database is not shipped with the source code because can be generated running a python script.

To generate the default empty **db/sqlite3/basil.db** database:

```sh

# Move to the db/models directory
cd db && cd models

# Initialize the sqlite database, you will find it in db/sqlite3/basil.db
pdm run python3 init_db.py

```
