'''
Simple working can we changed to anything u want just make sure it exits
'''
from __future__ import with_statement
from __future__ import print_function

import sys
import os
import subprocess
import pdb
import copy
import time
import zipfile
import pytest

import freeze_future
import variables as V
from utils import really_rmtree, InMemoryWriter, extract_zipfile

WORKING_SCRIPT = V.SCRIPT
ORIGINAL_CWD = os.getcwd()

if sys.version_info[0] > 2:
	PY3 = True
else:
	PY3 = False


class TestSetupTools():
	'''Make sure setuptools gets through untouched, Setuptools needs to be run before py2exe or other stuff
	patch it'''
	
	def teardown_class(cls):	#WHY IS IT DISTUTILS WORKS WITH TEARDOWN AND SETUPTOOLS NOT
		cleanup_dirs()
	

	def setuptools_setup(self, name, script, **changes):
		from setuptools import setup
		new_script = make_new_script_name(script)
		
		changes['scripts'] = [new_script]
		base_options = copy.deepcopy(V.DEFAULT_OPTIONS)
		changes.update({'name':name})
		base_options.update(changes)
		
		return setup, base_options, new_script		


	def test_setuptools_detected(self):
		'''make sure freeze_future knows that setuptoos is being used'''
		setup, options, name = self.setuptools_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.detect_freezer(options) == 'distutils'	# Right now setuptools is not distingued from distutils

	def test_setuptools_return_when_no_future_import(self):
		'''Make sure we don't do any work if not using the future library'''	
		setup, options, name = self.setuptools_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.setup(setup, **options) == False

	
	def test_setuptools_return_when_using_future(self):
		'''Tests that a script with the future imports runs as normal'''			
		setup, options, new_script = self.setuptools_setup('should run the setup stuff', 'disturils_return_working.py')
		insert_code(new_script,
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()")
					
		dummy_setup = lambda *args, **kwargs: 0
		
		assert freeze_future.setup(dummy_setup, **options) == False


	def test_setuptools_working(self):
		'''Test a small script to make sure it builds properly'''
		setup, options, name = self.setuptools_setup('Simple Working', WORKING_SCRIPT)
		setup(**options)
		assert run_script(WORKING_SCRIPT, freezer='setuptools')


	def test_setuptools_future(self):
		'''Testing adding the future imports doesn't fuck up the building'''
		setup, options, new_script = self.setuptools_setup('Working with Future Import', 'future_working.py')
		
		insert_code(new_script,
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()")

		setup(**options)
		assert run_script(new_script, freezer='setuptools')


	def test_setuptools_future_2(self):
		'''tests working with alot of imports urllib etc'''
		setup, options, new_script = self.setuptools_setup('cxfreeze fixed', 'cxfreeze_fixed.py')
		
		insert_code(new_script, 
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()",
					"import urllib.request, urllib.error, urllib.parse",
					"import collections",
					"from itertools import filterfalse",
					"from subprocess import getoutput",
					"from builtins import str",
					"from builtins import range",)
		
		setup(**options)
		assert run_script(new_script, freezer='setuptools')

class TestPy2exe():
	# http://www.py2exe.org/index.cgi/ListOfOptions
	def setup_class(cls):
		import py2exe
		cls.old_arg = sys.argv[1]
		sys.argv[1] = 'py2exe'

	def teardown_class(cls):
		sys.argv[1] = cls.old_arg
		# Unlike cxfreeze somehow if i cleanup after each build it fucks up...,
		# We cleanup at the end of the class
		cleanup_dirs()


	def py2exe_setup(self, name, script, **changes):
		from distutils.core import setup
		new_script = make_new_script_name(script)
		
		base_options = copy.deepcopy(V.DEFAULT_OPTIONS)
		changes['windows'] = [new_script]
		base_options.update(changes)
		base_options['py2exe'] = base_options['options']['build_exe']
		del base_options['options']['build_exe']
		changes.update({'name':name})
		
		return setup, base_options, new_script


	def test_py2exe_detected(self):
		'''make sure freeze_future knows that setuptoos is being used'''
		setup, options, name = self.py2exe_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.detect_freezer(options) == 'py2exe'
		

	def test_py2exe_running_when_using_future(self):
		'''Tests that a script with the future imports gets recognized and we run
		our code'''			
		setup, options, new_script = self.py2exe_setup('should run the setup stuff', 'py2exe_return_test.py')
		insert_code(new_script,
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()")
					
		dummy_setup = lambda *args, **kwargs: 0
		
		if PY3:
			assert freeze_future.setup(dummy_setup, **options) == False
		else:
			assert freeze_future.setup(dummy_setup, **options) == True


	def test_py2exe_return_when_no_future_import(self):
		'''Make sure we don't do any work if not using the future library'''
		setup, options, name = self.py2exe_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.setup(setup, **options) == False


	def test_p2exe_working(self):
		'''Test a small script to make sure it builds properly
		We have to insert import py2exe into our setup script'''
		setup, options, name = self.py2exe_setup('Simple Working', WORKING_SCRIPT)
		setup(**options)	
		assert run_script(WORKING_SCRIPT, freezer='py2exe')


	def test_py2exe_and_future(self):
		'''
		Testing adding the future imports doesn't fuck up the building on python3
		Fucks up python2 though'''
		setup, options, new_script = self.py2exe_setup('Working with Future Import', 'py2exe_future_working.py')
		
		insert_code(new_script,
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()")
		if PY3:
			setup(**options)
			assert run_script(new_script, freezer='py2exe')
		else:
			setup(**options)
			assert not run_script(new_script, freezer='py2exe')


	def test_py2exe_work_urllib(self):
		'''Testing py2exe works with urllib, just making sure the problem is with future'''
		if PY3:
			lib = "urllib"
		else:
			lib = "urllib2"		
		setup, options, new_script = self.py2exe_setup('py2exe working with urllib', 'py2exe_urllib_working.py')
		insert_code(new_script, "import " + lib)
		setup(**options)
		assert run_script(new_script, freezer='py2exe')


	def test_py2exe_fix_future(self):
		'''tests our fix'''
		setup, options, new_script = self.py2exe_setup('py2exe fixed', 'py2exe_fixed.py')
		
		insert_code(new_script, 
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()")
		
		if freeze_future.setup(setup, **options):
			assert run_script(new_script, freezer='py2exe')
		else:
			assert 0


	def test_py2exe_fix_future_2(self):
		'''tests our fix when importing everything under the sun! also
		import builtins'''
		setup, options, new_script = self.py2exe_setup('py2exe fixed', 'py2exe_fixed.py')
		
		insert_code(new_script, 
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()",
					"import urllib.request, urllib.error, urllib.parse",
					"import collections",
					"from itertools import filterfalse",
					"from subprocess import getoutput",
					"from builtins import str",
					"from builtins import range",)
		
		freeze_future.setup(setup, **options)
		assert run_script(new_script, freezer='py2exe')

#~ @pytest.mark.tim2
class TestCxFreeze():
	
	def teardown(self):
		cleanup_dirs()
		
	def cxfreeze_setup(self, name, script, **changes):
		from cx_Freeze import setup, Executable
		base = None
		if sys.platform == "win32":
			base = "Win32GUI"
		
		new_script = make_new_script_name(script)
		
		base_options = copy.deepcopy(V.DEFAULT_OPTIONS)
		changes['executables'] = [Executable(new_script, base=base, icon=V.ICON)]
		changes.update({'name':name})
		base_options.update(changes)
		
		return setup, base_options, new_script
	

	def test_cxfreeze_detected(self):
		'''make sure freeze_future knows that setuptoos is being used'''
		setup, options, name = self.cxfreeze_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.detect_freezer(options) == 'cxfreeze'
	
	
	def test_running_when_using_future(self):
		'''Tests that a script with the future imports gets recognized and we run
		our code'''			
		setup, options, new_script = self.cxfreeze_setup('should run the setup stuff', 'cxfreeze_reuturn_working.py')
		insert_code(new_script,
			"from __future__ import print_function",
			"from future import standard_library",
			"standard_library.install_aliases()")
		dummy_setup = lambda *args, **kwargs: 0
		
		if PY3:
			assert freeze_future.setup(dummy_setup, **options) == False
		else:
			assert freeze_future.setup(dummy_setup, **options) == True


	def test_cxfreeze_return_when_no_future_import(self):
		'''Make sure we don't do any work if not using the future library'''
		setup, options, name = self.cxfreeze_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.setup(setup, **options) == False


	def test_cxfreeze_working(self):
		'''Test a small script to make sure it builds properly'''
		setup, options, name = self.cxfreeze_setup('Simple Working', WORKING_SCRIPT)
		setup(**options)	
		assert run_script(WORKING_SCRIPT)
		

	def test_cxfreeze_and_future(self):
		'''
		Testing adding the future imports doesn't fuck up the building on python3
		Fucks up python2 though'''
		setup, options, new_script = self.cxfreeze_setup('Working with Future Import', 'cxfreeze_future_working.py')
		
		insert_code(new_script,
					"from future import standard_library",
					"standard_library.install_aliases()")
		if PY3:
			setup(**options)
			assert run_script(new_script)
		else:
			from cx_Freeze import ConfigError
			with pytest.raises(ConfigError):
				setup(**options)
				
		
	def test_cxfreeze_work_urllib(self):
		'''Testing cxfreeze works with urllib, just making sure the problem is with future'''
		if PY3:
			lib = "urllib"
		else:
			lib = "urllib2"		
		setup, options, new_script = self.cxfreeze_setup('cxfreeze working with urllib', 'cxfreeze_urllib_working.py')
		insert_code(new_script, "import " + lib)
		setup(**options)
		assert run_script(new_script)


	def test_cxfreeze_fix_future(self):
		'''tests our fix'''
		setup, options, new_script = self.cxfreeze_setup('cxfreeze fixed', 'cxfreeze_fixed.py')
		
		insert_code(new_script, 
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()")
		
		if freeze_future.setup(setup, **options):
			assert run_script(new_script)
		else:
			assert 0


	def test_cxfreeze_fix_future_2(self):
		'''tests our fix when importing everything under the sun! also
		import builtins'''
		setup, options, new_script = self.cxfreeze_setup('cxfreeze fixed', 'cxfreeze_fixed.py')
		
		insert_code(new_script, 
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()",
					"import urllib.request, urllib.error, urllib.parse",
					"import collections",
					"from itertools import filterfalse",
					"from subprocess import getoutput",
					"from builtins import str",
					"from builtins import range",)
		
		freeze_future.setup(setup, **options)
		assert run_script(new_script)


class TestDistutils():
	'''Make sure distutils gets through untouched'''
	
	def teardown_class(cls):	#TBD why does this fail when not using class..
		cleanup_dirs()


	def distutils_setup(self, name, script, **changes):
		from distutils.core import setup
		new_script = make_new_script_name(script)
		
		changes['scripts'] = [new_script]
		base_options = copy.deepcopy(V.DEFAULT_OPTIONS)
		changes.update({'name':name})
		base_options.update(changes)
		
		return setup, base_options, new_script		

	
	def test_distutils_detected(self):
		'''make sure freeze_future knows that setuptoos is being used'''
		setup, options, name = self.distutils_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.detect_freezer(options) == 'distutils'

	
	def test_distutils_return_when_no_future_import(self):
		'''Make sure we don't do any work if not using the future library'''	
		setup, options, name = self.distutils_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.setup(setup, **options) == False

	@pytest.mark.tim3	
	def test_distutils_working(self):
		'''Test a small script to make sure it builds properly'''
		setup, options, name = self.distutils_setup('Simple Working', WORKING_SCRIPT)
		setup(**options)
		assert run_script(WORKING_SCRIPT, freezer='distutils')

	@pytest.mark.tim3
	def test_distutils_and_future(self):
		'''
		Testing adding the future imports doesn't fuck up the building'''
		setup, options, new_script = self.distutils_setup('Working with Future Import', 'distutils_future_working.py')
		
		insert_code(new_script,
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()",
					"import urllib.request, urllib.error, urllib.parse",
					"import collections",
					"from itertools import filterfalse",
					"from subprocess import getoutput",
					"from builtins import str",
					"from builtins import range",
					"import builtins")

		setup(**options)
		assert run_script(new_script, freezer='distutils')


	def test_distutils_return_when_using_future(self):
		'''Tests that a script with the future imports runs as normal'''			
		setup, options, new_script = self.distutils_setup('should run the setup stuff', 'disturils_return_working.py')
		insert_code(new_script,
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()")
					
		dummy_setup = lambda *args, **kwargs: 0
		
		assert freeze_future.setup(dummy_setup, **options) == False

@pytest.mark.tim2
class TestEsky():
	
	def teardown(self):
		cleanup_dirs()
		
	def setup(self):
		'''moved this code into the module, still didnt fix the probem of 
		running multiple tests at same time'''
		from esky import bdist_esky
		from esky.bdist_esky import Executable	
		from distutils.core import setup
		self.Executable = Executable
		self.dist_setup = setup
	
	def esky_setup(self, name, script, **changes):
		new_script = make_new_script_name(script)

		base_options = {"version": "1.0"}
		changes.update({'name':name})
		base_options.update(changes)
		#~ base_options['scripts'] = [self.Executable(new_script, icon=V.ICON)]
		base_options['scripts'] = [new_script]
		base_options.update({'script_args':["bdist_esky"]})
		base_options.update({"bdist_esky":{
										"freezer_module": "cxfreeze"}})
		
		return self.dist_setup, base_options, new_script

	#~ @pytest.mark.tim2
	def test_esky_detected(self):
		'''make sure freeze_future knows that setuptoos is being used'''
		setup, options, name = self.esky_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.detect_freezer(options) == 'esky'
	
	#~ @pytest.mark.tim2
	def test_running_when_using_future(self):
		'''Tests that a script with the future imports gets recognized and we run
		our code'''			
		setup, options, new_script = self.esky_setup('should run the setup stuff', 'esky_reuturn_working.py')
		insert_code(new_script,
			"from __future__ import print_function",
			"from future import standard_library",
			"standard_library.install_aliases()")
		dummy_setup = lambda *args, **kwargs: 0
		
		if PY3:
			assert freeze_future.setup(dummy_setup, **options) == False
		else:
			assert freeze_future.setup(dummy_setup, **options) == True

	#~ @pytest.mark.tim2
	def test_esky_return_when_no_future_import(self):
		'''Make sure we don't do any work if not using the future library'''
		setup, options, name = self.esky_setup('working script no future should return', WORKING_SCRIPT)
		assert freeze_future.setup(setup, **options) == False

	#~ @pytest.mark.tim2
	def test_esky_working(self): # zz doesnt run if the above test runs before.. could be a reason why esky fucks up with temp files /folder rm_tree etc?
		'''Test a small script to make sure it builds properly'''
		setup, options, name = self.esky_setup('Simple Working', WORKING_SCRIPT)
		
		setup(**options)
		assert run_script(name, freezer='esky')
		
	#~ @pytest.mark.tim2
	def test_esky_and_future(self):
		'''
		Testing adding the future imports doesn't fuck up the building on python3
		Fucks up python2 though
		Esky allows setup to compile, but the script will not run
		'''
		
		setup, options, new_script = self.esky_setup('Working with Future Import', 'esky_future_working.py')
		
		insert_code(new_script,
					#~ "from __future__ import print_function",)
					"from future import standard_library",
					"standard_library.install_aliases()")
		
		if PY3:
			setup(**options)
			assert run_script(new_script, freezer='esky')
		else:
			#~ with pytest.raises(Exception):
			setup(**options)
			assert not run_script(new_script, freezer='esky')
				
	#~ @pytest.mark.tim2	
	def test_esky_work_urllib(self):
		'''Testing esky works with urllib, just making sure the problem is with future'''
		if PY3:
			lib = "urllib"
		else:
			lib = "urllib2"		
		setup, options, new_script = self.esky_setup('esky working with urllib', 'esky_urllib_working.py')
		insert_code(new_script, "import " + lib)
		setup(**options)
		assert run_script(new_script, freezer='esky')

	#~ @pytest.mark.tim2	
	def test_esky_fix_future(self):
		'''tests our fix'''
		setup, options, new_script = self.esky_setup('esky fixed', 'esky_fixed.py')
		
		insert_code(new_script, 
					"from future import standard_library",
					"standard_library.install_aliases()")
		
		if freeze_future.setup(setup, **options):
			assert run_script(new_script, freezer='esky')
		else:
			assert 0

	#~ @pytest.mark.tim2
	def test_esky_fix_future_2(self):
		'''tests our fix when importing everything under the sun! also
		import builtins'''
		setup, options, new_script = self.esky_setup('esky fixed2', 'esky_fixed2.py')
		
		insert_code(new_script, 
					"from __future__ import print_function",
					"from future import standard_library",
					"standard_library.install_aliases()",
					"import urllib.request, urllib.error, urllib.parse",
					"import collections",
					"from itertools import filterfalse",
					"from subprocess import getoutput",
					"from builtins import str",
					"from builtins import range",)
		
		freeze_future.setup(setup, **options)
		assert run_script(new_script, freezer='esky')
