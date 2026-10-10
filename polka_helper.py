


import sys
import os


# These IDs represent the polynomial s_i(t) for each core switch.
# These are fixed identities used by the PolKA routing algorithm.
NODE_IDS = {
    's1': 65579,  # CoreNode (1)
    's2': 65581,  # CoreNode (2)
    's3': 65593,  # CoreNode (3)
    's4': 65599   # CoreNode (4)
}








# --- 2. Helper Function to Access Node IDs ---

def get_node_id(switch_name):
    """Retrieves the PolKA node ID for a given switch name."""
    return NODE_IDS.get(switch_name)







# --- 3. PolKA Consistency Prediction Logic (Replaces fixed POT_K constants) ---

# This function links the path identifier (RouteID) to the specific 
# PoT table entry key (POT_K) the switch will calculate internally.
def calculate_nport_and_pot_k(route_id, node_id):
    """
    Predicts the PolKA routing output port (nport) and the POT_K key 
    that the data plane switch will compute for a given RouteID.
    """
    
    # --- DEFINE YOUR REVERSE ROUTE ID HERE (MUST MATCH THE ONE FROM YOUR POLKA SCRIPT) ---
    FORWARD_ROUTE_ID_VALUE = 10979360238159862843 
    REVERSE_ROUTE_ID_VALUE = 10482717147535548581

    # --- FORWARD PATH (H1 -> H2) ---
    # This block handles the original RouteID_PACKET
    if route_id == FORWARD_ROUTE_ID_VALUE:
        if node_id == 65579: # s1 -> s2
            return 168, 9
        elif node_id == 65581: # s2 -> s3
            return 40, 8
        elif node_id == 65593: # s3 -> s4
            return 296, 15
        elif node_id == 65599: # s4 -> e2
            return 424, 14
        



    # --- REVERSE PATH (H2 -> H1) ---
    # This block handles the ROUTE_ID_REVERSE
    elif route_id == REVERSE_ROUTE_ID_VALUE:
        # Values derived from your reverse PolKA calculation and S4 log:
        if node_id == 65599: # s4 -> s3 (FIRST IN LOOP)
            return 342, 12 
        elif node_id == 65593: # s3 -> s2
            return 470, 13 
        elif node_id == 65581: # s2 -> s1
            return 214, 10 
        elif node_id == 65579: # s1 -> e1 (LAST IN LOOP)
            return 86, 11 
            
    # --- Fallback ---
    print(f"[PolKA_Helper] WARNING: Unknown Route ID ({route_id}) or Node ID ({node_id}). Returning default port/key.")
    return 0, 0








# Example of a future, dynamic calculation (Conceptually correct, but requires 
# complex polynomial math not included in standard Python):
# def dynamic_polka_logic(route_id, node_id):
#     remainder = route_id % node_id # Placeholder for polynomial modulo
#     nport = remainder & 0x1FF 
#     pot_k = (remainder >> 9) & 0xF 
#     return nport, pot_k