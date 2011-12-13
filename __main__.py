#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pyxcf
# Copyright 2011 Grigory Petrov
# See LICENSE for details.

# Test.

import pyxcf

oImg = pyxcf.open( "test.xcf" )
print( "size: {0} x {1}".format( * oImg.size ) )
ABOUT_MODE = { 'RGB' : 'RGB', 'L' : 'Grayscale', 'P' : 'Indexed' }
print( "mode: {0}".format( ABOUT_MODE[ oImg.mode ] ) )
for oLayer in oImg.layers :
  print( "  Layer" )
  print( "  size: {0} x {1}".format( * oLayer.size ) )
  print( "  mode: {0}, alpha: {1}".format( oLayer.mode, oLayer.alpha ) )

