__author__ = 'timeyyy'
from utils import really_rmtree, InMemoryWriter, extract_zipfile, cleanup_dirs, \
    normalize_sysargs, make_new_script_name, insert_code, run_script
import variables as V
import copy
WORKING_SCRIPT = V.SCRIPT
from distutils.core import setup
base_options = copy.deepcopy(V.DEFAULT_OPTIONS)
import py2exe
new_script = make_new_script_name(WORKING_SCRIPT)
base_options['windows'] = [new_script]


base_options['py2exe'] = base_options['options']['build_exe']
del base_options['options']['build_exe']
# insert_code(new_script,
#                 "from __future__ import print_function",
#                 "from future import standard_library",
#                 "standard_library.install_aliases()")
import sys
print(sys.argv)
import pdb
pdb.set_trace()
setup(**base_options)
import os
print(os.getcwd())
