#!/usr/bin/env python3
"""
Comprehensive error handling and resilience mechanisms for the DataCleaner system.

This module provides robust error handling, retry mechanisms, circuit breakers,
and graceful degradation for production deployment.
"""

import time
import asyncio
import functools
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for specific handling strategies."""
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    CLEANING = "cleaning"
    NETWORK = "network"
    STORAGE = "storage"
    PROCESSING = "processing"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Context information for error handling and recovery."""
    operation: str
    component: str
    severity: ErrorSeverity
    category: ErrorCategory
    retry_count: int = 0
    max_retries: int = 3
    backoff_factor: float = 1.5
    context_data: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.context_data is None:
            self.context_data = {}


class CircuitBreakerState(Enum):
    """Circuit breaker states for resilience patterns."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker implementation for resilience."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                else:
                    raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class RetryStrategy:
    """Configurable retry strategy with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 backoff_factor: float = 2.0, max_delay: float = 60.0,
                 jitter: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                      backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """Decorator for retry with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            strategy = RetryStrategy(max_retries, base_delay, backoff_factor)
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = strategy.calculate_delay(attempt)
                        time.sleep(delay)
                    else:
                        break
            
            raise last_exception
        return wrapper
    return decorator


class ErrorHandler:
    """Centralized error handling and recovery system."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
        self.circuit_breakers = {}
        self.fallback_handlers = {}
        
    def register_circuit_breaker(self, operation: str, failure_threshold: int = 5, 
                                recovery_timeout: int = 60) -> CircuitBreaker:
        """Register a circuit breaker for an operation."""
        circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        self.circuit_breakers[operation] = circuit_breaker
        return circuit_breaker
    
    def register_fallback(self, operation: str, fallback_func: Callable):
        """Register a fallback function for an operation."""
        self.fallback_handlers[operation] = fallback_func
    
    def handle_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle error with appropriate strategy based on context."""
        try:
            # Log the error
            self._log_error(error, context)
            
            # Update error statistics
            self._update_error_stats(context)
            
            # Determine handling strategy
            if context.severity == ErrorSeverity.CRITICAL:
                return self._handle_critical_error(error, context)
            elif context.category == ErrorCategory.NETWORK:
                return self._handle_network_error(error, context)
            elif context.category == ErrorCategory.CONFIGURATION:
                return self._handle_configuration_error(error, context)
            else:
                return self._handle_general_error(error, context)
                
        except Exception as handling_error:
            # Fallback logging if logger fails
            print(f"Error in error handler: {handling_error}")
            raise error  # Re-raise original error if handling fails
    
    def _log_error(self, error: Exception, context: ErrorContext):
        """Log error with appropriate level and context."""
        log_data = {
            'operation': context.operation,
            'component': context.component,
            'severity': context.severity.value,
            'category': context.category.value,
            'retry_count': context.retry_count,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context_data': context.context_data
        }
        
        # Use simple print if logger doesn't have expected methods
        if hasattr(self.logger, 'error'):
            if context.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                self.logger.error(f"Error in {context.operation}: {error}", extra=log_data)
            elif context.severity == ErrorSeverity.MEDIUM:
                self.logger.warning(f"Warning in {context.operation}: {error}", extra=log_data)
            else:
                self.logger.info(f"Minor issue in {context.operation}: {error}", extra=log_data)
        else:
            # Fallback to print
            print(f"[{context.severity.value.upper()}] {context.operation}: {error}")
    
    def _update_error_stats(self, context: ErrorContext):
        """Update error statistics for monitoring."""
        key = f"{context.component}:{context.operation}"
        if key not in self.error_counts:
            self.error_counts[key] = {'count': 0, 'last_error': None}
        
        self.error_counts[key]['count'] += 1
        self.error_counts[key]['last_error'] = context.timestamp
    
    def _handle_critical_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle critical errors that require immediate attention."""
        print(f"CRITICAL ERROR in {context.operation}: {error}")
        
        # Try fallback if available
        if context.operation in self.fallback_handlers:
            try:
                return self.fallback_handlers[context.operation](error, context)
            except Exception as fallback_error:
                print(f"Fallback failed for {context.operation}: {fallback_error}")
        
        # For critical errors, we might want to raise immediately
        raise error
    
    def _handle_network_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle network-related errors with retry logic."""
        if context.retry_count < context.max_retries:
            delay = context.backoff_factor ** context.retry_count
            print(f"Retrying {context.operation} in {delay}s (attempt {context.retry_count + 1})")
            time.sleep(delay)
            context.retry_count += 1
            return None  # Signal to retry
        else:
            print(f"Max retries exceeded for {context.operation}")
            raise error
    
    def _handle_configuration_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle configuration errors with fallback to defaults."""
        print(f"Configuration error in {context.operation}, attempting fallback")
        
        # Try to use fallback configuration
        if context.operation in self.fallback_handlers:
            return self.fallback_handlers[context.operation](error, context)
        
        # If no fallback, this is critical
        context.severity = ErrorSeverity.CRITICAL
        return self._handle_critical_error(error, context)
    
    def _handle_general_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle general errors with standard retry logic."""
        if context.retry_count < context.max_retries:
            context.retry_count += 1
            return None  # Signal to retry
        else:
            raise error
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            'error_counts': self.error_counts.copy(),
            'circuit_breaker_states': {
                op: cb.state.value for op, cb in self.circuit_breakers.items()
            },
            'total_errors': sum(stats['count'] for stats in self.error_counts.values()),
            'operations_with_errors': len(self.error_counts)
        }


class GracefulDegradation:
    """Implements graceful degradation patterns for system resilience."""
    
    def __init__(self):
        self.degradation_levels = {
            'full': {'cleaning': True, 'validation': True, 'audit': True},
            'reduced': {'cleaning': True, 'validation': True, 'audit': False},
            'minimal': {'cleaning': True, 'validation': False, 'audit': False},
            'emergency': {'cleaning': False, 'validation': False, 'audit': False}
        }
        self.current_level = 'full'
        self.degradation_triggers = {
            'error_rate_threshold': 0.1,  # 10% error rate
            'response_time_threshold': 5.0,  # 5 seconds
            'memory_threshold': 0.9  # 90% memory usage
        }
    
    def should_degrade(self, metrics: Dict[str, float]) -> Optional[str]:
        """Determine if system should degrade based on metrics."""
        error_rate = metrics.get('error_rate', 0)
        response_time = metrics.get('avg_response_time', 0)
        memory_usage = metrics.get('memory_usage', 0)
        
        if error_rate > 0.5 or response_time > 10 or memory_usage > 0.95:
            return 'emergency'
        elif error_rate > 0.3 or response_time > 7 or memory_usage > 0.9:
            return 'minimal'
        elif error_rate > 0.1 or response_time > 5 or memory_usage > 0.8:
            return 'reduced'
        else:
            return 'full'
    
    def set_degradation_level(self, level: str):
        """Set the current degradation level."""
        if level in self.degradation_levels:
            self.current_level = level
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled at current degradation level."""
        return self.degradation_levels[self.current_level].get(feature, False)


