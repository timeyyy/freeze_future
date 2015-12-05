from __future__ import with_statement
from __future__ import print_function

import sys
import os
import pdb
import copy
import pytest

import freeze_future
import variables as V
from utils import really_rmtree, InMemoryWriter, extract_zipfile, cleanup_dirs, \
    normalize_sysargs, make_new_script_name, insert_code, run_script, \
    preserve_cwd

WORKING_SCRIPT = V.SCRIPT
ORIGINAL_CWD = os.getcwd()

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

def setup_function(func):
    normalize_sysargs()

def teardown_function(func):
    cleanup_dirs()

#TODO change for py2app..
def py2app_setup(name, script, **changes):
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

def test_py2app_detected():
    '''make sure freeze_future knows that py2app is being used'''
    setup, options, name = py2app_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.detect_freezer(options) == 'py2app'

def test_py2app_builds_and_runs():
    '''Test a small script to make sure it builds properly'''
    setup, options, new_script = py2app_setup('Simple Working', WORKING_SCRIPT)
    setup(**options)
    #TODO MAKE SURE run_script runs as it should...
    clean_exit, stderr = run_script(WORKING_SCRIPT, freezer='py2app')
    assert clean_exit

def test_py2app_failure_condition():
    '''Our script fails  to build under certain platforms and python versions due to dependancies
    not being found by our freezer, we need to manually include/exclude them'''
    setup, options, new_script = py2app_setup('test_condition', 'test_condition.py')
    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()",)
    if 'darwin' in sys.platform:
        #TODO confirm that mac handles the same as linux..
        if not PY3:
            with pytest.raises(Exception):
                setup(**options)
        else:
            setup(**options)

def test_py2app_failure_condition2():
    '''this module was playing up so testing it ..'''
    setup, options, new_script = py2app_setup('test_condition2', 'test_condition2.py')
    insert_code(new_script,
                "from __future__ import print_function",)
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='py2app')
    assert clean_exit

#TODO make sure the fail condition is met, then make sure the fix applies correctly
def test_py2app_failure_condition3_fixed():
    ''' basically using open function on a datafile will fail if the modulea and datafiles
    are inside a zip as open doesn't know how to look in a zip.
    Error -> No such file or directory grammer.txt
    https://bitbucket.org/anthony_tuininga/cx_freeze/issues/151/using-modules-that-use-open-on-data-files'''
    setup, options, new_script = py2app_setup('test_condition3', 'test_condition3.py')
    insert_code(new_script,
                "import past")
    # 'from past.builtins import basestring')
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='py2app')
    assert clean_exit

# THIS TEST IS MAKING SURE THE FREEZEFUTURE CODE IS WORKING PROPERLY
def test_freeze_future_running_when_using_future_with_py2app():
    '''Tests that a script with the future imports gets recognized and the freeze future code is run'''
    setup, options, new_script = py2app_setup('should run the setup stuff', 'py2app_reuturn_working.py')
    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()")
    if PY3:
        assert freeze_future.setup(test_setup=True, **options) == False
    else:
        assert freeze_future.setup(test_setup=True, **options) == True

# THIS TEST IS MAKING SURE THE FREEZEFUTURE CODE IS WORKING PROPERLY
def test_py2app_freeze_future_return_when_no_future_import():
    '''Make sure we don't do any work if not using the future library'''
    setup, options, new_script = py2app_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.setup(**options) == False


def test_py2app_work_with_no_standard_library():
    '''does our code with without the standard librar function call'''
    setup, options, new_script = py2app_setup('py2app works_nostandardlin', 'py2app_works_no_stdlib.py')
    insert_code(new_script,
                "from __future__ import absolute_import, division, print_function",
                "from builtins import (bytes, str, open, super, range,",
                "    zip, round, input, int, pow, object)")
    freeze_future.setup(**options)
    if PY3:
        clean_exit, stderr = run_script(new_script, freezer='py2app')
        assert clean_exit
    else:
        #with pytest.raises(Exception):# I think my exit code is shadowing the exception or sth?? or my sys.exit call
        clean_exit, stderr = run_script(new_script, freezer='py2app')
        assert clean_exit

def test_py2app_freeze_future_condition_one_fix():
    '''tests our fix when importing everything under the sun!, just another sanity check'''
    setup, options, new_script = py2app_setup('py2app fixed', 'py2app_fixed.py')
    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()",
                "import urllib.request, urllib.error, urllib.parse",
                "import collections",
                "from itertools import filterfalse",
                "from subprocess import getoutput",
                "from builtins import str",
                "from builtins import range",)
    freeze_future.setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='py2app')
    assert clean_exit

def test_py2app_future_condition_3_fix():
    '''tests our fix when importing everything under the sun!'''
    setup, options, new_script = py2app_setup('py2app fixed', 'py2app_fixed.py')
    insert_code(new_script,
                'import past')
    freeze_future.setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='py2app')
    assert clean_exit
