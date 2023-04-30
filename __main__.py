import socket
import click
import logging
import time
import select

from .hexdump import *


timer				= time.time

log				= logging.getLogger( "UDP-echo" )

log_cfg				= {
    "level":	logging.WARNING,
    "datefmt":	'%m-%d %H:%M:%S',
    "format":	'%(asctime)s.%(msecs).03d %(threadName)10.10s %(name)-8.8s %(levelname)-8.8s %(funcName)-10.10s %(message)s',
}

log_levelmap                    = {
    -2: logging.FATAL,
    -1: logging.ERROR,
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}

def log_level( adjust ):
    """Return a logging level corresponding to the +'ve/-'ve adjustment"""
    return log_levelmap[
        max(
            min(
                adjust,
                max( log_levelmap.keys() )
            ),
            min( log_levelmap.keys() )
        )
    ]


@click.group()
@click.option('-v', '--verbose', count=True)
@click.option('-q', '--quiet', count=True)
@click.option('-l', '--log-file', help="Log file name")
def cli( verbose, quiet, log_file ):
    cli.verbosity               = verbose - quiet
    log_cfg['level']            = log_level( cli.verbosity )
    if log_file:
        log_cfg['filename']     = log_file
    logging.basicConfig( **log_cfg )
    if verbose or quiet:
        logging.getLogger().setLevel( log_cfg['level'] )
cli.verbosity           = 0


@click.command()
@click.option('--ip', default='0.0.0.0', help='IP address to bind to')
@click.option('--port', default=4500, help='Port number to bind to')
@click.option('--timeout', default=None)
@click.option('--cycle', default=1.0)
def reflect(ip, port, timeout, cycle):
    if timeout is not None:
        timeout			= float( timeout )

    # create a UDP socket
    sock			= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # bind the socket to a specific IP address and port
    log.warning( f"{ip}:{port}: reflecting UDP/IP traffic" )
    server_address		= (ip, port)
    sock.bind(server_address)

    cyc = cnt = siz		= 0
    beg 			= timer()

    while True:
        now			= timer()
        lst,cyc			= cyc,int(( now - beg ) / cycle)
        if cyc > lst:
            log.warning(
                f"{cnt:6}p; {cnt/(now-beg):9.2f}p/s; {siz:9}b; {siz/(now-beg):9.2f}b/s" )
        r,w,e			= select.select([sock], [], [], timeout)
        if not r:
            continue

        # receive incoming data
        data, address		= sock.recvfrom(4096)
        cnt		       += 1
        siz		       += len( data )
        log.info( f"{address!r}" )
        log.debug("{dump}".format( address=address, dump=hexdump( data )))

        # swap the source and destination IP and port
        src_ip, src_port	= address
        dst_ip, dst_port	= server_address
        new_address		= (src_ip, src_port)
        new_data		= data

        # send the modified data back out
        sock.sendto(new_data, new_address)


cli.add_command( reflect )


try:
    cli()
except Exception as exc:
    log.warning( "Failed: {exc}".format( exc=exc ))
    sys.exit( 1 )
else:
    sys.exit( 0 )