class HealthChecker:
    """System health monitoring and reporting."""
    
    def __init__(self):
        self.health_checks = {}
        self.last_check_results = {}
    
    def register_health_check(self, name: str, check_func: Callable[[], bool], 
                            timeout: float = 5.0):
        """Register a health check function."""
        self.health_checks[name] = {
            'func': check_func,
            'timeout': timeout
        }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {
            'timestamp': time.time(),
            'overall_healthy': True,
            'checks': {}
        }
        
        for name, check_config in self.health_checks.items():
            try:
                # Run check with timeout
                start_time = time.time()
                healthy = check_config['func']()
                duration = time.time() - start_time
                
                results['checks'][name] = {
                    'healthy': healthy,
                    'duration': duration,
                    'status': 'pass' if healthy else 'fail'
                }
                
                if not healthy:
                    results['overall_healthy'] = False
                    
            except Exception as e:
                results['checks'][name] = {
                    'healthy': False,
                    'duration': 0,
                    'status': 'error',
                    'error': str(e)
                }
                results['overall_healthy'] = False
        
        self.last_check_results = results
        return results
    
    def get_health_status(self) -> str:
        """Get simple health status string."""
        if not self.last_check_results:
            return 'unknown'
        
        return 'healthy' if self.last_check_results['overall_healthy'] else 'unhealthy'


# Global error handler instance
global_error_handler = ErrorHandler()


# Convenience decorators
def resilient_operation(operation_name: str, component: str = 'data_cleaner',
                      severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                      category: ErrorCategory = ErrorCategory.PROCESSING,
                      max_retries: int = 3):
    """Decorator to make operations resilient with error handling."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = ErrorContext(
                operation=operation_name,
                component=component,
                severity=severity,
                category=category,
                max_retries=max_retries
            )
            
            while context.retry_count <= context.max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    result = global_error_handler.handle_error(e, context)
                    if result is None and context.retry_count < context.max_retries:
                        continue  # Retry
                    elif result is not None:
                        return result  # Fallback result
                    else:
                        raise e  # Max retries exceeded
            
        return wrapper
    return decorator


def with_circuit_breaker(operation_name: str, failure_threshold: int = 5):
    """Decorator to add circuit breaker protection."""
    circuit_breaker = global_error_handler.register_circuit_breaker(
        operation_name, failure_threshold
    )
    
    def decorator(func):
        return circuit_breaker(func)
    
    return decorator