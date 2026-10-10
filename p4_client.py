





import sys
import os
import grpc

# Assuming p4runtime_lib is correctly configured in your environment
# We import the necessary modules for P4Runtime interaction.
# These imports are self-contained within the P4Runtime utility structure.
# Note: The path below assumes your script is run from a location that can resolve 
# the 'p4runtime_lib' package, often found in a 'utils' directory.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../../utils/'))
import p4runtime_lib.helper
from p4runtime_lib.error_utils import printGrpcError






class P4RuntimeClient:
    """
    Handles all low-level communication with the P4 data plane switches 
    via the P4Runtime gRPC protocol.

    Methods build and install P4 table entries based on parameters 
    provided by the main SDN controller logic.
    """
    
    def __init__(self, p4info_helper, switch):
        """
        Initializes the P4RuntimeClient with a specific switch connection 
        and its corresponding P4Info helper.
        
        Args:
            p4info_helper (p4runtime_lib.helper.P4InfoHelper): Helper object for 
                the switch's P4 program configuration.
            switch (p4runtime_lib.switch.Bmv2SwitchConnection): The active 
                gRPC connection object to the switch.
        """
        self.p4info_helper = p4info_helper
        self.switch = switch
        self.name = switch.name
        print(f"[P4Client] Initialized client for switch: {self.name}")

  




    def _format_value(self, value):
        """Formats bytes values for display purposes (MAC, IP, etc.)."""
        if isinstance(value, bytes):
            # Handle MAC addresses (6 bytes)
            if len(value) == 6:
                return ':'.join(f'{b:02x}' for b in value)
            # Handle IPv4 addresses (4 bytes)
            elif len(value) == 4:
                return '.'.join(str(b) for b in value)
            # Convert other values to integers
            else:
                return str(int.from_bytes(value, 'big'))
        return str(value)




  

    def add_ipv4_forward_rule(self, dst_ip_addr, dst_mac_addr, egress_port):
        """Installs a standard IPv4 forwarding rule (LPM match)."""
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.ipv4_lpm",
            match_fields={
                "hdr.ipv4.dstAddr": (dst_ip_addr, 32)
            },
            action_name="MyIngress.ipv4_forward",
            action_params={
                "dstAddr": dst_mac_addr,
                "port": egress_port
            }
        )
        self.switch.WriteTableEntry(table_entry)
        print(f"[{self.name}] Installed IPv4 forwarding rule.")
        print("\n" + "="*70 + "\n")






    def Edge_Table_forward(self, dst_ip_addr, rnd, cml, dst_mac_addr, routeId, egress_port, secret):
        """Installs the Source Routing Encapsulation Rule at the Ingress Edge."""
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.process_tunnel_encap.tunnel_encap_process_sr",  
            match_fields={
                "hdr.ipv4.dstAddr": (dst_ip_addr, 32)
            },
            action_name="MyIngress.process_tunnel_encap.add_sourcerouting_header",
            action_params={
                "port": egress_port,
                "dmac": dst_mac_addr,
                "routeIdPacket": routeId,
                "rnd": rnd,
                "cml": cml,
                "secret": secret
            }
        )
        self.switch.WriteTableEntry(table_entry)
        print(f"[{self.name}] Installed Ingress SR/PoT Encapsulation rule.")
        print("\n" + "="*70 + "\n")







    def Edge_Verification(self, routeId, apply_sr_egress, mersenne_edge, mersenne_b_edge):
        """Installs the PoT Verification Rule at the Egress Edge."""
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.egress_verify",  
            match_fields={
                "hdr.potPolka.routeId": routeId
            },
            action_name="MyIngress.verify_pot", 
            action_params={
                "sr": apply_sr_egress,
                "mersenne": mersenne_edge,
                "mersenne_b": mersenne_b_edge
            }
        )
        self.switch.WriteTableEntry(table_entry)
        print(f"[{self.name}] Installed Egress PoT Verification rule.")
        print("\n" + "="*70 + "\n")






    def Core_Table_Forward(self, x_forward, y_forward, lpc_forward, Poly2_forward, mersenne_core, mersenne_b_core, pot_k_forward):
        """Installs the PoT parameters (SSSS shares) on a Core switch."""
        if pot_k_forward is None:
            print(f"[{self.name}] Error: pot_k_forward is None. Skipping installation.")
            return
        
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.pot_param",  
            match_fields={
                "meta.pot_k": pot_k_forward
            },
            action_name="MyIngress.initialize_param", 
            action_params={
                "x": x_forward,
                "y": y_forward,
                "lpc": lpc_forward,
                "mersenne": mersenne_core,
                "mersenne_b": mersenne_b_core,
                "poly2": Poly2_forward
            }
        )
        self.switch.WriteTableEntry(table_entry)
        print(f"[{self.name}] Installed PoT parameters using pot_k={pot_k_forward}.")
        print("\n" + "="*70 + "\n")






    def configure_node_id(self, node_id, routeId):
        """Installs the NodeID for the PolKA routing check."""
        table_entry_forward = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.node_config",
            match_fields={
                "hdr.potPolka.routeId": routeId
            },
            action_name="MyIngress.set_nodeid",
            action_params={
                "nodeid": node_id,
            }
        )
        self.switch.WriteTableEntry(table_entry_forward)
        print(f"[{self.name}] Configured Node ID {node_id}.")
        print("\n" + "="*70 + "\n")






    def add_port_mapping(self, calculated_port, physical_port):
        """Maps the PolKA calculated port ID to the physical switch port."""
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.port_map",
            match_fields={
                "meta.port": calculated_port
            },
            action_name="MyIngress.set_physical_port",
            action_params={
                "physical_port": physical_port
            }
        )
        self.switch.WriteTableEntry(table_entry)
        print(f"[{self.name}] Mapped PolKA Port {calculated_port} to Physical Port {physical_port}.")
        print("\n" + "="*70 + "\n")
    





    def readTableRules(self):
        """Reads all table entries installed on the switch for debugging/verification."""
        # ... (Implementation is the same as the original readTableRules logic) ...
        folder_name = 'table_entries'
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        filename = os.path.join(folder_name, f"{self.name}_table_rules.txt")

        with open(filename, 'w') as f:
            print(f'\n----- Reading tables rules for {self.name} -----')
            try:
                for response in self.switch.ReadTableEntries():
                    for entity in response.entities:
                        entry = entity.table_entry
                        table_name = self.p4info_helper.get_tables_name(entry.table_id)
                        
                        output = f'{table_name}: '
                        
                        for m in entry.match:
                            match_field_name = self.p4info_helper.get_match_field_name(table_name, m.field_id)
                            match_field_value = self._format_value(self.p4info_helper.get_match_field_value(m))
                            output += f'{match_field_name}={match_field_value} '

                        action = entry.action.action
                        action_name = self.p4info_helper.get_actions_name(action.action_id)
                        output += f'-> {action_name} '
                        
                        for p in action.params:
                            param_name = self.p4info_helper.get_action_param_name(action_name, p.param_id)
                            param_value = self._format_value(p.value)
                            output += f'{param_name}={param_value} '
                        
                        print(output)
                        f.write(output + '\n')
                
            except grpc.RpcError as e:
                print(f"gRPC Error reading rules from {self.name}: {e.details()}")
            print(f'----- Finished reading tables for {self.name} -----\n')
            print("\n" + "="*70 + "\n")