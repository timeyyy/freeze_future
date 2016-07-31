'''
Simple working can we changed to anything u want just make sure it exits
'''
from __future__ import with_statement
from __future__ import print_function

import sys
import os
import subprocess
import pdb
import pytest
import copy

from esky import bdist_esky
from distutils.core import setup as dist_setup
from esky.bdist_esky import Executable
from esky.util import deep_extract_zipfile, get_platform
import esky.patch

import freeze_future
import variables as V
from utils import really_rmtree, InMemoryWriter, extract_zipfile, cleanup_dirs, \
    normalize_sysargs, make_new_script_name, insert_code, run_script, get_zip_name

WORKING_SCRIPT = V.SCRIPT
ORIGINAL_CWD = os.getcwd()

FREEZER_TO_RUN_WITH_ESKY = 'cxfreeze'
assert FREEZER_TO_RUN_WITH_ESKY in ('cxfreeze', 'py2exe', 'esky', 'py2app')

try:
    import setuptools
except ImportError:
    pass

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

def setup_module():
    normalize_sysargs('bdist_esky')

def setup_function(func):
    cleanup_dirs()

def teardown_function(func):
    cleanup_dirs()

def esky_setup(name, script, **changes):
    new_script = make_new_script_name(script)
    base_options = {"version": "1.0"}
    changes.update({'name':name})
    base_options.update(changes)

    options = {"options":
                   {"bdist_esky":
                       {"compress": 'ZIP',
                        "freezer_module": FREEZER_TO_RUN_WITH_ESKY }}}

    base_options['scripts'] = [new_script]
    base_options.update({'script_args':["bdist_esky"]})
    base_options.update(options)
    return dist_setup, base_options, new_script
    #FIRST TEST USING THE FREEZE_FUTURE AND THE FIXES DEVELOPED THERE, WHEN ALL PASSING CHANGE TO distutils.setup
    return freeze_future.setup, base_options, new_script
    # return dist_setup, base_options, new_script

def test_esky_detected():
    '''make sure freeze_future knows that esky is being used'''
    setup, options, name = esky_setup('working script no future should return', WORKING_SCRIPT)
    assert freeze_future.detect_freezer(options) == 'esky'

def test_esky_builds_and_runs():
    '''Test a small script to make sure it builds properly
    If this fails it means you have a problem with ESKY so go fix it!!! '''
    setup, options, new_script = esky_setup('Simple Working', WORKING_SCRIPT)
    setup(**options)
    clean_exit, stderr = run_script(WORKING_SCRIPT, freezer='esky')
    print(stderr)
    assert clean_exit

def test_esky_failure_condition_fixed():
    setup, options, new_script = esky_setup('test_condition', 'test_condition.py')
    insert_code(new_script,
                "from future import standard_library",
                "standard_library.install_aliases()",)

    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='esky')

    assert clean_exit

@pytest.mark.xfail(reason="original esky failing under this condition")
def test_esky_failure_condition2_fixed():
    '''this error isn't mine to fix here, it is not present in the freezers o.0'''
    setup, options, new_script = esky_setup('test_condition2', 'test_condition2.py')
    insert_code(new_script,
                "from __future__ import print_function",)
    fail_cond = 'The process cannot access the file because it is being used by another process'
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='esky')

    assert clean_exit


@pytest.mark.tim
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
                "from builtins import range",
                "from queue import Queue")
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='esky')
    assert clean_exit

@pytest.mark.xfail(reason="need to implement fix2 zzz")
def test_esky_freeze_future_condition_two_fix():
    '''
    Testing adding the future imports doesn't fuck up the building on python3
    Fucks up python2 though
    Esky allows setup to compile, but the script will not run
    '''
    setup, options, new_script = esky_setup('Working with Future Import', 'esky_future_working.py')
    insert_code(new_script,
                "from __future__ import print_function",)
    if PY3:
        freeze_future.setup(**options)
        clean_exit, stderr = run_script(new_script, freezer='esky')
        assert clean_exit
    else:
        freeze_future.setup(**options)
        clean_exit, stderr = run_script(new_script, freezer='esky')
        assert not clean_exit

def test_esky_freeze_future_condition_three_fix():
    '''explictly telling freeze future we are using esky and cxfreeze'''
    setup, options, new_script = esky_setup('cxfreeze_esky_fixed', 'esky_cxfreeze_fixed.py')
    insert_code(new_script,
                "import past",)
    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='esky')
    assert clean_exit

