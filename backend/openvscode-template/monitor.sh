#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_TIMEOUT=10
MAX_CONTAINERS=50
VERBOSE=false
CONTINUOUS=false
INTERVAL=5

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -v, --verbose       Enable verbose output"
    echo "  -c, --continuous    Run continuously with specified interval"
    echo "  -i, --interval N    Set interval in seconds for continuous mode (default: 5)"
    echo "  -t, --timeout N     Set Docker timeout in seconds (default: 10)"
    echo "  -m, --max N         Set maximum containers to monitor (default: 50)"
    echo
    echo "Examples:"
    echo "  $0                  # Run once with default settings"
    echo "  $0 -v               # Run once with verbose output"
    echo "  $0 -c -i 10         # Run continuously every 10 seconds"
    echo "  $0 -t 15 -m 100     # Run with 15s timeout and max 100 containers"
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -c|--continuous)
                CONTINUOUS=true
                shift
                ;;
            -i|--interval)
                if [[ -n "${2:-}" && $2 =~ ^[0-9]+$ ]]; then
                    INTERVAL=$2
                    shift 2
                else
                    print_status "ERROR" "Invalid interval value: $2"
                    exit 1
                fi
                ;;
            -t|--timeout)
                if [[ -n "${2:-}" && $2 =~ ^[0-9]+$ ]]; then
                    DOCKER_TIMEOUT=$2
                    shift 2
                else
                    print_status "ERROR" "Invalid timeout value: $2"
                    exit 1
                fi
                ;;
            -m|--max)
                if [[ -n "${2:-}" && $2 =~ ^[0-9]+$ ]]; then
                    MAX_CONTAINERS=$2
                    shift 2
                else
                    print_status "ERROR" "Invalid max containers value: $2"
                    exit 1
                fi
                ;;
            *)
                print_status "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        "DEBUG") 
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "${YELLOW}[DEBUG]${NC} $message"
            fi
            ;;
    esac
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_status "ERROR" "Docker is not running or not accessible"
        exit 1
    fi
    print_status "DEBUG" "Docker daemon is accessible"
}

# Function to get system resources
get_system_resources() {
    print_status "INFO" "System Resource Overview"
    echo "=========================================="
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "CPU Usage: ${YELLOW}${cpu_usage}%${NC}"
    
    # Memory usage
    local mem_info=$(free -h | grep Mem)
    local mem_total=$(echo $mem_info | awk '{print $2}')
    local mem_used=$(echo $mem_info | awk '{print $3}')
    local mem_available=$(echo $mem_info | awk '{print $7}')
    echo -e "Memory: ${YELLOW}${mem_used}${NC} / ${GREEN}${mem_total}${NC} (${BLUE}${mem_available}${NC} available)"
    
    # Disk usage
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    local disk_total=$(df -h / | tail -1 | awk '{print $2}')
    local disk_used=$(df -h / | tail -1 | awk '{print $3}')
    local disk_available=$(df -h / | tail -1 | awk '{print $4}')
    echo -e "Disk: ${YELLOW}${disk_used}${NC} / ${GREEN}${disk_total}${NC} (${BLUE}${disk_available}${NC} available) - ${RED}${disk_usage}%${NC} used"
    
    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo -e "Load Average: ${YELLOW}${load_avg}${NC}"
    
    echo
}

# Function to check workspace health
check_workspace_health() {
    local container=$1
    local health_status=""
    
    # Check if container is running
    if ! docker ps --filter "name=$container" --filter "status=running" --quiet >/dev/null 2>&1; then
        health_status="STOPPED"
        return 1
    fi
    
    # Check container health status
    local health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
    case $health in
        "healthy") health_status="HEALTHY" ;;
        "unhealthy") health_status="UNHEALTHY" ;;
        "starting") health_status="STARTING" ;;
        *) health_status="UNKNOWN" ;;
    esac
    
    echo "$health_status"
    return 0
}

# Function to get detailed container stats
get_container_stats() {
    local container=$1
    local timeout_cmd="timeout $DOCKER_TIMEOUT"
    
    echo -e "${BLUE}Workspace: ${GREEN}$container${NC}"
    
    # Get container status and health
    local health_status=$(check_workspace_health "$container")
    if [ $? -eq 0 ]; then
        case $health_status in
            "HEALTHY") echo -e "  Status: ${GREEN}Running (Healthy)${NC}" ;;
            "UNHEALTHY") echo -e "  Status: ${RED}Running (Unhealthy)${NC}" ;;
            "STARTING") echo -e "  Status: ${YELLOW}Starting${NC}" ;;
            *) echo -e "  Status: ${BLUE}Running${NC}" ;;
        esac
    else
        echo -e "  Status: ${RED}Stopped${NC}"
        return 1
    fi
    
    # Get resource usage with timeout
    local stats_output=$($timeout_cmd docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" "$container" 2>/dev/null || echo "  Unable to get stats")
    
    if [[ "$stats_output" != "  Unable to get stats" ]]; then
        echo "  Resource Usage:"
        echo "$stats_output" | sed 's/^/    /'
    else
        print_status "WARNING" "Unable to get stats for $container"
    fi
    
    # Get container info
    local created=$(docker inspect --format='{{.Created}}' "$container" 2>/dev/null | cut -d'T' -f1 || echo "Unknown")
    local image=$(docker inspect --format='{{.Config.Image}}' "$container" 2>/dev/null || echo "Unknown")
    echo "  Created: $created"
    echo "  Image: $image"
    
    # Get port mappings
    local ports=$(docker port "$container" 2>/dev/null | grep -E ':[0-9]+->' | head -3 | sed 's/^/    /' || echo "    No ports exposed")
    echo "  Ports:"
    echo "$ports"
    
    # Get container labels if verbose
    if [[ "$VERBOSE" == "true" ]]; then
        local labels=$(docker inspect --format='{{range $k, $v := .Config.Labels}}{{$k}}={{$v}}{{"\n"}}{{end}}' "$container" 2>/dev/null | grep -v '^$' | head -5 | sed 's/^/    /' || echo "    No labels")
        echo "  Labels:"
        echo "$labels"
    fi
    
    echo
}

