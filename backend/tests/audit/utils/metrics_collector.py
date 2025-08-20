"""
Metrics collection utilities for audit suite
Handles statistical analysis (p50/p95/p99) and metric aggregation
"""
import tracemalloc
from typing import List, Dict, Any, Optional
import numpy as np
import psutil
import time
from contextlib import contextmanager


class MetricsCollector:
    def __init__(self):
        self.metrics = {}
        self.process = psutil.Process()
        
    def record_timing(self, operation: str, duration_ms: float):
        """Record timing for an operation"""
        if operation not in self.metrics:
            self.metrics[operation] = {'timings': []}
        self.metrics[operation]['timings'].append(duration_ms)
    
    def record_memory_usage(self, operation: str, rss_mb: float, peak_mb: Optional[float] = None):
        """Record memory usage for an operation"""
        if operation not in self.metrics:
            self.metrics[operation] = {}
        
        self.metrics[operation].update({
            'rss_mb': rss_mb,
            'peak_mb': peak_mb
        })
    
    def record_custom_metric(self, operation: str, metric_name: str, value: Any):
        """Record any custom metric"""
        if operation not in self.metrics:
            self.metrics[operation] = {}
        self.metrics[operation][metric_name] = value
    
    def calculate_percentiles(self, operation: str) -> Dict[str, float]:
        """Calculate p50, p95, p99 for an operation's timings"""
        if operation not in self.metrics or 'timings' not in self.metrics[operation]:
            return {}
            
        timings = self.metrics[operation]['timings']
        if not timings:
            return {}
            
        return {
            'count': len(timings),
            'mean_ms': float(np.mean(timings)),
            'median_ms': float(np.median(timings)),
            'p50_ms': float(np.percentile(timings, 50)),
            'p95_ms': float(np.percentile(timings, 95)),
            'p99_ms': float(np.percentile(timings, 99)),
            'min_ms': float(np.min(timings)),
            'max_ms': float(np.max(timings)),
            'std_ms': float(np.std(timings))
        }
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get current process memory information"""
        memory_info = self.process.memory_info()
        return {
            'rss_mb': memory_info.rss / (1024 * 1024),
            'vms_mb': memory_info.vms / (1024 * 1024)
        }
    
    @contextmanager
    def time_operation(self, operation: str):
        """Context manager for timing operations"""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            self.record_timing(operation, duration_ms)
    
    @contextmanager
    def memory_trace(self, operation: str):
        """Context manager for memory profiling with tracemalloc"""
        tracemalloc.start()
        start_memory = self.get_memory_info()
        
        try:
            yield
        finally:
            # Get peak memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            end_memory = self.get_memory_info()
            peak_mb = peak / (1024 * 1024)
            
            self.record_memory_usage(
                operation,
                rss_mb=end_memory['rss_mb'],
                peak_mb=peak_mb
            )
            
            # Also record memory delta
            self.record_custom_metric(
                operation,
                'memory_delta_mb',
                end_memory['rss_mb'] - start_memory['rss_mb']
            )
    
    def run_warmup(self, warmup_fn, iterations: int = 1):
        """Run warmup iterations before actual measurements"""
        print(f"  🏃 Running {iterations} warmup iteration(s)...")
        for _ in range(iterations):
            warmup_fn()
    
    def run_timed_iterations(self, operation: str, test_fn, iterations: int = 30) -> Dict[str, float]:
        """Run N iterations of a test function and collect timing metrics"""
        print(f"  📊 Running {iterations} iterations for {operation}...")
        
        # Clear previous timings for this operation
        if operation in self.metrics:
            self.metrics[operation]['timings'] = []
        
        # Run iterations
        for i in range(iterations):
            if i % 10 == 0 and i > 0:
                print(f"    Progress: {i}/{iterations}")
                
            with self.time_operation(operation):
                test_fn()
        
        # Calculate and return percentiles
        return self.calculate_percentiles(operation)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self.metrics.copy()
    
    def clear_metrics(self):
        """Clear all collected metrics"""
        self.metrics.clear()
    
    def get_operation_summary(self, operation: str) -> Dict[str, Any]:
        """Get comprehensive summary for an operation"""
        if operation not in self.metrics:
            return {}
        
        summary = self.metrics[operation].copy()
        
        # Add calculated percentiles if timings exist
        if 'timings' in summary:
            percentiles = self.calculate_percentiles(operation)
            summary.update(percentiles)
        
        return summary
    
    def evaluate_against_target(self, operation: str, target_p95_ms: float) -> Dict[str, Any]:
        """Evaluate operation performance against target"""
        percentiles = self.calculate_percentiles(operation)
        
        if not percentiles:
            return {'status': 'NO_DATA', 'message': 'No timing data available'}
        
        p95 = percentiles['p95_ms']
        passed = p95 <= target_p95_ms
        
        return {
            'status': 'PASS' if passed else 'FAIL',
            'p95_ms': p95,
            'target_ms': target_p95_ms,
            'margin_ms': target_p95_ms - p95,
            'margin_percent': ((target_p95_ms - p95) / target_p95_ms) * 100,
            'message': f"p95 {p95:.1f}ms {'≤' if passed else '>'} target {target_p95_ms}ms"
        }