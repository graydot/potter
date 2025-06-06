#!/usr/bin/env python3
"""
Resource Tracker
Detailed system resource monitoring and analysis
"""

import time
import threading
import logging
import psutil
import gc
import sys
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """Resource usage snapshot"""
    timestamp: float = field(default_factory=time.time)
    
    # CPU metrics
    cpu_percent: float = 0.0
    cpu_per_core: List[float] = field(default_factory=list)
    load_average: List[float] = field(default_factory=list)
    cpu_context_switches: int = 0
    cpu_interrupts: int = 0
    
    # Memory metrics
    memory_total: int = 0
    memory_available: int = 0
    memory_used: int = 0
    memory_free: int = 0
    memory_percent: float = 0.0
    memory_buffers: int = 0
    memory_cached: int = 0
    
    # Swap metrics
    swap_total: int = 0
    swap_used: int = 0
    swap_free: int = 0
    swap_percent: float = 0.0
    
    # Process metrics
    process_memory_rss: int = 0
    process_memory_vms: int = 0
    process_memory_percent: float = 0.0
    process_cpu_percent: float = 0.0
    process_num_threads: int = 0
    process_num_fds: int = 0
    
    # Disk metrics
    disk_usage_total: int = 0
    disk_usage_used: int = 0
    disk_usage_free: int = 0
    disk_usage_percent: float = 0.0
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    disk_read_count: int = 0
    disk_write_count: int = 0
    
    # Network metrics
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    network_packets_sent: int = 0
    network_packets_recv: int = 0
    network_connections: int = 0
    
    # Python-specific metrics
    gc_objects: int = 0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    python_memory_usage: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'timestamp': self.timestamp,
            'cpu': {
                'percent': self.cpu_percent,
                'per_core': self.cpu_per_core,
                'load_average': self.load_average,
                'context_switches': self.cpu_context_switches,
                'interrupts': self.cpu_interrupts
            },
            'memory': {
                'total': self.memory_total,
                'available': self.memory_available,
                'used': self.memory_used,
                'free': self.memory_free,
                'percent': self.memory_percent,
                'buffers': self.memory_buffers,
                'cached': self.memory_cached
            },
            'swap': {
                'total': self.swap_total,
                'used': self.swap_used,
                'free': self.swap_free,
                'percent': self.swap_percent
            },
            'process': {
                'memory_rss': self.process_memory_rss,
                'memory_vms': self.process_memory_vms,
                'memory_percent': self.process_memory_percent,
                'cpu_percent': self.process_cpu_percent,
                'num_threads': self.process_num_threads,
                'num_fds': self.process_num_fds
            },
            'disk': {
                'usage_total': self.disk_usage_total,
                'usage_used': self.disk_usage_used,
                'usage_free': self.disk_usage_free,
                'usage_percent': self.disk_usage_percent,
                'read_bytes': self.disk_read_bytes,
                'write_bytes': self.disk_write_bytes,
                'read_count': self.disk_read_count,
                'write_count': self.disk_write_count
            },
            'network': {
                'bytes_sent': self.network_bytes_sent,
                'bytes_recv': self.network_bytes_recv,
                'packets_sent': self.network_packets_sent,
                'packets_recv': self.network_packets_recv,
                'connections': self.network_connections
            },
            'python': {
                'gc_objects': self.gc_objects,
                'gc_collections': self.gc_collections,
                'memory_usage': self.python_memory_usage
            }
        }


@dataclass
class ResourceAlert:
    """Resource usage alert"""
    resource_type: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str
    message: str
    timestamp: float = field(default_factory=time.time)


