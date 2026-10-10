




#!/usr/bin/env python3

import argparse
import os
import sys
import grpc
import random
import time
import threading

# --- New Imports for Modular SDN Architecture ---
# These imports link your main controller to the functional modules
from pot_calculator import calculate_path_secrets_set
from p4_client import P4RuntimeClient
from polka_helper import calculate_nport_and_pot_k, get_node_id

# --- P4Runtime Library Setup ---
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../../utils/'))
import p4runtime_lib.bmv2
import p4runtime_lib.helper
from p4runtime_lib.switch import ShutdownAllSwitchConnections

# --- Global Utilities ---
def log_to_console_and_file(switch_name, message):
    print(f"[{switch_name}] {message}")
    sys.stdout.flush() 

def printGrpcError(e):
    print("gRPC Error:", e.details(), end="")
    status_code = e.code()
    print("(%s)" % status_code.name, end="")
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))

#####################################################################
#                           CONSTANTS (Infrastructure & Policy)
#####################################################################

# Network configuration
HOST_1_IPV4 = "10.0.1.1"
HOST_2_IPV4 = "10.0.2.2"


# 1. Gateway MACs (Used for L2 forwarding/Encapsulation)
HOST_MAC_GW_1 = "08:00:00:00:01:00" 
HOST_MAC_GW_2 = "08:00:00:00:02:00" 

# 2. True Host MACs (Used for final delivery)
HOST_MAC_TRUE_1 = "08:00:00:00:01:11" 
HOST_MAC_TRUE_2 = "08:00:00:00:02:22"


# Switch and hosts ports
SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2
SWITCH_TO_SWITCH_PORT_REVERSE = 1

# PoT Policy Configuration (Used as input for pot_calculator)
MERSENNE_B = 5
X_VALUES_LIST = [1, 3, 5, 7] # Represents the four nodes in the path
X_VALUES_LIST_REVERSE = [1, 3, 5, 7]
RANDOM_VALUE = 50 # Fixed RND for this test, later will be random.randint(1, MERSENNE)




# PoT Protocol Flags
EGRESS_SR = 1
CUMULATIVE = 0
SECRET = 0
ROUTE_ID_PACKET = 10979360238159862843 


ROUTE_ID_REVERSE = 10482717147535548581
RND_REVERSE = 50                   
CML_REVERSE = 0                     
SECRET_REVERSE = 0





# Switch connection configuration
SWITCH_CONFIG = {
    'e1': {'name': 'e1', 'address': '127.0.0.1:50051', 'device_id': 0},
    's1': {'name': 's1', 'address': '127.0.0.1:50053', 'device_id': 2},
    's2': {'name': 's2', 'address': '127.0.0.1:50054', 'device_id': 3},
    's3': {'name': 's3', 'address': '127.0.0.1:50055', 'device_id': 4},
    's4': {'name': 's4', 'address': '127.0.0.1:50056', 'device_id': 5},
    'e2': {'name': 'e2', 'address': '127.0.0.1:50052', 'device_id': 1},
}
  
#####################################################################
#                            MAIN SECTION
#####################################################################

