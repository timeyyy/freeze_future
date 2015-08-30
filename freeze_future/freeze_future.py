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
import pdb

import future

import pdb

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

def using_future(freezer, executables):
    '''is our main program script using future?'''
    def check(file):
        for line in file:
            if 'install_aliases()' in line:
                return True
        else:
            return False
            
    for aexec in executables:
        if hasattr(aexec, 'script'):
            with open(aexec.script, 'r') as file:
                if check(file):
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
    elif options.get('bdist_esky'):
        return 'esky'
    elif options.get('packages'):
        return 'setuptools' # this isn't sufficent, atm setuptools is returning distutils
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

    
def setup(dist_setup, **options):
    # We return False when we haven't done anything
    freezer = detect_freezer(options)
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
                    #from esky import bdist_esky
                    options.setdefault('bdist_esky', {}).setdefault('includes', [])
                    options.setdefault('bdist_esky', {}).setdefault('excludes', [])
                    options['bdist_esky']['excludes'].extend(EXCLUDES_LIST)
                    options['bdist_esky']['includes'].extend(INCLUDES_LIST)
                    # pdb.set_trace()
                dist_setup(**options)
                return True
        
        #~ if freezer == 'disutils':
    dist_setup(**options)
    return False
