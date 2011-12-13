#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pyxcf
# Copyright 2011 Grigory Petrov
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

class CImage( object ) :
  def __init__( self ) :
    self.size   = (0,0)
    self.mode   = ""
    self.props  = []
    self.layers = []

class CProp( dict ) :
  def __init__( self ) :
    super( CProp, self ).__init__()
    self.type = PROP_END
    ##! Can be incorrect for known property types.
    self.size = 0

class CLayer( dict ) :
  def __init__( self ) :
    super( CLayer, self ).__init__()
    self.size  = (0,0)
    self.mode  = ""
    self.alpha = False

class CReader( object ) :
  def __init__( self, i_sData ) :
    self.m_sData = i_sData
    self.m_nOffset = 0
    self.m_lOffsets = []
  def Read( self, i_sFormat ) :
    ABOUT = { '!' : 0, 'B' : 1, 'H' : 2, 'I' : 4, 'f' : 4 }
    nLen = reduce( lambda x, y : x + y, [ ABOUT[ x ] for x in i_sFormat ] )
    sSplice = self.m_sData[ self.m_nOffset : self.m_nOffset + nLen ]
    gItems = struct.unpack( i_sFormat, sSplice )
    self.m_nOffset += nLen
    return gItems if len( gItems ) > 1 else gItems[ 0 ]
  def ReadArray( self, i_nLen ) :
    sSplice = self.m_sData[ self.m_nOffset : self.m_nOffset + i_nLen ]
    self.m_nOffset += i_nLen
    return sSplice
  def Push( self, i_nNewOffset ) :
    self.m_lOffsets.append( self.m_nOffset )
    self.m_nOffset = i_nNewOffset
  def Pop( self ) :
    self.m_nOffset = self.m_lOffsets.pop()

