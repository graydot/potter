#!/usr/bin/env python3
"""
Load Tester
Automated load testing framework for performance validation
"""

import time
import threading
import logging
import asyncio
import random
import statistics
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class LoadTestScenario:
    """Load test scenario definition"""
    name: str
    target_function: Callable
    virtual_users: int
    duration_seconds: int
    requests_per_user: int = 0  # 0 means unlimited during duration
    ramp_up_seconds: int = 0
    think_time_range: tuple = (0.1, 0.5)  # Min/max think time between requests
    request_data_generator: Optional[Callable] = None
    success_criteria: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set default success criteria"""
        if not self.success_criteria:
            self.success_criteria = {
                'max_response_time': 2.0,  # 2 seconds
                'max_error_rate': 5.0,     # 5%
                'min_throughput': 1.0      # 1 request/second
            }


@dataclass
class LoadTestResult:
    """Result of a load test execution"""
    scenario_name: str
    start_time: float
    end_time: float
    duration: float
    virtual_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    throughput: float  # requests per second
    
    # Response time statistics
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    
    # Error breakdown
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Performance metrics
    cpu_usage_during_test: List[float] = field(default_factory=list)
    memory_usage_during_test: List[float] = field(default_factory=list)
    
    # Success criteria evaluation
    success_criteria_met: bool = False
    criteria_results: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'scenario_name': self.scenario_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'virtual_users': self.virtual_users,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'error_rate': self.error_rate,
            'throughput': self.throughput,
            'response_times': {
                'average': self.avg_response_time,
                'minimum': self.min_response_time,
                'maximum': self.max_response_time,
                'p50': self.p50_response_time,
                'p95': self.p95_response_time,
                'p99': self.p99_response_time
            },
            'errors_by_type': self.errors_by_type,
            'performance_metrics': {
                'cpu_usage': self.cpu_usage_during_test,
                'memory_usage': self.memory_usage_during_test
            },
            'success_criteria_met': self.success_criteria_met,
            'criteria_results': self.criteria_results,
            'start_datetime': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_datetime': datetime.fromtimestamp(self.end_time).isoformat()
        }


@dataclass
class VirtualUser:
    """Virtual user for load testing"""
    user_id: int
    scenario: LoadTestScenario
    request_count: int = 0
    error_count: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def execute_requests(self, stop_event: threading.Event) -> Dict[str, Any]:
        """Execute requests according to scenario"""
        start_time = time.time()
        
        while not stop_event.is_set():
            # Check if we've reached the request limit
            if (self.scenario.requests_per_user > 0 and 
                self.request_count >= self.scenario.requests_per_user):
                break
            
            try:
                # Generate request data if needed
                request_data = None
                if self.scenario.request_data_generator:
                    request_data = self.scenario.request_data_generator()
                
                # Execute request with timing
                request_start = time.time()
                
                if request_data:
                    result = self.scenario.target_function(request_data)
                else:
                    result = self.scenario.target_function()
                
                request_end = time.time()
                response_time = request_end - request_start
                
                self.response_times.append(response_time)
                self.request_count += 1
                
            except Exception as e:
                self.error_count += 1
                self.errors.append(str(e))
            
            # Think time (simulate user delay)
            if not stop_event.is_set():
                think_time = random.uniform(*self.scenario.think_time_range)
                stop_event.wait(think_time)
        
        return {
            'user_id': self.user_id,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'response_times': self.response_times,
            'errors': self.errors,
            'duration': time.time() - start_time
        }


class BenchmarkSuite:
    """Performance benchmarking tools"""
    
    def __init__(self):
        self.logger = logging.getLogger("performance.benchmark")
        self.benchmarks: Dict[str, Callable] = {}
        self.baseline_results: Dict[str, Dict[str, float]] = {}
        self.current_results: Dict[str, Dict[str, float]] = {}
    
    def register_benchmark(self, name: str, benchmark_func: Callable, 
                          iterations: int = 100):
        """Register a performance benchmark"""
        self.benchmarks[name] = {
            'function': benchmark_func,
            'iterations': iterations
        }
        self.logger.debug(f"Registered benchmark: {name}")
    
    def run_benchmark(self, name: str) -> Dict[str, Any]:
        """Run a specific benchmark"""
        if name not in self.benchmarks:
            raise ValueError(f"Benchmark '{name}' not found")
        
        benchmark = self.benchmarks[name]
        func = benchmark['function']
        iterations = benchmark['iterations']
        
        self.logger.info(f"Running benchmark: {name} ({iterations} iterations)")
        
        execution_times = []
        errors = []
        
        for i in range(iterations):
            try:
                start_time = time.time()
                result = func()
                end_time = time.time()
                
                execution_times.append(end_time - start_time)
                
            except Exception as e:
                errors.append(str(e))
        
        if not execution_times:
            return {
                'name': name,
                'status': 'failed',
                'error': 'All iterations failed',
                'errors': errors
            }
        
        # Calculate statistics
        results = {
            'name': name,
            'status': 'completed',
            'iterations': len(execution_times),
            'errors': len(errors),
            'execution_times': {
                'average': statistics.mean(execution_times),
                'median': statistics.median(execution_times),
                'min': min(execution_times),
                'max': max(execution_times),
                'stdev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            },
            'throughput': 1.0 / statistics.mean(execution_times),  # operations per second
            'timestamp': time.time()
        }
        
        self.current_results[name] = results
        return results
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all registered benchmarks"""
        results = {}
        total_time = 0
        
        for name in self.benchmarks:
            benchmark_result = self.run_benchmark(name)
            results[name] = benchmark_result
            
            if benchmark_result['status'] == 'completed':
                total_time += benchmark_result['execution_times']['average'] * benchmark_result['iterations']
        
        return {
            'benchmarks': results,
            'total_benchmarks': len(self.benchmarks),
            'successful_benchmarks': len([r for r in results.values() if r['status'] == 'completed']),
            'total_execution_time': total_time,
            'timestamp': time.time()
        }
    
    def set_baseline(self, name: str = None):
        """Set current results as baseline"""
        if name:
            if name in self.current_results:
                self.baseline_results[name] = self.current_results[name].copy()
                self.logger.info(f"Set baseline for benchmark: {name}")
        else:
            self.baseline_results = self.current_results.copy()
            self.logger.info("Set baseline for all benchmarks")
    
    def compare_with_baseline(self, name: str = None) -> Dict[str, Any]:
        """Compare current results with baseline"""
        if name:
            if name not in self.current_results or name not in self.baseline_results:
                return {'error': f'Missing results for {name}'}
            
            current = self.current_results[name]
            baseline = self.baseline_results[name]
            
            return self._compare_benchmark_results(name, current, baseline)
        else:
            comparisons = {}
            for benchmark_name in self.current_results:
                if benchmark_name in self.baseline_results:
                    current = self.current_results[benchmark_name]
                    baseline = self.baseline_results[benchmark_name]
                    comparisons[benchmark_name] = self._compare_benchmark_results(
                        benchmark_name, current, baseline
                    )
            
            return {
                'comparisons': comparisons,
                'timestamp': time.time()
            }
    
    def _compare_benchmark_results(self, name: str, current: Dict, baseline: Dict) -> Dict[str, Any]:
        """Compare two benchmark results"""
        current_avg = current['execution_times']['average']
        baseline_avg = baseline['execution_times']['average']
        
        improvement_percent = ((baseline_avg - current_avg) / baseline_avg) * 100
        
        return {
            'benchmark': name,
            'current_average': current_avg,
            'baseline_average': baseline_avg,
            'improvement_percent': improvement_percent,
            'status': 'improved' if improvement_percent > 0 else 'degraded',
            'throughput_change': current['throughput'] - baseline['throughput']
        }