def test_multiple_runs_of_setup_function():
    '''make sure our fixes support multiple runs '''
    from esky.bdist_esky import Executable
    setup, options, new_script = esky_setup('Simple Working', WORKING_SCRIPT)
    new_script2 = make_new_script_name('test_multiple_working.py')
    insert_code(new_script2,'import sys')
    options2 = copy.deepcopy(options)
    options2['scripts'] = [new_script2]
    options2['version'] = '0.2'
    esky_zip_name = get_zip_name(options2)

    # Now test that freeze future works as well
    cleanup_dirs()

    setup(**options)
    clean_exit, stderr = run_script(new_script, freezer='esky')
    assert clean_exit

    # only works if we cleanup dirs.. same as original esky
    cleanup_dirs()

    setup(**options2)
    if os.name == 'nt':
        platform = get_platform()
        esky_zip_name = 'Simple Working-0.2.%s.zip' % platform
    clean_exit, stderr = run_script(new_script2, freezer='esky', zip_name=esky_zip_name)
    assert clean_exit

def test_esky_bdist_esky_patch_command():
    '''this test is overkill just need to make sure patch command returns esky'''
    # TODO this made it clear i need to force the selection of freezer rather trying than smart detect it
    setup, options, new_script = esky_setup('Simple Working', WORKING_SCRIPT)
    setup(**options)

    new_script2 = make_new_script_name('testing_patching.py')
    insert_code(new_script2,'import sys')
    options2 = copy.deepcopy(options)
    options2['scripts'] = [new_script2]
    options2['script_args'] = ['bdist_esky_patch']
    options2['version'] = '0.2'
    setup(**options2)
    esky_zip_name = get_zip_name(options2)
    clean_exit, stderr = run_script(new_script2, freezer='esky', zip_name=esky_zip_name)
    assert clean_exit

def test_esky_patch():
    '''need to have our esky fixes developed in freeze future moved to f_py2exe or f_cxfrexe etc for patchingo work'''
    tdir=os.getcwd()
    uzdir = os.path.join(tdir,"unzip")
    try:
        really_rmtree(uzdir)
    except Exception:
        pass

    setup, options, new_script = esky_setup('Simple Working', WORKING_SCRIPT)
    setup(**options)

    new_script2 = make_new_script_name('testing_patching.py')
    insert_code(new_script2,'import sys')
    options2 = copy.deepcopy(options)
    options2['scripts'] = [new_script2]
    options2['script_args'] = ['bdist_esky_patch']
    options2['version'] = '2.0'
    options2['freezer'] = '2.0'
    setup(**options2)

    platform = get_platform()
    deep_extract_zipfile(os.path.join(tdir,"dist","Simple Working-1.0.%s.zip"%(platform,)),uzdir)
    with open(os.path.join(tdir,"dist","Simple Working-2.0.%s.from-1.0.patch"%(platform,)),"rb") as f:
        esky.patch.apply_patch(uzdir,f)

    filewithext = os.path.basename(new_script2)
    file = os.path.splitext(filewithext)[0]
    path_file = os.path.join(uzdir, file)
    cmd = [path_file]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    errs = proc.communicate()
    if not proc.returncode:
        exit_code = True
    else:
        exit_code = False
    assert exit_code
    really_rmtree(uzdir)

@pytest.mark.xfail(os.name == 'posix',reason='only applies on windwos')
@pytest.mark.f
def test_esky_bundle_mscrvt():
    setup, options, new_script = esky_setup('Simple Working', WORKING_SCRIPT)
    # setup(**options)

    new_script2 = make_new_script_name('testing_patching.py')
    insert_code(new_script2,
                'import sys',
                'import os',
                'versiondir = os.path.dirname(sys.executable)',
                'for nm in os.listdir(versiondir):',
                '    if nm.startswith("Microsoft.") and nm.endswith(".CRT"):',
                '        msvcrt_dir = os.path.join(versiondir,nm)',
                '        assert os.path.isdir(msvcrt_dir)',
                '        assert len(os.listdir(msvcrt_dir)) >= 2',
                '        break',
                'else:',
                '    assert False, "MSVCRT not bundled in version dir "+versiondir')
    options2 = copy.deepcopy(options)
    options2['options']['bdist_esky']['bundle_msvcrt'] = True
    options2['scripts'] = [new_script2]
    # options2['script_args'] = ['bdist_esky_patch']
    options2['version'] = '2.0'
    setup(**options2)

        # esky_zip_name = 'Simple Working-0.2.win32.zip'
    esky_zip_name = get_zip_name(options2)
    clean_exit, stderr = run_script(new_script2, freezer='esky', zip_name=esky_zip_name)
    assert clean_exit
