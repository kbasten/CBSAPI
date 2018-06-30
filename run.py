import pathlib
import sys

sys.path.insert(0, (pathlib.Path.cwd() / 'cbsapi').as_posix())

from cbsapi import app

app.run(**app.config['FLASK'])