def main(p4info_edge, p4info_core, bmv2_file_path_edge, bmv2_file_path_core):

    # Set up P4Runtime clients and helpers
    p4info_helper_core = p4runtime_lib.helper.P4InfoHelper(p4info_core)
    p4info_helper_edge = p4runtime_lib.helper.P4InfoHelper(p4info_edge)
   
    try:
        # 1. Establish Switch Connections
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(name=SWITCH_CONFIG['s1']['name'], address=SWITCH_CONFIG['s1']['address'], device_id=SWITCH_CONFIG['s1']['device_id'], proto_dump_file='logs/s1-p4runtime-requests.txt')
        s2 = p4runtime_lib.bmv2.Bmv2SwitchConnection(name=SWITCH_CONFIG['s2']['name'], address=SWITCH_CONFIG['s2']['address'], device_id=SWITCH_CONFIG['s2']['device_id'], proto_dump_file='logs/s2-p4runtime-requests.txt')
        s3 = p4runtime_lib.bmv2.Bmv2SwitchConnection(name=SWITCH_CONFIG['s3']['name'], address=SWITCH_CONFIG['s3']['address'], device_id=SWITCH_CONFIG['s3']['device_id'], proto_dump_file='logs/s3-p4runtime-requests.txt')
        s4 = p4runtime_lib.bmv2.Bmv2SwitchConnection(name=SWITCH_CONFIG['s4']['name'], address=SWITCH_CONFIG['s4']['address'], device_id=SWITCH_CONFIG['s4']['device_id'], proto_dump_file='logs/s4-p4runtime-requests.txt')
        e1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(name=SWITCH_CONFIG['e1']['name'], address=SWITCH_CONFIG['e1']['address'], device_id=SWITCH_CONFIG['e1']['device_id'], proto_dump_file='logs/e1-p4runtime-requests.txt')
        e2 = p4runtime_lib.bmv2.Bmv2SwitchConnection(name=SWITCH_CONFIG['e2']['name'], address=SWITCH_CONFIG['e2']['address'], device_id=SWITCH_CONFIG['e2']['device_id'], proto_dump_file='logs/e2-p4runtime-requests.txt')

        # Send master arbitration update message
        for switch in [e1, e2, s1, s2, s3, s4]:
            switch.MasterArbitrationUpdate()
            time.sleep(0.1)





        # Install the P4 program on the switches
        for switch in [e1, e2]:
        #e1.SetForwardingPipelineConfig(p4info=p4info_helper_edge.p4info, bmv2_json_file_path=bmv2_file_path_edge)
        #e2.SetForwardingPipelineConfig(p4info=p4info_helper_edge.p4info, bmv2_json_file_path=bmv2_file_path_edge)
            switch.SetForwardingPipelineConfig(p4info=p4info_helper_edge.p4info, bmv2_json_file_path=bmv2_file_path_edge)
            switch.p4info = p4info_helper_edge.p4info
            print(f"Installed P4 Program on {switch.name}")
        print(f"Installed P4 Program on {switch.name}")
        for switch in [s1, s2, s3, s4]:
            switch.SetForwardingPipelineConfig(p4info=p4info_helper_core.p4info, bmv2_json_file_path=bmv2_file_path_core)
            switch.p4info = p4info_helper_core.p4info
            print(f"Installed P4 Program on {switch.name}")
        print("\n" + "="*70 + "\n")

        # 2. Instantiate P4Runtime Clients (New SDN Structure)
        e1_client = P4RuntimeClient(p4info_helper_edge, e1)
        e2_client = P4RuntimeClient(p4info_helper_edge, e2)
        s1_client = P4RuntimeClient(p4info_helper_core, s1)
        s2_client = P4RuntimeClient(p4info_helper_core, s2)
        s3_client = P4RuntimeClient(p4info_helper_core, s3)
        s4_client = P4RuntimeClient(p4info_helper_core, s4)

        CORE_SWITCH_CLIENTS = {
            's1': s1_client, 's2': s2_client, 's3': s3_client, 's4': s4_client
        }

        
        # The main SDN logic asks the calculator for the complete set of parameters
        path_secrets = calculate_path_secrets_set(x_values=X_VALUES_LIST, mersenne_b=MERSENNE_B, random_value=RANDOM_VALUE 
        )
        
        RND_VALUE = path_secrets['random_value']
        SECRETS = path_secrets['core_node_secrets']
        MERSENNE = path_secrets['mersenne']
        MERSENNE_B_EXP = path_secrets['mersenne_b']

        print(f"Final CML (Verification Check): {path_secrets['expected_final_cml']}")
        print(f"Random Number (RND): {RND_VALUE}")
        print("\n" + "="*70 + "\n")







        print("Configuring E1 (Ingress Edge)")

        # 1. Forwarding to H1 (FINAL HOP - E1 acts as Egress for Reply Path)
        # Fix 1: Use the TRUE MAC of H1 for final delivery.
        e1_client.add_ipv4_forward_rule(
            HOST_1_IPV4, 
            HOST_MAC_TRUE_1, # <--- Use the TRUE MAC for H1 (e.g., "08:00:00:00:01:11")
            SWITCH_TO_HOST_PORT 
        )

        # 2. Forwarding to H2 (Core-bound for decapsulated traffic)
        # Use the Gateway MAC of E2 (which is E1's next hop for that traffic).
        e1_client.add_ipv4_forward_rule(
            HOST_2_IPV4, 
            HOST_MAC_GW_2, # <--- Use the Gateway MAC for E2 (e.g., "08:00:00:00:02:00")
            SWITCH_TO_SWITCH_PORT
        )

        # 3. PoT-PolKA Encapsulation Rule (Forward Path: H1 -> H2)
        # Uses the FORWARD path parameters (your existing constants).
        e1_client.Edge_Table_forward( 
            dst_ip_addr=HOST_2_IPV4, 
            dst_mac_addr=HOST_MAC_GW_2, 
            egress_port=SWITCH_TO_SWITCH_PORT,
            rnd=RND_VALUE,             # RND for H1 -> H2
            cml=CUMULATIVE,            # CML for H1 -> H2
            routeId=ROUTE_ID_PACKET,   # RouteID for H1 -> H2
            secret=SECRET
        )

        # 4. PoT Verification Rule (Reply Path: H2 -> H1)
        # Fix 2: Use the new, calculated REVERSE path cryptographic parameters.
        print("Configuring E1 for Reply Path Verification (E1 acts as Egress)")
        e1_client.Edge_Verification(
            routeId=ROUTE_ID_REVERSE, 
            apply_sr_egress=EGRESS_SR, 
            mersenne_edge=MERSENNE,
            mersenne_b_edge=MERSENNE_B_EXP
        )








        print("\n" + "="*70 + "\n")
        print("Configuring E2 (Egress Edge)")

        # 1. Forwarding to H2 (FINAL HOP - E2 acts as Egress for Forward Path)
        # Fix 1: Use the TRUE MAC of H2 for final delivery.
        e2_client.add_ipv4_forward_rule(
            HOST_2_IPV4, 
            HOST_MAC_TRUE_2, # <--- CRITICAL FIX: Use TRUE MAC for final delivery (H2)
            SWITCH_TO_HOST_PORT
        )

        # 2. Forwarding to H1 (Core-bound for decapsulated traffic)
        # Uses the Gateway MAC of E1 (which is E2's next hop for that traffic).
        e2_client.add_ipv4_forward_rule(
            HOST_1_IPV4, 
            HOST_MAC_GW_1, # <--- Use the Gateway MAC for E1 (E2's next hop)
            SWITCH_TO_SWITCH_PORT
        )

        # 3. PoT-PolKA Encapsulation Rule (Reverse Path: H2 -> H1)
        # Fix 2: Use the newly defined REVERSE PATH cryptographic constants.
        print("Configuring E2 for Reverse Path Encapsulation (H2 -> H1)")
        e2_client.Edge_Table_forward( 
            dst_ip_addr=HOST_1_IPV4,            # Target destination is H1
            dst_mac_addr=HOST_MAC_GW_1,       # Target MAC is E1's Gateway MAC (next hop)
            egress_port=SWITCH_TO_SWITCH_PORT,
            rnd=RND_REVERSE,                  # <--- MUST BE RND_REVERSE (e.g., 50)
            cml=CML_REVERSE,                  # <--- MUST BE CML_REVERSE (0)
            routeId=ROUTE_ID_REVERSE,         # <--- MUST BE ROUTE_ID_REVERSE (1097...)
            secret=SECRET_REVERSE             # <--- MUST BE SECRET_REVERSE (0)
        )
                
        # 4. PoT Verification Rule (Forward Path: H1 -> H2)
        # E2 verifies the initial H1->H2 packet. Must use the FORWARD path parameters.
        e2_client.Edge_Verification( 
            routeId=ROUTE_ID_PACKET,   
            apply_sr_egress=EGRESS_SR, 
            mersenne_edge=MERSENNE,
            mersenne_b_edge=MERSENNE_B_EXP
        )








        # 5. Installation: Core Switches (s1, s2, s3, s4) with PolKA Consistency Check
        print("\n" + "="*70 + "\n")
        print("\nConfiguring Core Switches with Dynamic POT_K Check")
        for i, switch_name in enumerate(['s1', 's2', 's3', 's4']):
            client = CORE_SWITCH_CLIENTS[switch_name]
            secret_data = SECRETS[i] # PoT shares for this node
            
            # --- PoLKA Helper Logic (CRITICAL for consistency) ---
            node_id = get_node_id(switch_name)
            
            # Predict the PolKA routing result using the helper function
            nport_predicted, pot_k_calculated = calculate_nport_and_pot_k(ROUTE_ID_PACKET, node_id)
            
            if pot_k_calculated == 0:
                print(f"[ERROR] Could not calculate POT_K for {switch_name}. Skipping configuration.")
                continue

            # 1. Install Node ID and Forwarding
            client.configure_node_id(node_id=node_id, routeId=ROUTE_ID_PACKET)
            client.add_port_mapping(calculated_port=nport_predicted, physical_port=SWITCH_TO_SWITCH_PORT)
            
            # 2. Install PoT Secrets using the PREDICTED POT_K as the match key
            # This ensures the PoT policy is only active if the PolKA path-finding succeeds.
            client.Core_Table_Forward(
                x_forward=secret_data['x'], 
                y_forward=secret_data['y'],
                lpc_forward=secret_data['lpc'],
                mersenne_core=MERSENNE, 
                mersenne_b_core=MERSENNE_B_EXP,
                Poly2_forward=secret_data['poly2'],
                pot_k_forward=pot_k_calculated 
            )






        # --- Reverse Path Calculation (H2 -> H1) ---
        print("\n[PoT] Calculating PoT Shares for REVERSE Path (H2 -> H1)...")

        # CRITICAL CALL: Use the reverse path inputs
        reverse_path_secrets = calculate_path_secrets_set(x_values=X_VALUES_LIST_REVERSE, mersenne_b=MERSENNE_B, random_value=RND_REVERSE        
        )

        # --- Define Global Constants for Reverse Path Configuration ---

        RND_REVERSE_VALUE = reverse_path_secrets['random_value']
        CML_REVERSE_EXPECTED = reverse_path_secrets['expected_final_cml']
        REVERSE_SECRETS_DATA = reverse_path_secrets['core_node_secrets']

        print(f"Reverse Path Expected CML: {CML_REVERSE_EXPECTED}")
        print(f"Reverse Path RND: {RND_REVERSE_VALUE}")

        # --- Map Calculated Secrets to Named Variables for the Configuration Loop ---
        # The calculated list is naturally in the correct processing order: [S4, S3, S2, S1]

        # S4 shares (first element in the calculated list)
        SECRETS_REVERSE_S4 = REVERSE_SECRETS_DATA[0] 
        # S3 shares
        SECRETS_REVERSE_S3 = REVERSE_SECRETS_DATA[1]
        # S2 shares
        SECRETS_REVERSE_S2 = REVERSE_SECRETS_DATA[2]
        # S1 shares (last element in the calculated list)
        SECRETS_REVERSE_S1 = REVERSE_SECRETS_DATA[3]

        # Define the final list for the configuration loop (S4, S3, S2, S1 order)
        REVERSE_SECRETS_LIST = [
            SECRETS_REVERSE_S4, 
            SECRETS_REVERSE_S3,
            SECRETS_REVERSE_S2, 
            SECRETS_REVERSE_S1
        ]
        print("\n" + "="*70 + "\n")




        print("\n" + "="*70 + "\n")
        print("\nConfiguring Core Switches for REVERSE Path (H2 -> H1)")

        # 1. Define the switches in the REVERSE ORDER: S4 -> S3 -> S2 -> S1
        reverse_switch_names = ['s4', 's3', 's2', 's1']

        # NOTE: Assumes CORE_SWITCH_CLIENTS, ROUTE_ID_REVERSE, MERSENNE_PRIME, 
        # MERSENNE_B_EXP, and SWITCH_TO_SWITCH_PORT_REVERSE are defined.

        for i, switch_name in enumerate(reverse_switch_names):
            client = CORE_SWITCH_CLIENTS[switch_name]
            secret_data = REVERSE_SECRETS_LIST[i] # Shares for S4, S3, S2, S1 in order
            
            # --- PolKA Helper Logic ---
            node_id = get_node_id(switch_name) 
            
            # Predict nport/pot_k using the REVERSE Route ID
            nport_predicted, pot_k_calculated = calculate_nport_and_pot_k(ROUTE_ID_REVERSE, node_id)
            
            if pot_k_calculated == 0:
                print(f"[ERROR] Could not calculate POT_K for {switch_name} on REVERSE path. Skipping.")
                continue

            # 1. Configure Node ID and Port Mapping (FIXES ROUTING AND nport MISSES)
            client.configure_node_id(node_id=node_id, routeId=ROUTE_ID_REVERSE) # Use the reverse Route ID
            client.add_port_mapping(calculated_port=nport_predicted, physical_port=SWITCH_TO_SWITCH_PORT_REVERSE)
            
            # 2. Install PoT Secrets using Core_Table_Forward (FIXES POT_PARAM MISSES)
            client.Core_Table_Forward(
                x_forward=secret_data['x'], 
                y_forward=secret_data['y'],
                lpc_forward=secret_data['lpc'],
                mersenne_core=MERSENNE, 
                mersenne_b_core=MERSENNE_B_EXP,
                Poly2_forward=secret_data['poly2'],
                pot_k_forward=pot_k_calculated # Use the dynamically calculated key
            )

        print("Reverse path core configuration complete.")












        # 6. Read tables (Using the New Client Objects)
        print("\n" + "="*70 + "\n")
        print("\nReading table entries for verification:")
        for switch in [e1_client, s1_client, s2_client, s3_client, s4_client, e2_client]:
            switch.readTableRules()
        print("Finished reading all table entries.")



        
        print("\nSetup complete. The network is now ready.")
        print("You can use mininet")
        print("\nPress Ctrl+C to exit.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Exiting...")
        print(" Shutting down.")
    except grpc.RpcError as e:
        print(f"Error setting forwarding pipeline config: {str(e)}")
        printGrpcError(e)
    
    finally:
        # Shutdown switch connections at the end
        ShutdownAllSwitchConnections()
        print("All switch connections shut down successfully.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--edge-p4info', help='p4info proto in text format for edge switch',
                        type=str, action="store", required=False,
                        default='./build/pot-polka-edge.p4info.txt')
    parser.add_argument('--core-p4info', help='p4info proto in text format for core switch',
                        type=str, action="store", required=False,
                        default='./build/pot-polka-core.p4info.txt')
    parser.add_argument('--bmv2-edge-json', help='Edge switch JSON file',
                        type=str, action="store", required=False,
                        default='./build/pot-polka-edge.json')
    parser.add_argument('--bmv2-core-json', help='Core switch JSON file',
                        type=str, action="store", required=False,
                        default='./build/pot-polka-core.json')
    args = parser.parse_args()

    # Check if files exist (as in your original structure)
    if not os.path.exists(args.edge_p4info) or not os.path.exists(args.core_p4info) or \
       not os.path.exists(args.bmv2_edge_json) or not os.path.exists(args.bmv2_core_json):
        parser.print_help()
        print("\nRequired P4 info/JSON files not found. Have you run 'make' in your build directory?")
        parser.exit(1)

    # Call the main function
    main(args.edge_p4info, args.core_p4info, args.bmv2_edge_json, args.bmv2_core_json)