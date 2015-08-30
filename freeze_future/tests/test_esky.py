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
import logging

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

def setup_logger(log_file):
    '''One function call to set up logging with some nice logs about the machine'''
    logging.basicConfig(
        filename=log_file,
        filemode='w',
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s: %(message)s')  # one run
setup_logger('t_esky_log.log')

def setup_module():
    cleanup_dirs()

def teardown():
    cleanup_dirs()

def esky_setup(name, script, **changes):
    from esky import bdist_esky
    from distutils.core import setup
    from esky.bdist_esky import Executable
    new_script = make_new_script_name(script)
    base_options = {"version": "1.0"}
    changes.update({'name':name})
    base_options.update(changes)
    base_options['scripts'] = [new_script]
    base_options.update({'script_args':["bdist_esky"]})
    base_options.update({"bdist_esky":{
                                    "freezer_module": "cxfreeze"}})
    return setup, base_options, new_script

@pytest.mark.one
def test_esky_detected():
    '''make sure freeze_future knows that esky is being used'''
    setup, options, name = esky_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.detect_freezer(options) == 'esky'


def test_esky_builds_and_runs():
    '''Test a small script to make sure it builds properly
    If this fails it means you have a problem with ESKY so go fix it!!! '''
    setup, options, new_script = esky_setup('Simple Working', WORKING_SCRIPT)
    freeze_future.setup(setup, **options)
    assert run_script(WORKING_SCRIPT, freezer='esky')

def test_esky_failure_condition():
    setup, options, new_script = esky_setup('test_condition', 'test_condition.py')
    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()",)

    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='esky')

    if PY3:
        # Im thinking this is my py3 fixes... as cxfreeze works with fthe standard_library() fine
        fail_cond = 'Grammar.txt'
        assert not clean_exit and fail_cond in str(stderr)
    else:
        #this failure condition is from cxfreeze and py2exe.. they need to get their shit together
        fail_cond = 'No module named UserList'
        assert not clean_exit and fail_cond in stderr

def test_esky_failure_condition2():
    '''not sure who is responsibile for this failure on py2 have to confirm TODO'''
    setup, options, new_script = esky_setup('test_condition2', 'test_condition2.py')
    insert_code(new_script,
                "from __future__ import print_function",)
    fail_cond = 'The process cannot access the file because it is being used by another process'
    try:
        setup(**options)
    except SystemExit as err:
        assert fail_cond in str(err)


def test_esky_freeze_future_running_when_using_future_import():
    '''Tests that a script with the future imports gets recognized and we run
    our code'''
    setup, options, new_script = esky_setup('should run the setup stuff', 'esky_reuturn_working.py')
    insert_code(new_script,
        "from __future__ import print_function",
        "from future import standard_library",
        "standard_library.install_aliases()")
    dummy_setup = lambda *args, **kwargs: 0
    if PY3:
        assert freeze_future.setup(dummy_setup, **options) == True
    else:
        assert freeze_future.setup(dummy_setup, **options) == True


def test_esky_no_return_when_no_future_import():
    '''Make sure freeze_future code always runs if using esky as esky uses the future model'''
    setup, options, name = esky_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.setup(setup, **options) == True


def test_esky_freeze_future_condition_one_fix():
    '''tests our fix when importing everything under the sun! also
    import builtins'''
    setup, options, new_script = esky_setup('esky fixed2', 'esky_fixed2.py')
    insert_code(new_script,
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


@pytest.mark.fail
@pytest.mark.fail6
def test_esky_freeze_future_condition_two_fix():
    '''
    Testing adding the future imports doesn't fuck up the building on python3
    Fucks up python2 though
    Esky allows setup to compile, but the script will not run
    '''
    setup, options, new_script = esky_setup('Working with Future Import', 'esky_future_working.py')
    insert_code(new_script,
                "from __future__ import print_function",)
                #"from future import standard_libry",
                #"standard_library.install_aliasesra()")
    if PY3:
        freeze_future.setup(setup, **options)
        # freeze_future.setup(setup, **options)
        assert run_script(new_script, freezer='esky')
    else:
        #~ with pytest.raises(Exception):
        freeze_future.setup(setup, **options)
        assert not run_script(new_script, freezer='esky')
