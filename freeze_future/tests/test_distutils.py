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
    
def teardown_module():
    cleanup_dirs()


def distutils_setup(name, script, **changes):
    from distutils.core import setup
    new_script = make_new_script_name(script)
    
    changes['scripts'] = [new_script]
    base_options = copy.deepcopy(V.DEFAULT_OPTIONS)
    changes.update({'name':name})
    base_options.update(changes)
    
    return setup, base_options, new_script      


def test_distutils_detected():
    '''make sure freeze_future knows that distutils is being used'''
    setup, options, name = distutils_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.detect_freezer(options) == 'distutils'

def test_distutils_return_when_no_future_import():
    '''Make sure we don't do any work if not using the future library'''    
    setup, options, name = distutils_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.setup(**options) == False

def test_distutils_return_when_using_future():
    '''Tests that a script with the future imports runs as normal'''            
    setup, options, new_script = distutils_setup('should run the setup stuff', 'disturils_return_working.py')
    insert_code(new_script,
                "from __future__ import print_function",
                "from future import standard_library",
                "standard_library.install_aliases()")
    assert freeze_future.setup(**options) == False

def test_distutils_working():
    '''Test a small script to make sure it builds properly'''
    setup, options, name = distutils_setup('Simple Working', WORKING_SCRIPT)
    setup(**options)
    clean_exit, stderr = run_script(WORKING_SCRIPT, freezer='distutils')
    assert clean_exit

def test_distutils_condition():
    '''Testing adding the future imports doesn't fuck up the building'''
    setup, options, new_script = distutils_setup('cxfreeze fixed', 'cxfreeze_fixed.py')

    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()",
                "import urllib.request, urllib.error, urllib.parse",
                "import collections",
                "from itertools import filterfalse",
                "from subprocess import getoutput",
                "from builtins import str",
                "from builtins import range",)

    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='distutils')
    assert clean_exit

def test_distutils_condition2():
    '''Testing adding the future imports doesn't fuck up the building'''
    setup, options, new_script = distutils_setup('Working with Future Import', 'future_working.py')

    insert_code(new_script,
                "from __future__ import print_function")

    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='distutils')
    assert clean_exit

