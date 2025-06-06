#!/usr/bin/env python3
"""
Unit Test Runner for Potter
Discovers and runs all unit tests with coverage reporting
"""

import os
import sys
import unittest
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def discover_and_run_tests():
    """Discover and run all unit tests"""
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Count tests
    test_count = suite.countTestCases()
    logger.info(f"Discovered {test_count} tests")
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure
    return result.wasSuccessful()


def run_with_coverage():
    """Run tests with coverage reporting"""
    try:
        import coverage
        
        # Start coverage
        cov = coverage.Coverage(source=['src'])
        cov.start()
        
        # Run tests
        success = discover_and_run_tests()
        
        # Stop coverage
        cov.stop()
        cov.save()
        
        # Report coverage
        print("\n" + "="*70)
        print("COVERAGE REPORT")
        print("="*70)
        cov.report()
        
        # Generate HTML report
        html_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'htmlcov')
        cov.html_report(directory=html_dir)
        print(f"\nDetailed HTML coverage report generated in: {html_dir}")
        
        return success
        
    except ImportError:
        logger.warning("Coverage module not installed. Running without coverage.")
        logger.info("Install with: pip install coverage")
        return discover_and_run_tests()


def main():
    """Main entry point"""
    print("🧪 Potter Unit Test Runner")
    print("=" * 70)
    
    # Check if coverage is requested
    use_coverage = '--coverage' in sys.argv or '-c' in sys.argv
    
    if use_coverage:
        success = run_with_coverage()
    else:
        success = discover_and_run_tests()
    
    # Print summary
    print("\n" + "=" * 70)
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 