from __future__ import with_statement
from __future__ import print_function

import sys
import os
import pdb
import copy
import pytest

import freeze_future
import variables as V
from utils import really_rmtree, InMemoryWriter, extract_zipfile, cleanup_dirs,\
                normalize_sysargs, make_new_script_name, insert_code, run_script

WORKING_SCRIPT = V.SCRIPT
ORIGINAL_CWD = os.getcwd()

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

def setup():
    normalize_sysargs()

def teardown():
    cleanup_dirs()

def cxfreeze_setup(name, script, **changes):
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

def test_cxfreeze_detected():
    '''make sure freeze_future knows that setuptoos is being used'''
    setup, options, name = cxfreeze_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.detect_freezer(options) == 'cxfreeze'

@pytest.mark.cond
def test_esky_failure_condition():
    setup, options, new_script = cxfreeze_setup('test_condition', 'test_condition.py')
    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()",)
    clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
    if PY3:
        setup(**options)
        assert clean_exit
    else:
        #this failure condition is from cxfreeze and py2exe.. they need to get their shit together
        fail_cond = 'No module named UserList'
        assert not clean_exit and fail_cond in stderr

def test_cxfreeze_failure_condition2():
    '''cxfreeze is not responsible for this failure condition that esky experiences... it is us'''
    setup, options, new_script = cxfreeze_setup('test_condition2', 'test_condition2.py')
    insert_code(new_script,
                "from __future__ import print_function",)
    #fail_cond = 'The process cannot access the file because it is being used by another process'
    setup(**options)
    assert run_script(new_script, freezer='cxfreeze')


def test_freeze_future_running_when_using_future_with_cxfreeze():
    '''Tests that a script with the future imports gets recognized and the freeze future code is run'''
    setup, options, new_script = cxfreeze_setup('should run the setup stuff', 'cxfreeze_reuturn_working.py')
    insert_code(new_script,
        "from __future__ import print_function",
        "from future import standard_library",
        "standard_library.install_aliases()")
    dummy_setup = lambda *args, **kwargs: 0

    if PY3:
        assert freeze_future.setup(dummy_setup, **options) == False
    else:
        assert freeze_future.setup(dummy_setup, **options) == True


def test_cxfreeze_freeze_future_return_when_no_future_import():
    '''Make sure we don't do any work if not using the future library'''
    setup, options, new_script = cxfreeze_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.setup(setup, **options) == False


def test_cxfreeze_working():
    '''Test a small script to make sure it builds properly'''
    setup, options, new_script = cxfreeze_setup('Simple Working', WORKING_SCRIPT)
    setup(**options)
    assert run_script(WORKING_SCRIPT)

def test_cxfreeze_and_future():
    '''
    Testing adding the future imports doesn't fuck up the building on python3
    Fucks up python2 though'''
    setup, options, new_script = cxfreeze_setup('Working with Future Import', 'cxfreeze_future_working.py')

    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()")
    if PY3:
        setup(**options)
        assert run_script(new_script)
    else:
        # from cx_Freeze import ConfigError
        with pytest.raises(Exception):
            setup(**options)
            assert run_script(new_script)

def test_cxfreeze_work_with_no_standard_library():# TBD BECAUSE OF THIS ONLY RUN ON PYTHON 2 IF THE STANDARD LIBRARY IS BEING USED IN THE PROJECT zzz much harder
    '''does our code with without the standard librar function call'''
    setup, options, new_script = cxfreeze_setup('cxfreeze works_nostandardlin', 'cxfreeze_works_no_stdlib.py')
    insert_code(new_script,
                "from __future__ import absolute_import, division, print_function",
                "from builtins import (bytes, str, open, super, range,",
                "    zip, round, input, int, pow, object)")
    freeze_future.setup(setup, **options)
    if PY3:
        assert run_script(new_script)
    else:
        #with pytest.raises(Exception):# I think my exit code is shadowing the exception or sth?? or my sys.exit call
        assert run_script(new_script)

def test_cxfreeze_fix_future():
    '''tests our fix when importing everything under the sun! also
    import builtins TBD this test is a bit flakey when running the entire suite and doing tests on py 2 and py3'''
    setup, options, new_script = cxfreeze_setup('cxfreeze fixed', 'cxfreeze_fixed.py')

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

@pytest.mark.fail
def test_freeze_future_with_cxfreeze_and_esky():
    '''explictly telling freeze future we are using esky and cxfreeze'''
    from test_esky import esky_setup
    setup, options, new_script = esky_setup('cxfreeze_esky_fixed', 'esky_fixed2.py')

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

    sys.argv=[]
    setup(**options)
    #print(sys.argv)
    assert run_script(new_script, freezer='esky')
