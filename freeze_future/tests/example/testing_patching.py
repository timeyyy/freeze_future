"""
Example module for testing this should work fine on 2 and 3
"""

import sys
import os
versiondir = os.path.dirname(sys.executable)
for nm in os.listdir(versiondir):
    if nm.startswith("Microsoft.") and nm.endswith(".CRT"):
        msvcrt_dir = os.path.join(versiondir,nm)
        assert os.path.isdir(msvcrt_dir)
        assert len(os.listdir(msvcrt_dir)) >= 2
        break
else:
    assert False, "MSVCRT not bundled in version dir "+versiondir

import sys
import time

try:
	import tkinter as tk
except ImportError:
	import Tkinter as tk

LABELS = ['ham', 'spam', 'foo', 'bar']

#~ time.sleep(0.1)
#~ sys.exit()

root = tk.Tk()
for text in LABELS:
	tk.Label(root, text=text).pack()
root.after(100, sys.exit)
root.mainloop()
