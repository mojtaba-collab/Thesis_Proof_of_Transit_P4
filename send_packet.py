




#!/usr/bin/env python3

from scapy.all import *
import time
import socket
import sys
import argparse # Addition 3: Argument parsing

# --- Configuration (Verified with your Topology) ---
HOST_CONFIG = {
    "10.0.1.1": {
        'HOSTNAME': "h1",
        'DST_IP': "10.0.2.2",
        'DST_MAC': "08:00:00:00:01:00", 
        'IFACE': 'eth0',
        'SRC_PORT': 5001,
        'DST_PORT': 5002
    },
    "10.0.2.2": {
        'HOSTNAME': "h2",
        'DST_IP': "10.0.1.1",
        'DST_MAC': "08:00:00:00:02:00", 
        'IFACE': 'eth0',
        'SRC_PORT': 5002,
        'DST_PORT': 5001
    }
}

def get_local_ip(iface):
    try:
        return get_if_addr(iface)
    except Exception:
        return None

def setup_and_send():
    # Addition 3: Allow port overrides via command line
    parser = argparse.ArgumentParser(description='PoT-PolKA Traffic Generator')
    parser.add_argument('--sport', type=int, help='Override Source Port')
    parser.add_argument('--dport', type=int, help='Override Dest Port')
    parser.add_argument('--interval', type=float, default=1.0, help='Seconds between packets')
    args = parser.parse_args()

    IFACE_NAME = 'eth0' 
    local_ip = get_local_ip(IFACE_NAME)
    
    if local_ip not in HOST_CONFIG:
        print(f"ERROR: Host IP {local_ip} not in config.", file=sys.stderr)
        sys.exit(1)

    config = HOST_CONFIG[local_ip]
    
    # Use overrides if provided, otherwise use defaults
    src_port = args.sport if args.sport else config['SRC_PORT']
    dst_port = args.dport if args.dport else config['DST_PORT']
    
    seq_num = 1 
    print("=" * 70)
    print(f"PoT-PolKA SENDER: {config['HOSTNAME'].upper()}")
    print(f"Flow: {local_ip}:{src_port} -> {config['DST_IP']}:{dst_port}")
    print("=" * 70)
    
    

    while True:
        try:
            # Addition 1 & 2: Constructing the packet
            # We use the standard IPv4 EtherType (0x0800) unless your P4 requires 0x1234 here
            payload = f"FROM_{config['HOSTNAME'].upper()}_SEQ_{seq_num}_TIME_{time.time()}"
            
            udp_packet = Ether(dst=config['DST_MAC']) / \
                         IP(src=local_ip, dst=config['DST_IP']) / \
                         UDP(sport=src_port, dport=dst_port) / \
                         Raw(load=payload)

            # Addition 1: Padding to 64 bytes to prevent BMv2 dropping short frames
            if len(udp_packet) < 64:
                udp_packet = udp_packet / Raw(load='\x00' * (64 - len(udp_packet)))

            sendp(udp_packet, iface=IFACE_NAME, verbose=False)  
            
            sys.stdout.write(f'[{time.strftime("%H:%M:%S")}] Sent Seq={seq_num} | Size={len(udp_packet)} bytes\r')
            sys.stdout.flush()
            
            seq_num += 1
            time.sleep(args.interval) 
            
        except KeyboardInterrupt:
            print("\nStopped.")
            break

if __name__ == '__main__':
    setup_and_send()


