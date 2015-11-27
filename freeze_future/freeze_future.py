'''
When using the future library, freezing in python2 stopped working,
Made a whole bunch of tests and we find out that the problem is with using
the standard_aliases function

Currently alfa stage, easy enought to support cxfreeze and py2exe but esky is harder hmm

This code is a fix that should run only if using python2 to freeze, adds
excpetions and so on.

the meat and potatoes is actually the test files
makes sure all the conditions for why we are using this for the
different modules hold
'''
import sys
import os
import pdb
import logging
import zipfile
import shutil
import future
import tempfile

from .tests.utils import setup_logger, preserve_cwd, extract_zipfile, create_zipfile,\
                            really_rmtree, get_zip_name

setup_logger('fuck2.txt')

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False
#TBD find how disutils finds the packages, emulate and do a re expresiion
EXCLUDES_LIST = ('urllib.StringIO',          
                'urllib.UserDict',          
                'urllib.__builtin__',       
                'urllib.__future__',        
                'urllib.__main__',          
                'urllib._abcoll',           
                'urllib._collections',      
                'urllib._functools',        
                'urllib._hashlib',          
                'urllib._heapq',            
                'urllib._io',               
                'urllib._locale',           
                'urllib._md5',              
                'urllib._random',           
                'urllib._sha',              
                'urllib._sha256',           
                'urllib._sha512',           
                'urllib._socket',           
                'urllib._sre',              
                'urllib._ssl',              
                'urllib._struct',           
                'urllib._subprocess',       
                'urllib._threading_local',  
                'urllib._warnings',         
                'urllib._weakref',          
                'urllib._weakrefset',       
                'urllib._winreg',           
                'urllib.abc',               
                'urllib.array',             
                'urllib.base64',            
                'urllib.bdb',               
                'urllib.binascii',          
                'urllib.cPickle',           
                'urllib.cStringIO',         
                'urllib.calendar',          
                'urllib.cmd',               
                'urllib.collections',       
                'urllib.contextlib',        
                'urllib.copy',              
                'urllib.copy_reg',          
                'urllib.datetime',          
                'urllib.difflib',           
                'urllib.dis',               
                'urllib.doctest',           
                'urllib.dummy_thread',      
                'urllib.email',             
                'urllib.email.utils',       
                'urllib.encodings',         
                'urllib.encodings.aliases', 
                'urllib.errno',             
                'urllib.exceptions',        
                'urllib.fnmatch',           
                'urllib.ftplib',            
                'urllib.functools',         
                'urllib.gc',                
                'urllib.genericpath',       
                'urllib.getopt',            
                'urllib.getpass',           
                'urllib.gettext',           
                'urllib.hashlib',           
                'urllib.heapq',
                'urllib.httplib',
                'urllib.imp',
                'urllib.inspect',           
                'urllib.io',                
                'urllib.itertools',         
                'urllib.keyword',           
                'urllib.linecache',         
                'urllib.locale',            
                'urllib.logging',           
                'urllib.marshal',           
                'urllib.math',              
                'urllib.mimetools',         
                'urllib.mimetypes',         
                'urllib.msvcrt',            
                'urllib.nt',                
                'urllib.ntpath',            
                'urllib.nturl2path',        
                'urllib.opcode',            
                'urllib.operator',          
                'urllib.optparse',          
                'urllib.os',                
                'urllib.os2emxpath',        
                'urllib.pdb',           
                'urllib.pickle',            
                'urllib.posixpath',         
                'urllib.pprint',            
                'urllib.quopri',            
                'urllib.random ',           
                'urllib.re',                
                'urllib.repr',              
                'urllib.rfc822',            
                'urllib.robotparser',       
                'urllib.select',            
                'urllib.shlex',             
                'urllib.signal',            
                'urllib.socket',            
                'urllib.sre_compile',       
                'urllib.sre_constants',     
                'urllib.sre_parse',         
                'urllib.ssl',               
                'urllib.stat',              
                'urllib.string',            
                'urllib.strop',             
                'urllib.struct',            
                'urllib.subprocess',        
                'urllib.sys',               
                'urllib.tempfile',          
                'urllib.textwrap',          
                'urllib.thread',            
                'urllib.threading',         
                'urllib.time',              
                'urllib.token',             
                'urllib.tokenize',          
                'urllib.traceback',         
                'urllib.types',             
                'urllib.unittest',          
                'urllib.unittest.case',     
                'urllib.unittest.loader',   
                'urllib.unittest.main',     
                'urllib.unittest.result',   
                'urllib.unittest.runner',   
                'urllib.unittest.signals',  
                'urllib.unittest.suite',    
                'urllib.unittest.util',     
                'urllib.urllib',            
                'urllib.urlparse',          
                'urllib.uu',                
                'urllib.warnings',          
                'urllib.weakref',
                'collections.sys',
                'collections.abc'
                'collections.types'
                'collections._weakrefset',
                'collections._weakref')


