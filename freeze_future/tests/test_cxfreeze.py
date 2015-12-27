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
    '''Our script fails  to build under certain platforms and python versions due to dependancies
    not being found by our freezer, we need to manually include/exclude them'''
    setup, options, new_script = cxfreeze_setup('test_condition', 'test_condition.py')
    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()",)
    if 'linux' in sys.path or 'darwin' in sys.platform:
        #TODO confirm that mac handles the same as linux..
        if not PY3:
            with pytest.raises(Exception):
                setup(**options)
        else:
            setup(**options)
    elif sys.platform == 'win32':
        setup(**options)
        clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
        if PY3:
            assert clean_exit
        else:
            #this failure condition is from cxfreeze and py2exe.. missing modules ..
            assert not clean_exit

def test_cxfreeze_failure_condition2():
    '''this module was playing up so testing it ..'''
    setup, options, new_script = cxfreeze_setup('test_condition2', 'test_condition2.py')
    insert_code(new_script,
                "from __future__ import print_function",)
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
    assert clean_exit

@pytest.mark.f
def test_cxfreeze_failure_condition3():
    ''' basically using open function on a datafile will fail if the modulea and datafiles
    are inside a zip as open doesn't know how to look in a zip.
    Error -> No such file or directory grammer.txt
    https://bitbucket.org/anthony_tuininga/cx_freeze/issues/151/using-modules-that-use-open-on-data-files'''
    setup, options, new_script = cxfreeze_setup('test_condition3', 'test_condition3.py')
    insert_code(new_script,
                "import past")
                # 'from past.builtins import basestring')
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
    assert not clean_exit

# THIS TEST IS MAKING SURE THE FREEZEFUTURE CODE IS WORKING PROPERLY
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
# THIS TEST IS MAKING SURE THE FREEZEFUTURE CODE IS WORKING PROPERLY
def test_cxfreeze_freeze_future_return_when_no_future_import():
    '''Make sure we don't do any work if not using the future library'''
    setup, options, new_script = cxfreeze_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.setup(**options) == False


@pytest.mark.xfail(os.name == 'nt' ,
                   reason="on windows py3 permission errors sometimes")
def test_cxfreeze_freeze_future_condition_one_fix():
    '''tests our fix when importing everything under the sun!, just another sanity check'''
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
    clean_exit, stderr = run_script(new_script, freezer='cxfreeze')
    assert clean_exit

