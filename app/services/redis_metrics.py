"""
Redis Metrics and Monitoring Service
Collects Redis performance metrics and provides alerting capabilities
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedisMetricsService:
    """Service for collecting and monitoring Redis metrics"""

    def __init__(self):
        self._redis_service = None
        self.metrics_history = []
        self.alerts = []
        self.alert_thresholds = {
            "connection_errors": 5,  # Max connection errors per minute
            "cache_hit_ratio": 0.5,  # Min cache hit ratio
            "memory_usage": 0.9,     # Max memory usage ratio
            "response_time": 1000,   # Max response time in ms
        }

    async def _get_redis_service(self):
        """Lazy load Redis service"""
        if self._redis_service is None:
            try:
                from app.services.redis_service import redis_service
                self._redis_service = redis_service
            except ImportError:
                logger.error("Redis service not available for metrics")
                return None
        return self._redis_service

    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect comprehensive Redis metrics
        """
        redis_service = await self._get_redis_service()
        if not redis_service:
            return {"error": "Redis service unavailable"}

        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "connection": await self._get_connection_metrics(redis_service),
                "performance": await self._get_performance_metrics(redis_service),
                "memory": await self._get_memory_metrics(redis_service),
                "cache": await self._get_cache_metrics(redis_service),
                "queues": await self._get_queue_metrics(redis_service),
            }

            # Store metrics history (keep last 100 entries)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)

            # Check for alerts
            await self._check_alerts(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {e}")
            return {"error": str(e)}

    async def _get_connection_metrics(self, redis_service) -> Dict[str, Any]:
        """Get Redis connection metrics"""
        try:
            # Test connection
            start_time = time.time()
            pong = await redis_service.ping()
            response_time = (time.time() - start_time) * 1000  # ms

            return {
                "connected": pong == "PONG",
                "response_time_ms": round(response_time, 2),
                "status": "healthy" if pong == "PONG" else "unhealthy"
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "status": "error"
            }

    async def _get_performance_metrics(self, redis_service) -> Dict[str, Any]:
        """Get Redis performance metrics"""
        try:
            info = await redis_service.get_info()

            return {
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "total_connections_received": info.get("total_connections_received", 0),
                "rejected_connections": info.get("rejected_connections", 0),
                "expired_keys": info.get("expired_keys", 0),
                "evicted_keys": info.get("evicted_keys", 0),
            }
        except Exception as e:
            logger.warning(f"Could not get performance metrics: {e}")
            return {"error": str(e)}

    async def _get_memory_metrics(self, redis_service) -> Dict[str, Any]:
        """Get Redis memory metrics"""
        try:
            info = await redis_service.get_info()

            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0)
            memory_usage_ratio = used_memory / max_memory if max_memory > 0 else 0

            return {
                "used_memory_bytes": used_memory,
                "max_memory_bytes": max_memory,
                "memory_usage_ratio": round(memory_usage_ratio, 3),
                "memory_fragmentation_ratio": float(info.get("mem_fragmentation_ratio", 0)),
                "used_memory_peak": info.get("used_memory_peak", 0),
            }
        except Exception as e:
            logger.warning(f"Could not get memory metrics: {e}")
            return {"error": str(e)}

    async def _get_cache_metrics(self, redis_service) -> Dict[str, Any]:
        """Get cache-specific metrics"""
        try:
            # Get cache hit/miss statistics from Redis
            info = await redis_service.get_info()

            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)
            total_requests = keyspace_hits + keyspace_misses

            hit_ratio = keyspace_hits / total_requests if total_requests > 0 else 0

            return {
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses,
                "total_requests": total_requests,
                "hit_ratio": round(hit_ratio, 3),
                "total_keys": await redis_service.get_key_count(),
            }
        except Exception as e:
            logger.warning(f"Could not get cache metrics: {e}")
            return {"error": str(e)}

    async def _get_queue_metrics(self, redis_service) -> Dict[str, Any]:
        """Get queue-specific metrics"""
        try:
            queue_lengths = {}
            total_queued = 0

            # Check known queues
            queues = ["email_queue", "paddle_queue"]
            for queue in queues:
                length = await redis_service.get_queue_length(queue)
                queue_lengths[queue] = length
                total_queued += length

            return {
                "queue_lengths": queue_lengths,
                "total_queued_tasks": total_queued,
                "queues_monitored": len(queues),
            }
        except Exception as e:
            logger.warning(f"Could not get queue metrics: {e}")
            return {"error": str(e)}

    async def _check_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        alerts = []

        # Connection alerts
        connection = metrics.get("connection", {})
        if not connection.get("connected", False):
            alerts.append({
                "type": "connection",
                "severity": "critical",
                "message": "Redis connection failed",
                "timestamp": metrics["timestamp"]
            })

        if connection.get("response_time_ms", 0) > self.alert_thresholds["response_time"]:
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": f"High Redis response time: {connection['response_time_ms']}ms",
                "timestamp": metrics["timestamp"]
            })

        # Memory alerts
        memory = metrics.get("memory", {})
        if memory.get("memory_usage_ratio", 0) > self.alert_thresholds["memory_usage"]:
            alerts.append({
                "type": "memory",
                "severity": "warning",
                "message": f"High memory usage: {memory['memory_usage_ratio']:.1%}",
                "timestamp": metrics["timestamp"]
            })

        # Cache alerts
        cache = metrics.get("cache", {})
        if cache.get("hit_ratio", 1.0) < self.alert_thresholds["cache_hit_ratio"]:
            alerts.append({
                "type": "cache",
                "severity": "warning",
                "message": f"Low cache hit ratio: {cache['hit_ratio']:.1%}",
                "timestamp": metrics["timestamp"]
            })

        # Store alerts
        self.alerts.extend(alerts)

        # Keep only recent alerts (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        self.alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff
        ]

        # Log alerts
        for alert in alerts:
            logger.warning(f"Redis Alert [{alert['severity']}]: {alert['message']}")

    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall Redis health status"""
        if not self.metrics_history:
            return {"status": "unknown", "message": "No metrics collected yet"}

        latest_metrics = self.metrics_history[-1]

        # Determine health based on latest metrics
        connection = latest_metrics.get("connection", {})
        memory = latest_metrics.get("memory", {})
        cache = latest_metrics.get("cache", {})

        issues = []

        if not connection.get("connected", False):
            issues.append("Redis connection failed")

        if memory.get("memory_usage_ratio", 0) > 0.95:
            issues.append("Memory usage critical")

        if cache.get("hit_ratio", 1.0) < 0.3:
            issues.append("Cache performance degraded")

        if issues:
            return {
                "status": "unhealthy",
                "issues": issues,
                "last_check": latest_metrics["timestamp"]
            }

        return {
            "status": "healthy",
            "last_check": latest_metrics["timestamp"],
            "metrics": {
                "response_time_ms": connection.get("response_time_ms"),
                "memory_usage": memory.get("memory_usage_ratio"),
                "cache_hit_ratio": cache.get("hit_ratio"),
            }
        }

    async def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff
        ]

    async def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metrics history"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            metric for metric in self.metrics_history
            if datetime.fromisoformat(metric["timestamp"]) > cutoff
        ]

# Global metrics service instance
redis_metrics = RedisMetricsService()