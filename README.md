PoT-PolKA SDN Architecture

An implementation of Proof of Transit (PoT) combined with PolKA (Polynomial Key-based Architecture) Source Routing using P4 and P4Runtime. This repository demonstrates secure, verifiable path routing and telemetry on programmable data planes (BMv2).

📋 Table of Contents

Overview

Repository Structure

Prerequisites & Installation

Running the Experiment

Components & Scripts

🔍 Overview

This project implements an SDN-managed pipeline where:

Edge Switches (e1, e2) handle encapsulation (pot-polka-edge.p4), tunnel creation, and final PoT cryptographic verification.

Core Switches (s1–s4) process PolKA source routing headers and incrementally compute secret shares (pot-polka-core.p4).

The Controller (controller.py) computes polynomial shares via pot_calculator.py, configures forwarding tables using P4Runtime, and manages dynamic path consistency.

📁 Repository Structure

├── pot-polka-edge.p4        # P4 program for edge switches (Encapsulation/Verification)
├── pot-polka-core.p4        # P4 program for core switches (PolKA routing & PoT shares)
├── controller.py            # Main SDN controller script using P4Runtime
├── p4_client.py             # P4Runtime client library wrapper for table entries
├── polka_helper.py          # PolKA helper logic for port prediction and node IDs
├── pot_calculator.py        # Polynomial secret-sharing and CML calculation engine
├── send_packet.py           # Scapy traffic generator for hosts
├── receive_packet.py        # Scapy packet receiver / ACK responder
├── topology.json            # Mininet / topology configuration file
├── Makefile                 # Build rules for compilation using p4c
└── logs/                    # Directory containing switch runtime logs (e.g., e1.log, s2.log, s3.log)


🚀 Running the Experiment

To run the experiment, follow these steps across multiple terminal windows:

Initialize the Environment:
Run the make command in your terminal to compile the P4 programs, spin up the Mininet topology environment, and set up the network.

make


Start the SDN Controller:
Open a separate terminal window and run the controller script to configure table entries via P4Runtime:

python3 controller.py


Open Host Terminals in Mininet:
Inside your Mininet CLI prompt, spawn xterm windows for host h1 and host h2:

xterm h1 h2


Send and Receive Traffic:

In the terminal window for h1, start the packet generator:

sudo python3 send_packet.py


In the terminal window for h2, start the packet receiver / ACK responder:

sudo python3 receive_packet.py