class ResourceAnalyzer:
    """Analyzes resource usage patterns and trends"""
    
    def __init__(self):
        self.logger = logging.getLogger("resource.analyzer")
    
    def analyze_resource_trends(self, usage_history: List[ResourceUsage], 
                              window_size: int = 20) -> Dict[str, Any]:
        """Analyze resource usage trends"""
        if len(usage_history) < window_size:
            return {'status': 'insufficient_data'}
        
        recent_usage = usage_history[-window_size:]
        
        # CPU trend analysis
        cpu_values = [u.cpu_percent for u in recent_usage]
        cpu_trend = self._calculate_trend(cpu_values)
        
        # Memory trend analysis
        memory_values = [u.memory_percent for u in recent_usage]
        memory_trend = self._calculate_trend(memory_values)
        
        # Process memory trend analysis
        process_memory_values = [u.process_memory_rss for u in recent_usage]
        process_memory_trend = self._calculate_trend(process_memory_values)
        
        return {
            'status': 'analyzed',
            'window_size': window_size,
            'trends': {
                'cpu': cpu_trend,
                'memory': memory_trend,
                'process_memory': process_memory_trend
            },
            'analysis_timestamp': time.time()
        }
    
    def detect_memory_leaks(self, usage_history: List[ResourceUsage]) -> Dict[str, Any]:
        """Detect potential memory leaks"""
        if len(usage_history) < 10:
            return {'status': 'insufficient_data'}
        
        # Analyze process memory growth over time
        memory_values = [u.process_memory_rss for u in usage_history]
        
        # Look for consistent upward trend
        trend = self._calculate_trend(memory_values)
        
        # Check for significant growth
        start_memory = memory_values[0]
        end_memory = memory_values[-1]
        growth_percent = ((end_memory - start_memory) / start_memory) * 100 if start_memory > 0 else 0
        
        # Memory leak indicators
        leak_indicators = []
        
        if trend['slope'] > 0 and trend['correlation'] > 0.7:
            leak_indicators.append('consistent_upward_trend')
        
        if growth_percent > 50:  # More than 50% growth
            leak_indicators.append('significant_growth')
        
        # Check GC behavior
        gc_values = [len(u.gc_collections) for u in usage_history if u.gc_collections]
        if gc_values and len(gc_values) > 5:
            gc_trend = self._calculate_trend(gc_values)
            if gc_trend['slope'] > 0:
                leak_indicators.append('increasing_gc_activity')
        
        leak_probability = min(len(leak_indicators) / 3.0, 1.0)  # Normalize to 0-1
        
        return {
            'status': 'analyzed',
            'leak_probability': leak_probability,
            'indicators': leak_indicators,
            'memory_growth_percent': growth_percent,
            'trend_analysis': trend,
            'recommendation': self._get_memory_leak_recommendation(leak_probability)
        }
    
    def analyze_resource_efficiency(self, usage_history: List[ResourceUsage]) -> Dict[str, Any]:
        """Analyze resource usage efficiency"""
        if not usage_history:
            return {'status': 'no_data'}
        
        # Calculate averages
        avg_cpu = sum(u.cpu_percent for u in usage_history) / len(usage_history)
        avg_memory = sum(u.memory_percent for u in usage_history) / len(usage_history)
        
        # Calculate peak usage
        peak_cpu = max(u.cpu_percent for u in usage_history)
        peak_memory = max(u.memory_percent for u in usage_history)
        
        # Calculate efficiency scores (lower is better for resource usage)
        cpu_efficiency = self._calculate_efficiency_score(avg_cpu, peak_cpu)
        memory_efficiency = self._calculate_efficiency_score(avg_memory, peak_memory)
        
        # Overall efficiency
        overall_efficiency = (cpu_efficiency + memory_efficiency) / 2
        
        return {
            'status': 'analyzed',
            'averages': {
                'cpu_percent': avg_cpu,
                'memory_percent': avg_memory
            },
            'peaks': {
                'cpu_percent': peak_cpu,
                'memory_percent': peak_memory
            },
            'efficiency_scores': {
                'cpu': cpu_efficiency,
                'memory': memory_efficiency,
                'overall': overall_efficiency
            },
            'recommendations': self._get_efficiency_recommendations(cpu_efficiency, memory_efficiency)
        }
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """Calculate trend using simple linear regression"""
        n = len(values)
        if n < 2:
            return {'slope': 0.0, 'correlation': 0.0}
        
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0.0
        
        # Calculate correlation coefficient
        x_var = sum((x[i] - x_mean) ** 2 for i in range(n))
        y_var = sum((values[i] - y_mean) ** 2 for i in range(n))
        correlation = numerator / ((x_var * y_var) ** 0.5) if x_var * y_var > 0 else 0.0
        
        return {'slope': slope, 'correlation': correlation}
    
    def _calculate_efficiency_score(self, avg_usage: float, peak_usage: float) -> float:
        """Calculate efficiency score (0-100, where 100 is most efficient)"""
        if peak_usage == 0:
            return 100.0
        
        # Efficiency is better when average is close to peak (consistent usage)
        # and when overall usage is not too high
        consistency_score = (avg_usage / peak_usage) * 100
        usage_score = max(0, 100 - avg_usage)  # Lower usage is better
        
        return (consistency_score + usage_score) / 2
    
    def _get_memory_leak_recommendation(self, leak_probability: float) -> str:
        """Get memory leak recommendation based on probability"""
        if leak_probability > 0.7:
            return "High probability of memory leak. Investigate object retention and garbage collection."
        elif leak_probability > 0.4:
            return "Possible memory leak. Monitor memory usage patterns closely."
        else:
            return "Memory usage appears normal."
    
    def _get_efficiency_recommendations(self, cpu_efficiency: float, 
                                      memory_efficiency: float) -> List[str]:
        """Get efficiency improvement recommendations"""
        recommendations = []
        
        if cpu_efficiency < 60:
            recommendations.append("Consider optimizing CPU-intensive operations")
        
        if memory_efficiency < 60:
            recommendations.append("Consider optimizing memory usage patterns")
        
        if cpu_efficiency < 40 or memory_efficiency < 40:
            recommendations.append("System may be under-resourced or inefficiently utilized")
        
        return recommendations


