import sys

from cx_Freeze import setup, Executable

buildOptions = dict(packages = [],
			excludes=[],
			include_files=[])


base = 'Win32GUI' if sys.platform=='win32' else None	

executables = [Executable('foo.py', base=base, icon='mario.ico')]

setup(name="foo it up",
	  version = '99',
	  description = "AHH BAR FOO HAM SPAM",
	  options = dict(build_exe = buildOptions),
	  executables = executables)
