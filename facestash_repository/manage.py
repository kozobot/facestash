#!/usr/bin/env python
from migrate.versioning.shell import main

if __name__ == '__main__':
    main(repository='facestash_repository', url='sqlite:///api/facestash.db', debug='False')