# Function to show summary statistics
show_summary_stats() {
    local container_count=$1
    local healthy_count=0
    local unhealthy_count=0
    local stopped_count=0
    
    # Count health statuses
    for container in $(docker ps -a --filter "label=com.fisamy.workspace.name" --format "{{.Names}}" 2>/dev/null || true); do
        if [ -n "$container" ]; then
            local health=$(check_workspace_health "$container" 2>/dev/null || echo "STOPPED")
            case $health in
                "HEALTHY") ((healthy_count++)) ;;
                "UNHEALTHY") ((unhealthy_count++)) ;;
                "STOPPED") ((stopped_count++)) ;;
            esac
        fi
    done
    
    echo "Summary Statistics:"
    echo "=================="
    echo -e "Total workspaces: ${GREEN}$container_count${NC}"
    echo -e "Healthy: ${GREEN}$healthy_count${NC}"
    echo -e "Unhealthy: ${RED}$unhealthy_count${NC}"
    echo -e "Stopped: ${YELLOW}$stopped_count${NC}"
    echo -e "Monitoring completed at: ${BLUE}$(date '+%H:%M:%S')${NC}"
}

# Main execution
main() {
    # Parse command line arguments
    parse_args "$@"
    
    # Show configuration if verbose
    if [[ "$VERBOSE" == "true" ]]; then
        print_status "DEBUG" "Configuration:"
        print_status "DEBUG" "  Docker timeout: ${DOCKER_TIMEOUT}s"
        print_status "DEBUG" "  Max containers: ${MAX_CONTAINERS}"
        print_status "DEBUG" "  Continuous mode: ${CONTINUOUS}"
        if [[ "$CONTINUOUS" == "true" ]]; then
            print_status "DEBUG" "  Interval: ${INTERVAL}s"
        fi
        echo
    fi
    
    # Main monitoring loop
    while true; do
        echo -e "${BLUE}OpenVSCode Workspace Monitor${NC}"
        echo "=========================================="
        echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
        echo
        
        # Check Docker availability
        check_docker
        
        # Get system resources
        get_system_resources
        
        # Get all containers with fisamy labels
        print_status "INFO" "Scanning for OpenVSCode workspaces..."
        local workspace_containers=$(docker ps --filter "label=com.fisamy.workspace.name" --format "{{.Names}}" 2>/dev/null || true)
        
        if [ -z "$workspace_containers" ]; then
            print_status "WARNING" "No OpenVSCode workspaces found"
            echo
            print_status "INFO" "Checking for stopped workspaces..."
            local stopped_containers=$(docker ps -a --filter "label=com.fisamy.workspace.name" --filter "status=exited" --format "{{.Names}}" 2>/dev/null || true)
            if [ -n "$stopped_containers" ]; then
                echo "Stopped workspaces:"
                echo "$stopped_containers" | sed 's/^/  /'
            fi
            
            if [[ "$CONTINUOUS" == "true" ]]; then
                echo
                print_status "INFO" "Waiting ${INTERVAL} seconds before next check..."
                sleep $INTERVAL
                clear
                continue
            else
                exit 0
            fi
        fi
        
        # Count containers
        local container_count=$(echo "$workspace_containers" | wc -l)
        print_status "SUCCESS" "Found $container_count active workspace(s)"
        echo
        
        # Check if we have too many containers
        if [ "$container_count" -gt "$MAX_CONTAINERS" ]; then
            print_status "WARNING" "Large number of containers detected ($container_count). This may impact performance."
            echo
        fi
        
        echo "Workspace Details:"
        echo "=================="
        
        # Process each container
        local processed=0
        for container in $workspace_containers; do
            if [ -n "$container" ]; then
                get_container_stats "$container"
                ((processed++))
                
                # Add a small delay to prevent overwhelming Docker daemon
                if [ $processed -lt $container_count ]; then
                    sleep 0.1
                fi
            fi
        done
        
        # Show summary
        show_summary_stats $container_count
        
        # Show quick status overview
        echo
        print_status "INFO" "Quick Status Overview:"
        docker ps --filter "label=com.fisamy.workspace.name" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || print_status "ERROR" "Unable to get workspace overview"
        
        # Exit if not continuous mode
        if [[ "$CONTINUOUS" != "true" ]]; then
            break
        fi
        
        echo
        print_status "INFO" "Waiting ${INTERVAL} seconds before next check..."
        sleep $INTERVAL
        clear
    done
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Monitoring interrupted. Exiting...${NC}"; exit 130' INT TERM

# Run main function
main "$@"
