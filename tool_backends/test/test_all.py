#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Runner: Automatically run all test files in the tool_backends/test directory
Supports running both standard unittest format and custom test_tool format tests
"""

import os
import sys
import unittest
import importlib.util
import argparse
import time
import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional

class CustomTestResult:
    """Custom test result class for recording test running status"""
    def __init__(self):
        self.test_count = 0  # Records the actual number of test cases
        self.pass_count = 0  # Records the number of passed test cases
        self.error = None
        self.output = []

class Capturing:
    """Context manager for capturing stdout"""
    def __init__(self):
        self.output = []
    
    def write(self, s):
        self.output.append(s)
    
    def flush(self):
        pass
    
    def __enter__(self):
        self.old_stdout = sys.stdout
        sys.stdout = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
        return False  # Don't suppress exceptions

class TestRunner:
    """Test runner class for loading and running test files"""
    
    def __init__(self, test_dir: str, verbose: bool = False, parallel: bool = False, max_workers: int = 4):
        """
        Initialize the test runner
        
        Args:
            test_dir: Directory containing test files
            verbose: Whether to show detailed output
            parallel: Whether to run tests in parallel
            max_workers: Maximum number of worker threads for parallel execution
        """
        self.test_dir = test_dir
        self.verbose = verbose
        self.parallel = parallel
        self.max_workers = max_workers
        self.test_files = []
        self.results = {}
        
    def find_test_files(self) -> List[str]:
        """Find all test files in the directory"""
        test_files = []
        for file in os.listdir(self.test_dir):
            # Exclude current script and non-Python files, only include files ending with _test.py
            if file.endswith('_test.py') and file != 'test_all.py':
                test_files.append(os.path.join(self.test_dir, file))
        self.test_files = sorted(test_files)
        return self.test_files
    
    def run_standard_unittest(self, module) -> unittest.TestResult:
        """Run standard unittest tests"""
        test_suite = unittest.TestLoader().loadTestsFromModule(module)
        result = unittest.TestResult()
        test_suite.run(result)
        return result
    
    def _run_function_with_capturing(self, func, name=None, args=None, kwargs=None):
        """Helper method to run a function with stdout capturing and exception handling"""
        args = args or ()
        kwargs = kwargs or {}
        
        try:
            with Capturing() as captured_output:
                func(*args, **kwargs)
            output = '\n'.join(captured_output.output)
            return True, output, None
        except Exception as e:
            error_msg = f"Error running {name if name else 'function'}: {str(e)}"
            return False, None, error_msg
    
    def run_custom_test(self, module, file_path: str) -> CustomTestResult:
        """Run custom test functions"""
        result = CustomTestResult()
        file_name = os.path.basename(file_path)
        module_name = file_name[:-3]
        
        try:
            # First check if the module has a main function - key for handling files like biomcp_test.py
            if hasattr(module, 'main'):
                if self.verbose:
                    print(f"  Found main function, running complete test suite")
                
                success, output, error = self._run_function_with_capturing(module.main, "main function")
                
                if output:
                    result.output.append(output)
                    
                    # Analyze output to count test cases and passes
                    lines = output.split('\n')
                    total_tests = 0
                    passed_tests = 0
                    failed_tests = 0
                    
                    for line in lines:
                        if "Testing tool:" in line:
                            total_tests += 1
                        elif "✅ Test succeeded" in line:
                            passed_tests += 1
                        elif line.startswith("❌"):
                            failed_tests += 1
                    
                    # If test case markers are found, use these counts
                    if total_tests > 0:
                        result.test_count = total_tests
                        result.pass_count = passed_tests
                        if failed_tests > 0:
                            result.error = f"Found {failed_tests} failed tests"
                    else:
                        # Otherwise assume at least one test
                        result.test_count = 1
                        result.pass_count = 1 if success else 0
                else:
                    # If no output, assume at least one test
                    result.test_count = 1
                    result.pass_count = 1 if success else 0
                
                if error:
                    result.test_count = 1
                    result.pass_count = 0
                    result.error = error
                    if self.verbose:
                        print(f"  Error: {error}")
            
            # Next check if the module has test_tool function
            elif hasattr(module, 'test_tool'):
                # Find all test-related functions
                functions = inspect.getmembers(module, inspect.isfunction)
                test_functions = [(name, func) for name, func in functions 
                                  if (name.startswith('test_') or name.endswith('_test')) and name != 'test_tool']
                
                # If specific test functions found, run them
                if test_functions:
                    for name, func in test_functions:
                        if self.verbose:
                            print(f"  Running test function: {name}")
                        result.test_count += 1
                        
                        # Try to run without arguments first
                        success, output, error = self._run_function_with_capturing(func, name)
                        
                        # If needs arguments, try with default method
                        if not success and error and "missing" in error and "required positional argument" in error:
                            if self.verbose:
                                print(f"    Function needs arguments, trying with default method")
                            success, output, error = self._run_function_with_capturing(
                                func, name, kwargs={'method': module_name}
                            )
                        
                        if success:
                            result.pass_count += 1
                        elif error:
                            result.error = error
                            if self.verbose:
                                print(f"  Error: {error}")
                        
                        if output:
                            result.output.append(f"Function {name} output:\n{output}")
                
                # If no specific test functions, run test_tool directly
                else:
                    if self.verbose:
                        print(f"  No specific test functions found, trying test_tool")
                    
                    result.test_count = 1
                    success, output, error = self._run_function_with_capturing(
                        module.test_tool, "test_tool", kwargs={'method': module_name}
                    )
                    
                    if success:
                        result.pass_count = 1
                    elif error:
                        result.error = error
                        if self.verbose:
                            print(f"  Error: {error}")
                    
                    if output:
                        result.output.append(output)
            
            # If no test_tool function, try to run all functions in the module
            else:
                if self.verbose:
                    print(f"  No test_tool function found in module, trying all functions")
                
                functions = inspect.getmembers(module, inspect.isfunction)
                for name, func in functions:
                    if not name.startswith('__') and name != 'test_tool':
                        if self.verbose:
                            print(f"  Running function: {name}")
                        
                        # Try to run without arguments
                        success, output, error = self._run_function_with_capturing(func, name)
                        
                        if self.verbose and error:
                            print(f"  Error running function {name}: {error}")
                        
                        if output:
                            result.output.append(f"Function {name} output:\n{output}")
        
        except Exception as e:
            result.test_count = 1
            result.pass_count = 0
            result.error = f"Exception running test file: {str(e)}"
            if self.verbose:
                print(f"  Exception: {result.error}")
        
        return result
    
    def run_single_test(self, file_path: str) -> Tuple[str, object]:
        """Load and run a single test file"""
        file_name = os.path.basename(file_path)
        start_time = None
        
        if self.verbose:
            print(f"\nStarting test: {file_name}")
            start_time = time.time()
        
        try:
            module_name = file_name[:-3]  # Remove .py suffix
            
            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # First try to run standard unittest tests
                result = self.run_standard_unittest(module)
                
                # If no standard test cases found, try custom tests
                if result.testsRun == 0:
                    if self.verbose:
                        print(f"  No standard unittest test cases found, trying custom tests")
                    result = self.run_custom_test(module, file_path)
        except Exception as e:
            result = CustomTestResult()
            result.test_count = 1
            result.pass_count = 0
            result.error = f"Error loading test file: {str(e)}"
            if self.verbose:
                print(f"  Error: {result.error}")
        
        # Print verbose output if enabled
        if self.verbose and start_time:
            elapsed_time = time.time() - start_time
            
            if isinstance(result, unittest.TestResult):
                success_count = result.testsRun - len(getattr(result, 'failures', [])) - len(getattr(result, 'errors', []))
                failure_count = len(getattr(result, 'failures', []))
                error_count = len(getattr(result, 'errors', []))
                print(f"Test {file_name} completed in {elapsed_time:.2f} seconds")
                print(f"  Success: {success_count}")
                print(f"  Failures: {failure_count}")
                print(f"  Errors: {error_count}")
            else:
                status = "Success" if result.pass_count == result.test_count else "Failed"
                print(f"Test {file_name} completed in {elapsed_time:.2f} seconds")
                print(f"  Status: {status}")
                print(f"  Results: {result.pass_count}/{result.test_count} passed")
                if result.error:
                    print(f"  Error: {result.error}")
                if hasattr(result, 'output') and result.output:
                    print(f"  Output lines: {sum(len(output.split('\n')) for output in result.output)}")
        
        self.results[file_name] = result
        return file_name, result
    
    def run_all_tests(self) -> Dict[str, object]:
        """Run all test files"""
        self.find_test_files()
        
        if not self.test_files:
            print("No test files found!")
            return self.results
        
        print(f"Found {len(self.test_files)} test files, ready to run...")
        
        if self.parallel and len(self.test_files) > 1:
            # Run tests in parallel
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(self.test_files))) as executor:
                executor.map(self.run_single_test, self.test_files)
        else:
            # Run tests sequentially
            for file_path in self.test_files:
                self.run_single_test(file_path)
        
        return self.results
    
    def print_summary(self) -> None:
        """Print test results summary"""
        total_tests = 0
        total_success = 0
        total_failures = 0
        total_errors = 0
        
        print("\n===== Test Results Summary =====")
        
        for file_name, result in self.results.items():
            if isinstance(result, unittest.TestResult):
                # Standard unittest results
                tests_run = result.testsRun
                failures = len(getattr(result, 'failures', []))
                errors = len(getattr(result, 'errors', []))
                success = tests_run - failures - errors
            else:
                # Custom test results
                tests_run = getattr(result, 'test_count', 1)
                success = getattr(result, 'pass_count', 0)
                failures = 0
                errors = tests_run - success
            
            total_tests += tests_run
            total_success += success
            total_failures += failures
            total_errors += errors
            
            status = "✅ Passed" if success == tests_run and errors == 0 else "❌ Failed"
            print(f"{status} - {file_name}: {success}/{tests_run} passed")
            
            # Print detailed failure and error information
            if isinstance(result, unittest.TestResult):
                if hasattr(result, 'failures') and result.failures:
                    for test, err in result.failures:
                        print(f"  Failure: {test.id()}")
                if hasattr(result, 'errors') and result.errors:
                    for test, err in result.errors:
                        print(f"  Error: {test.id()}")
            else:
                if hasattr(result, 'error') and result.error:
                    print(f"  Error: {result.error}")
            
            # If output exists, optionally print preview
            if hasattr(result, 'output') and result.output and self.verbose:
                print(f"  Output preview:")
                for output in result.output[:1]:  # Only show preview of first output
                    preview = '\n'.join(output.split('\n')[:3])
                    if len(output.split('\n')) > 3:
                        preview += '\n...'
                    print(f"    {preview}")
        
        print("\n===== Overall Statistics =====")
        print(f"Total tests: {total_tests}")
        print(f"Success: {total_success}")
        print(f"Failures: {total_failures}")
        print(f"Errors: {total_errors}")
        print(f"Pass rate: {total_success/total_tests*100:.1f}%" if total_tests > 0 else "Pass rate: 0%")
        print("==================")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run all tests in tool_backends')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('-p', '--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('-w', '--workers', type=int, default=4, help='Maximum number of worker threads for parallel execution')
    parser.add_argument('-d', '--dir', type=str, default=os.path.dirname(os.path.abspath(__file__)), 
                        help='Directory containing test files')
    
    args = parser.parse_args()
    
    # Ensure test directory exists
    if not os.path.isdir(args.dir):
        print(f"Error: Directory {args.dir} does not exist!")
        sys.exit(1)
    
    # Create and run test runner
    runner = TestRunner(
        test_dir=args.dir,
        verbose=args.verbose,
        parallel=args.parallel,
        max_workers=args.workers
    )
    
    # Run all tests
    results = runner.run_all_tests()
    
    # Print test summary
    if results:
        runner.print_summary()
    
    # Set exit code based on test results
    all_passed = True
    for result in results.values():
        if isinstance(result, unittest.TestResult):
            # Standard unittest results
            if len(getattr(result, 'failures', [])) > 0 or len(getattr(result, 'errors', [])) > 0:
                all_passed = False
                break
        else:
            # Custom test results
            if getattr(result, 'pass_count', 0) < getattr(result, 'test_count', 1):
                all_passed = False
                break
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()