INCLUDES_LIST = ('future', 'builtins')

ESKY_INCLUDES_LIST = ('UserList',
                      'UserString',
                      'commands',
                      )

INCLUDES_COND_3 = ("past", "builtins", "lib2to3", "past.builtins")
FUTURE_PACKAGES = ["future",
            "future.builtins",
            "future.types",
            "future.standard_library",
            "future.backports",
            "future.backports.email",
            "future.backports.email.mime",
            "future.backports.html",
            "future.backports.http",
            "future.backports.test",
            "future.backports.urllib",
            "future.backports.xmlrpc",
            "future.backports.misc",
            "future.moves",
            "future.moves.dbm",
            "future.moves.html",
            "future.moves.http",
            "future.moves.test",
            "future.moves.tkinter",
            "future.moves.urllib",
            "future.moves.xmlrpc",
            "future.tests",     # for future.tests.base
            # "future.tests.test_email",
            "future.utils",
            "past",
            "past.builtins",
            "past.types",
            "past.utils",
            # "past.tests",
            "past.translation",
            "libfuturize",
            "libfuturize.fixes",
            "libpasteurize",
            "libpasteurize.fixes",
           ]

def compulsory_fixers_start(freezer, **options):
    '''we just always apply this fix as it doesnt really hurt anything
    solves problem of datafiles being in zipfiles cxfreeze test failure condition 3'''
    if freezer == 'cxfreeze': # TODO esky actually could be any of the freezer have to do more work and be specific fuck
        options.setdefault('options', {}).setdefault('build_exe', {}).setdefault('zip_includes', [])
        zipincludes = options['options']['build_exe']['zip_includes']
    elif freezer == 'esky':
        options.setdefault('options', {}).setdefault('bdist_esky', {}).setdefault('freezer_options', {}).setdefault('zipIncludes', [])
        zipincludes = options['options']['bdist_esky']['freezer_options']['zipIncludes']
    else:
        return
    # todo have to make this more dynamic..
    if os.name == 'nt':
        zipincludes.extend([('C:/Python27/Lib/lib2to3/Grammar.txt', r'lib2to3/Grammar.txt')])
        zipincludes.extend([('C:/Python27/Lib/lib2to3/PatternGrammar.txt', r'lib2to3/PatternGrammar.txt')])
    else:
        pypath = '/usr/lib/python2.7'
        zipincludes.extend([(os.path.join(pypath, 'lib2to3/Grammar.txt'), r'lib2to3/Grammar.txt')])
        zipincludes.extend([(os.path.join(pypath, 'lib2to3/PatternGrammar.txt'), r'lib2to3/PatternGrammar.txt')])
        return
        py_check_path = os.path.join('/usr', 'lib', 'python')
        for path in sys.path:
            if py_check_path in path:
                pypath = path.split(os.sep)[:2]
                break
        zipincludes.extend([(os.path.join(pypath, 'lib2to3/Grammer.txt'), r'lib2to3/Grammar.txt')])
        zipincludes.extend([(os.path.join(pypath, 'lib2to3/PatternGrammar.txt'), r'lib2to3/PatternGrammar.txt')])


@preserve_cwd
def compulsory_fixers_end(freezer, **options):
    '''gotta extract the files from the zip so it find the module next to the zip'''#TODO delete the problem files from the library.zip as well
    if freezer in ('cxfreeze', 'esky'):
        modules_to_unzip = ('lib2to3',)
        zip_archive_name = 'library.zip'
        if freezer == 'cxfreeze':
            os.chdir('build')
            folder = os.listdir(os.getcwd())[0] #TODO multiple setupfiles at once
        elif freezer == 'esky':
            os.chdir('dist')
            zfname = os.path.join(os.getcwd(), get_zip_name(options))
            deploydir = os.path.join(os.getcwd(), os.path.splitext(zfname)[0])
            os.makedirs(deploydir)
            extract_zipfile(zfname, deploydir)
            # remove the esky zip
            os.remove(zfname)
            folder = os.path.join(deploydir, deploydir.split(os.sep)[-1])
        # extract the problem files
        os.chdir(folder)
        archive = zipfile.ZipFile(zip_archive_name)
        for file in archive.namelist():
            for bad_module in modules_to_unzip:
                if file.startswith(bad_module + '/'):
                    archive.extract(file, os.getcwd())
        archive.close()

        if freezer == 'esky':
            os.chdir('..')
            # rezip our esky
            create_zipfile(os.getcwd(), zfname)
            os.chdir('..')
            really_rmtree(deploydir)
        # elif freezer == 'py2exe':
        #     os.chdir('dist')
        # elif freezer == 'esky':
        #     os.chdir('dist')
        #     deploydir = os.getcwd()
        #     zfname = os.listdir(deploydir)[0]
        #     extract_zipfile(zfname,deploydir)

