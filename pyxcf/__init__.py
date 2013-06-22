#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pyxcf implementation.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

# Main library code.

import __builtin__, struct

PROP_END         = 0
PROP_COMPRESSION = 17
PROP_RESOLUTION  = 19
PROP_TATTOO      = 20
PROP_PARASITES   = 21
PROP_UNIT        = 22
PROP_VECTORS     = 25


class CImage( object ):


  def __init__( self ):
    self.size_g   = (0,0)
    self.mode_s   = ""
    self.props_l  = []
    self.layers_l = []


class CProp( dict ):


  def __init__( self ):
    dict.__init__( self )
    self.type_n = PROP_END
    ##! Can be incorrect for known property types.
    self.size_n = 0


class CLayer( dict ):


  def __init__( self ):
    super( CLayer, self ).__init__()
    self.size_g  = (0,0)
    self.mode_s  = ""
    self.alpha_f = False


class CReader( object ):


  def __init__( self, s_data ):
    self.data_s = s_data
    self.offset_n = 0
    self.offsets_l = []


  def read( self, s_format ):
    ABOUT = { '!': 0, 'B': 1, 'H': 2, 'I': 4, 'f': 4 }
    nLen = reduce( lambda x, y: x + y, [ ABOUT[ x ] for x in s_format ] )
    sSplice = self.data_s[ self.offset_n: self.offset_n + nLen ]
    gItems = struct.unpack( s_format, sSplice )
    self.offset_n += nLen
    return gItems if len( gItems ) > 1 else gItems[ 0 ]


  def readArray( self, n_len ):
    sSplice = self.data_s[ self.offset_n: self.offset_n + n_len ]
    self.offset_n += n_len
    return sSplice


  def Push( self, n_newOffset ):
    self.offsets_l.append( self.offset_n )
    self.offset_n = n_newOffset


  def Pop( self ):
    self.offset_n = self.offsets_l.pop()


