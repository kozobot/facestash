# FaceStash
Face recognition companion app to StashApp

* Must have the stash app installed.
  * Install the facestash plugin
* Run the facestash service
  * Configure API Key
* Run the facestash Generate Performers task

## Set Up
 
### Docker
 
### Database
Initialize the database management.  This only needed to be done once.  These files are now checked in.
 ```shell script
migrate create facestash_repository "FaceStash"
migrate manage facestash_repository/manage.py --repository=facestash_repository --url=sqlite:///api/facestash.db
```

Create the database
```python
import sqlite3
sqlite3.connect('api/facestash.db')
```

Create the database schema
```shell script
python facestash_repository/manage.py version_control
python facestash_repository/manage.py upgrade
```

