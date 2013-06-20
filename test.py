#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pyxcf simple test.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

# Test.

import pyxcf

oImg = pyxcf.open( "test.xcf" )
print( "size: {0} x {1}".format( * oImg.size_g ) )
ABOUT_MODE = { 'RGB': 'RGB', 'L': 'Grayscale', 'P': 'Indexed' }
print( "mode: {0}".format( ABOUT_MODE[ oImg.mode_s ] ) )
for oLayer in oImg.layers_l:
  print( "  Layer" )
  print( "  size: {0} x {1}".format( * oLayer.size_g ) )
  print( "  mode: {0}, alpha: {1}".format( oLayer.mode_s, oLayer.alpha_f ) )