class CReaderXcf( CReader ):


  def readStr( self ):
    nLen = self.read( '!I' )
    assert nLen > 0
    ##  Length includes terminating zero byte.
    sData = self.readArray( nLen - 1 )
    ##  Terminating zero byte.
    self.read( '!B' )
    return sData.decode( 'utf-8' )


  def readBool( self ):
    return { 1: True, 0: False }[ self.read( '!I' ) ]


  def readPropEnd( self, o_prop ):
    assert 0 == o_prop.size_n
    pass


  def readPropCompression( self, o_prop ):
    assert 1 == o_prop.size_n
    o_prop[ 'COMPRESSION' ] = self.read( '!B' )


  def readPropResolution( self, o_prop ):
    assert 8 == o_prop.size_n
    o_prop[ 'RES_X' ], o_prop[ 'RES_Y' ] = self.read( '!ff' )


  def readPropTattoo( self, o_prop ):
    assert 4 == o_prop.size_n
    ##  Highest tattoo in image, used to generate new tattoos.
    o_prop[ 'TATTOO' ] = self.read( '!I' )


  def readPropParasites( self, o_prop ):
    self.readArray( o_prop.size_n )


  def readPropUnit( self, o_prop ):
    assert 4 == o_prop.size_n
    ##  Print resolution units.
    ABOUT_UNIT = { 0: 'inch', 1: 'mm', 2: 'point', 3: 'pica' }
    o_prop[ 'TATTOO' ] = ABOUT_UNIT[ self.read( '!I' ) ]


  def readPropVectors( self, o_prop ):
    o_prop[ 'VER' ] = self.read( '!I' )
    assert 1 == o_prop[ 'VER' ]
    o_prop[ 'ACTIVE_PATH_IDX' ] = self.read( '!I' )
    nPaths = self.read( '!I' )
    o_prop[ 'PATHS' ] = []
    for i in range( nPaths ):
      mPath = {}
      mPath[ 'NAME' ]    = self.readStr()
      mPath[ 'TATTOO' ]  = self.read( '!I' )
      mPath[ 'VISIBLE' ] = self.readBool()
      mPath[ 'LINKED' ]  = self.readBool()
      mPath[ 'STROKES' ] = []
      nParasites = self.read( '!I' )
      nStrokes = self.read( '!I' )
      for i in range( nParasites ):
        oProp = CProp()
        oProp.type_n = self.read( '!I' )
        oProp.size_n = self.read( '!I' )
        assert PROP_PARASITES == oProp.type_n
        self.readPropParasites( oProp )
      for i in range( nStrokes ):
        mStroke = {}
        ABOUT_TYPES = { 1: 'bezier' }
        mStroke[ 'TYPE' ] = ABOUT_TYPES[ self.read( '!I' ) ]
        mStroke[ 'CLOSED' ] = self.readBool()
        mStroke[ 'POINTS' ] = []
        nFloats = self.read( '!I' )
        assert 2 <= nFloats <= 6
        nPoints = self.read( '!I' )
        for i in range( nPoints ):
          mPoint = {}
          ABOUT_TYPES = { 0: 'anchor', 1: 'control' }
          mPoint[ 'TYPE' ]     = ABOUT_TYPES[ self.read( '!I' ) ]
          mPoint[ 'X' ]        = self.read( '!f' )
          mPoint[ 'Y' ]        = self.read( '!f' )
          mPoint[ 'PRESSURE' ] = self.read( '!f' ) if nFloats >=3 else 1.0
          mPoint[ 'XTILT' ]    = self.read( '!f' ) if nFloats >=4 else 0.5
          mPoint[ 'YTILT' ]    = self.read( '!f' ) if nFloats >=5 else 0.5
          mPoint[ 'WHEEL' ]    = self.read( '!f' ) if nFloats >=6 else 0.5
          mStroke[ 'POINTS' ].append( mPoint )
        mPath[ 'STROKES' ].append( mStroke )
      o_prop[ 'PATHS' ].append( mPath )


  def readProp( self ):
    oProp = CProp()
    oProp.type_n = self.read( '!I' )
    oProp.size_n = self.read( '!I' )
    ABOUT_READERS = {
      PROP_END        : self.readPropEnd,
      PROP_COMPRESSION: self.readPropCompression,
      PROP_RESOLUTION : self.readPropResolution,
      PROP_TATTOO     : self.readPropTattoo,
      PROP_PARASITES  : self.readPropParasites,
      PROP_UNIT       : self.readPropUnit,
      PROP_VECTORS    : self.readPropVectors
    }
    if oProp.type_n in ABOUT_READERS:
      ABOUT_READERS[ oProp.type_n ]( oProp )
    else:
      print( "Ignoring unknown property of type {0}".format( oProp.type_n ) )
      self.readArray( oProp.size_n )
    return oProp


  def readLayer( self, n_offset ):
    self.Push( n_offset )
    oLayer = CLayer()
    oLayer.size_g = self.read( '!II' )
    ABOUT_MODES = {
      0: ('RGB', False),
      1: ('RGB', True),
      2: ('L', False),
      3: ('L', True),
      4: ('P', False),
      5: ('P', True) }
    oLayer.mode_s, oLayer.alpha_f = ABOUT_MODES[ self.read( '!I' ) ]
    self.Pop()
    return oLayer


def open( fp, mode = 'r' ):
  assert 'r' == mode
  with __builtin__.open( fp, mode + 'b' ) as oFile:
    oReader = CReaderXcf( oFile.read() )
  oImg = CImage()

  ##  Read header
  sMagic = oReader.readArray( 9 )
  assert sMagic.startswith( 'gimp xcf' )
  sVer = oReader.readArray( 4 )
  assert sVer in [ 'file', 'v001', 'v002' ]
  assert 0 == oReader.read( '!B' )
  oImg.size_g = oReader.read( '!II' )
  assert oImg.size_g[ 0 ] > 0 and oImg.size_g[ 1 ] > 0
  ABOUT_MODE = { 0: 'RGB', 1: 'L', 2: 'P' }
  oImg.mode_s = ABOUT_MODE[ oReader.read( '!I' ) ]

  ##  Read properties.
  while True:
    oProp = oReader.readProp()
    ##  Last property will have type PROP_END and size 0.
    if PROP_END == oProp.type_n:
      break
    oImg.props_l.append( oProp )

  ##  Read layers.
  while True:
    nOffset = oReader.read( '!I' )
    if 0 == nOffset:
      break
    oImg.layers_l.append( oReader.readLayer( nOffset ) )

  return oImg

