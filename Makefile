#P4C = p4c
#CORE = pot-polka-core.p4
#EDGE = pot-polka-edge.p4

#all: build

#build: edge
	#${P4C} ${CORE}

#edge:
	#${P4C} ${EDGE}
	
	
	
#CORE = pot-polka-core.p4
#EDGE = pot-polka-edge.p4

#BMV2_SWITCH_EXE = simple_switch_grpc
#P4C = p4c

#all: build

#build: logs core edge 

#logs:
	#mkdir -p logs

#core:
	#${P4C} --target bmv2 --arch v1model --output pot-polka-core --p4runtime-files pot-polka-core.p4info.txt --p4runtime-format text ${CORE}

#edge:
	#${P4C} --target bmv2 --arch v1model --output pot-polka-edge --p4runtime-files pot-polka-edge.p4info.txt --p4runtime-format text ${EDGE}



BMV2_SWITCH_EXE = simple_switch_grpc

include ../../../utils/Makefile
	
	

