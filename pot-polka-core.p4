/* -- P4_16 -- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_SRCROUTING = 0x1234;

//counter(256, CounterType.packets) ingress_counter;




/*************************
******** H E A D E R S  ************
*************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<16> rnd_t;
typedef bit<16> cml_t;
typedef bit<16> mersenne_t;
typedef bit<4> mersenne_b_t;
typedef bit<16> x_t;
typedef bit<16> y_t;
typedef bit<16> lpc_t;
typedef bit<16> poly2_t;
typedef bit<4> pot_k_t;
typedef bit<16> secret_t;


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




struct metadata {
    bit<160>  routeId;
    bit<16>   etherType;
    bit<1> apply_sr;
    bit<1> apply_decap;
    bit<9> port;
    poly2_t poly2;
    lpc_t lpc;
    rnd_t new_rnd;
    cml_t new_cml;
    x_t x;
    y_t y;
    mersenne_t mersenne;
    mersenne_b_t mersenne_b;
    pot_k_t pot_k;
    bit<32>  node_id;
    secret_t  secret;
    bit<16>  new_secret;
}





struct polka_t_top {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
    bit<160>   routeId;
}




struct headers {
    ethernet_t  ethernet;
    potPolka_t  potPolka;
    ipv4_t      ipv4;
}




/*************************
******** P A R S E R  ************
*************************/

parser MyParser(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    state start {
        meta.apply_sr = 0;
        transition verify_ethernet;
    }

    state verify_ethernet {
        packet.extract(hdr.ethernet);
        log_msg("etherType: {}", {hdr.ethernet.etherType});   
        transition select(hdr.ethernet.etherType) {
            TYPE_SRCROUTING: get_routeId;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state get_routeId {
		meta.apply_sr = 1;
        packet.extract(hdr.potPolka);
        log_msg("potPolka header extracted. Valid: {}", {hdr.potPolka.isValid()});
        log_msg("potPolka.secret after extraction: {}", {hdr.potPolka.secret});
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }


}


/*************************
****   C H E C K S U M    V E R I F I C A T I O N   *****
*************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************
*****  I N G R E S S   P R O C E S S I N G   ********
*************************/

control MyIngress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    //@register_readable
    //register<bit<9>>(1) meta_port_register;


    action drop() {
        mark_to_drop(standard_metadata);
    }


    action set_nodeid(bit<32> nodeid) {
        meta.node_id = nodeid;
        log_msg("Switch node ID set to {}", {meta.node_id});
    }



    
    action srcRoute_nhop() {

        bit<16> nbase=0;
        bit<64> ncount=4294967296*2;
        bit<16> nresult;
        bit<16> nport;


        bit<160>routeid = (bit<160>) hdr.potPolka.routeId;

        //DATA is  ndata and calculated by (routeID / 2^r) (SHIFT RIGHT)
        bit<160>ndata = routeid >> 16;

        //dif is calculated by (routeID - D * 2^r) (SHIFT LEFT, XOR)
        bit<16> dif = (bit<16>) (routeid ^ (ndata << 16));



        //ncount act as modulus
        hash(
          nresult,
          HashAlgorithm.crc16_custom,
          nbase,

          // ndata << 16 mod node_id , ncount performs mod 
          {ndata, meta.node_id},ncount
        );

        nport = nresult ^ dif;
        meta.pot_k = nport[12:9];
        meta.port = nport[8:0];
        log_msg("Port assigned from nport: meta.port = {}", {meta.port});
    }





   
    table node_config {
        key = {
            hdr.potPolka.routeId: exact;
        }
        actions = {
            set_nodeid;
        }
        size = 2;
        default_action = set_nodeid(0);
    }







    action initialize_param (
        x_t x, 
        y_t y, 
        lpc_t lpc, 
        mersenne_t mersenne, 
        mersenne_b_t mersenne_b, 
        poly2_t poly2
    ){
        meta.x = x;
        meta.y = y;
        meta.lpc = lpc;
        meta.mersenne = mersenne;
        meta.mersenne_b = mersenne_b;
        meta.poly2 = poly2;

        log_msg("pot_param: x={}, y={}, lpc={}, mersenne={}, mersenne_b={}, poly2={}", {x, y, lpc, mersenne, mersenne_b, poly2});

    }
    
    table pot_param {
        key = {
            meta.pot_k: exact;
        }
        actions = {
            initialize_param;
            drop;
        }
        size = 128;
        default_action = drop();
    }

    




    action set_physical_port(bit<9> physical_port) {
        standard_metadata.egress_spec = physical_port;
        log_msg("Port mapping applied: Calculated port {} mapped to actual port {}", {meta.port, physical_port});
    }


    table port_map {
        key = {
            meta.port: exact;
        }
        actions = {
            set_physical_port;
            NoAction;
        }
        size = 256;
        default_action = NoAction();
    }






    action cal_secret(){

        meta.secret = (meta.y * meta.lpc);
        log_msg("y={}, lpc={}", {meta.y, meta.lpc});
        log_msg("Calculated y*lpc: {}", {meta.secret});

    }





    action calc_cml(){

        log_msg("calc_cml initial values: y={}, poly2={}, lpc={}, mersenne={}, mersenne_b={}", 
            {meta.y, meta.poly2, meta.lpc, meta.mersenne, meta.mersenne_b});


        meta.new_cml = (meta.y + meta.poly2) * meta.lpc;
        log_msg("calc_cml after first calculation: new_cml={}", {meta.new_cml});


        meta.new_cml = (meta.new_cml & meta.mersenne) + (meta.new_cml >> meta.mersenne_b);
        log_msg("calc_cml final result: new_cml={}", {meta.new_cml});
    }





    //action log_message(bit<32> msg_type) {
        //ingress_counter.count(msg_type);
        //log_msg("Ingress: Message type {}", {msg_type});
    //}




    apply {


        node_config.apply();
        
        if (meta.apply_sr==1){


            srcRoute_nhop();
            pot_param.apply();
            log_msg("After pot_param lookup: pot_k={}", {meta.pot_k});



            
            
            log_msg("Incoming secret from packet: {}", {hdr.potPolka.secret});
            cal_secret();
            hdr.potPolka.secret = hdr.potPolka.secret + meta.secret;
            log_msg("SECRET: {}", {hdr.potPolka.secret});




            calc_cml();

            if (meta.new_cml > meta.mersenne){
                meta.new_cml = meta.new_cml - meta.mersenne;
                log_msg("Adjusted new_cml: {}", {meta.new_cml});
            
            } else {
                log_msg("No adjustment needed for new_cml");
            }


            log_msg("Before final calc: hdr.potPolka.cml={}, meta.new_cml={}", {hdr.potPolka.cml, meta.new_cml});
            meta.new_cml = hdr.potPolka.cml + meta.new_cml;
            hdr.potPolka.cml = meta.new_cml;
            //meta.new_cml = hdr.potPolka.cml + meta.new_cml;
            log_msg("CML: {}", {hdr.potPolka.cml});



            port_map.apply();


        }else{

            // Dropping non-PoLKA packet
            drop();
        }
    }
}

/*************************
******  E G R E S S   P R O C E S S I N G   *******
*************************/

control MyEgress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {}
}

/*************************
*****   C H E C K S U M    C O M P U T A T I O N   ******
*************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
    apply {}
   
}

/*************************
********  D E P A R S E R  ************
*************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.potPolka);
        packet.emit(hdr.ipv4);
    }
}

/*************************
********  S W I T C H  ************
*************************/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;
