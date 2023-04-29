import socket
import click
import logging
import time
import select

from .hexdump import *


timer				= time.time

log				= logging.getLogger( __package__ )

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
        if cyc > lst or True:
            log.warning( f"{cnt:6}p; {cnt/(now-beg):9.2f}p/s; {siz:9}b; {siz/(now-beg):9.2f}b/s" )
        r,w,e			= select.select([sock], [], [], timeout)
        if not r:
            continue

        # receive incoming data
        data, address		= sock.recvfrom(4096)
        cnt		       += 1
        siz		       += len( data )
        log.warning( "{address!r}: {dump}".format( address=address, dump=hexdump( data )))

        # swap the source and destination IP and port
        src_ip, src_port	= address
        dst_ip, dst_port	= server_address
        new_address		= (src_ip, src_port)
        new_data		= data

        # send the modified data back out
        sock.sendto(new_data, new_address)

reflect()
