"""
Example module for testing this should work fine on 2 and 3
"""

from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

#~ import sys

try:
	import tkinter as tk
except ImportError:
	import Tkinter as tk
	
LABELS = ['ham', 'spam', 'foo', 'bar']

root = tk.Tk()
for text in LABELS:
	tk.Label(root, text=text).pack()
root.mainloop()

