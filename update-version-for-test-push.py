#!/usr/bin/env python3
# vim: ts=4 sw=4 et
# coding: -*- utf-8 -*-

# This script takes the current version number (from the VERSION file,
# containing a valid Public version identifier), and turns it into a
# Developmental release.  It is meant to be run prior to uploading to Test
# PyPi, so that the version uploaded is unique, and is also 'earlier' (in
# version-numbering terms) than the public version identifier.

# For more information about version numbering, see
# https://packaging.python.org/en/latest/specifications/version-specifiers/

# © 2021 The Board of Trustees of the Leland Stanford Junior University.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import logging
import logging.config
import os
import pathlib
from sys import exit
from typing import *

# Configure program logging
log_level = 'INFO'
if 'LOG_LEVEL' in os.environ:
    log_level = os.environ['LOG_LEVEL']
logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "basic": {"format": "[%(levelname)s] %(message)s"}
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "formatter": "basic",
        },
    },
     "loggers": {"": {"level": log_level, "handlers": ["stderr"]}}
})

# Set up logging
logger = logging.getLogger()
debug = logger.debug
info = logger.info
error = logger.error

# Open up the version file
version_path = pathlib.Path('VERSION')
debug(f"Opening file {version_path}")
version_file = version_path.open(mode='r+', encoding='ascii')

# Read in the version string, and try splitting our version into three parts.
debug('Reading version line')
version_string = version_file.readline().rstrip("\n")
try:
    (a_str, b_str, c_str) = version_string.split('.')
except ValueError:
    error(f"Version '{version_string}' is not in the expected three-part form")
    exit(1)
info(f"Old version number was {a_str}.{b_str}.{c_str}")

# Convert the versions to int.
try:
    a = int(a_str)
    b = int(b_str)
    c = int(c_str)
except ValueError:
    error(f"Unable to parse '{a_str}', '{b_str}', or '{c_str}' as integers.")
    exit(1)

# Append `.dev` and the current date & time (to the second).
# NOTE: This can trigger a race condition, if multiple pushes happen around the
# same time.  If that happens, I'm sorry, I hope you (future me?) gets a laugh
# out of it!
version_string = f"{a}.{b}.{c}"
version_string += ('.dev' + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
info(f"New version number is {version_string}")

# Seek back and truncate the version file
debug('Preparing for write')
version_file.seek(os.SEEK_SET, 0)
version_file.truncate(0)

# Write out the new version, and close.
debug('Writing out new version')
version_file.write(f"{version_string}\n")
version_file.close()

# That's it!
exit(0)
