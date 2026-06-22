#!/bin/bash

# Simple launcher for uart_fusion_decoder.py
# Default parameters – adjust as needed
PYTHON_EXEC=python3
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DECODER="$SCRIPT_DIR/uart_fusion_decoder.py"

# Default options (can be overridden via command‑line arguments)
PORT="/dev/ttyUSB0"
BAUD=115200
OUTPUT="decoded.csv"

# Parse optional arguments
while getopts "p:b:o:h" opt; do
  case $opt in
    p) PORT="$OPTARG" ;;
    b) BAUD="$OPTARG" ;;
    o) OUTPUT="$OPTARG" ;;
    h) echo "Usage: $0 [-p <port>] [-b <baud>] [-o <output>]"
       exit 0 ;;
    *) echo "Invalid option" ; exit 1 ;;
  esac
done

# Run the decoder
$PYTHON_EXEC "$DECODER" -p "$PORT" -b "$BAUD" -o "$OUTPUT"
