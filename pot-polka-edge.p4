/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_SRCROUTING = 0x1234;
const bit<8> PROTO_UDP = 17;
const bit<16> TYPE_IPV6 = 0x86dd;

//Ethernet frame payload padding and P4
//https://github.com/p4lang/p4-spec/issues/587

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<16> mersenne_t;
typedef bit<4> mersenne_b_t;


header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header potPolka_t {
    bit<160>   routeId;
    bit<16>    rnd;
    bit<16>    cml;
    bit<16>    secret;
    //bit<32>    saved_ip; 
    bit<32>    saved_dst_ip;
    bit<32>    saved_src_ip;   // Original Source IP
    bit<16>    saved_src_port; // Original Source Port
    bit<16>    saved_dst_port; // Original Destination Port
    //bit<16>    saved_totalLen; // To save original IPv4 totalLen
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}



header ipv6_t {
    bit<4>   version;
    bit<8>   traffic_class;
    bit<20>  flow_label;
    bit<16>  payload_len;
    bit<8>   next_hdr;
    bit<8>   hop_limit;
    bit<128> src_addr;
    bit<128> dst_addr;
}




struct metadata {
    bit<160>   routeId;
    bit<16>    etherType;
    bit<1>     apply_sr;
    bit<9>     port;
    bit<16>    poly1;
    bit<16>    secret;
    bit<16>    mersenne;
    bit<4>     mersenne_b;
    bit<1>     POT_flag;
    bit<16>    verification;
    bit<16>    rnd;
    bit<16>    cml;
    bit<16>    prev_rnd;
    bit<16>    prev_cml;
    ip4Addr_t  ipAddr;
    bit<9>     egress_port;

}

