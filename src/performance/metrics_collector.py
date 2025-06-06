#!/usr/bin/env python3
"""
Metrics Collector
Comprehensive metrics collection system for performance monitoring
"""

import time
import threading
import logging
import psutil
import os
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"        # Monotonically increasing values
    GAUGE = "gauge"           # Current value that can go up/down
    HISTOGRAM = "histogram"   # Distribution of values
    TIMER = "timer"           # Duration measurements
    RATE = "rate"             # Rate per time period


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    unit: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary representation"""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'labels': self.labels,
            'timestamp': self.timestamp,
            'unit': self.unit,
            'description': self.description
        }


@dataclass
class MetricSeries:
    """Series of metric values over time"""
    name: str
    metric_type: MetricType
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    labels: Dict[str, str] = field(default_factory=dict)
    
    def add_value(self, value: float, timestamp: float = None):
        """Add a value to the series"""
        self.values.append({
            'value': value,
            'timestamp': timestamp or time.time()
        })
    
    def get_latest(self) -> Optional[float]:
        """Get the latest value"""
        return self.values[-1]['value'] if self.values else None
    
    def get_average(self, window: int = None) -> float:
        """Get average value over specified window"""
        if not self.values:
            return 0.0
        
        values = list(self.values)
        if window:
            values = values[-window:]
        
        return sum(v['value'] for v in values) / len(values)
    
    def get_percentile(self, percentile: float, window: int = None) -> float:
        """Get percentile value over specified window"""
        if not self.values:
            return 0.0
        
        values = [v['value'] for v in self.values]
        if window:
            values = values[-window:]
        
        values.sort()
        index = int(len(values) * percentile / 100)
        return values[min(index, len(values) - 1)]


class MetricsStorage:
    """Time-series storage for metrics"""
    
    def __init__(self, max_series: int = 10000, max_points_per_series: int = 1000):
        self.max_series = max_series
        self.max_points_per_series = max_points_per_series
        self.series: Dict[str, MetricSeries] = {}
        self.lock = threading.RLock()
    
    def store_metric(self, metric: Metric):
        """Store a metric in the time series"""
        with self.lock:
            series_key = self._get_series_key(metric)
            
            if series_key not in self.series:
                if len(self.series) >= self.max_series:
                    # Remove oldest series
                    oldest_key = next(iter(self.series))
                    del self.series[oldest_key]
                
                self.series[series_key] = MetricSeries(
                    name=metric.name,
                    metric_type=metric.metric_type,
                    values=deque(maxlen=self.max_points_per_series),
                    labels=metric.labels
                )
            
            self.series[series_key].add_value(metric.value, metric.timestamp)
    
    def get_series(self, name: str, labels: Dict[str, str] = None) -> Optional[MetricSeries]:
        """Get metric series by name and labels"""
        series_key = f"{name}:{self._serialize_labels(labels or {})}"
        return self.series.get(series_key)
    
    def get_all_series(self) -> Dict[str, MetricSeries]:
        """Get all metric series"""
        return self.series.copy()
    
    def _get_series_key(self, metric: Metric) -> str:
        """Generate unique key for metric series"""
        return f"{metric.name}:{self._serialize_labels(metric.labels)}"
    
    def _serialize_labels(self, labels: Dict[str, str]) -> str:
        """Serialize labels to string for key generation"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class SystemMetricsCollector:
    """Collects system-level metrics (CPU, memory, disk, network)"""
    
    def __init__(self):
        self.logger = logging.getLogger("metrics.system")
        self.process = psutil.Process()
        self.boot_time = psutil.boot_time()
    
    def collect_cpu_metrics(self) -> List[Metric]:
        """Collect CPU usage metrics"""
        metrics = []
        
        try:
            # System CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            metrics.append(Metric(
                name="system_cpu_usage_percent",
                value=cpu_percent,
                metric_type=MetricType.GAUGE,
                unit="percent",
                description="System CPU usage percentage"
            ))
            
            # Per-core CPU usage
            cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
            for i, usage in enumerate(cpu_per_core):
                metrics.append(Metric(
                    name="system_cpu_usage_percent",
                    value=usage,
                    metric_type=MetricType.GAUGE,
                    labels={"core": str(i)},
                    unit="percent",
                    description=f"CPU core {i} usage percentage"
                ))
            
            # Process CPU usage
            process_cpu = self.process.cpu_percent()
            metrics.append(Metric(
                name="process_cpu_usage_percent",
                value=process_cpu,
                metric_type=MetricType.GAUGE,
                unit="percent",
                description="Process CPU usage percentage"
            ))
            
            # System load average (Unix systems)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                for i, avg in enumerate(load_avg):
                    period = ["1m", "5m", "15m"][i]
                    metrics.append(Metric(
                        name="system_load_average",
                        value=avg,
                        metric_type=MetricType.GAUGE,
                        labels={"period": period},
                        description=f"System load average ({period})"
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error collecting CPU metrics: {e}")
        
        return metrics
    
    def collect_memory_metrics(self) -> List[Metric]:
        """Collect memory usage metrics"""
        metrics = []
        
        try:
            # System memory
            mem = psutil.virtual_memory()
            metrics.extend([
                Metric(
                    name="system_memory_total",
                    value=mem.total,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Total system memory"
                ),
                Metric(
                    name="system_memory_available",
                    value=mem.available,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Available system memory"
                ),
                Metric(
                    name="system_memory_used",
                    value=mem.used,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Used system memory"
                ),
                Metric(
                    name="system_memory_usage_percent",
                    value=mem.percent,
                    metric_type=MetricType.GAUGE,
                    unit="percent",
                    description="System memory usage percentage"
                )
            ])
            
            # Swap memory
            swap = psutil.swap_memory()
            metrics.extend([
                Metric(
                    name="system_swap_total",
                    value=swap.total,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Total swap memory"
                ),
                Metric(
                    name="system_swap_used",
                    value=swap.used,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Used swap memory"
                ),
                Metric(
                    name="system_swap_usage_percent",
                    value=swap.percent,
                    metric_type=MetricType.GAUGE,
                    unit="percent",
                    description="Swap memory usage percentage"
                )
            ])
            
            # Process memory
            proc_mem = self.process.memory_info()
            metrics.extend([
                Metric(
                    name="process_memory_rss",
                    value=proc_mem.rss,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Process resident set size"
                ),
                Metric(
                    name="process_memory_vms",
                    value=proc_mem.vms,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Process virtual memory size"
                )
            ])
            
            # Process memory percentage
            proc_mem_percent = self.process.memory_percent()
            metrics.append(Metric(
                name="process_memory_usage_percent",
                value=proc_mem_percent,
                metric_type=MetricType.GAUGE,
                unit="percent",
                description="Process memory usage percentage"
            ))
            
        except Exception as e:
            self.logger.error(f"Error collecting memory metrics: {e}")
        
        return metrics
    
    def collect_disk_metrics(self) -> List[Metric]:
        """Collect disk I/O metrics"""
        metrics = []
        
        try:
            # Disk usage for root partition
            disk_usage = psutil.disk_usage('/')
            metrics.extend([
                Metric(
                    name="disk_usage_total",
                    value=disk_usage.total,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Total disk space"
                ),
                Metric(
                    name="disk_usage_used",
                    value=disk_usage.used,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Used disk space"
                ),
                Metric(
                    name="disk_usage_free",
                    value=disk_usage.free,
                    metric_type=MetricType.GAUGE,
                    unit="bytes",
                    description="Free disk space"
                ),
                Metric(
                    name="disk_usage_percent",
                    value=(disk_usage.used / disk_usage.total) * 100,
                    metric_type=MetricType.GAUGE,
                    unit="percent",
                    description="Disk usage percentage"
                )
            ])
            
            # Disk I/O statistics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.extend([
                    Metric(
                        name="disk_read_bytes",
                        value=disk_io.read_bytes,
                        metric_type=MetricType.COUNTER,
                        unit="bytes",
                        description="Total bytes read from disk"
                    ),
                    Metric(
                        name="disk_write_bytes",
                        value=disk_io.write_bytes,
                        metric_type=MetricType.COUNTER,
                        unit="bytes",
                        description="Total bytes written to disk"
                    ),
                    Metric(
                        name="disk_read_count",
                        value=disk_io.read_count,
                        metric_type=MetricType.COUNTER,
                        description="Total number of read operations"
                    ),
                    Metric(
                        name="disk_write_count",
                        value=disk_io.write_count,
                        metric_type=MetricType.COUNTER,
                        description="Total number of write operations"
                    )
                ])
                
        except Exception as e:
            self.logger.error(f"Error collecting disk metrics: {e}")
        
        return metrics
    
    def collect_network_metrics(self) -> List[Metric]:
        """Collect network I/O metrics"""
        metrics = []
        
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                metrics.extend([
                    Metric(
                        name="network_bytes_sent",
                        value=net_io.bytes_sent,
                        metric_type=MetricType.COUNTER,
                        unit="bytes",
                        description="Total bytes sent over network"
                    ),
                    Metric(
                        name="network_bytes_recv",
                        value=net_io.bytes_recv,
                        metric_type=MetricType.COUNTER,
                        unit="bytes",
                        description="Total bytes received over network"
                    ),
                    Metric(
                        name="network_packets_sent",
                        value=net_io.packets_sent,
                        metric_type=MetricType.COUNTER,
                        description="Total packets sent over network"
                    ),
                    Metric(
                        name="network_packets_recv",
                        value=net_io.packets_recv,
                        metric_type=MetricType.COUNTER,
                        description="Total packets received over network"
                    )
                ])
                
        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {e}")
        
        return metrics


