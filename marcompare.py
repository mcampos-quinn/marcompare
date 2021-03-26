#!/usr/bin/env python3
'''
This is the FLASK_APP that runs the show.

First it inits the app based on the __init__.py file,
then runs the thing.
'''

import os

# local stuff
from app import create_app

app = create_app()

if __name__ == '__main__':
	app.run()