struct polka_t_top {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
    bit<160>    routeId;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

struct headers {
    ethernet_t  ethernet;
    potPolka_t  potPolka;
    ipv4_t      ipv4;
    ipv6_t      ipv6;
    udp_t       udp;
}





/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            TYPE_SRCROUTING: parse_srcRouting;
            TYPE_IPV6: parse_ipv6;
            default: accept;
        }
    }

    
    state parse_srcRouting {
        packet.extract(hdr.potPolka);
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        //transition accept;
        transition select(hdr.ipv4.protocol){
            PROTO_UDP: parse_udp;
            default: accept;
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }   


    state parse_ipv6 {
        packet.extract(hdr.ipv6);
        transition accept;         // Just accept it, no need to parse UDP for IPv6
    }

}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**********************  T U N N E L   E N C A P   ************************
*************************************************************************/
control process_tunnel_encap(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {




    action drop() {
        mark_to_drop(standard_metadata);
    }



    action add_sourcerouting_header ( egressSpec_t port, macAddr_t dmac, bit<160>  routeIdPacket, bit<16> rnd, bit<16> cml, bit<16> secret){


        standard_metadata.egress_spec = port;

        hdr.ethernet.dstAddr = dmac;
        
        
        hdr.potPolka.setValid();
        log_msg("Ingress: POT-POLKA is valid");
        hdr.potPolka.routeId = routeIdPacket;
        hdr.potPolka.rnd = rnd;
        hdr.potPolka.cml = cml;
        hdr.potPolka.secret = secret;
        log_msg("Initial secret_shares value: {}", {hdr.potPolka.secret});





        hdr.potPolka.saved_dst_ip = hdr.ipv4.dstAddr;
        log_msg("Encapsulating with Dst IP: {}.{}.{}.{}", {
            (bit<32>)hdr.potPolka.saved_dst_ip >> 24,         // A (First Octet)
            ((bit<32>)hdr.potPolka.saved_dst_ip >> 16) & 0xFF, // B (Second Octet)
            ((bit<32>)hdr.potPolka.saved_dst_ip >> 8) & 0xFF,  // C (Third Octet)
            (bit<32>)hdr.potPolka.saved_dst_ip & 0xFF          // D (Fourth Octet)
        });


        hdr.potPolka.saved_src_ip = hdr.ipv4.srcAddr; 
        log_msg("Saved Src IP: {}.{}.{}.{}", {
            (bit<32>)hdr.potPolka.saved_src_ip >> 24,
            ((bit<32>)hdr.potPolka.saved_src_ip >> 16) & 0xFF,
            ((bit<32>)hdr.potPolka.saved_src_ip >> 8) & 0xFF,
            (bit<32>)hdr.potPolka.saved_src_ip & 0xFF
        });

        hdr.potPolka.saved_src_port = hdr.udp.srcPort; 
        log_msg("Saved Src Port: {}", {hdr.potPolka.saved_src_port});

        hdr.potPolka.saved_dst_port = hdr.udp.dstPort;
        log_msg("Saved Dst Port: {}", {hdr.potPolka.saved_dst_port});






        hdr.ipv4.setInvalid();
        //log_msg("Ingress: IPV4 is not valid _ Must be removed");

        if (hdr.udp.isValid()) {
            hdr.udp.setInvalid(); 
            log_msg("Encapsulation: UDP header invalidated.");
        }

        hdr.ethernet.etherType = TYPE_SRCROUTING;
        log_msg("Ingress: etherType is changed to TYPE_SRCROUTING");

        //truncate((bit<32>)64);
        truncate((bit<32>)standard_metadata.packet_length + 12);

        log_msg("add_sourcerouting_header: port={}, rnd={}, cml={}, dmac={}, routeIdPacket={}, secret={}", 
            {port, rnd, cml, dmac, routeIdPacket, secret});

    }




    table tunnel_encap_process_sr {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            add_sourcerouting_header;
            drop;
        }
        size = 1024;
        default_action = drop();
    }





    apply {

        if (hdr.ipv4.isValid()) {
        log_msg("Ingress: IPV4 is valid");

        log_msg("IPv4 dstAddr = {}.{}.{}.{}", {
            (bit<32>)hdr.ipv4.dstAddr >> 24,       // A (First Octet)
            ((bit<32>)hdr.ipv4.dstAddr >> 16) & 0xFF, // B (Second Octet)
            ((bit<32>)hdr.ipv4.dstAddr >> 8) & 0xFF,  // C (Third Octet)
            (bit<32>)hdr.ipv4.dstAddr & 0xFF          // D (Fourth Octet)
        });

            tunnel_encap_process_sr.apply();
        }
  
    }

}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    


    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }




    action verify_pot(bit<1> sr, mersenne_t mersenne, mersenne_b_t mersenne_b) {
        meta.POT_flag = sr;
        meta.mersenne = mersenne;
        meta.mersenne_b = mersenne_b;
        //meta.secret = secret;
    }



    table egress_verify {
        key = {
            hdr.potPolka.routeId: exact;
        }
        actions = {
            verify_pot;
            drop;
        }
        size = 1024;
        default_action = drop();
    }





    apply {
        if (hdr.ethernet.etherType == TYPE_IPV4) {

            log_msg("Ingress: Received IPv4 packet");
            process_tunnel_encap.apply(hdr, meta, standard_metadata);


        } else if (hdr.ethernet.etherType == TYPE_SRCROUTING) {

            log_msg("Ingress: Received SRCROUTING packet");
            if (hdr.potPolka.isValid()) {
                log_msg("Egress: Verifying Path with RouteID: {}", {hdr.potPolka.routeId});
                egress_verify.apply();



                if (meta.POT_flag == 1) {
                    meta.rnd = hdr.potPolka.rnd;
                    meta.cml = hdr.potPolka.cml;
                    log_msg("RND = {}, CML without MOD operation = {}", {meta.rnd, meta.cml});
                    


                    meta.secret = hdr.potPolka.secret;
                    log_msg("Final accumulated secret received: {}", {meta.secret});
                    meta.secret = (meta.secret & meta.mersenne) + (meta.secret >> meta.mersenne_b);
                    if (meta.secret > meta.mersenne){
                        meta.secret = meta.secret - meta.mersenne;
                        log_msg("Adjusted secret: {}", {meta.secret});
                    
                    } else {
                        log_msg("No adjustment needed for secret");
                    }
                    log_msg("last secret = {}", {meta.secret});



                    meta.verification = (meta.rnd + meta.secret);
                    meta.verification = (meta.verification & meta.mersenne) + (meta.verification >> meta.mersenne_b);
                    log_msg("Verification: {}", {meta.verification});

                    meta.cml = (meta.cml & meta.mersenne) + (meta.cml >> meta.mersenne_b);
                    log_msg("CML_POT = {}", {meta.cml});

                    
                    if(meta.verification ==  meta.cml){

                        log_msg("Verification EQUALS CML_POT");
                        log_msg("PoT verification successful");
                        //hdr.ethernet.etherType = TYPE_IPV4;
                        


                    

                        hdr.ipv4.setValid();
                        hdr.ipv4.version = 4;
                        hdr.ipv4.ihl = 5;
                        hdr.ipv4.protocol = 17; // Set to UDP
                        //hdr.ipv4.totalLen = hdr.potPolka.saved_totalLen;
                        hdr.ipv4.totalLen = 38;
                        hdr.ipv4.hdrChecksum = 0;
                       



                        hdr.ipv4.dstAddr = hdr.potPolka.saved_dst_ip;
                        log_msg("Final Restored IPv4 dstAddr = {}.{}.{}.{}", {
                            (bit<32>)hdr.ipv4.dstAddr >> 24,       // A
                            ((bit<32>)hdr.ipv4.dstAddr >> 16) & 0xFF, // B
                            ((bit<32>)hdr.ipv4.dstAddr >> 8) & 0xFF,  // C
                            (bit<32>)hdr.ipv4.dstAddr & 0xFF          // D
                        });



                        hdr.ipv4.srcAddr = hdr.potPolka.saved_src_ip;
                        log_msg("Final Restored IPv4 srcAddr = {}.{}.{}.{}", {
                            (bit<32>)hdr.ipv4.srcAddr >> 24,       // A
                            ((bit<32>)hdr.ipv4.srcAddr >> 16) & 0xFF, // B
                            ((bit<32>)hdr.ipv4.srcAddr >> 8) & 0xFF,  // C
                            (bit<32>)hdr.ipv4.srcAddr & 0xFF          // D
                        });






                        hdr.udp.setValid();
                        hdr.udp.length = 18; // 8 (header) + 11 (payload)
                        hdr.udp.srcPort = hdr.potPolka.saved_src_port;
                        hdr.udp.dstPort = hdr.potPolka.saved_dst_port;


                        hdr.potPolka.setInvalid();
                        hdr.ethernet.etherType = TYPE_IPV4;
                        //truncate((bit<32>)52);
                        truncate((bit<32>)hdr.ipv4.totalLen + 14);
                        ipv4_lpm.apply();




                    } else {
                        log_msg("PoT verification failed: incorrect RND or CML values");
                        drop();
                    }




                } else {
                    log_msg("PoT verification failed: invalid POT_flag flag");
                    drop();
                }


            } else {
                log_msg("Ingress: potPolka header is not valid");
                drop();
            }
        }




        else if (hdr.ethernet.etherType == TYPE_IPV6) { 
            // 0x86dd is the Hex code for IPv6
            // We just give it a destination port so BMv2 doesn't log an error
            standard_metadata.egress_spec = 2; 
            log_msg("Bypassing background IPv6 traffic to port 2");
        }



    }
}



/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {  
        log_msg("Secret value before leaving ingress edge: {}", {hdr.potPolka.secret});
    }
}



/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply { 
        // 1. IPv4 Header Checksum
        update_checksum(
            hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);

        // 2. UDP Header Checksum (Pseudo-header + UDP fields)
        // Moved inside the apply block
        update_checksum(
            hdr.udp.isValid(),
            { hdr.ipv4.srcAddr, 
              hdr.ipv4.dstAddr, 
              (bit<8>)0, 
              hdr.ipv4.protocol, 
              hdr.udp.length, 
              hdr.udp.srcPort, 
              hdr.udp.dstPort, 
              hdr.udp.length },
            hdr.udp.checksum, 
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.potPolka);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.ipv6);
        packet.emit(hdr.udp);
    }
}
 

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;