class ApplicationMetricsCollector:
    """Collects application-specific metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger("metrics.application")
        self.request_metrics = defaultdict(list)
        self.operation_timers = {}
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
    
    def record_request(self, endpoint: str, duration: float, status_code: int = 200):
        """Record an API request metric"""
        self.request_metrics[endpoint].append({
            'duration': duration,
            'status_code': status_code,
            'timestamp': time.time()
        })
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = f"{name}:{self._serialize_labels(labels or {})}"
        self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value"""
        key = f"{name}:{self._serialize_labels(labels or {})}"
        self.gauges[key] = value
    
    @contextmanager
    def timer(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            key = f"{name}:{self._serialize_labels(labels or {})}"
            if key not in self.operation_timers:
                self.operation_timers[key] = []
            self.operation_timers[key].append(duration)
    
    def collect_metrics(self) -> List[Metric]:
        """Collect all application metrics"""
        metrics = []
        
        # Request metrics
        for endpoint, requests in self.request_metrics.items():
            if requests:
                durations = [r['duration'] for r in requests]
                avg_duration = sum(durations) / len(durations)
                
                metrics.extend([
                    Metric(
                        name="http_request_duration_avg",
                        value=avg_duration,
                        metric_type=MetricType.GAUGE,
                        labels={"endpoint": endpoint},
                        unit="seconds",
                        description=f"Average request duration for {endpoint}"
                    ),
                    Metric(
                        name="http_request_count",
                        value=len(requests),
                        metric_type=MetricType.COUNTER,
                        labels={"endpoint": endpoint},
                        description=f"Total requests for {endpoint}"
                    )
                ])
        
        # Counter metrics
        for key, value in self.counters.items():
            name, labels_str = key.split(':', 1)
            labels = self._deserialize_labels(labels_str)
            metrics.append(Metric(
                name=name,
                value=value,
                metric_type=MetricType.COUNTER,
                labels=labels
            ))
        
        # Gauge metrics
        for key, value in self.gauges.items():
            name, labels_str = key.split(':', 1)
            labels = self._deserialize_labels(labels_str)
            metrics.append(Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                labels=labels
            ))
        
        # Timer metrics
        for key, durations in self.operation_timers.items():
            if durations:
                name, labels_str = key.split(':', 1)
                labels = self._deserialize_labels(labels_str)
                
                avg_duration = sum(durations) / len(durations)
                metrics.append(Metric(
                    name=f"{name}_duration_avg",
                    value=avg_duration,
                    metric_type=MetricType.GAUGE,
                    labels=labels,
                    unit="seconds",
                    description=f"Average duration for {name}"
                ))
        
        return metrics
    
    def _serialize_labels(self, labels: Dict[str, str]) -> str:
        """Serialize labels to string"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    def _deserialize_labels(self, labels_str: str) -> Dict[str, str]:
        """Deserialize labels from string"""
        if not labels_str:
            return {}
        labels = {}
        for pair in labels_str.split(','):
            if '=' in pair:
                k, v = pair.split('=', 1)
                labels[k] = v
        return labels


class MetricsCollector:
    """Main metrics collector orchestrating all metric collection"""
    
    def __init__(self, collection_interval: float = 10.0):
        """
        Initialize metrics collector
        
        Args:
            collection_interval: Interval between metric collections in seconds
        """
        self.logger = logging.getLogger("metrics")
        self.collection_interval = collection_interval
        self.enabled = True
        
        # Storage
        self.storage = MetricsStorage()
        
        # Collectors
        self.system_collector = SystemMetricsCollector()
        self.application_collector = ApplicationMetricsCollector()
        
        # Collection thread
        self.collection_thread = None
        self.stop_event = threading.Event()
        
        # Callbacks
        self.metric_callbacks: List[Callable[[Metric], None]] = []
    
    def start_collection(self):
        """Start automatic metric collection"""
        if self.collection_thread and self.collection_thread.is_alive():
            self.logger.warning("Metrics collection already running")
            return
        
        self.stop_event.clear()
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        self.logger.info(f"Started metrics collection with {self.collection_interval}s interval")
    
    def stop_collection(self):
        """Stop automatic metric collection"""
        self.stop_event.set()
        if self.collection_thread:
            self.collection_thread.join(timeout=5.0)
        self.logger.info("Stopped metrics collection")
    
    def collect_metric(self, name: str, value: float, metric_type: MetricType,
                      labels: Dict[str, str] = None, unit: str = "",
                      description: str = ""):
        """Collect a single metric manually"""
        if not self.enabled:
            return
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
            unit=unit,
            description=description
        )
        
        self._process_metric(metric)
    
    def get_metric_series(self, name: str, labels: Dict[str, str] = None) -> Optional[MetricSeries]:
        """Get metric series by name and labels"""
        return self.storage.get_series(name, labels)
    
    def get_all_metrics(self) -> Dict[str, MetricSeries]:
        """Get all metric series"""
        return self.storage.get_all_series()
    
    def add_metric_callback(self, callback: Callable[[Metric], None]):
        """Add callback to be called for each metric"""
        self.metric_callbacks.append(callback)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        all_series = self.storage.get_all_series()
        
        summary = {
            'total_series': len(all_series),
            'collection_enabled': self.enabled,
            'collection_interval': self.collection_interval,
            'metrics_by_type': defaultdict(int)
        }
        
        for series in all_series.values():
            summary['metrics_by_type'][series.metric_type.value] += 1
        
        return summary
    
    def _collection_loop(self):
        """Main collection loop"""
        while not self.stop_event.wait(self.collection_interval):
            if not self.enabled:
                continue
            
            try:
                self._collect_all_metrics()
            except Exception as e:
                self.logger.error(f"Error in metrics collection: {e}")
    
    def _collect_all_metrics(self):
        """Collect metrics from all collectors"""
        all_metrics = []
        
        # System metrics
        all_metrics.extend(self.system_collector.collect_cpu_metrics())
        all_metrics.extend(self.system_collector.collect_memory_metrics())
        all_metrics.extend(self.system_collector.collect_disk_metrics())
        all_metrics.extend(self.system_collector.collect_network_metrics())
        
        # Application metrics
        all_metrics.extend(self.application_collector.collect_metrics())
        
        # Process all metrics
        for metric in all_metrics:
            self._process_metric(metric)
    
    def _process_metric(self, metric: Metric):
        """Process a single metric"""
        # Store in time series
        self.storage.store_metric(metric)
        
        # Call callbacks
        for callback in self.metric_callbacks:
            try:
                callback(metric)
            except Exception as e:
                self.logger.error(f"Error in metric callback: {e}")
        
        # Log debug info
        self.logger.debug(f"Collected metric: {metric.name} = {metric.value} {metric.unit}")
    
    # Convenience methods for application metrics
    def record_request(self, endpoint: str, duration: float, status_code: int = 200):
        """Record an API request metric"""
        self.application_collector.record_request(endpoint, duration, status_code)
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        self.application_collector.increment_counter(name, value, labels)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value"""
        self.application_collector.set_gauge(name, value, labels)
    
    def timer(self, name: str, labels: Dict[str, str] = None):
        """Get timer context manager"""
        return self.application_collector.timer(name, labels) 