class LoadTester:
    """
    Automated load testing framework
    
    Features:
    - Multi-threaded load testing
    - Configurable virtual users
    - Ramp-up scenarios
    - Real-time monitoring
    - Success criteria validation
    - Performance benchmarking
    """
    
    def __init__(self, max_workers: int = 100):
        """
        Initialize load tester
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.logger = logging.getLogger("performance.loadtester")
        self.max_workers = max_workers
        
        # Test state
        self.active_tests: Dict[str, bool] = {}
        self.test_results: Dict[str, LoadTestResult] = {}
        
        # Components
        self.benchmark_suite = BenchmarkSuite()
        
        # Monitoring during tests
        self.monitoring_enabled = True
        self.resource_tracker = None  # Will be injected if available
    
    def create_scenario(self, name: str, target_function: Callable,
                       virtual_users: int, duration_seconds: int,
                       **kwargs) -> LoadTestScenario:
        """Create a load test scenario"""
        scenario = LoadTestScenario(
            name=name,
            target_function=target_function,
            virtual_users=virtual_users,
            duration_seconds=duration_seconds,
            **kwargs
        )
        
        self.logger.debug(f"Created scenario: {name} with {virtual_users} users for {duration_seconds}s")
        return scenario
    
    def run_load_test(self, scenario: LoadTestScenario) -> LoadTestResult:
        """Execute a load test scenario"""
        if scenario.name in self.active_tests:
            raise RuntimeError(f"Test '{scenario.name}' is already running")
        
        self.logger.info(f"Starting load test: {scenario.name}")
        self.active_tests[scenario.name] = True
        
        start_time = time.time()
        
        try:
            # Prepare virtual users
            virtual_users = [
                VirtualUser(user_id=i, scenario=scenario)
                for i in range(scenario.virtual_users)
            ]
            
            # Monitoring setup
            cpu_usage = []
            memory_usage = []
            monitor_stop_event = threading.Event()
            
            def monitor_resources():
                """Monitor system resources during test"""
                if not self.resource_tracker:
                    return
                
                while not monitor_stop_event.is_set():
                    try:
                        usage = self.resource_tracker.get_current_usage()
                        cpu_usage.append(usage.cpu_percent)
                        memory_usage.append(usage.memory_percent)
                    except:
                        pass
                    monitor_stop_event.wait(1.0)  # Sample every second
            
            # Start resource monitoring
            monitor_thread = None
            if self.monitoring_enabled and self.resource_tracker:
                monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
                monitor_thread.start()
            
            # Execute load test
            result = self._execute_load_test(scenario, virtual_users)
            
            # Stop monitoring
            if monitor_thread:
                monitor_stop_event.set()
                monitor_thread.join(timeout=1.0)
            
            # Add monitoring data to result
            result.cpu_usage_during_test = cpu_usage
            result.memory_usage_during_test = memory_usage
            
            # Evaluate success criteria
            result.success_criteria_met, result.criteria_results = self._evaluate_success_criteria(
                scenario, result
            )
            
            self.test_results[scenario.name] = result
            
            self.logger.info(f"Completed load test: {scenario.name} - "
                           f"Throughput: {result.throughput:.2f} req/s, "
                           f"Error rate: {result.error_rate:.1f}%")
            
            return result
            
        finally:
            self.active_tests.pop(scenario.name, None)
    
    def run_stress_test(self, target_function: Callable, max_users: int = 1000,
                       step_size: int = 100, step_duration: int = 60) -> Dict[str, Any]:
        """
        Run a stress test with gradually increasing load
        
        Args:
            target_function: Function to test
            max_users: Maximum number of concurrent users
            step_size: Number of users to add each step
            step_duration: Duration of each step in seconds
        """
        self.logger.info(f"Starting stress test up to {max_users} users")
        
        stress_results = []
        breaking_point = None
        
        for user_count in range(step_size, max_users + 1, step_size):
            scenario = LoadTestScenario(
                name=f"stress_test_{user_count}_users",
                target_function=target_function,
                virtual_users=user_count,
                duration_seconds=step_duration,
                success_criteria={
                    'max_response_time': 5.0,  # More lenient for stress test
                    'max_error_rate': 20.0,
                    'min_throughput': 0.1
                }
            )
            
            try:
                result = self.run_load_test(scenario)
                stress_results.append(result)
                
                # Check if we've hit the breaking point
                if (result.error_rate > 50.0 or 
                    result.avg_response_time > 10.0 or
                    not result.success_criteria_met):
                    breaking_point = user_count
                    self.logger.warning(f"Breaking point reached at {user_count} users")
                    break
                    
            except Exception as e:
                self.logger.error(f"Stress test failed at {user_count} users: {e}")
                breaking_point = user_count
                break
        
        return {
            'stress_test_results': [r.to_dict() for r in stress_results],
            'breaking_point': breaking_point,
            'max_sustainable_users': breaking_point - step_size if breaking_point else max_users,
            'test_duration': step_duration * len(stress_results),
            'timestamp': time.time()
        }
    
    def get_test_results(self, scenario_name: str = None) -> Union[LoadTestResult, Dict[str, LoadTestResult]]:
        """Get test results"""
        if scenario_name:
            return self.test_results.get(scenario_name)
        return self.test_results.copy()
    
    def clear_results(self):
        """Clear all test results"""
        self.test_results.clear()
        self.logger.info("Cleared all load test results")
    
    def set_resource_tracker(self, resource_tracker):
        """Set resource tracker for monitoring during tests"""
        self.resource_tracker = resource_tracker
        self.logger.debug("Resource tracker set for load testing")
    
    def _execute_load_test(self, scenario: LoadTestScenario, 
                          virtual_users: List[VirtualUser]) -> LoadTestResult:
        """Execute the actual load test"""
        stop_event = threading.Event()
        
        # Schedule test duration
        def stop_test():
            time.sleep(scenario.duration_seconds)
            stop_event.set()
        
        stop_timer = threading.Thread(target=stop_test, daemon=True)
        stop_timer.start()
        
        # Execute with ramp-up if specified
        if scenario.ramp_up_seconds > 0:
            results = self._execute_with_ramp_up(scenario, virtual_users, stop_event)
        else:
            results = self._execute_parallel(virtual_users, stop_event)
        
        # Aggregate results
        return self._aggregate_results(scenario, results, time.time())
    
    def _execute_parallel(self, virtual_users: List[VirtualUser], 
                         stop_event: threading.Event) -> List[Dict[str, Any]]:
        """Execute all virtual users in parallel"""
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(virtual_users))) as executor:
            futures = [
                executor.submit(user.execute_requests, stop_event)
                for user in virtual_users
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Virtual user failed: {e}")
            
            return results
    
    def _execute_with_ramp_up(self, scenario: LoadTestScenario, 
                             virtual_users: List[VirtualUser], 
                             stop_event: threading.Event) -> List[Dict[str, Any]]:
        """Execute with gradual ramp-up of users"""
        ramp_delay = scenario.ramp_up_seconds / len(virtual_users)
        
        results = []
        futures = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for i, user in enumerate(virtual_users):
                if stop_event.is_set():
                    break
                
                # Submit user with delay
                future = executor.submit(user.execute_requests, stop_event)
                futures.append(future)
                
                # Ramp-up delay
                if i < len(virtual_users) - 1:  # Don't delay after last user
                    time.sleep(ramp_delay)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Virtual user failed: {e}")
        
        return results
    
    def _aggregate_results(self, scenario: LoadTestScenario, 
                          user_results: List[Dict[str, Any]], 
                          end_time: float) -> LoadTestResult:
        """Aggregate results from all virtual users"""
        if not user_results:
            raise RuntimeError("No results from virtual users")
        
        start_time = end_time - scenario.duration_seconds
        
        # Aggregate basic metrics
        total_requests = sum(r['request_count'] for r in user_results)
        total_errors = sum(r['error_count'] for r in user_results)
        successful_requests = total_requests - total_errors
        
        # Aggregate response times
        all_response_times = []
        for result in user_results:
            all_response_times.extend(result['response_times'])
        
        if not all_response_times:
            all_response_times = [0.0]  # Prevent division by zero
        
        # Calculate statistics
        avg_response_time = statistics.mean(all_response_times)
        min_response_time = min(all_response_times)
        max_response_time = max(all_response_times)
        
        sorted_times = sorted(all_response_times)
        n = len(sorted_times)
        p50_response_time = sorted_times[int(n * 0.5)]
        p95_response_time = sorted_times[int(n * 0.95)]
        p99_response_time = sorted_times[int(n * 0.99)]
        
        # Calculate rates
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        throughput = total_requests / scenario.duration_seconds
        
        # Aggregate errors by type
        errors_by_type = defaultdict(int)
        for result in user_results:
            for error in result['errors']:
                error_type = type(error).__name__ if hasattr(error, '__class__') else 'Unknown'
                errors_by_type[error_type] += 1
        
        return LoadTestResult(
            scenario_name=scenario.name,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            virtual_users=scenario.virtual_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=total_errors,
            error_rate=error_rate,
            throughput=throughput,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            errors_by_type=dict(errors_by_type)
        )
    
    def _evaluate_success_criteria(self, scenario: LoadTestScenario, 
                                  result: LoadTestResult) -> tuple[bool, Dict[str, bool]]:
        """Evaluate success criteria"""
        criteria_results = {}
        
        # Check response time criteria
        if 'max_response_time' in scenario.success_criteria:
            criteria_results['response_time'] = (
                result.avg_response_time <= scenario.success_criteria['max_response_time']
            )
        
        # Check error rate criteria
        if 'max_error_rate' in scenario.success_criteria:
            criteria_results['error_rate'] = (
                result.error_rate <= scenario.success_criteria['max_error_rate']
            )
        
        # Check throughput criteria
        if 'min_throughput' in scenario.success_criteria:
            criteria_results['throughput'] = (
                result.throughput >= scenario.success_criteria['min_throughput']
            )
        
        # Overall success
        all_criteria_met = all(criteria_results.values()) if criteria_results else True
        
        return all_criteria_met, criteria_results 