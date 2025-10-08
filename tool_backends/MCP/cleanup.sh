#!/bin/bash

echo "Cleaning up all relevant processes..."

# Use /proc/net/tcp to find processes using a specific port
cleanup_port() {
    local port=$1
    local hex_port=$(printf '%04X' $port)
    for pid in $(ls /proc | grep -E '^[0-9]+$'); do
        # The 2>/dev/null suppresses errors if a process folder disappears
        if grep -q "$hex_port" /proc/$pid/net/tcp 2>/dev/null; then
            echo "Found port $port occupied by process $pid"
            kill -9 $pid 2>/dev/null
            echo "Terminated process $pid"
        fi
    done
}

# Clean up proxy service (port 30009)
echo "Cleaning up proxy service process..."
cleanup_port 30009

# Clean up worker instances (port 40001 and above)
echo "Cleaning up worker instance processes..."
for port in $(seq 40001 40010); do
    cleanup_port $port
done

# Clean up related Python processes
echo "Cleaning up related Python processes..."
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
    # Check if the cmdline file exists to avoid errors on short-lived processes
    if [ -f /proc/$pid/cmdline ]; then
        # Check for specific Python scripts in the command line
        if grep -q "tool_server.py\|proxy_service.py" /proc/$pid/cmdline 2>/dev/null; then
            echo "Found related Python process $pid"
            kill -9 $pid 2>/dev/null
            echo "Terminated process $pid"
        fi
    fi
done

echo "Cleanup complete"