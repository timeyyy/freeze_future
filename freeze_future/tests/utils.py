from __future__ import with_statement
from __future__ import print_function

from builtins import object
import shutil
import os
import errno
import time
import functools
import zipfile
import sys
import subprocess
import pdb
import logging
import contextlib

from esky.util import get_platform

try:
    import variables as V
except ImportError:
    from . import variables as V


WORKING_SCRIPT = V.SCRIPT
ORIGINAL_CWD = os.getcwd()

def normalize_sysargs(arg='build'):#TODO delete this parameter
    '''Normailze sys args as setup function use them'''
    try:
        sys.argv[1] = arg
    except IndexError:
        sys.argv.append(arg)
    try:
        del sys.argv[2:]
    except IndexError:
        pass
    cleanup_dirs()
    if os.path.exists('build') or os.path.exists('dist'):
        raise SystemError("Build and dist dirs cannot be cleaned up, remove before testing")



def cleanup_dirs():
    '''Remove the build dir as multiple programs built at once causes
    failures'''
    # os.chdir(ORIGINAL_CWD)
    try:
        really_rmtree(os.path.abspath('build'))
    except (IOError, OSError):
        pass

    try:
        # Created by py2exe and esky
        really_rmtree(os.path.abspath('dist'))
    except (IOError, OSError):
        pass

    try:
        really_rmtree(os.path.abspath('__pycache__'))
    except (IOError, OSError):
        pass


def make_new_script_name(name):
    '''Script path taken from the working script and added to our name'''
    new_script = os.path.join(os.path.dirname(WORKING_SCRIPT), name)
    return new_script


def insert_code(new_script, *code):
    '''Insert code into our working script and save as'''
    def find_start(file):
        '''we want to insert after doc string, find the position'''
        for i, line in enumerate(file):
            if i == 0:
                continue
            if "'''" in line or "\"\"\"" in line:
                return i + 1
    
    file = InMemoryWriter(WORKING_SCRIPT, verbose=True)
    i = find_start(file )
    for j, line in enumerate(code):
        file.insert(i+j+1, line+"\n")
    try:
        file.insert(j+i+2, "\n")
    # no lines where given to be inserted
    except UnboundLocalError:
        pass
    file.save(new_script)


def preserve_cwd(function):
    @functools.wraps(function)
    def decorator(*args, **kwargs):
        cwd = os.getcwd()
        try:
            return function(*args, **kwargs)
        finally:
            os.chdir(cwd)
    return decorator


@preserve_cwd
def run_script(script, freezer='cxfreeze', zip_name=None):
    '''run the executable and return True if it ran!'''
    filewithext = os.path.basename(script)
    file = os.path.splitext(filewithext)[0]
    if freezer in ('cxfreeze', 'distutils', 'setuptools'):
        os.chdir('build')
        folder = os.listdir(os.getcwd())[0]
        os.chdir(folder)
    elif freezer == 'py2exe':
        os.chdir('dist')
    elif freezer == 'esky':     #TODO MAKE ESKY NOT ZIP PER DEFAULT
        os.chdir('dist')
        deploydir = os.getcwd()
        if not zip_name:
            zip_name = os.listdir(deploydir)[0]
        extract_zipfile(zip_name,deploydir)
        
    if freezer in ('distutils', 'setuptools'):
        cmd = ['python', '{0}.py'.format(file)] 
    else:
        cmd = [os.path.abspath(file)]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    errs = proc.communicate()
    os.chdir(ORIGINAL_CWD)
    if not proc.returncode:
        return True, errs[1]
    else:
        return False, errs[1]


class InMemoryWriter(list, object): #TBD UPDATE ORIGINAL WITH THIS
    """
    Used to defer saving and opening files to later controllers
    just write data to here
    
    On creation you can read all contents either from:
    an open file,
    a list
    a path/name to a file
    
    by default if the file is not found it will add the str as a row,
    set verbose to True to throw an error instead
    
    While iterating you can set copy=True to edit data
    as you iterate over it
    
    you can accesses the current position using self.i, useful if 
    you are using filter or something like that while iterating
    
    #NOTE NAME VERBOSE IS VERY INAPT I KNOW BUT CBF ATM
    
    NO ERRORS WILL BE RAISED ON OVERWRITING XD
    
    """
    def __init__(self, insert_me=None, verbose=False, copy=False):
        list.__init__(self)
        self.copy = copy
        self.data = self            # i was using data variable instead of inheriting from list to lazy to rename old code
        self.i=0
        if type(insert_me) == str:
            try:
                with open(insert_me, 'r') as file: 
                    self.writelines(file)
                    self.original_filename = insert_me
            except (IOError, OSError) as err:
                if not verbose:
                    self.append(insert_me)
                raise err
        elif insert_me:
            self.writelines(insert_me)
    
    def write(self, stuff):
        self.append(stuff)
    
    def writelines(self, passed_data):
        for item in passed_data:
            self.data.append(item)
    
    def close(self):
        self.strData = json.dumps(self.data)    # turned into str
    
    def __call__(self, copy=None):
        if copy:
            self.copy = True
        return self
    
    def __iter__(self):                 
        self.i=0
        if self.copy:
            self.data_copy = self.data[:]
        return self
    
    def __next__(self):
        if self.i+1 > len(self.data):
            try:
                del self.data_copy
            except AttributeError:
                pass
            raise StopIteration  
        if not self.copy:
            requested = self.data[self.i]
        else:
            requested = self.data_copy[self.i]
        self.i+=1
        return requested
    
    def readlines(self):
        return self.data
    
    def save(self, path=False):
        '''If you passed the filename as a str will default to that otherwise pass in a name'''
        if not path:
            path = self.original_filename
    
        with open(path, 'w') as file: 
            for row in self.data:
                file.write(row)

