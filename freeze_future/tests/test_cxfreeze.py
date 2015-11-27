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
                normalize_sysargs, make_new_script_name, insert_code, run_script,\
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


def test_cxfreeze_builds_and_runs():
    '''Test a small script to make sure it builds properly'''
    setup, options, new_script = cxfreeze_setup('Simple Working', WORKING_SCRIPT)
    setup(**options)
    clean_exit, stderr = run_script(WORKING_SCRIPT, freezer='cxfreeze')
    assert clean_exit


def test_cxfreeze_failure_condition():
    setup, options, new_script = cxfreeze_setup('test_condition', 'test_condition.py')
    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()",)
    if os.name == 'posix':
        if not PY3:
            with pytest.raises(Exception):
                setup(**options)
        else:
            setup(**options)
    else:
        setup(**options)
        clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
        if PY3:
            assert clean_exit
        else:
            #this failure condition is from cxfreeze and py2exe.. they need to get their shit together
            #'No module named UserList' etc..
            assert not clean_exit

def test_cxfreeze_failure_condition2():
    '''cxfreeze is not responsible for this failure condition that esky experiences... it is us'''
    setup, options, new_script = cxfreeze_setup('test_condition2', 'test_condition2.py')
    insert_code(new_script,
                "from __future__ import print_function",)
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
    assert clean_exit

@pytest.mark.xfail(reason='the fix is being non discrimately applied')
def test_cxfreeze_failure_condition3():
    '''ffs another different error No such file or directory grammer.txt
    https://bitbucket.org/anthony_tuininga/cx_freeze/issues/151/using-modules-that-use-open-on-data-files'''
    setup, options, new_script = cxfreeze_setup('test_condition3', 'test_condition3.py')
    insert_code(new_script,
                "import past")
                # 'from past.builtins import basestring')
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
    assert not clean_exit

def test_freeze_future_running_when_using_future_with_cxfreeze():
    '''Tests that a script with the future imports gets recognized and the freeze future code is run'''
    setup, options, new_script = cxfreeze_setup('should run the setup stuff', 'cxfreeze_reuturn_working.py')
    insert_code(new_script,
        "from future import standard_library",
        "standard_library.install_aliases()")
    if PY3:
        assert freeze_future.setup(test_setup=True, **options) == False
    else:
        assert freeze_future.setup(test_setup=True, **options) == True


def test_cxfreeze_freeze_future_return_when_no_future_import():
    '''Make sure we don't do any work if not using the future library'''
    setup, options, new_script = cxfreeze_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.setup(**options) == False


def test_cxfreeze_work_with_no_standard_library():# TBD BECAUSE OF THIS ONLY RUN ON PYTHON 2 IF THE STANDARD LIBRARY IS BEING USED IN THE PROJECT zzz much harder
    '''does our code with without the standard librar function call'''
    setup, options, new_script = cxfreeze_setup('cxfreeze works_nostandardlin', 'cxfreeze_works_no_stdlib.py')
    insert_code(new_script,
                "from __future__ import absolute_import, division, print_function",
                "from builtins import (bytes, str, open, super, range,",
                "    zip, round, input, int, pow, object)")
    freeze_future.setup(**options)
    if PY3:
        clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
        assert clean_exit
    else:
        #with pytest.raises(Exception):# I think my exit code is shadowing the exception or sth?? or my sys.exit call
        clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
        assert clean_exit

@pytest.mark.xfail(sys.version_info >= (3,0) and os.name == 'nt' ,
                   reason="on windows py3 permission errors sometimes")
def test_cxfreeze_freeze_future_condition_one_fix():
    '''tests our fix when importing everything under the sun! also
    import builtins TBD this test is a bit flakey when running the entire suite and doing tests on py 2 and py3'''
    setup, options, new_script = cxfreeze_setup('cxfreeze fixed', 'cxfreeze_fixed.py')
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
    clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
    assert clean_exit

def test_cxfreeze_future_condition_3_fix():
    '''tests our fix when importing everything under the sun! also
    import builtins TBD this test is a bit flakey when running the entire suite and doing tests on py 2 and py3'''
    setup, options, new_script = cxfreeze_setup('cxfreeze fixed', 'cxfreeze_fixed.py')
    insert_code(new_script,
                'import past')
    freeze_future.setup(**options)
    # pdb.set_trace()
    clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
    assert clean_exit

