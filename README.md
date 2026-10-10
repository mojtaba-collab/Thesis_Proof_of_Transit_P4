

# PoT-PolKA SDN Architecture

An implementation of Proof of Transit (PoT) combined with PolKA (Polynomial Key-based Architecture) Source Routing using P4 and P4Runtime. This repository demonstrates secure, verifiable path routing and telemetry on programmable data planes (BMv2).

## 📋 Table of Contents
- [Overview](#-overview)
- [Repository Structure](#-repository-structure)
- [Prerequisites & Installation](#-prerequisites--installation)
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
