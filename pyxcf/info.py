#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

# pyxcf information.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

import os
import pkg_resources

NAME_SHORT = "pyxcf"
VER_MAJOR = 0
VER_MINOR = 1
try :
  VER_TXT = pkg_resources.require( NAME_SHORT )[ 0 ].version
##  Installing via 'setup.py develop'?
except pkg_resources.DistributionNotFound :
  VER_BUILD = 0
  VER_TXT = ".".join( map( str, [ VER_MAJOR, VER_MINOR, VER_BUILD ] ) )
DIR_THIS = os.path.dirname( os.path.abspath( __file__ ) )
NAME_FULL = "Python XCF"
DESCR = """
{s_name_short} v. {s_ver_txt}\\n\\n
A simple python lib that can read some of .xcf file data into memory.
""".replace( '\n', '' ).replace( '\\n', '\n' ).strip().format(
  s_name_short = NAME_SHORT,
  s_ver_txt = VER_TXT )

