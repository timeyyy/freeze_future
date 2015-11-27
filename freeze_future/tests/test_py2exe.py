'''
Simple working can we changed to anything u want just make sure it exits
'''
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
    normalize_sysargs, make_new_script_name, insert_code, run_script

WORKING_SCRIPT = V.SCRIPT
ORIGINAL_CWD = os.getcwd()

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False


def setup_module():
    normalize_sysargs()
    sys.argv[1] = 'py2exe'

# http://www.py2exe.org/index.cgi/ListOfOptions
def teardown_module():
    # Unlike cxfreeze somehow if i cleanup after each build it fucks up...,
    cleanup_dirs()

def py2exe_setup(name, script, **changes):
    import py2exe
    from distutils.core import setup
    new_script = make_new_script_name(script)
    base_options = copy.deepcopy(V.DEFAULT_OPTIONS)
    changes['windows'] = [new_script]
    base_options.update(changes)
    base_options['py2exe'] = base_options['options']['build_exe']
    del base_options['options']['build_exe']
    changes.update({'name':name})
    return setup, base_options, new_script


def test_detected():
    '''make sure freeze_future knows that setuptoos is being used'''
    setup, options, name = py2exe_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.detect_freezer(options) == 'py2exe'


def test_freeze_future_running_when_using_future_with_py2exe():
    '''Tests that a script with the future imports gets recognized and we run
    our code'''
    setup, options, new_script = py2exe_setup('should run the setup stuff', 'py2exe_return_test.py')
    insert_code(new_script,
                "from __future__ import print_function",
                "from future import standard_library",
                "standard_library.install_aliases()")
    if PY3:
        assert freeze_future.setup(test_setup=True, **options) == False
    else:
        assert freeze_future.setup(test_setup=True, **options) == True



def test_py2exe_freeze_future_return_when_no_future_import():
    '''Make sure we don't do any work if not using the future library'''
    setup, options, name = py2exe_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.setup(**options) == False


def test_p2exe_working():
    '''Test a small script to make sure it builds properly
    We have to insert import py2exe into our setup script'''
    setup, options, name = py2exe_setup('Simple Working', WORKING_SCRIPT)
    setup(**options)
    assert run_script(WORKING_SCRIPT, freezer='py2exe')


def test_py2exe_and_future():
    '''
    Testing adding the future imports doesn't fuck up the building on python3
    Fucks up python2 though'''
    pdb.set_trace()
    setup, options, new_script = py2exe_setup('Working with Future Import', 'py2exe_future_working.py')

    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()")
    if PY3:
        pdb.set_trace()
        # sys.argv[0] = os.path.basename(new_script)
        # sys.argv[1] = 'py2exe'
        print(sys.argv)
        setup(**options)
        assert run_script(new_script, freezer='py2exe')
    else:
        setup(**options)
        assert not run_script(new_script, freezer='py2exe')


def test_py2exe_fix_future():
    '''tests our fix when importing everything under the sun! also
    import builtins'''
    setup, options, new_script = py2exe_setup('py2exe fixed', 'py2exe_fixed.py')

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

    freeze_future.setup(**options)
    assert run_script(new_script, freezer='py2exe')
