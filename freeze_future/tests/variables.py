
from os.path import join
import os

NAME = 'foo'
VERSION = '99'
DESCRIPTION = 'so much foo bar AHH'
PACKAGES_INCLUDES_EXCLUDES = dict(
									packages = [],
									excludes=[],
									include_files=[])
DEFAULT_OPTIONS = dict(
				name = NAME,
				version= VERSION ,
				options=dict(build_exe=PACKAGES_INCLUDES_EXCLUDES))

if os.path.exists('example'):
	#~ print(os.getcwd())
	ICON = join(os.getcwd(), 'example','mario.ico')
	SCRIPT = join(os.getcwd(), 'example', 'simple_working.py')
else:
	ICON = join(os.getcwd(), 'freeze_future', 'tests', 'example','mario.ico')
	SCRIPT = join(os.getcwd(), 'freeze_future', 'tests','example', 'simple_working.py')
