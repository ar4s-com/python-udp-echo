import re

try:
    xrange(0,1)
except NameError:
    xrange 			= range


def hexdumper( src, offset=0, length=16, sep='.', quote='|' ):
    '''
    @brief Return {src} in hex dump.
    @param[in] length   {Int} Nb Bytes by row.
    @param[in] sep      {Char} For the text part, {sep} will be used for non ASCII char.
    @return 		{Str} The hexdump

    @note Full support for python2 and python3 !
    '''
    for i in xrange(0, len(src), length):
        subSrc = src[i:i+length];
        hexa = '';
        for h in xrange(0,len(subSrc)):
            if h == length/2:
                hexa += ' ';
            h = subSrc[h];
            if not isinstance(h, int):
                h = ord(h);
            h = hex(h).replace('0x','');
            if len(h) == 1:
                h = '0'+h;
            hexa += h+' ';
        hexa = hexa.strip(' ');
        text = '';
        for c in subSrc:
            if not isinstance(c, int):
                c = ord(c);
            if 0x20 <= c < 0x7F:
                text += chr(c);
            else:
                text += sep;
        yield "{addr:08X}:  {hexa:<{hexawidth}s}  {quote}{text}{quote}".format(
            addr=i+offset, hexa=hexa, hexawidth=length*(2+1)+1, text=text, quote=quote or '' )


def hexdump( src, offset=0, length=16, sep='.', quote='|' ):
    return '\n'.join( hexdumper( src, offset=offset, length=length, sep=sep, quote=quote ))


def hexdump_differs( *dumps, **kwds ): # Python3 version: ', inclusive=False ):'
    """Compare a number of hexdump outputs side by side, returning differing lines."""
    inclusive			= kwds.get( 'inclusive', False ) # for Python2 compatibility
    lines			= [ d.split( '\n' ) for d in dumps ]
    differs			= []
    for cols in zip( *lines ):
        same			= all( c == cols[0] for c in cols[1:] )
        if not same or inclusive:
            differs.append(( ' == ' if same else ' != ' ).join( cols ))
    return '\n'.join( differs )


def hexdecode( enc, offset=0, sep=':' ):
    """Decode hex octets "ab:cd:ef:01..." (starting at off bytes in) into b"\xab\xcd\xef\x01..." """
    return bytes(bytearray.fromhex( ''.join( enc.split( sep ))))[offset:]


def hexloader( dump, offset=0, fill=False, skip=False ):
    """Load data from a iterable hex dump, eg, either as a sequence of rows or a string:

        00003FD0:  3F D0 00 00 00 00 00 00  00 00 00 00 12 00 00 00   |................|

        00003FF0:  3F F0 00 00 00 00 00 00  00 00 00 00 12 00 00 00   |................|
        00004000:  40 00 30 31 20 53 45 34  20 45 20 32 33 2e 35 63   |@.01 SE4 E 23.5c|

    Yields a corresponding sequence of address,bytes.  To ignore the address
    and get the data:

        b''.join( data for addr,data in hexload( ... )

    If fill may be False/b'', or a single-byte value used to in-fill any missing
    address ranges.

    If skip is Truthy, we allow and skip empty/non-matching lines.
    If gaps is Truthy, allow gaps in addresses.
    """
    if fill:
        assert isinstance( fill, bytes ) and len( fill ) == 1, \
            "fill must be a bytes singleton, not {fill!r}".format( fill=fill )
    if isinstance( dump, basestring if sys.version_info[0] < 3 else str ): # noqa: F821
        dump			= dump.split( '\n' )
    for row in dump:
        if not row.strip():
            continue # all whitespace; ignore
        match			= hexloader.parser.match( row )
        if not match:
            assert skip, \
                "Failed to match a hex dump on row: {row!r}".format( row=row )
            continue
        addr			= int( match.group( 'address' ), 16 )
        data			= hexdecode( match.group( 'values' ), sep=' ' )

        if addr > offset:
            # row address is beyond current offset; fill, or skip offset ahead
            if fill:
                yield offset,(fill * ( addr - offset ))
            offset		= addr
        if addr < offset:
            # Row starts before desired offset; skip or clip
            if addr + len( data ) <= offset:
                continue
            data		= data[offset-addr:]
            addr		= offset
        yield addr,data
        offset			= addr + len( data )

hexloader.parser		= re.compile(
    r"""^
            \s*
        (?P<address>
          {hexclass}{{1,16}}			# address
        )
	    [:]\s*				#     : whitespace
        (?P<values>
          (?:\s{{0,2}}{hexclass}{{2}})+		# hex pairs separated by 0-2 whitespace
        )
	(?:
            \s+					#     whitespace at end
          (?P<quote>\|?)			#   | (optional ..print.. quote)
          (?P<print>
            .*					# |..print..|
          )
          (?P=quote)				#   | (optional ..print.. quote)
        )?					# entire ..print.. section optional
        $""".format( hexclass='[0-9A-Fa-f]' ), re.VERBOSE )


def hexload( dump, offset=0, fill=False, skip=False ):
    """Return bytes data specified from dump"""
    return b''.join( d for a,d in hexloader( dump, offset=offset, fill=fill, skip=skip ))


