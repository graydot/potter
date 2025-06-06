#!/usr/bin/env python3
"""
Performance Monitor
Real-time system performance monitoring with alerting
"""

import time
import threading
import logging
import statistics
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta

from .metrics_collector import MetricsCollector, MetricType

logger = logging.getLogger(__name__)


@dataclass
class PerformanceThreshold:
    """Performance threshold definition"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = ">"  # >, <, ==, >=, <=
    window_size: int = 5   # Number of samples to evaluate
    description: str = ""


@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a point in time"""
    timestamp: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: Dict[str, float] = field(default_factory=dict)
    request_latency: Dict[str, float] = field(default_factory=dict)
    active_connections: int = 0
    error_rate: float = 0.0
    throughput: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary"""
        return {
            'timestamp': self.timestamp,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_io': self.network_io,
            'request_latency': self.request_latency,
            'active_connections': self.active_connections,
            'error_rate': self.error_rate,
            'throughput': self.throughput,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat()
        }


@dataclass
class PerformanceAlert:
    """Performance alert notification"""
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str  # "warning", "critical"
    message: str
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'severity': self.severity,
            'message': self.message,
            'timestamp': self.timestamp,
            'resolved': self.resolved,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat()
        }


class PerformanceAnalyzer:
    """Analyzes performance data for trends and anomalies"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.logger = logging.getLogger("performance.analyzer")
    
    def analyze_trend(self, values: List[float]) -> Dict[str, Any]:
        """Analyze trend in performance values"""
        if len(values) < 2:
            return {'trend': 'insufficient_data', 'slope': 0.0}
        
        # Simple linear regression for trend analysis
        n = len(values)
        x = list(range(n))
        
        # Calculate slope (trend)
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0.0
        else:
            slope = numerator / denominator
        
        # Determine trend direction
        if abs(slope) < 0.01:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        return {
            'trend': trend,
            'slope': slope,
            'correlation': self._calculate_correlation(x, values)
        }
    
    def detect_anomalies(self, values: List[float], threshold: float = 2.0) -> List[int]:
        """Detect anomalies using standard deviation"""
        if len(values) < 3:
            return []
        
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        
        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
            if z_score > threshold:
                anomalies.append(i)
        
        return anomalies
    
    def calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate performance percentiles"""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            'p50': sorted_values[int(n * 0.5)],
            'p75': sorted_values[int(n * 0.75)],
            'p90': sorted_values[int(n * 0.9)],
            'p95': sorted_values[int(n * 0.95)],
            'p99': sorted_values[int(n * 0.99)]
        }
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
        
        x_var = sum((x[i] - x_mean) ** 2 for i in range(len(x)))
        y_var = sum((y[i] - y_mean) ** 2 for i in range(len(y)))
        
        denominator = (x_var * y_var) ** 0.5
        
        return numerator / denominator if denominator > 0 else 0.0


class PerformanceMonitor:
    """
    Real-time performance monitoring system
    
    Features:
    - Continuous performance tracking
    - Threshold-based alerting
    - Trend analysis
    - Performance snapshots
    - Anomaly detection
    """
    
    def __init__(self, metrics_collector: MetricsCollector, 
                 monitoring_interval: float = 5.0):
        """
        Initialize performance monitor
        
        Args:
            metrics_collector: MetricsCollector instance
            monitoring_interval: Monitoring interval in seconds
        """
        self.logger = logging.getLogger("performance.monitor")
        self.metrics_collector = metrics_collector
        self.monitoring_interval = monitoring_interval
        
        # State
        self.enabled = False
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        
        # Performance data
        self.snapshots = deque(maxlen=1000)
        self.performance_history = {}
        
        # Thresholds and alerting
        self.thresholds: List[PerformanceThreshold] = []
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # Analysis
        self.analyzer = PerformanceAnalyzer()
        
        # Initialize default thresholds
        self._setup_default_thresholds()
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.logger.warning("Performance monitoring already running")
            return
        
        self.stop_event.clear()
        self.enabled = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info(f"Started performance monitoring with {self.monitoring_interval}s interval")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.enabled = False
        self.stop_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        
        self.logger.info("Stopped performance monitoring")
    
    def add_threshold(self, threshold: PerformanceThreshold):
        """Add performance threshold"""
        self.thresholds.append(threshold)
        self.logger.debug(f"Added threshold for {threshold.metric_name}")
    
    def remove_threshold(self, metric_name: str):
        """Remove performance threshold"""
        self.thresholds = [t for t in self.thresholds if t.metric_name != metric_name]
        self.logger.debug(f"Removed threshold for {metric_name}")
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def get_current_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        snapshot = PerformanceSnapshot()
        
        # Get latest metrics from collector
        all_metrics = self.metrics_collector.get_all_metrics()
        
        # CPU usage
        cpu_series = all_metrics.get('system_cpu_usage_percent:')
        if cpu_series:
            snapshot.cpu_usage = cpu_series.get_latest() or 0.0
        
        # Memory usage
        memory_series = all_metrics.get('system_memory_usage_percent:')
        if memory_series:
            snapshot.memory_usage = memory_series.get_latest() or 0.0
        
        # Disk usage
        disk_series = all_metrics.get('disk_usage_percent:')
        if disk_series:
            snapshot.disk_usage = disk_series.get_latest() or 0.0
        
        # Network I/O
        net_sent_series = all_metrics.get('network_bytes_sent:')
        net_recv_series = all_metrics.get('network_bytes_recv:')
        if net_sent_series and net_recv_series:
            snapshot.network_io = {
                'bytes_sent': net_sent_series.get_latest() or 0.0,
                'bytes_received': net_recv_series.get_latest() or 0.0
            }
        
        # Request latency (from application metrics)
        for metric_name, series in all_metrics.items():
            if 'request_duration_avg' in metric_name:
                endpoint = self._extract_endpoint_from_metric_name(metric_name)
                if endpoint:
                    snapshot.request_latency[endpoint] = series.get_latest() or 0.0
        
        return snapshot
    
    def get_performance_summary(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for specified duration"""
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_snapshots = [s for s in self.snapshots if s.timestamp >= cutoff_time]
        
        if not recent_snapshots:
            return {'error': 'No recent performance data available'}
        
        # Calculate averages
        avg_cpu = statistics.mean(s.cpu_usage for s in recent_snapshots)
        avg_memory = statistics.mean(s.memory_usage for s in recent_snapshots)
        avg_disk = statistics.mean(s.disk_usage for s in recent_snapshots)
        
        # Calculate throughput
        total_throughput = sum(s.throughput for s in recent_snapshots)
        avg_throughput = total_throughput / len(recent_snapshots)
        
        # Calculate error rate
        avg_error_rate = statistics.mean(s.error_rate for s in recent_snapshots)
        
        # Analyze trends
        cpu_values = [s.cpu_usage for s in recent_snapshots]
        memory_values = [s.memory_usage for s in recent_snapshots]
        
        cpu_trend = self.analyzer.analyze_trend(cpu_values)
        memory_trend = self.analyzer.analyze_trend(memory_values)
        
        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_snapshots),
            'averages': {
                'cpu_usage': avg_cpu,
                'memory_usage': avg_memory,
                'disk_usage': avg_disk,
                'throughput': avg_throughput,
                'error_rate': avg_error_rate
            },
            'trends': {
                'cpu': cpu_trend,
                'memory': memory_trend
            },
            'percentiles': {
                'cpu': self.analyzer.calculate_percentiles(cpu_values),
                'memory': self.analyzer.calculate_percentiles(memory_values)
            },
            'active_alerts': len(self.active_alerts),
            'timestamp': time.time()
        }
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get all active performance alerts"""
        return list(self.active_alerts.values())
    
    def resolve_alert(self, metric_name: str):
        """Manually resolve a performance alert"""
        if metric_name in self.active_alerts:
            alert = self.active_alerts[metric_name]
            alert.resolved = True
            del self.active_alerts[metric_name]
            self.logger.info(f"Resolved alert for {metric_name}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self.stop_event.wait(self.monitoring_interval):
            if not self.enabled:
                continue
            
            try:
                # Take performance snapshot
                snapshot = self.get_current_snapshot()
                self.snapshots.append(snapshot)
                
                # Update performance history
                self._update_performance_history(snapshot)
                
                # Check thresholds and generate alerts
                self._check_thresholds()
                
                self.logger.debug(f"Performance snapshot: CPU={snapshot.cpu_usage:.1f}% "
                                f"Memory={snapshot.memory_usage:.1f}% "
                                f"Disk={snapshot.disk_usage:.1f}%")
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
    
    def _update_performance_history(self, snapshot: PerformanceSnapshot):
        """Update performance history with new snapshot"""
        timestamp = snapshot.timestamp
        
        # Store key metrics in history
        metrics = {
            'cpu_usage': snapshot.cpu_usage,
            'memory_usage': snapshot.memory_usage,
            'disk_usage': snapshot.disk_usage,
            'error_rate': snapshot.error_rate,
            'throughput': snapshot.throughput
        }
        
        for metric_name, value in metrics.items():
            if metric_name not in self.performance_history:
                self.performance_history[metric_name] = deque(maxlen=1000)
            
            self.performance_history[metric_name].append({
                'value': value,
                'timestamp': timestamp
            })
    
    def _check_thresholds(self):
        """Check performance thresholds and generate alerts"""
        for threshold in self.thresholds:
            try:
                # Get recent values for this metric
                if threshold.metric_name in self.performance_history:
                    history = self.performance_history[threshold.metric_name]
                    if len(history) >= threshold.window_size:
                        recent_values = [h['value'] for h in list(history)[-threshold.window_size:]]
                        avg_value = statistics.mean(recent_values)
                        
                        # Check threshold
                        alert_triggered = self._evaluate_threshold(avg_value, threshold)
                        
                        if alert_triggered:
                            # Determine severity
                            severity = self._determine_severity(avg_value, threshold)
                            
                            # Create or update alert
                            alert_key = f"{threshold.metric_name}_{severity}"
                            
                            if alert_key not in self.active_alerts:
                                alert = PerformanceAlert(
                                    metric_name=threshold.metric_name,
                                    current_value=avg_value,
                                    threshold_value=threshold.warning_threshold if severity == 'warning' else threshold.critical_threshold,
                                    severity=severity,
                                    message=f"{threshold.metric_name} {threshold.comparison} {threshold.warning_threshold if severity == 'warning' else threshold.critical_threshold} ({threshold.description})"
                                )
                                
                                self.active_alerts[alert_key] = alert
                                self._send_alert(alert)
                        else:
                            # Check if we should resolve existing alert
                            alert_key_warning = f"{threshold.metric_name}_warning"
                            alert_key_critical = f"{threshold.metric_name}_critical"
                            
                            if alert_key_warning in self.active_alerts:
                                self.resolve_alert(alert_key_warning)
                            if alert_key_critical in self.active_alerts:
                                self.resolve_alert(alert_key_critical)
                                
            except Exception as e:
                self.logger.error(f"Error checking threshold for {threshold.metric_name}: {e}")
    
    def _evaluate_threshold(self, value: float, threshold: PerformanceThreshold) -> bool:
        """Evaluate if threshold is violated"""
        if threshold.comparison == '>':
            return value > threshold.warning_threshold
        elif threshold.comparison == '<':
            return value < threshold.warning_threshold
        elif threshold.comparison == '>=':
            return value >= threshold.warning_threshold
        elif threshold.comparison == '<=':
            return value <= threshold.warning_threshold
        elif threshold.comparison == '==':
            return abs(value - threshold.warning_threshold) < 0.01
        else:
            return False
    
    def _determine_severity(self, value: float, threshold: PerformanceThreshold) -> str:
        """Determine alert severity"""
        if threshold.comparison == '>':
            return 'critical' if value > threshold.critical_threshold else 'warning'
        elif threshold.comparison == '<':
            return 'critical' if value < threshold.critical_threshold else 'warning'
        elif threshold.comparison == '>=':
            return 'critical' if value >= threshold.critical_threshold else 'warning'
        elif threshold.comparison == '<=':
            return 'critical' if value <= threshold.critical_threshold else 'warning'
        else:
            return 'warning'
    
    def _send_alert(self, alert: PerformanceAlert):
        """Send alert to all registered callbacks"""
        self.logger.warning(f"Performance alert: {alert.message}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    def _extract_endpoint_from_metric_name(self, metric_name: str) -> Optional[str]:
        """Extract endpoint name from metric name"""
        # Example: "http_request_duration_avg:endpoint=/api/process"
        if 'endpoint=' in metric_name:
            parts = metric_name.split('endpoint=')
            if len(parts) > 1:
                return parts[1].split(',')[0]  # Get endpoint value
        return None
    
    def _setup_default_thresholds(self):
        """Setup default performance thresholds"""
        default_thresholds = [
            PerformanceThreshold(
                metric_name='cpu_usage',
                warning_threshold=70.0,
                critical_threshold=90.0,
                comparison='>',
                description='High CPU usage'
            ),
            PerformanceThreshold(
                metric_name='memory_usage',
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison='>',
                description='High memory usage'
            ),
            PerformanceThreshold(
                metric_name='disk_usage',
                warning_threshold=85.0,
                critical_threshold=95.0,
                comparison='>',
                description='High disk usage'
            ),
            PerformanceThreshold(
                metric_name='error_rate',
                warning_threshold=5.0,
                critical_threshold=10.0,
                comparison='>',
                description='High error rate'
            )
        ]
        
        for threshold in default_thresholds:
            self.add_threshold(threshold) 