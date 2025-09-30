#!/usr/bin/env python3
"""
Performance regression checker for CI/CD pipeline.
Compares current performance metrics against baseline.
"""

import json
import sys
import argparse
from typing import Dict, Any, List
from pathlib import Path

# Performance thresholds (configurable)
PERFORMANCE_THRESHOLDS = {
    "response_time": {
        "warning": 2.0,    # seconds
        "critical": 5.0    # seconds
    },
    "throughput": {
        "min_requests_per_second": 1.0,
        "warning_decrease": 0.2  # 20% decrease
    },
    "memory_usage": {
        "warning": 512,    # MB
        "critical": 1024   # MB
    },
    "error_rate": {
        "warning": 0.05,   # 5%
        "critical": 0.10   # 10%
    }
}

def load_performance_data(file_path: str) -> Dict[str, Any]:
    """Load performance data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Performance file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return {}

def load_baseline_data() -> Dict[str, Any]:
    """Load baseline performance data."""
    baseline_path = Path(__file__).parent.parent / "baseline" / "performance-baseline.json"

    if not baseline_path.exists():
        print("No baseline performance data found. Creating baseline from current run.")
        return {}

    return load_performance_data(str(baseline_path))

def check_response_time(current: Dict[str, Any], baseline: Dict[str, Any]) -> List[str]:
    """Check response time regression."""
    issues = []

    current_avg = current.get("avg_response_time", 0)
    baseline_avg = baseline.get("avg_response_time", 0)

    if current_avg > PERFORMANCE_THRESHOLDS["response_time"]["critical"]:
        issues.append(f"CRITICAL: Average response time {current_avg:.2f}s exceeds critical threshold")
    elif current_avg > PERFORMANCE_THRESHOLDS["response_time"]["warning"]:
        issues.append(f"WARNING: Average response time {current_avg:.2f}s exceeds warning threshold")

    if baseline_avg > 0:
        increase_ratio = (current_avg - baseline_avg) / baseline_avg
        if increase_ratio > 0.3:  # 30% increase
            issues.append(f"WARNING: Response time increased by {increase_ratio*100:.1f}% from baseline")

    return issues

def check_throughput(current: Dict[str, Any], baseline: Dict[str, Any]) -> List[str]:
    """Check throughput regression."""
    issues = []

    current_throughput = current.get("throughput", {}).get("requests_per_second", 0)
    baseline_throughput = baseline.get("throughput", {}).get("requests_per_second", 0)

    if current_throughput < PERFORMANCE_THRESHOLDS["throughput"]["min_requests_per_second"]:
        issues.append(f"CRITICAL: Throughput {current_throughput:.2f} req/s below minimum threshold")

    if baseline_throughput > 0:
        decrease_ratio = (baseline_throughput - current_throughput) / baseline_throughput
        if decrease_ratio > PERFORMANCE_THRESHOLDS["throughput"]["warning_decrease"]:
            issues.append(f"WARNING: Throughput decreased by {decrease_ratio*100:.1f}% from baseline")

    return issues

def check_memory_usage(current: Dict[str, Any], baseline: Dict[str, Any]) -> List[str]:
    """Check memory usage regression."""
    issues = []

    current_memory = current.get("memory_usage", {}).get("peak_mb", 0)

    if current_memory > PERFORMANCE_THRESHOLDS["memory_usage"]["critical"]:
        issues.append(f"CRITICAL: Peak memory usage {current_memory:.1f}MB exceeds critical threshold")
    elif current_memory > PERFORMANCE_THRESHOLDS["memory_usage"]["warning"]:
        issues.append(f"WARNING: Peak memory usage {current_memory:.1f}MB exceeds warning threshold")

    return issues

def check_error_rate(current: Dict[str, Any], baseline: Dict[str, Any]) -> List[str]:
    """Check error rate regression."""
    issues = []

    current_error_rate = current.get("error_rate", 0)
    baseline_error_rate = baseline.get("error_rate", 0)

    if current_error_rate > PERFORMANCE_THRESHOLDS["error_rate"]["critical"]:
        issues.append(f"CRITICAL: Error rate {current_error_rate*100:.2f}% exceeds critical threshold")
    elif current_error_rate > PERFORMANCE_THRESHOLDS["error_rate"]["warning"]:
        issues.append(f"WARNING: Error rate {current_error_rate*100:.2f}% exceeds warning threshold")

    if baseline_error_rate >= 0:
        if current_error_rate > baseline_error_rate * 2:  # Double the baseline error rate
            issues.append(f"WARNING: Error rate {current_error_rate*100:.2f}% significantly higher than baseline {baseline_error_rate*100:.2f}%")

    return issues

def check_endpoint_performance(current: Dict[str, Any], baseline: Dict[str, Any]) -> List[str]:
    """Check individual endpoint performance."""
    issues = []

    current_endpoints = current.get("endpoints", {})
    baseline_endpoints = baseline.get("endpoints", {})

    for endpoint, current_data in current_endpoints.items():
        baseline_data = baseline_endpoints.get(endpoint, {})

        current_time = current_data.get("avg_response_time", 0)
        baseline_time = baseline_data.get("avg_response_time", 0)

        if current_time > 3.0:  # 3 second threshold for any endpoint
            issues.append(f"WARNING: Endpoint {endpoint} response time {current_time:.2f}s is high")

        if baseline_time > 0 and current_time > baseline_time * 1.5:  # 50% increase
            issues.append(f"WARNING: Endpoint {endpoint} response time increased significantly")

    return issues

def generate_performance_report(current: Dict[str, Any], baseline: Dict[str, Any], issues: List[str]) -> str:
    """Generate a comprehensive performance report."""
    report = []
    report.append("# Performance Analysis Report")
    report.append("")

    # Summary
    if not issues:
        report.append("✅ **Status**: PASSED - No performance regressions detected")
    else:
        critical_issues = [i for i in issues if "CRITICAL" in i]
        warning_issues = [i for i in issues if "WARNING" in i]

        if critical_issues:
            report.append("❌ **Status**: FAILED - Critical performance issues detected")
        else:
            report.append("⚠️ **Status**: PASSED WITH WARNINGS")

        report.append(f"- Critical Issues: {len(critical_issues)}")
        report.append(f"- Warning Issues: {len(warning_issues)}")

    report.append("")

    # Current metrics
    report.append("## Current Performance Metrics")
    report.append(f"- Average Response Time: {current.get('avg_response_time', 0):.2f}s")
    report.append(f"- Throughput: {current.get('throughput', {}).get('requests_per_second', 0):.2f} req/s")
    report.append(f"- Peak Memory: {current.get('memory_usage', {}).get('peak_mb', 0):.1f}MB")
    report.append(f"- Error Rate: {current.get('error_rate', 0)*100:.2f}%")
    report.append("")

    # Issues
    if issues:
        report.append("## Issues Detected")
        for issue in issues:
            report.append(f"- {issue}")
        report.append("")

    # Recommendations
    if issues:
        report.append("## Recommendations")
        if any("response_time" in i.lower() for i in issues):
            report.append("- Consider optimizing slow endpoints")
            report.append("- Review database queries for efficiency")
            report.append("- Check for resource contention")

        if any("memory" in i.lower() for i in issues):
            report.append("- Review memory usage patterns")
            report.append("- Consider implementing memory pooling")
            report.append("- Check for memory leaks")

        if any("error" in i.lower() for i in issues):
            report.append("- Investigate error causes")
            report.append("- Improve error handling")
            report.append("- Review input validation")

    return "\n".join(report)

def save_baseline(current_data: Dict[str, Any]):
    """Save current performance data as new baseline."""
    baseline_dir = Path(__file__).parent.parent / "baseline"
    baseline_dir.mkdir(exist_ok=True)

    baseline_file = baseline_dir / "performance-baseline.json"

    with open(baseline_file, 'w') as f:
        json.dump(current_data, f, indent=2)

    print(f"Saved new baseline to {baseline_file}")

def main():
    parser = argparse.ArgumentParser(description="Check for performance regressions")
    parser.add_argument("performance_file", help="Path to current performance data JSON file")
    parser.add_argument("--save-baseline", action="store_true",
                       help="Save current data as new baseline")
    parser.add_argument("--output-report", help="Path to save performance report")
    parser.add_argument("--fail-on-warning", action="store_true",
                       help="Fail the check on warnings (not just critical issues)")

    args = parser.parse_args()

    # Load performance data
    current_data = load_performance_data(args.performance_file)
    if not current_data:
        print("ERROR: Could not load current performance data")
        sys.exit(1)

    baseline_data = load_baseline_data()

    # Run performance checks
    all_issues = []
    all_issues.extend(check_response_time(current_data, baseline_data))
    all_issues.extend(check_throughput(current_data, baseline_data))
    all_issues.extend(check_memory_usage(current_data, baseline_data))
    all_issues.extend(check_error_rate(current_data, baseline_data))
    all_issues.extend(check_endpoint_performance(current_data, baseline_data))

    # Generate report
    report = generate_performance_report(current_data, baseline_data, all_issues)
    print(report)

    # Save report if requested
    if args.output_report:
        with open(args.output_report, 'w') as f:
            f.write(report)
        print(f"\nReport saved to {args.output_report}")

    # Save baseline if requested
    if args.save_baseline:
        save_baseline(current_data)

    # Determine exit code
    critical_issues = [i for i in all_issues if "CRITICAL" in i]
    warning_issues = [i for i in all_issues if "WARNING" in i]

    if critical_issues:
        print(f"\n❌ FAILED: {len(critical_issues)} critical performance issues detected")
        sys.exit(1)
    elif warning_issues and args.fail_on_warning:
        print(f"\n⚠️ FAILED: {len(warning_issues)} performance warnings detected (fail-on-warning enabled)")
        sys.exit(1)
    elif warning_issues:
        print(f"\n⚠️ PASSED WITH WARNINGS: {len(warning_issues)} performance warnings detected")
        sys.exit(0)
    else:
        print("\n✅ PASSED: No performance regressions detected")
        sys.exit(0)

if __name__ == "__main__":
    main()