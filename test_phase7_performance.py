#!/usr/bin/env python3
"""
Phase 7 Performance Optimization & Monitoring Tests
Comprehensive test suite for performance monitoring system
"""

import os
import time
import tempfile
import unittest
import threading
from unittest.mock import Mock, patch, MagicMock

# Install psutil for testing if not available
try:
    import psutil
except ImportError:
    os.system("pip install psutil")
    import psutil

# Import performance components
from src.performance.metrics_collector import (
    MetricsCollector, Metric, MetricType, MetricsStorage, 
    SystemMetricsCollector, ApplicationMetricsCollector
)
from src.performance.performance_monitor import (
    PerformanceMonitor, PerformanceSnapshot, PerformanceThreshold,
    PerformanceAlert, PerformanceAnalyzer
)
from src.performance.resource_tracker import (
    ResourceTracker, ResourceUsage, ResourceAlert, ResourceAnalyzer
)


class TestMetricsCollector(unittest.TestCase):
    """Test metrics collection functionality"""
    
    def setUp(self):
        self.collector = MetricsCollector(collection_interval=0.1)
    
    def tearDown(self):
        if self.collector.collection_thread and self.collector.collection_thread.is_alive():
            self.collector.stop_collection()
    
    def test_metric_creation(self):
        """Test metric creation and storage"""
        metric = Metric(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.GAUGE,
            labels={"service": "test"},
            unit="bytes"
        )
        
        self.assertEqual(metric.name, "test_metric")
        self.assertEqual(metric.value, 42.0)
        self.assertEqual(metric.metric_type, MetricType.GAUGE)
        self.assertEqual(metric.labels["service"], "test")
        self.assertEqual(metric.unit, "bytes")
    
    def test_metrics_storage(self):
        """Test metrics storage and retrieval"""
        storage = MetricsStorage(max_series=10, max_points_per_series=5)
        
        # Store metrics
        for i in range(10):
            metric = Metric(
                name="test_counter",
                value=float(i),
                metric_type=MetricType.COUNTER
            )
            storage.store_metric(metric)
        
        # Retrieve series
        series = storage.get_series("test_counter")
        self.assertIsNotNone(series)
        self.assertEqual(len(series.values), 5)  # Limited by max_points_per_series
        self.assertEqual(series.get_latest(), 9.0)
    
    def test_system_metrics_collection(self):
        """Test system metrics collection"""
        system_collector = SystemMetricsCollector()
        
        # Test CPU metrics
        cpu_metrics = system_collector.collect_cpu_metrics()
        self.assertGreater(len(cpu_metrics), 0)
        
        # Find system CPU usage metric
        cpu_metric = next((m for m in cpu_metrics if m.name == "system_cpu_usage_percent" and not m.labels), None)
        self.assertIsNotNone(cpu_metric)
        self.assertGreaterEqual(cpu_metric.value, 0.0)
        self.assertLessEqual(cpu_metric.value, 100.0)
        
        # Test memory metrics
        memory_metrics = system_collector.collect_memory_metrics()
        self.assertGreater(len(memory_metrics), 0)
        
        # Find system memory usage metric
        memory_metric = next((m for m in memory_metrics if m.name == "system_memory_total"), None)
        self.assertIsNotNone(memory_metric)
        self.assertGreater(memory_metric.value, 0)
    
    def test_application_metrics(self):
        """Test application metrics collection"""
        app_collector = ApplicationMetricsCollector()
        
        # Record some test metrics
        app_collector.record_request("/api/test", 0.1, 200)
        app_collector.increment_counter("test_counter", 5)
        app_collector.set_gauge("test_gauge", 42.0)
        
        # Test timer context manager
        with app_collector.timer("test_operation"):
            time.sleep(0.01)  # Simulate work
        
        # Collect metrics
        metrics = app_collector.collect_metrics()
        self.assertGreater(len(metrics), 0)
        
        # Check that we have different types of metrics
        metric_names = [m.name for m in metrics]
        self.assertIn("test_counter", metric_names)
        self.assertIn("test_gauge", metric_names)
    
    def test_metrics_collector_lifecycle(self):
        """Test metrics collector start/stop lifecycle"""
        # Start collection
        self.collector.start_collection()
        self.assertTrue(self.collector.collection_thread.is_alive())
        
        # Wait a bit for collection
        time.sleep(0.2)
        
        # Check that metrics are being collected
        all_metrics = self.collector.get_all_metrics()
        self.assertGreater(len(all_metrics), 0)
        
        # Stop collection
        self.collector.stop_collection()
        self.assertFalse(self.collector.collection_thread.is_alive())
    
    def test_manual_metric_collection(self):
        """Test manual metric collection"""
        self.collector.collect_metric(
            name="manual_test",
            value=100.0,
            metric_type=MetricType.GAUGE,
            labels={"type": "manual"},
            unit="count"
        )
        
        # Retrieve the metric
        series = self.collector.get_metric_series("manual_test", {"type": "manual"})
        self.assertIsNotNone(series)
        self.assertEqual(series.get_latest(), 100.0)


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring functionality"""
    
    def setUp(self):
        self.metrics_collector = MetricsCollector(collection_interval=0.1)
        self.monitor = PerformanceMonitor(self.metrics_collector, monitoring_interval=0.1)
    
    def tearDown(self):
        if self.monitor.enabled:
            self.monitor.stop_monitoring()
        if self.metrics_collector.collection_thread and self.metrics_collector.collection_thread.is_alive():
            self.metrics_collector.stop_collection()
    
    def test_performance_snapshot(self):
        """Test performance snapshot creation"""
        # Start metrics collection to have some data
        self.metrics_collector.start_collection()
        time.sleep(0.2)  # Let it collect some metrics
        
        snapshot = self.monitor.get_current_snapshot()
        
        self.assertIsInstance(snapshot, PerformanceSnapshot)
        self.assertGreaterEqual(snapshot.cpu_usage, 0.0)
        self.assertGreaterEqual(snapshot.memory_usage, 0.0)
        self.assertGreater(snapshot.timestamp, 0)
    
    def test_performance_thresholds(self):
        """Test performance threshold management"""
        threshold = PerformanceThreshold(
            metric_name="test_metric_unique",
            warning_threshold=70.0,
            critical_threshold=90.0,
            comparison=">",
            description="Test metric"
        )
        
        # Add threshold
        initial_count = len(self.monitor.thresholds)
        self.monitor.add_threshold(threshold)
        self.assertEqual(len(self.monitor.thresholds), initial_count + 1)
        
        # Remove threshold
        self.monitor.remove_threshold("test_metric_unique")
        self.assertEqual(len(self.monitor.thresholds), initial_count)
    
    def test_performance_monitoring_lifecycle(self):
        """Test performance monitoring start/stop"""
        # Start monitoring
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.enabled)
        self.assertTrue(self.monitor.monitoring_thread.is_alive())
        
        # Wait for some monitoring
        time.sleep(0.2)
        
        # Check that snapshots are being collected
        self.assertGreater(len(self.monitor.snapshots), 0)
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.enabled)
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        # Create some mock snapshots
        for i in range(5):
            snapshot = PerformanceSnapshot(
                timestamp=time.time() - (60 - i * 10),  # Spread over last minute
                cpu_usage=20.0 + i * 5,
                memory_usage=30.0 + i * 3,
                throughput=100.0 + i * 10
            )
            self.monitor.snapshots.append(snapshot)
        
        summary = self.monitor.get_performance_summary(duration_minutes=1)
        
        self.assertIn('averages', summary)
        self.assertIn('trends', summary)
        self.assertIn('percentiles', summary)
        self.assertGreater(summary['averages']['cpu_usage'], 0)
        self.assertGreater(summary['averages']['memory_usage'], 0)
    
    def test_performance_analyzer(self):
        """Test performance trend analysis"""
        analyzer = PerformanceAnalyzer()
        
        # Test trend analysis with increasing values
        increasing_values = [10.0, 15.0, 20.0, 25.0, 30.0]
        trend = analyzer.analyze_trend(increasing_values)
        
        self.assertEqual(trend['trend'], 'increasing')
        self.assertGreater(trend['slope'], 0)
        
        # Test anomaly detection
        normal_values = [10.0, 12.0, 11.0, 13.0, 50.0, 12.0, 11.0]  # 50.0 is anomaly
        anomalies = analyzer.detect_anomalies(normal_values, threshold=2.0)
        
        self.assertGreater(len(anomalies), 0)
        self.assertIn(4, anomalies)  # Index of the anomaly (50.0)
        
        # Test percentiles calculation
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        percentiles = analyzer.calculate_percentiles(values)
        
        self.assertIn('p50', percentiles)
        self.assertIn('p95', percentiles)
        self.assertAlmostEqual(percentiles['p50'], 5.0, delta=1.0)


class TestResourceTracker(unittest.TestCase):
    """Test resource tracking functionality"""
    
    def setUp(self):
        self.tracker = ResourceTracker(tracking_interval=0.1, history_size=10)
    
    def tearDown(self):
        if self.tracker.enabled:
            self.tracker.stop_tracking()
    
    def test_resource_usage_collection(self):
        """Test resource usage data collection"""
        usage = self.tracker.get_current_usage()
        
        self.assertIsInstance(usage, ResourceUsage)
        self.assertGreaterEqual(usage.cpu_percent, 0.0)
        self.assertLessEqual(usage.cpu_percent, 100.0)
        self.assertGreater(usage.memory_total, 0)
        self.assertGreaterEqual(usage.memory_percent, 0.0)
        self.assertLessEqual(usage.memory_percent, 100.0)
        self.assertGreater(usage.process_memory_rss, 0)
    
    def test_resource_tracking_lifecycle(self):
        """Test resource tracking start/stop"""
        # Start tracking
        self.tracker.start_tracking()
        self.assertTrue(self.tracker.enabled)
        self.assertTrue(self.tracker.tracking_thread.is_alive())
        
        # Wait for some tracking
        time.sleep(0.2)
        
        # Check that usage history is being collected
        self.assertGreater(len(self.tracker.usage_history), 0)
        
        # Stop tracking
        self.tracker.stop_tracking()
        self.assertFalse(self.tracker.enabled)
    
    def test_resource_summary(self):
        """Test resource usage summary"""
        # Add some mock usage data
        for i in range(5):
            usage = ResourceUsage(
                timestamp=time.time() - (60 - i * 10),
                cpu_percent=20.0 + i * 5,
                memory_percent=30.0 + i * 3,
                process_memory_rss=100 * 1024 * 1024 + i * 10 * 1024 * 1024  # 100MB + growth
            )
            self.tracker.usage_history.append(usage)
        
        summary = self.tracker.get_resource_summary(duration_minutes=1)
        
        self.assertIn('averages', summary)
        self.assertIn('peaks', summary)
        self.assertIn('trends', summary)
        self.assertGreater(summary['averages']['cpu_percent'], 0)
        self.assertGreater(summary['averages']['memory_percent'], 0)
    
    def test_resource_analyzer(self):
        """Test resource analysis functionality"""
        analyzer = ResourceAnalyzer()
        
        # Create mock usage history with memory leak pattern
        usage_history = []
        for i in range(20):
            usage = ResourceUsage(
                timestamp=time.time() - (200 - i * 10),
                process_memory_rss=100 * 1024 * 1024 + i * 5 * 1024 * 1024,  # Growing memory
                cpu_percent=20.0 + (i % 5) * 2,  # Variable CPU
                memory_percent=30.0 + i * 0.5  # Slowly growing system memory
            )
            usage_history.append(usage)
        
        # Test trend analysis
        trends = analyzer.analyze_resource_trends(usage_history)
        self.assertEqual(trends['status'], 'analyzed')
        self.assertIn('trends', trends)
        
        # Test memory leak detection
        leak_analysis = analyzer.detect_memory_leaks(usage_history)
        self.assertEqual(leak_analysis['status'], 'analyzed')
        self.assertGreater(leak_analysis['leak_probability'], 0.5)  # Should detect growing memory
        
        # Test efficiency analysis
        efficiency = analyzer.analyze_resource_efficiency(usage_history)
        self.assertEqual(efficiency['status'], 'analyzed')
        self.assertIn('efficiency_scores', efficiency)
    
    def test_resource_alerts(self):
        """Test resource alert generation"""
        # Set low thresholds for testing
        self.tracker.set_alert_threshold('cpu_percent', 10.0)
        self.tracker.set_alert_threshold('memory_percent', 10.0)
        
        # Create usage that exceeds thresholds
        high_usage = ResourceUsage(
            cpu_percent=50.0,  # Above 10% threshold
            memory_percent=50.0  # Above 10% threshold
        )
        
        # Simulate checking alerts
        initial_alerts = len(self.tracker.get_alerts())
        self.tracker._check_resource_alerts(high_usage)
        
        # Should have generated alerts
        alerts = self.tracker.get_alerts()
        self.assertGreater(len(alerts), initial_alerts)


class TestPerformanceIntegration(unittest.TestCase):
    """Test integrated performance monitoring system"""
    
    def setUp(self):
        self.metrics_collector = MetricsCollector(collection_interval=0.1)
        self.performance_monitor = PerformanceMonitor(self.metrics_collector, monitoring_interval=0.1)
        self.resource_tracker = ResourceTracker(tracking_interval=0.1)
    
    def tearDown(self):
        # Clean up all components
        if self.performance_monitor.enabled:
            self.performance_monitor.stop_monitoring()
        if self.resource_tracker.enabled:
            self.resource_tracker.stop_tracking()
        if self.metrics_collector.collection_thread and self.metrics_collector.collection_thread.is_alive():
            self.metrics_collector.stop_collection()
    
    def test_integrated_monitoring_system(self):
        """Test complete integrated monitoring system"""
        # Start all components
        self.metrics_collector.start_collection()
        self.performance_monitor.start_monitoring()
        self.resource_tracker.start_tracking()
        
        # Let the system run for a bit
        time.sleep(0.3)
        
        # Verify all components are working
        self.assertTrue(self.metrics_collector.collection_thread.is_alive())
        self.assertTrue(self.performance_monitor.monitoring_thread.is_alive())
        self.assertTrue(self.resource_tracker.tracking_thread.is_alive())
        
        # Check data collection
        metrics = self.metrics_collector.get_all_metrics()
        self.assertGreater(len(metrics), 0)
        
        snapshots = self.performance_monitor.snapshots
        self.assertGreater(len(snapshots), 0)
        
        usage_history = self.resource_tracker.usage_history
        self.assertGreater(len(usage_history), 0)
        
        # Test metric callback integration
        callback_called = threading.Event()
        
        def test_callback(metric):
            callback_called.set()
        
        self.metrics_collector.add_metric_callback(test_callback)
        
        # Trigger a manual metric
        self.metrics_collector.collect_metric("test_integration", 42.0, MetricType.GAUGE)
        
        # Wait for callback
        callback_called.wait(timeout=1.0)
        self.assertTrue(callback_called.is_set())
    
    def test_performance_monitoring_with_alerts(self):
        """Test performance monitoring with alert callbacks"""
        alert_received = threading.Event()
        received_alert = None
        
        def alert_callback(alert):
            nonlocal received_alert
            received_alert = alert
            alert_received.set()
        
        # Add alert callback
        self.performance_monitor.add_alert_callback(alert_callback)
        
        # Add a threshold that will trigger
        threshold = PerformanceThreshold(
            metric_name="test_metric",
            warning_threshold=10.0,
            critical_threshold=20.0,
            comparison=">",
            window_size=1
        )
        self.performance_monitor.add_threshold(threshold)
        
        # Manually add performance history that exceeds threshold
        self.performance_monitor.performance_history["test_metric"] = [
            {'value': 50.0, 'timestamp': time.time()}  # Exceeds 10.0 threshold
        ]
        
        # Start monitoring
        self.performance_monitor.start_monitoring()
        
        # Wait a bit for threshold checking
        time.sleep(0.2)
        
        # Should have received an alert
        alert_received.wait(timeout=1.0)
        if received_alert:
            self.assertEqual(received_alert.metric_name, "test_metric")
            self.assertEqual(received_alert.severity, "critical")  # Should be critical (50 > 20)


def run_tests():
    """Run all Phase 7 performance tests"""
    test_classes = [
        TestMetricsCollector,
        TestPerformanceMonitor,
        TestResourceTracker,
        TestPerformanceIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n--- Running {test_class.__name__} ---")
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        
        if result.failures:
            failed_tests.extend([f"{test_class.__name__}: {f[0]}" for f in result.failures])
        if result.errors:
            failed_tests.extend([f"{test_class.__name__}: {e[0]}" for e in result.errors])
    
    print(f"\n{'='*60}")
    print(f"PHASE 7 PERFORMANCE MONITORING TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print(f"\nFailed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # Install required dependency
    try:
        import psutil
    except ImportError:
        print("Installing psutil dependency...")
        os.system("pip install psutil")
    
    success = run_tests()
    exit(0 if success else 1) 