class ResourceTracker:
    """
    Comprehensive resource tracking system
    
    Features:
    - Detailed system resource monitoring
    - Process-specific resource tracking
    - Python runtime metrics
    - Resource trend analysis
    - Memory leak detection
    - Resource efficiency analysis
    """
    
    def __init__(self, tracking_interval: float = 5.0, history_size: int = 1000):
        """
        Initialize resource tracker
        
        Args:
            tracking_interval: Resource tracking interval in seconds
            history_size: Maximum number of resource snapshots to keep
        """
        self.logger = logging.getLogger("resource.tracker")
        self.tracking_interval = tracking_interval
        self.history_size = history_size
        
        # State
        self.enabled = False
        self.tracking_thread = None
        self.stop_event = threading.Event()
        
        # Resource data
        self.usage_history: deque[ResourceUsage] = deque(maxlen=history_size)
        self.resource_alerts: List[ResourceAlert] = []
        
        # System info
        self.process = psutil.Process()
        self.boot_time = psutil.boot_time()
        
        # Analysis
        self.analyzer = ResourceAnalyzer()
        
        # Thresholds
        self.alert_thresholds = {
            'cpu_percent': 90.0,
            'memory_percent': 95.0,
            'disk_usage_percent': 90.0,
            'process_memory_growth': 200.0  # 200% growth threshold
        }
    
    def start_tracking(self):
        """Start resource tracking"""
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.logger.warning("Resource tracking already running")
            return
        
        self.stop_event.clear()
        self.enabled = True
        self.tracking_thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self.tracking_thread.start()
        
        self.logger.info(f"Started resource tracking with {self.tracking_interval}s interval")
    
    def stop_tracking(self):
        """Stop resource tracking"""
        self.enabled = False
        self.stop_event.set()
        
        if self.tracking_thread:
            self.tracking_thread.join(timeout=5.0)
        
        self.logger.info("Stopped resource tracking")
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage snapshot"""
        usage = ResourceUsage()
        
        try:
            # CPU metrics
            usage.cpu_percent = psutil.cpu_percent(interval=None)
            usage.cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
            
            # Load average (Unix systems)
            try:
                import os
                if hasattr(os, 'getloadavg'):
                    usage.load_average = list(os.getloadavg())
            except:
                pass
            
            # CPU stats
            cpu_stats = psutil.cpu_stats()
            usage.cpu_context_switches = cpu_stats.ctx_switches
            usage.cpu_interrupts = cpu_stats.interrupts
            
            # Memory metrics
            memory = psutil.virtual_memory()
            usage.memory_total = memory.total
            usage.memory_available = memory.available
            usage.memory_used = memory.used
            usage.memory_free = memory.free
            usage.memory_percent = memory.percent
            
            if hasattr(memory, 'buffers'):
                usage.memory_buffers = memory.buffers
            if hasattr(memory, 'cached'):
                usage.memory_cached = memory.cached
            
            # Swap metrics
            swap = psutil.swap_memory()
            usage.swap_total = swap.total
            usage.swap_used = swap.used
            usage.swap_free = swap.free
            usage.swap_percent = swap.percent
            
            # Process metrics
            proc_memory = self.process.memory_info()
            usage.process_memory_rss = proc_memory.rss
            usage.process_memory_vms = proc_memory.vms
            usage.process_memory_percent = self.process.memory_percent()
            usage.process_cpu_percent = self.process.cpu_percent()
            usage.process_num_threads = self.process.num_threads()
            
            # File descriptors (Unix systems)
            try:
                usage.process_num_fds = self.process.num_fds()
            except:
                usage.process_num_fds = 0
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            usage.disk_usage_total = disk_usage.total
            usage.disk_usage_used = disk_usage.used
            usage.disk_usage_free = disk_usage.free
            usage.disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                usage.disk_read_bytes = disk_io.read_bytes
                usage.disk_write_bytes = disk_io.write_bytes
                usage.disk_read_count = disk_io.read_count
                usage.disk_write_count = disk_io.write_count
            
            # Network metrics
            net_io = psutil.net_io_counters()
            if net_io:
                usage.network_bytes_sent = net_io.bytes_sent
                usage.network_bytes_recv = net_io.bytes_recv
                usage.network_packets_sent = net_io.packets_sent
                usage.network_packets_recv = net_io.packets_recv
            
            # Network connections
            try:
                connections = psutil.net_connections()
                usage.network_connections = len(connections)
            except:
                usage.network_connections = 0
            
            # Python-specific metrics
            usage.gc_objects = len(gc.get_objects())
            usage.gc_collections = {i: gc.get_count()[i] for i in range(3)}
            usage.python_memory_usage = sys.getsizeof(gc.get_objects())
            
        except Exception as e:
            self.logger.error(f"Error collecting resource usage: {e}")
        
        return usage
    
    def get_usage_history(self, duration_minutes: int = None) -> List[ResourceUsage]:
        """Get resource usage history"""
        if duration_minutes is None:
            return list(self.usage_history)
        
        cutoff_time = time.time() - (duration_minutes * 60)
        return [usage for usage in self.usage_history if usage.timestamp >= cutoff_time]
    
    def get_resource_summary(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get resource usage summary for specified duration"""
        history = self.get_usage_history(duration_minutes)
        
        if not history:
            return {'error': 'No resource data available'}
        
        # Calculate averages and peaks
        summary = {
            'duration_minutes': duration_minutes,
            'sample_count': len(history),
            'averages': {
                'cpu_percent': sum(u.cpu_percent for u in history) / len(history),
                'memory_percent': sum(u.memory_percent for u in history) / len(history),
                'disk_usage_percent': sum(u.disk_usage_percent for u in history) / len(history),
                'process_memory_mb': sum(u.process_memory_rss for u in history) / len(history) / (1024 * 1024),
                'process_cpu_percent': sum(u.process_cpu_percent for u in history) / len(history)
            },
            'peaks': {
                'cpu_percent': max(u.cpu_percent for u in history),
                'memory_percent': max(u.memory_percent for u in history),
                'disk_usage_percent': max(u.disk_usage_percent for u in history),
                'process_memory_mb': max(u.process_memory_rss for u in history) / (1024 * 1024),
                'process_cpu_percent': max(u.process_cpu_percent for u in history)
            },
            'timestamp': time.time()
        }
        
        # Add trend analysis
        trend_analysis = self.analyzer.analyze_resource_trends(history)
        summary['trends'] = trend_analysis
        
        # Add memory leak detection
        leak_analysis = self.analyzer.detect_memory_leaks(history)
        summary['memory_leak_analysis'] = leak_analysis
        
        # Add efficiency analysis
        efficiency_analysis = self.analyzer.analyze_resource_efficiency(history)
        summary['efficiency_analysis'] = efficiency_analysis
        
        return summary
    
    def get_alerts(self) -> List[ResourceAlert]:
        """Get resource alerts"""
        return self.resource_alerts.copy()
    
    def clear_alerts(self):
        """Clear all resource alerts"""
        self.resource_alerts.clear()
    
    def set_alert_threshold(self, metric: str, threshold: float):
        """Set alert threshold for a metric"""
        self.alert_thresholds[metric] = threshold
        self.logger.debug(f"Set alert threshold for {metric}: {threshold}")
    
    def _tracking_loop(self):
        """Main resource tracking loop"""
        while not self.stop_event.wait(self.tracking_interval):
            if not self.enabled:
                continue
            
            try:
                # Collect current resource usage
                usage = self.get_current_usage()
                self.usage_history.append(usage)
                
                # Check for alerts
                self._check_resource_alerts(usage)
                
                self.logger.debug(f"Resource usage: CPU={usage.cpu_percent:.1f}% "
                                f"Memory={usage.memory_percent:.1f}% "
                                f"Process Memory={usage.process_memory_rss/(1024*1024):.1f}MB")
                
            except Exception as e:
                self.logger.error(f"Error in resource tracking loop: {e}")
    
    def _check_resource_alerts(self, usage: ResourceUsage):
        """Check for resource usage alerts"""
        alerts = []
        
        # CPU usage alert
        if usage.cpu_percent > self.alert_thresholds.get('cpu_percent', 90):
            alerts.append(ResourceAlert(
                resource_type='cpu',
                metric_name='cpu_percent',
                current_value=usage.cpu_percent,
                threshold_value=self.alert_thresholds['cpu_percent'],
                severity='critical',
                message=f"High CPU usage: {usage.cpu_percent:.1f}%"
            ))
        
        # Memory usage alert
        if usage.memory_percent > self.alert_thresholds.get('memory_percent', 95):
            alerts.append(ResourceAlert(
                resource_type='memory',
                metric_name='memory_percent',
                current_value=usage.memory_percent,
                threshold_value=self.alert_thresholds['memory_percent'],
                severity='critical',
                message=f"High memory usage: {usage.memory_percent:.1f}%"
            ))
        
        # Disk usage alert
        if usage.disk_usage_percent > self.alert_thresholds.get('disk_usage_percent', 90):
            alerts.append(ResourceAlert(
                resource_type='disk',
                metric_name='disk_usage_percent',
                current_value=usage.disk_usage_percent,
                threshold_value=self.alert_thresholds['disk_usage_percent'],
                severity='warning',
                message=f"High disk usage: {usage.disk_usage_percent:.1f}%"
            ))
        
        # Process memory growth alert
        if len(self.usage_history) > 10:
            initial_memory = self.usage_history[0].process_memory_rss
            current_memory = usage.process_memory_rss
            if initial_memory > 0:
                growth_percent = ((current_memory - initial_memory) / initial_memory) * 100
                threshold = self.alert_thresholds.get('process_memory_growth', 200)
                
                if growth_percent > threshold:
                    alerts.append(ResourceAlert(
                        resource_type='process',
                        metric_name='memory_growth',
                        current_value=growth_percent,
                        threshold_value=threshold,
                        severity='warning',
                        message=f"High process memory growth: {growth_percent:.1f}%"
                    ))
        
        # Add new alerts
        for alert in alerts:
            self.resource_alerts.append(alert)
            self.logger.warning(f"Resource alert: {alert.message}")
        
        # Limit alert history
        if len(self.resource_alerts) > 100:
            self.resource_alerts = self.resource_alerts[-50:]  # Keep last 50 alerts 