class CReaderXcf( CReader ) :

  def ReadStr( self ) :
    nLen = self.Read( '!I' )
    assert nLen > 0
    ##  Length includes terminating zero byte.
    sData = self.ReadArray( nLen - 1 )
    ##  Terminating zero byte.
    self.Read( '!B' )
    return sData.decode( 'utf-8' )

  def ReadBool( self ) :
    return { 1 : True, 0 : False }[ self.Read( '!I' ) ]

  def ReadPropEnd( self, b_oProp ) :
    assert 0 == b_oProp.size
    pass

  def ReadPropCompression( self, b_oProp ) :
    assert 1 == b_oProp.size
    b_oProp[ 'COMPRESSION' ] = self.Read( '!B' )

  def ReadPropResolution( self, b_oProp ) :
    assert 8 == b_oProp.size
    b_oProp[ 'RES_X' ], b_oProp[ 'RES_Y' ] = self.Read( '!ff' )

  def ReadPropTattoo( self, b_oProp ) :
    assert 4 == b_oProp.size
    ##  Highest tattoo in image, used to generate new tattoos.
    b_oProp[ 'TATTOO' ] = self.Read( '!I' )

  def ReadPropParasites( self, b_oProp ) :
    self.ReadArray( b_oProp.size )

  def ReadPropUnit( self, b_oProp ) :
    assert 4 == b_oProp.size
    ##  Print resolution units.
    ABOUT_UNIT = { 0 : 'inch', 1 : 'mm', 2 : 'point', 3 : 'pica' }
    b_oProp[ 'TATTOO' ] = ABOUT_UNIT[ self.Read( '!I' ) ]

  def ReadPropVectors( self, b_oProp ) :
    b_oProp[ 'VER' ] = self.Read( '!I' )
    assert 1 == b_oProp[ 'VER' ]
    b_oProp[ 'ACTIVE_PATH_IDX' ] = self.Read( '!I' )
    nPaths = self.Read( '!I' )
    b_oProp[ 'PATHS' ] = []
    for i in range( nPaths ) :
      mPath = {}
      mPath[ 'NAME' ]    = self.ReadStr()
      mPath[ 'TATTOO' ]  = self.Read( '!I' )
      mPath[ 'VISIBLE' ] = self.ReadBool()
      mPath[ 'LINKED' ]  = self.ReadBool()
      mPath[ 'STROKES' ] = []
      nParasites = self.Read( '!I' )
      nStrokes = self.Read( '!I' )
      for i in range( nParasites ) :
        oProp = CProp()
        oProp.type = self.Read( '!I' )
        oProp.size = self.Read( '!I' )
        assert PROP_PARASITES == oProp.type
        self.ReadPropParasites( oProp )
      for i in range( nStrokes ) :
        mStroke = {}
        ABOUT_TYPES = { 1 : 'bezier' }
        mStroke[ 'TYPE' ] = ABOUT_TYPES[ self.Read( '!I' ) ]
        mStroke[ 'CLOSED' ] = self.ReadBool()
        mStroke[ 'POINTS' ] = []
        nFloats = self.Read( '!I' )
        assert 2 <= nFloats <= 6
        nPoints = self.Read( '!I' )
        for i in range( nPoints ) :
          mPoint = {}
          ABOUT_TYPES = { 0 : 'anchor', 1 : 'control' }
          mPoint[ 'TYPE' ]     = ABOUT_TYPES[ self.Read( '!I' ) ]
          mPoint[ 'X' ]        = self.Read( '!f' )
          mPoint[ 'Y' ]        = self.Read( '!f' )
          mPoint[ 'PRESSURE' ] = self.Read( '!f' ) if nFloats >=3 else 1.0
          mPoint[ 'XTILT' ]    = self.Read( '!f' ) if nFloats >=4 else 0.5
          mPoint[ 'YTILT' ]    = self.Read( '!f' ) if nFloats >=5 else 0.5
          mPoint[ 'WHEEL' ]    = self.Read( '!f' ) if nFloats >=6 else 0.5
          mStroke[ 'POINTS' ].append( mPoint )
        mPath[ 'STROKES' ].append( mStroke )
      b_oProp[ 'PATHS' ].append( mPath )

  def ReadProp( self ) :
    oProp = CProp()
    oProp.type = self.Read( '!I' )
    oProp.size = self.Read( '!I' )
    ABOUT_READERS = {
      PROP_END         : self.ReadPropEnd,
      PROP_COMPRESSION : self.ReadPropCompression,
      PROP_RESOLUTION  : self.ReadPropResolution,
      PROP_TATTOO      : self.ReadPropTattoo,
      PROP_PARASITES   : self.ReadPropParasites,
      PROP_UNIT        : self.ReadPropUnit,
      PROP_VECTORS     : self.ReadPropVectors
    }
    if oProp.type in ABOUT_READERS :
      ABOUT_READERS[ oProp.type ]( oProp )
    else :
      print( "Ignoring unknown property of type {0}".format( oProp.type ) )
      self.ReadArray( oProp.size )
    return oProp

  def ReadLayer( self, i_nOffset ) :
    self.Push( i_nOffset )
    oLayer = CLayer()
    oLayer.size = self.Read( '!II' )
    ABOUT_MODES = {
      0 : ('RGB', False),
      1 : ('RGB', True),
      2 : ('L', False),
      3 : ('L', True),
      4 : ('P', False),
      5 : ('P', True) }
    oLayer.mode, oLayer.alpha = ABOUT_MODES[ self.Read( '!I' ) ]
    self.Pop()
    return oLayer

def open( fp, mode = 'r' ) :
  assert 'r' == mode
  with __builtin__.open( fp, mode ) as oFile :
    oReader = CReaderXcf( oFile.read() )
  oImg = CImage()

  ##  Read header
  sMagic = oReader.ReadArray( 9 )
  assert sMagic.startswith( 'gimp xcf' )
  sVer = oReader.ReadArray( 4 )
  assert sVer in [ 'file', 'v001', 'v002' ]
  assert 0 == oReader.Read( '!B' )
  oImg.size = oReader.Read( '!II' )
  assert oImg.size[ 0 ] > 0 and oImg.size[ 1 ] > 0
  ABOUT_MODE = { 0 : 'RGB', 1 : 'L', 2 : 'P' }
  oImg.mode = ABOUT_MODE[ oReader.Read( '!I' ) ]

  ##  Read properties.
  while True :
    oProp = oReader.ReadProp()
    ##  Last property will have type PROP_END and size 0.
    if PROP_END == oProp.type :
      break
    oImg.props.append( oProp )

  ##  Read layers.
  while True :
    nOffset = oReader.Read( '!I' )
    if 0 == nOffset :
      break
    oImg.layers.append( oReader.ReadLayer( nOffset ) )

  return oImg