def using_future(freezer, executables):
    '''is our main program script using future?'''
    def check(file):
        for line in file:
            if any(x for x in('install_aliases()',) if x in line):
                return True
        else:
            return False
            
    for aexec in executables:
        if hasattr(aexec, 'script'):
            try:
                with open(aexec.script, 'r') as file:
                    if check(file):
                        return True
            except TypeError:
                return True
        else:
            with open(aexec, 'r') as file:
                if check(file):
                    return True
    else:
        return False

        
    
def detect_freezer(options):
    '''What freezer program are we using'''
    #~ if func.__module__ == 'cx_Freeze.dist'
    if options.get('executables'):
        return 'cxfreeze'
    elif options.get('console') or options.get('windows'):
        return 'py2exe'
    try:
        script_args = options.get('script_args')
    except Exception:
        pass
    else:
        if any(x for x in ('bdist_esky', 'bdist_esky_patch') if x in script_args):
            return 'esky'
    if options.get('packages'):
        return 'setuptools' #TODO this isn't sufficent, distutils also has packages ..
    else:
        return 'distutils'


def get_executables(freezer, options):
    '''returns the executables'''
    if freezer == 'cxfreeze':
        return options['executables']
    elif freezer == 'py2exe':
        if options.get('console'):  # can you have both? #TBD
            return options['console']
        else:
            return options['windows']
    elif freezer == 'esky':
        return options['scripts']
    else:
        return options['scripts']
from setuptools import setup

def get_setup_function(freezer):
    if freezer == 'cxfreeze':
        from cx_Freeze import setup
        return setup
    elif freezer in ('py2exe', 'esky', 'distutils'):
        from distutils.core import setup
        return setup
    elif freezer == 'setuptools':
        from setuptools import setup
        return setup


def setup(test_setup=False, **options):
    # We return False when we haven't done anything
    freezer = detect_freezer(options)
    if test_setup:
        dist_setup = lambda *args, **kwargs: 0
    else:
        dist_setup = get_setup_function(freezer)
    executables = get_executables(freezer, options)
    if not PY3 or freezer == 'esky':
        if freezer in ('cxfreeze', 'py2exe', 'esky'):
            if using_future(freezer, executables) or freezer == 'esky':
                if freezer == 'cxfreeze':
                    options.setdefault('options', {}).setdefault('build_exe', {}).setdefault('excludes', [])
                    options['options']['build_exe'].setdefault('packages', [])
                    options['options']['build_exe']['excludes'].extend(EXCLUDES_LIST)
                    options['options']['build_exe']['packages'].extend(INCLUDES_LIST)

                elif freezer == 'py2exe':
                    options.setdefault('options', {}).setdefault('py2exe', {}).setdefault('excludes', [])
                    options['options']['py2exe'].setdefault('packages', [])
                    options['options']['py2exe']['excludes'].extend(EXCLUDES_LIST)
                    options['options']['py2exe']['packages'].extend(INCLUDES_LIST)
                
                elif freezer == 'esky':
                    options.setdefault('options', {}).setdefault('bdist_esky', {}).setdefault('includes', [])
                    options.setdefault('options', {}).setdefault('bdist_esky', {}).setdefault('excludes', [])
                    if os.name == 'posix':
                        if not PY3:
                            options['options']['bdist_esky']['excludes'].extend(EXCLUDES_LIST)
                            options['options']['bdist_esky']['includes'].extend(FUTURE_PACKAGES)


                    elif os.name == 'nt':
                        if not PY3:
                            options['options']['bdist_esky']['includes'].extend(ESKY_INCLUDES_LIST)

                    # options['options'].setdefault('freezer_options', {}).setdefault('build_exe',{}).setdefault('packages', [])
                    # options['options']['freezer_options']['build_exe'].setdefault('excludes', [])
                    # options['options']['freezer_options']['build_exe']['excludes'].extend(EXCLUDES_LIST)
                    # options['options']['freezer_options']['build_exe']['packages'].extend(INCLUDES_LIST)

                    # options['options'].setdefault('freezer_options', {}).setdefault('build_exe',{}).setdefault('packages', [])
                    # options['options']['freezer_options']['bdist_esky'].setdefault('excludes', [])
                    # options['options']['freezer_options']['bdist_esky']['excludes'].extend(EXCLUDES_LIST)
                    # options['options']['freezer_options']['bdist_esky']['packages'].extend(INCLUDES_LIST)
                if not test_setup:
                    compulsory_fixers_start(freezer, **options)
                dist_setup(**options)
                if not test_setup:
                    compulsory_fixers_end(freezer, **options)
                return True
        
    if not test_setup:
        compulsory_fixers_start(freezer, **options)
    dist_setup(**options)
    if not test_setup:
        compulsory_fixers_end(freezer, **options)
    return False

