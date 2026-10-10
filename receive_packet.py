



#!/usr/bin/env python3

from scapy.all import *
import time
import socket
import sys
import threading

# --- Configuration ---
HOST_IP_MAP = {
    "10.0.1.1": ("h1", 5001),
    "10.0.2.2": ("h2", 5002)
}

# CRITICAL MAC FIX (Same as before)
# E1 Gateway for H1 / E2 Gateway for H2
GATEWAY_MACS = {
    "h1": "08:00:00:00:01:00", # E1 MAC
    "h2": "08:00:00:00:02:00"  # E2 MAC
}

GLOBAL_CONFIG = {}

# --- Utility Functions ---

def get_local_ip(iface='eth0'):
    try:
        return get_if_addr(iface)
    except Exception:
        return None

def setup_config():
    IFACE_NAME = 'eth0'
    local_ip = get_local_ip(IFACE_NAME)

    if local_ip in HOST_IP_MAP:
        #hostname = HOST_IP_MAP[local_ip]
        hostname, identity_port = HOST_IP_MAP[local_ip]
        config = {
            'HOSTNAME': hostname,
            'LISTEN_IP': local_ip,
            'IFACE': IFACE_NAME,
            'PORT': identity_port,
            'GATEWAY_MAC': GATEWAY_MACS.get(hostname, None)
        }
        GLOBAL_CONFIG.update(config)
        return config
    else:
        print(f"ERROR: IP {local_ip} not recognized.", file=sys.stderr)
        sys.exit(1)





def packet_callback(packet):
    if IP in packet and UDP in packet and Raw in packet:


        if packet[UDP].dport != GLOBAL_CONFIG['PORT']:
            return

        try:
            # Decode the message
            payload = packet[Raw].load.decode('utf-8', errors='ignore')
            
            # --- ADD THE CHECK HERE ---
            if "ACK" in payload:
                # This is a reply coming back. STOP HERE.
                #print(f"[*] Received ACK: {payload}. Doing nothing.")
                return 
            # ---------------------------

        except Exception as e:
            return

        # 2. READ the ports and IPs from the incoming packet AS THEY ARE
        received_sport = packet[UDP].sport 
        received_dport = packet[UDP].dport
        incoming_src_ip = packet[IP].src
        incoming_dst_ip = packet[IP].dst

        # 3. DEFINE the reply message
        reply_msg = f"ACK_FROM_{GLOBAL_CONFIG['HOSTNAME'].upper()}"


        # 4. DYNAMICALLY SWAP for the reply
        # Source port of reply = destination port of request
        # Destination port of reply = source port of request
        reply_packet = Ether(dst=GLOBAL_CONFIG['GATEWAY_MAC']) / \
               IP(src=incoming_dst_ip, dst=incoming_src_ip) / \
               UDP(sport=received_dport, dport=received_sport) / \
               Raw(load=reply_msg.encode('utf-8'))



        # Add padding if the reply packet is too small for Ethernet standards
        if len(reply_packet) < 64:
            reply_packet = reply_packet / Raw(load='\x00' * (64 - len(reply_packet)))

        # 5. SEND and LOG
        sendp(reply_packet, iface=GLOBAL_CONFIG['IFACE'], verbose=0)
        print(f"SUCCESS: Request[{received_sport}->{received_dport}] -> Reply[{received_dport}->{received_sport}]")



# --- Main Execution ---

def main():
    if os.geteuid() != 0:
        print("Run with sudo.")
        sys.exit(1)

    config = setup_config()
    
    # *** SIMPLIFIED FILTER ***
    # We only care that it is UDP and destined for THIS IP.
    # We do NOT care what port it is on.
    filter_string = f"udp and dst host {config['LISTEN_IP']}"
    
    print("=" * 60)
    print(f"Host {config['HOSTNAME'].upper()} ({config['LISTEN_IP']}) Listening...")
    print(f"Filter: {filter_string}")
    print("=" * 60)

    try:
        sniff(iface=config['IFACE'], filter=filter_string, prn=packet_callback, store=0)
    except KeyboardInterrupt:
        print("\nStopping.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()