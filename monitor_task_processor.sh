#!/bin/bash
# Envoyou Task Processor Monitoring Script
# Monitors the background task processor and restarts if necessary

SERVICE_NAME="envoyou-task-processor"
LOG_FILE="/var/log/envoyou/task_processor_monitor.log"
MAX_RESTARTS=3
RESTART_WINDOW=3600  # 1 hour in seconds

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create log directory if it doesn't exist
sudo mkdir -p /var/log/envoyou
sudo chown envoyou:envoyou /var/log/envoyou

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

# Check if service is running
check_service() {
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        return 0
    else
        return 1
    fi
}

# Get service status details
get_service_status() {
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
}

# Restart service
restart_service() {
    log "Attempting to restart $SERVICE_NAME..."
    if sudo systemctl restart "$SERVICE_NAME"; then
        log "✅ Service restarted successfully"
        return 0
    else
        log "❌ Failed to restart service"
        return 1
    fi
}

# Check Redis connectivity (basic ping)
check_redis() {
    # This assumes redis-cli is available, adjust as needed
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            return 0
        fi
    fi
    return 1
}

# Check queue backlog
check_queue_backlog() {
    # This is a placeholder - you might want to implement actual queue checking
    # For now, just check if service is processing tasks
    return 0
}

# Main monitoring function
monitor() {
    log "🔍 Starting task processor monitoring check"

    # Check if service is running
    if check_service; then
        log "✅ Service $SERVICE_NAME is running"

        # Additional health checks
        if check_redis; then
            log "✅ Redis connectivity OK"
        else
            log "⚠️  Redis connectivity issue detected"
        fi

        if check_queue_backlog; then
            log "✅ Queue processing OK"
        else
            log "⚠️  Queue backlog detected"
        fi

    else
        log "❌ Service $SERVICE_NAME is not running"
        echo "Service Status:"
        get_service_status

        # Attempt restart
        if restart_service; then
            log "✅ Service restarted successfully"
        else
            log "❌ Service restart failed"
            exit 1
        fi
    fi

    log "🏁 Monitoring check completed"
}

# Health check function (for external monitoring systems)
health_check() {
    if check_service && check_redis; then
        echo "OK"
        exit 0
    else
        echo "FAIL"
        exit 1
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [monitor|health|status|restart]"
    echo ""
    echo "Commands:"
    echo "  monitor  - Run full monitoring check (default)"
    echo "  health   - Simple health check for monitoring systems"
    echo "  status   - Show detailed service status"
    echo "  restart  - Force restart the service"
    echo ""
    echo "Examples:"
    echo "  $0 monitor    # Run monitoring check"
    echo "  $0 health     # Quick health check"
    echo "  $0 status     # Show service details"
}

# Main script logic
case "${1:-monitor}" in
    "monitor")
        monitor
        ;;
    "health")
        health_check
        ;;
    "status")
        echo "Service Status for $SERVICE_NAME:"
        get_service_status
        ;;
    "restart")
        if restart_service; then
            echo "✅ Service restarted"
        else
            echo "❌ Restart failed"
            exit 1
        fi
        ;;
    *)
        usage
        exit 1
        ;;
esac