import glob
from setuptools import find_packages, setup

PACKAGE = 'verarun'
VERSION = '0.0.20'

setup(
    name = PACKAGE,
    version = VERSION,
    description = 'VERA job submitter',
    license = '3-Clause BSD',
    #url = 'https://github.com/CASL/VERAview/',
    #py_modules = [ 'veraview' ],
    package_data = { '': [ '*.conf', '*.pbs', '*.json', '*.sh' ] },
    packages = find_packages( 'src' ),
    package_dir = { '': 'src' },
    install_requires =
      [
	'six'
	#'argparse >= 1.1',
	#'logging', 'os', 'six', 'sys', 'threading', 'time', 'traceback'
      ],
    scripts = [ 'bin/verarun', 'bin/verastat' ],
    zip_safe = False
    )
