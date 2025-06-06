#!/usr/bin/env python3
"""
Performance Profiler
Advanced code profiling and hotspot detection system
"""

import time
import cProfile
import pstats
import io
import threading
import logging
import functools
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Result of a profiling operation"""
    name: str
    duration: float
    call_count: int
    cumulative_time: float
    per_call_time: float
    filename: str = ""
    line_number: int = 0
    function_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'duration': self.duration,
            'call_count': self.call_count,
            'cumulative_time': self.cumulative_time,
            'per_call_time': self.per_call_time,
            'filename': self.filename,
            'line_number': self.line_number,
            'function_name': self.function_name
        }


@dataclass
class HotspotAnalysis:
    """Analysis of performance hotspots"""
    function_name: str
    total_time: float
    call_count: int
    average_time: float
    percentage_of_total: float
    file_location: str
    line_number: int
    optimization_suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'function_name': self.function_name,
            'total_time': self.total_time,
            'call_count': self.call_count,
            'average_time': self.average_time,
            'percentage_of_total': self.percentage_of_total,
            'file_location': self.file_location,
            'line_number': self.line_number,
            'optimization_suggestions': self.optimization_suggestions
        }


@dataclass
class CallGraphNode:
    """Node in call graph analysis"""
    function_name: str
    call_count: int
    total_time: float
    own_time: float
    callers: Dict[str, int] = field(default_factory=dict)
    callees: Dict[str, int] = field(default_factory=dict)


class CallGraphAnalyzer:
    """Analyzes function call relationships and performance"""
    
    def __init__(self):
        self.logger = logging.getLogger("profiler.callgraph")
        self.call_graph: Dict[str, CallGraphNode] = {}
    
    def analyze_call_graph(self, profile_stats: pstats.Stats) -> Dict[str, CallGraphNode]:
        """Analyze call graph from profile statistics"""
        self.call_graph.clear()
        
        # Process profile statistics
        for func_key, (call_count, _, total_time, cumulative_time, callers) in profile_stats.stats.items():
            filename, line_number, function_name = func_key
            full_name = f"{filename}:{line_number}({function_name})"
            
            node = CallGraphNode(
                function_name=full_name,
                call_count=call_count,
                total_time=total_time,
                own_time=total_time
            )
            
            # Process callers
            for caller_key, caller_stats in callers.items():
                caller_filename, caller_line, caller_function = caller_key
                caller_name = f"{caller_filename}:{caller_line}({caller_function})"
                node.callers[caller_name] = caller_stats[0]  # call count
            
            self.call_graph[full_name] = node
        
        return self.call_graph
    
    def find_critical_path(self) -> List[str]:
        """Find the critical path (most time-consuming call chain)"""
        if not self.call_graph:
            return []
        
        # Sort by total time
        sorted_functions = sorted(
            self.call_graph.items(),
            key=lambda x: x[1].total_time,
            reverse=True
        )
        
        # Build critical path
        critical_path = []
        visited = set()
        
        def build_path(func_name: str, depth: int = 0):
            if depth > 10 or func_name in visited:  # Prevent infinite recursion
                return
            
            visited.add(func_name)
            critical_path.append(func_name)
            
            node = self.call_graph.get(func_name)
            if node and node.callees:
                # Find the callee with highest total time
                heaviest_callee = max(
                    node.callees.keys(),
                    key=lambda callee: self.call_graph.get(callee, CallGraphNode("", 0, 0, 0)).total_time
                )
                build_path(heaviest_callee, depth + 1)
        
        if sorted_functions:
            build_path(sorted_functions[0][0])
        
        return critical_path
    
    def get_bottlenecks(self, top_n: int = 10) -> List[CallGraphNode]:
        """Get top bottleneck functions"""
        return sorted(
            self.call_graph.values(),
            key=lambda x: x.total_time,
            reverse=True
        )[:top_n]


class PerformanceProfiler:
    """
    Advanced performance profiling system
    
    Features:
    - Function-level profiling
    - Context manager profiling
    - Decorator-based profiling
    - Hotspot detection
    - Call graph analysis
    - Performance recommendations
    """
    
    def __init__(self, enable_profiling: bool = True):
        """
        Initialize performance profiler
        
        Args:
            enable_profiling: Whether profiling is enabled by default
        """
        self.logger = logging.getLogger("performance.profiler")
        self.enabled = enable_profiling
        
        # Profiling data
        self.profiler = None
        self.profiles: Dict[str, pstats.Stats] = {}
        self.profile_results: Dict[str, List[ProfileResult]] = defaultdict(list)
        
        # Analysis components
        self.call_graph_analyzer = CallGraphAnalyzer()
        
        # Timing data for custom profiling
        self.timing_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Hotspot detection
        self.hotspot_threshold = 0.1  # 100ms
        self.hotspots: List[HotspotAnalysis] = []
    
    def enable_profiling(self):
        """Enable performance profiling"""
        self.enabled = True
        self.logger.info("Performance profiling enabled")
    
    def disable_profiling(self):
        """Disable performance profiling"""
        self.enabled = False
        self.logger.info("Performance profiling disabled")
    
    @contextmanager
    def profile_context(self, name: str):
        """
        Context manager for profiling code blocks
        
        Args:
            name: Name of the profiling context
        """
        if not self.enabled:
            yield
            return
        
        start_time = time.time()
        profiler = cProfile.Profile()
        
        try:
            profiler.enable()
            yield
        finally:
            profiler.disable()
            end_time = time.time()
            duration = end_time - start_time
            
            # Store profiling results
            with self.lock:
                # Convert profiler to stats
                stats_stream = io.StringIO()
                stats = pstats.Stats(profiler, stream=stats_stream)
                
                self.profiles[name] = stats
                self.timing_data[name].append(duration)
                
                # Analyze and store results
                self._analyze_profile(name, stats, duration)
    
    def profile_function(self, name: str = None) -> Callable:
        """
        Decorator for profiling functions
        
        Args:
            name: Custom name for the profile (uses function name if None)
        """
        def decorator(func: Callable) -> Callable:
            profile_name = name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                with self.profile_context(profile_name):
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def profile_method(self, method: Callable) -> Callable:
        """Profile a specific method call"""
        if not self.enabled:
            return method(*args, **kwargs)
        
        method_name = f"{method.__self__.__class__.__name__}.{method.__name__}"
        
        with self.profile_context(method_name):
            return method()
    
    def start_global_profiling(self):
        """Start global profiling for the entire application"""
        if not self.enabled:
            self.logger.warning("Profiling is disabled")
            return
        
        with self.lock:
            if self.profiler is not None:
                self.logger.warning("Global profiling already active")
                return
            
            self.profiler = cProfile.Profile()
            self.profiler.enable()
            self.logger.info("Started global profiling")
    
    def stop_global_profiling(self, name: str = "global") -> Optional[pstats.Stats]:
        """Stop global profiling and return results"""
        with self.lock:
            if self.profiler is None:
                self.logger.warning("No active global profiling")
                return None
            
            self.profiler.disable()
            
            # Convert to stats
            stats_stream = io.StringIO()
            stats = pstats.Stats(self.profiler, stream=stats_stream)
            
            self.profiles[name] = stats
            self.profiler = None
            
            self.logger.info(f"Stopped global profiling, stored as '{name}'")
            return stats
    
    def analyze_hotspots(self, profile_name: str = None) -> List[HotspotAnalysis]:
        """
        Analyze performance hotspots
        
        Args:
            profile_name: Specific profile to analyze (analyzes all if None)
        """
        if profile_name:
            profiles_to_analyze = {profile_name: self.profiles.get(profile_name)}
        else:
            profiles_to_analyze = self.profiles
        
        all_hotspots = []
        
        for name, stats in profiles_to_analyze.items():
            if stats is None:
                continue
            
            # Sort by cumulative time
            stats.sort_stats('cumulative')
            
            # Analyze top functions
            total_time = stats.total_tt
            
            for func_key, (call_count, _, own_time, cumulative_time, _) in stats.stats.items():
                filename, line_number, function_name = func_key
                
                if cumulative_time > self.hotspot_threshold:
                    percentage = (cumulative_time / total_time) * 100 if total_time > 0 else 0
                    
                    hotspot = HotspotAnalysis(
                        function_name=function_name,
                        total_time=cumulative_time,
                        call_count=call_count,
                        average_time=cumulative_time / call_count if call_count > 0 else 0,
                        percentage_of_total=percentage,
                        file_location=filename,
                        line_number=line_number,
                        optimization_suggestions=self._get_optimization_suggestions(
                            function_name, cumulative_time, call_count
                        )
                    )
                    
                    all_hotspots.append(hotspot)
        
        # Sort by total time and keep top hotspots
        all_hotspots.sort(key=lambda x: x.total_time, reverse=True)
        self.hotspots = all_hotspots[:20]  # Keep top 20
        
        return self.hotspots
    
    def get_profile_summary(self, profile_name: str) -> Dict[str, Any]:
        """Get summary of a specific profile"""
        if profile_name not in self.profiles:
            return {'error': f'Profile {profile_name} not found'}
        
        stats = self.profiles[profile_name]
        timing_history = list(self.timing_data.get(profile_name, []))
        
        # Basic statistics
        total_calls = stats.total_calls
        total_time = stats.total_tt
        
        # Timing statistics
        avg_duration = sum(timing_history) / len(timing_history) if timing_history else 0
        min_duration = min(timing_history) if timing_history else 0
        max_duration = max(timing_history) if timing_history else 0
        
        # Top functions by cumulative time
        stats.sort_stats('cumulative')
        top_functions = []
        
        for i, (func_key, (call_count, _, own_time, cumulative_time, _)) in enumerate(stats.stats.items()):
            if i >= 10:  # Top 10 functions
                break
            
            filename, line_number, function_name = func_key
            top_functions.append({
                'function': function_name,
                'file': filename,
                'line': line_number,
                'calls': call_count,
                'total_time': cumulative_time,
                'own_time': own_time,
                'per_call': cumulative_time / call_count if call_count > 0 else 0
            })
        
        return {
            'profile_name': profile_name,
            'total_calls': total_calls,
            'total_time': total_time,
            'execution_count': len(timing_history),
            'timing_stats': {
                'average_duration': avg_duration,
                'min_duration': min_duration,
                'max_duration': max_duration
            },
            'top_functions': top_functions,
            'analysis_timestamp': time.time()
        }
    
    def get_all_profiles_summary(self) -> Dict[str, Any]:
        """Get summary of all profiles"""
        summaries = {}
        
        for profile_name in self.profiles.keys():
            summaries[profile_name] = self.get_profile_summary(profile_name)
        
        return {
            'total_profiles': len(self.profiles),
            'profiling_enabled': self.enabled,
            'profiles': summaries,
            'hotspots_count': len(self.hotspots)
        }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        # Analyze all hotspots
        hotspots = self.analyze_hotspots()
        
        # Get all profile summaries
        profiles_summary = self.get_all_profiles_summary()
        
        # Performance recommendations
        recommendations = self._generate_recommendations()
        
        return {
            'timestamp': time.time(),
            'profiling_enabled': self.enabled,
            'total_profiles': len(self.profiles),
            'hotspots': [h.to_dict() for h in hotspots[:10]],  # Top 10 hotspots
            'profiles_summary': profiles_summary,
            'recommendations': recommendations,
            'performance_insights': self._generate_insights()
        }
    
    def clear_profiles(self):
        """Clear all stored profiles"""
        with self.lock:
            self.profiles.clear()
            self.profile_results.clear()
            self.timing_data.clear()
            self.hotspots.clear()
            self.logger.info("Cleared all profile data")
    
    def _analyze_profile(self, name: str, stats: pstats.Stats, duration: float):
        """Analyze a profile and store results"""
        # Store basic timing
        result = ProfileResult(
            name=name,
            duration=duration,
            call_count=stats.total_calls,
            cumulative_time=stats.total_tt,
            per_call_time=duration / stats.total_calls if stats.total_calls > 0 else 0
        )
        
        self.profile_results[name].append(result)
        
        # Analyze call graph
        call_graph = self.call_graph_analyzer.analyze_call_graph(stats)
        
        self.logger.debug(f"Analyzed profile '{name}': {duration:.3f}s, {stats.total_calls} calls")
    
    def _get_optimization_suggestions(self, function_name: str, total_time: float, call_count: int) -> List[str]:
        """Get optimization suggestions for a function"""
        suggestions = []
        
        avg_time = total_time / call_count if call_count > 0 else 0
        
        if call_count > 1000:
            suggestions.append("High call count - consider caching or reducing call frequency")
        
        if avg_time > 0.01:  # 10ms per call
            suggestions.append("High per-call time - consider algorithm optimization")
        
        if total_time > 1.0:  # 1 second total
            suggestions.append("High total time - major optimization target")
        
        # Function-specific suggestions
        if 'database' in function_name.lower() or 'query' in function_name.lower():
            suggestions.append("Database operation - consider query optimization or connection pooling")
        
        if 'network' in function_name.lower() or 'request' in function_name.lower():
            suggestions.append("Network operation - consider async operations or request batching")
        
        if 'file' in function_name.lower() or 'io' in function_name.lower():
            suggestions.append("File I/O operation - consider buffering or async file operations")
        
        return suggestions
    
    def _generate_recommendations(self) -> List[str]:
        """Generate general performance recommendations"""
        recommendations = []
        
        if len(self.hotspots) > 0:
            top_hotspot = self.hotspots[0]
            recommendations.append(
                f"Primary bottleneck: {top_hotspot.function_name} "
                f"({top_hotspot.percentage_of_total:.1f}% of total time)"
            )
        
        # Analyze timing patterns
        total_executions = sum(len(timings) for timings in self.timing_data.values())
        if total_executions > 100:
            recommendations.append("High profiling activity detected - consider reducing profiling scope in production")
        
        # Call count analysis
        high_call_count_functions = [
            h for h in self.hotspots 
            if h.call_count > 1000
        ]
        
        if high_call_count_functions:
            recommendations.append(
                f"Functions with high call counts: {len(high_call_count_functions)} "
                "functions called >1000 times - consider optimization"
            )
        
        return recommendations
    
    def _generate_insights(self) -> Dict[str, Any]:
        """Generate performance insights"""
        insights = {
            'total_profiled_functions': len(self.hotspots),
            'major_bottlenecks': len([h for h in self.hotspots if h.percentage_of_total > 5.0]),
            'optimization_opportunities': len([h for h in self.hotspots if h.optimization_suggestions])
        }
        
        if self.hotspots:
            insights['top_time_consumer'] = {
                'function': self.hotspots[0].function_name,
                'percentage': self.hotspots[0].percentage_of_total,
                'total_time': self.hotspots[0].total_time
            }
        
        return insights 