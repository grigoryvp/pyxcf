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


class CImage( object ) :


  def __init__( self ) :
    self.size   = (0,0)
    self.mode   = ""
    self.props  = []
    self.layers = []


class CProp( dict ) :


  def __init__( self ) :
    dict.__init__( self )
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


  def __init__( self, s_data ) :
    self.m_sData = s_data
    self.m_nOffset = 0
    self.m_lOffsets = []


  def read( self, s_format ) :
    ABOUT = { '!' : 0, 'B' : 1, 'H' : 2, 'I' : 4, 'f' : 4 }
    nLen = reduce( lambda x, y : x + y, [ ABOUT[ x ] for x in s_format ] )
    sSplice = self.m_sData[ self.m_nOffset : self.m_nOffset + nLen ]
    print( len( sSplice ), nLen )
    gItems = struct.unpack( s_format, sSplice )
    self.m_nOffset += nLen
    return gItems if len( gItems ) > 1 else gItems[ 0 ]


  def readArray( self, n_len ) :
    sSplice = self.m_sData[ self.m_nOffset : self.m_nOffset + n_len ]
    self.m_nOffset += n_len
    return sSplice


  def Push( self, i_nNewOffset ) :
    self.m_lOffsets.append( self.m_nOffset )
    self.m_nOffset = i_nNewOffset


  def Pop( self ) :
    self.m_nOffset = self.m_lOffsets.pop()


class CReaderXcf( CReader ) :


  def readStr( self ) :
    nLen = self.read( '!I' )
    assert nLen > 0
    ##  Length includes terminating zero byte.
    sData = self.readArray( nLen - 1 )
    ##  Terminating zero byte.
    self.read( '!B' )
    return sData.decode( 'utf-8' )


  def readBool( self ) :
    return { 1 : True, 0 : False }[ self.read( '!I' ) ]


  def readPropEnd( self, o_prop ) :
    assert 0 == o_prop.size
    pass


  def readPropCompression( self, o_prop ) :
    assert 1 == o_prop.size
    o_prop[ 'COMPRESSION' ] = self.read( '!B' )


  def readPropResolution( self, o_prop ) :
    assert 8 == o_prop.size
    o_prop[ 'RES_X' ], o_prop[ 'RES_Y' ] = self.read( '!ff' )


  def readPropTattoo( self, o_prop ) :
    assert 4 == o_prop.size
    ##  Highest tattoo in image, used to generate new tattoos.
    o_prop[ 'TATTOO' ] = self.read( '!I' )


  def readPropParasites( self, o_prop ) :
    self.readArray( o_prop.size )


  def readPropUnit( self, o_prop ) :
    assert 4 == o_prop.size
    ##  Print resolution units.
    ABOUT_UNIT = { 0 : 'inch', 1 : 'mm', 2 : 'point', 3 : 'pica' }
    o_prop[ 'TATTOO' ] = ABOUT_UNIT[ self.read( '!I' ) ]


  def readPropVectors( self, o_prop ) :
    o_prop[ 'VER' ] = self.read( '!I' )
    assert 1 == o_prop[ 'VER' ]
    o_prop[ 'ACTIVE_PATH_IDX' ] = self.read( '!I' )
    nPaths = self.read( '!I' )
    o_prop[ 'PATHS' ] = []
    for i in range( nPaths ) :
      mPath = {}
      mPath[ 'NAME' ]    = self.readStr()
      mPath[ 'TATTOO' ]  = self.read( '!I' )
      mPath[ 'VISIBLE' ] = self.readBool()
      mPath[ 'LINKED' ]  = self.readBool()
      mPath[ 'STROKES' ] = []
      nParasites = self.read( '!I' )
      nStrokes = self.read( '!I' )
      for i in range( nParasites ) :
        oProp = CProp()
        oProp.type = self.read( '!I' )
        oProp.size = self.read( '!I' )
        assert PROP_PARASITES == oProp.type
        self.readPropParasites( oProp )
      for i in range( nStrokes ) :
        mStroke = {}
        ABOUT_TYPES = { 1 : 'bezier' }
        mStroke[ 'TYPE' ] = ABOUT_TYPES[ self.read( '!I' ) ]
        mStroke[ 'CLOSED' ] = self.readBool()
        mStroke[ 'POINTS' ] = []
        nFloats = self.read( '!I' )
        assert 2 <= nFloats <= 6
        nPoints = self.read( '!I' )
        for i in range( nPoints ) :
          mPoint = {}
          ABOUT_TYPES = { 0 : 'anchor', 1 : 'control' }
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


  def readProp( self ) :
    oProp = CProp()
    oProp.type = self.read( '!I' )
    oProp.size = self.read( '!I' )
    ABOUT_READERS = {
      PROP_END         : self.readPropEnd,
      PROP_COMPRESSION : self.readPropCompression,
      PROP_RESOLUTION  : self.readPropResolution,
      PROP_TATTOO      : self.readPropTattoo,
      PROP_PARASITES   : self.readPropParasites,
      PROP_UNIT        : self.readPropUnit,
      PROP_VECTORS     : self.readPropVectors
    }
    if oProp.type in ABOUT_READERS :
      ABOUT_READERS[ oProp.type ]( oProp )
    else :
      print( "Ignoring unknown property of type {0}".format( oProp.type ) )
      self.readArray( oProp.size )
    return oProp


  def readLayer( self, i_nOffset ) :
    self.Push( i_nOffset )
    oLayer = CLayer()
    oLayer.size = self.read( '!II' )
    ABOUT_MODES = {
      0 : ('RGB', False),
      1 : ('RGB', True),
      2 : ('L', False),
      3 : ('L', True),
      4 : ('P', False),
      5 : ('P', True) }
    oLayer.mode, oLayer.alpha = ABOUT_MODES[ self.read( '!I' ) ]
    self.Pop()
    return oLayer


def open( fp, mode = 'r' ) :
  assert 'r' == mode
  with __builtin__.open( fp, mode ) as oFile :
    oReader = CReaderXcf( oFile.read() )
  oImg = CImage()

  ##  Read header
  sMagic = oReader.readArray( 9 )
  assert sMagic.startswith( 'gimp xcf' )
  sVer = oReader.readArray( 4 )
  assert sVer in [ 'file', 'v001', 'v002' ]
  assert 0 == oReader.read( '!B' )
  oImg.size = oReader.read( '!II' )
  assert oImg.size[ 0 ] > 0 and oImg.size[ 1 ] > 0
  ABOUT_MODE = { 0 : 'RGB', 1 : 'L', 2 : 'P' }
  oImg.mode = ABOUT_MODE[ oReader.read( '!I' ) ]

  ##  Read properties.
  while True :
    oProp = oReader.readProp()
    ##  Last property will have type PROP_END and size 0.
    if PROP_END == oProp.type :
      break
    oImg.props.append( oProp )

  ##  Read layers.
  while True :
    nOffset = oReader.read( '!I' )
    if 0 == nOffset :
      break
    oImg.layers.append( oReader.readLayer( nOffset ) )

  return oImg

