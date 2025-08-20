#!/bin/bash
echo "📊 Coder Template Performance Monitor"
echo "===================================="

# Monitor container resources
echo "Container Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" $(docker ps -q --filter "label=coder.template") 2>/dev/null || echo "No containers running"

# Monitor startup times
echo -e "\nStartup Script Performance:"
for log in /tmp/coder-startup-script.log; do
    if [ -f "$log" ]; then
        echo "Startup script log: $log"
        grep "Starting.*script" "$log" | tail -1
        grep "completed successfully" "$log" | tail -1
    fi
done

# Monitor health check response times
echo -e "\nHealth Check Performance:"
time curl -s http://localhost:13133 > /dev/null && echo "Health check response time measured above"
