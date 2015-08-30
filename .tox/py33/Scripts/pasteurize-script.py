#!D:\STORAGE\Dropbox\programming\freeze_future\.tox\py33\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'future==0.14.3','console_scripts','pasteurize'
__requires__ = 'future==0.14.3'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('future==0.14.3', 'console_scripts', 'pasteurize')()
    )
