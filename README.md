
# PoT-PolKA SDN Architecture

An implementation of Proof of Transit (PoT) combined with PolKA (Polynomial Key-based Architecture) Source Routing using P4 and P4Runtime. This repository demonstrates secure, verifiable path routing and telemetry on programmable data planes (BMv2).

## 📋 Table of Contents
- [Overview](#-overview)
- [Repository Structure](#-repository-structure)
- [Running the Experiment](#-running-the-experiment)
- [Components & Scripts](#-components--scripts)

## 🔍 Overview

This project implements an SDN-managed pipeline where:
- **Edge Switches (e1, e2)** handle encapsulation (`pot-polka-edge.p4`), tunnel creation, and final PoT cryptographic verification.
- **Core Switches (s1–s4)** process PolKA source routing headers and incrementally compute secret shares (`pot-polka-core.p4`).
- **The Controller (`controller.py`)** computes polynomial shares via `pot_calculator.py`, configures forwarding tables using P4Runtime, and manages dynamic path consistency.

## 📁 Repository Structure

```text
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




📦 Prerequisites & Installation

Before executing the project, ensure that you have all necessary dependencies, libraries, and tools installed on your system. This environment typically requires:

- **Environment:** Ubuntu (strongly recommended for native P4 development, though VMs or Docker containers can also be used).
- **P4C:** P4 Compiler.
- **BMv2:** Behavioral Model version 2 (`simple_switch_grpc`).
- **Mininet:** Network emulator.
- **Python 3:** With required libraries (including Scapy and P4Runtime libraries).

Make sure your P4 development environment and toolchain are fully set up according to the official [P4.org tutorial instructions](https://github.com/p4lang/tutorials) before proceeding.










Architecture Flow During Execution
[Host h1] 
     │ (Standard IPv4 Packet)
     ▼
 [Edge Switch e1] ──(Encapsulates: Adds PolKA source route & PoT header)
     │
     ▼
 [Core Switches: s1 -> s2 -> s3 -> s4] ──(Processes PolKA routing & accumulates PoT secret shares)
     │
     ▼
 [Edge Switch e2] ──(Verifies Proof of Transit cryptographic path & strips headers)
     │
     ▼
 [Host h2]




Steps to Execute......

1- Initialize the Environment: Run the make command in your terminal to compile the P4 programs, spin up the Mininet topology environment, and set up the network.
Terminal1:
make

2- Start the SDN Controller: Open a separate terminal window and run the controller script to configure table entries via P4Runtime:
Terminal2:
python3 controller.py

3- Open Host Terminals in Mininet: Inside your Mininet CLI prompt, spawn xterm windows for host h1 and host h2:
mininet> xterm h1 h2


4- Send and Receive Traffic:
In the terminal window for h1, start the packet generator:
sudo python3 send_packet.py

In the terminal window for h2, start the packet receiver / ACK responder:
sudo python3 receive_packet.py
