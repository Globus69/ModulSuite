#!/bin/bash

echo "🖥️  SYSTEM INFORMATION"
echo "================================"
echo "Hostname:    $(hostname)"
echo "OS:          $(uname -s)"
echo "Kernel:      $(uname -r)"
echo "Architektur: $(uname -m)"
echo "Uptime:      $(uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}')"
echo "================================"
echo ""
echo "💾 SPEICHER"
echo "================================"
df -h / | tail -1 | awk '{print "Disk:        " $3 " / " $2 " (" $5 " verwendet)"}'
echo "================================"