def really_rmtree(path):
    """Like shutil.rmtree, but try to work around some win32 wierdness.

    Every so often windows likes to throw a spurious error about not being
    able to remove a directory - like claiming it still contains files after
    we just deleted all the files in the directory.  If we sleep for a brief
    period and try again it seems to get over it.
    """
    if sys.platform != "win32":
        shutil.rmtree(path)
    else:
        #  If it's going to error out legitimately, let it do so.
        if not os.path.exists(path):
            shutil.rmtree(path)
        #  This is a little retry loop that catches troublesome errors.
        for _ in range(100):
            try:
                shutil.rmtree(path)
            except WindowsError as e:
                if e.errno in (errno.ENOTEMPTY,errno.EACCES,):
                    time.sleep(0.01)
                elif e.errno == errno.ENOENT:
                    if not os.path.exists(path):
                        return
                    time.sleep(0.01)
                else:
                    raise
            else:
                break
        else:
            shutil.rmtree(path)

def extract_zipfile(source,target,name_filter=None):
    """Extract the contents of a zipfile into a target directory.

    The argument 'source' names the zipfile to read, while 'target' names
    the directory into which to extract.  If given, the optional argument
    'name_filter' must be a function mapping names from the zipfile to names
    in the target directory.
    """
    zf = zipfile.ZipFile(source,"r")
    try:
        if hasattr(zf,"open"):
            zf_open = zf.open
        else:
            def zf_open(nm,mode):
                return StringIO.StringIO(zf.read(nm))
        for nm in zf.namelist():
            if nm.endswith("/"):
                continue
            if name_filter:
                outfilenm = name_filter(nm)
                if outfilenm is None:
                    continue
                outfilenm = os.path.join(target,outfilenm)
            else:
                outfilenm = os.path.join(target,nm)
            if not os.path.isdir(os.path.dirname(outfilenm)):
                os.makedirs(os.path.dirname(outfilenm))
            infile = zf_open(nm,"r")
            try:
                outfile = open(outfilenm,"wb")
                try:
                    shutil.copyfileobj(infile,outfile)
                finally:
                    outfile.close()
            finally:
                infile.close()
            mode = zf.getinfo(nm).external_attr >> 16
            if mode:
                os.chmod(outfilenm,mode)
    finally:
        zf.close()

def create_zipfile(source,target,get_zipinfo=None,members=None,compress=None):
    """Bundle the contents of a given directory into a zipfile.

    The argument 'source' names the directory to read, while 'target' names
    the zipfile to be written.

    If given, the optional argument 'get_zipinfo' must be a function mapping
    filenames to ZipInfo objects.  It may also return None to indicate that
    defaults should be used, or a string to indicate that defaults should be
    used with a new archive name.

    If given, the optional argument 'members' must be an iterable yielding
    names or ZipInfo objects.  Files will be added to the archive in the
    order specified by this function.

    If the optional argument 'compress' is given, it must be a bool indicating
    whether to compress the files by default.  The default is no compression.
    """
    if not compress:
        compress_type = zipfile.ZIP_STORED
    else:
        compress_type = zipfile.ZIP_DEFLATED
    zf = zipfile.ZipFile(target,"w",compression=compress_type)
    if members is None:
        def gen_members():
            for (dirpath,dirnames,filenames) in os.walk(source):
                for fn in filenames:
                    yield os.path.join(dirpath,fn)[len(source)+1:]
        members = gen_members()
    for fpath in members:
        if isinstance(fpath,zipfile.ZipInfo):
            zinfo = fpath
            fpath = os.path.join(source,zinfo.filename)
        else:
            if get_zipinfo:
                zinfo = get_zipinfo(fpath)
            else:
                zinfo = None
            fpath = os.path.join(source,fpath)
        if os.path.islink(fpath):
            # For information about adding symlinks to a zip file, see
            # https://mail.python.org/pipermail/python-list/2005-June/322180.html
            dest = os.readlink(fpath)
            if zinfo is None:
                zinfo = zipfile.ZipInfo()
                zinfo.filename = fpath[len(source)+1:]
            elif isinstance(zinfo,basestring):
                link = zinfo
                zinfo = zipfile.ZipInfo()
                zinfo.filename = link
            else: # isinstance(zinfo,zipfile.ZipInfo)
                pass
            zinfo.create_system = 3
            zinfo.external_attr = 2716663808 # symlink: 0xA1ED0000
            zf.writestr(zinfo,dest)
        else: # not a symlink
            if zinfo is None:
                zf.write(fpath,fpath[len(source)+1:])
            elif isinstance(zinfo,basestring):
                zf.write(fpath,zinfo)
            else:
                with open(fpath,"rb") as f:
                    zf.writestr(zinfo,f.read())
    zf.close()

def setup_logger(log_file):
    '''One function call to set up logging with some nice logs about the machine'''
    logging.basicConfig(
        filename=log_file,
        filemode='w',
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s: %(message)s')  # one run

@contextlib.contextmanager
def remember_cwd():
    curdir= os.getcwd()
    try: yield
    finally: os.chdir(curdir)

def get_zip_name(options):
    '''mirrors the esky behaviour of creating a zipfile name, '''
    def get_name():
        try:
            return options['name'] or "UNKNOWN"
        except KeyError:
            return "UNKNOWN"
    def get_version():
        try:
            return options['version'] or "0.0.0"
        except KeyError:
            return "0.0.0"

    fullname = "%s-%s" % (get_name(), get_version())
    platform = get_platform()
    zfname = os.path.join("%s.%s.zip"%(fullname,platform,))
    return zfname
