"""
Assisted Testing Runner

Provides a command-line interface for running assisted testing scenarios.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from voice_rag_system.tests.assisted_testing.core import AssistedTestFramework
from voice_rag_system.tests.assisted_testing.voice_scenarios import VoiceAssistedTestFramework


class AssistedTestRunner:
    """
    Command-line runner for assisted testing scenarios.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or "./tests/assisted_testing/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize frameworks
        self.general_framework = AssistedTestFramework(str(self.output_dir))
        self.voice_framework = VoiceAssistedTestFramework(str(self.output_dir))
        
        # Session info
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_results: List[Dict[str, Any]] = []
    
    def list_scenarios(self, category: Optional[str] = None, framework: str = "all") -> List[Dict[str, Any]]:
        """List available scenarios"""
        scenarios = []
        
        if framework in ["all", "general"]:
            for scenario in self.general_framework.list_scenarios(category):
                scenarios.append({
                    "id": scenario.id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "category": scenario.category,
                    "duration": scenario.estimated_duration_minutes,
                    "difficulty": scenario.difficulty_level,
                    "framework": "general"
                })
        
        if framework in ["all", "voice"]:
            for scenario in self.voice_framework.list_scenarios(category):
                scenarios.append({
                    "id": scenario.id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "category": scenario.category,
                    "duration": scenario.estimated_duration_minutes,
                    "difficulty": scenario.difficulty_level,
                    "framework": "voice"
                })
        
        return scenarios
    
    async def run_scenario(self, scenario_id: str, tester_name: Optional[str] = None, framework: str = "auto") -> Dict[str, Any]:
        """Run a single scenario"""
        logger.info(f"Running scenario: {scenario_id}")
        
        # Determine which framework to use
        if framework == "auto":
            # Try voice framework first, then general
            if self.voice_framework.get_scenario(scenario_id):
                framework = "voice"
            elif self.general_framework.get_scenario(scenario_id):
                framework = "general"
            else:
                raise ValueError(f"Scenario not found: {scenario_id}")
        
        # Run the scenario
        if framework == "voice":
            result = await self.voice_framework.run_scenario(scenario_id, tester_name)
        elif framework == "general":
            result = await self.general_framework.run_scenario(scenario_id, tester_name)
        else:
            raise ValueError(f"Unknown framework: {framework}")
        
        # Convert to dict for JSON serialization
        result_dict = result.to_dict()
        result_dict["framework"] = framework
        result_dict["session_id"] = self.session_id
        
        # Add to session results
        self.session_results.append(result_dict)
        
        # Save session results
        self._save_session_results()
        
        return result_dict
    
    async def run_category(self, category: str, tester_name: Optional[str] = None, framework: str = "all") -> List[Dict[str, Any]]:
        """Run all scenarios in a category"""
        scenarios = self.list_scenarios(category, framework)
        
        if not scenarios:
            logger.warning(f"No scenarios found for category: {category}")
            return []
        
        logger.info(f"Running {len(scenarios)} scenarios in category: {category}")
        
        results = []
        for scenario in scenarios:
            logger.info(f"Running scenario: {scenario['name']}")
            try:
                result = await self.run_scenario(scenario['id'], tester_name, scenario['framework'])
                results.append(result)
                
                # Brief pause between scenarios
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to run scenario {scenario['id']}: {e}")
                results.append({
                    "scenario_id": scenario['id'],
                    "status": "error",
                    "error_message": str(e),
                    "framework": scenario['framework'],
                    "session_id": self.session_id
                })
        
        return results
    
    async def run_all(self, tester_name: Optional[str] = None, framework: str = "all") -> List[Dict[str, Any]]:
        """Run all available scenarios"""
        scenarios = self.list_scenarios(framework=framework)
        
        if not scenarios:
            logger.warning("No scenarios found")
            return []
        
        logger.info(f"Running all {len(scenarios)} scenarios")
        
        results = []
        for scenario in scenarios:
            logger.info(f"Running scenario: {scenario['name']}")
            try:
                result = await self.run_scenario(scenario['id'], tester_name, scenario['framework'])
                results.append(result)
                
                # Brief pause between scenarios
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to run scenario {scenario['id']}: {e}")
                results.append({
                    "scenario_id": scenario['id'],
                    "status": "error",
                    "error_message": str(e),
                    "framework": scenario['framework'],
                    "session_id": self.session_id
                })
        
        return results
    
    def _save_session_results(self):
        """Save session results to file"""
        session_file = self.output_dir / f"session_{self.session_id}.json"
        
        session_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "total_scenarios": len(self.session_results),
            "results": self.session_results
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        
        logger.info(f"Session results saved to: {session_file}")
    
    def generate_report(self, format: str = "text") -> str:
        """Generate a report of the current session"""
        if not self.session_results:
            return "No test results available"
        
        # Calculate statistics
        total = len(self.session_results)
        passed = sum(1 for r in self.session_results if r.get("status") == "passed")
        failed = sum(1 for r in self.session_results if r.get("status") == "failed")
        partially_completed = sum(1 for r in self.session_results if r.get("status") == "partially_completed")
        errors = sum(1 for r in self.session_results if r.get("status") == "error")
        
        # Category breakdown
        categories = {}
        frameworks = {}
        
        for result in self.session_results:
            category = result.get("category", "unknown")
            framework = result.get("framework", "unknown")
            
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0}
            categories[category]["total"] += 1
            if result.get("status") == "passed":
                categories[category]["passed"] += 1
            elif result.get("status") == "failed":
                categories[category]["failed"] += 1
            
            if framework not in frameworks:
                frameworks[framework] = {"total": 0, "passed": 0, "failed": 0}
            frameworks[framework]["total"] += 1
            if result.get("status") == "passed":
                frameworks[framework]["passed"] += 1
            elif result.get("status") == "failed":
                frameworks[framework]["failed"] += 1
        
        # Generate report
        if format == "json":
            return json.dumps({
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_scenarios": total,
                    "passed": passed,
                    "failed": failed,
                    "partially_completed": partially_completed,
                    "errors": errors,
                    "success_rate": passed / total if total > 0 else 0
                },
                "category_breakdown": categories,
                "framework_breakdown": frameworks,
                "results": self.session_results
            }, indent=2, default=str)
        
        else:  # text format
            report = []
            report.append("=" * 60)
            report.append("ASSISTED TESTING REPORT")
            report.append("=" * 60)
            report.append(f"Session ID: {self.session_id}")
            report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            
            report.append("SUMMARY")
            report.append("-" * 20)
            report.append(f"Total Scenarios: {total}")
            report.append(f"Passed: {passed}")
            report.append(f"Failed: {failed}")
            report.append(f"Partially Completed: {partially_completed}")
            report.append(f"Errors: {errors}")
            report.append(f"Success Rate: {passed / total * 100:.1f}%" if total > 0 else "Success Rate: N/A")
            report.append("")
            
            report.append("CATEGORY BREAKDOWN")
            report.append("-" * 20)
            for category, stats in categories.items():
                report.append(f"{category}: {stats['passed']}/{stats['total']} passed")
            report.append("")
            
            report.append("FRAMEWORK BREAKDOWN")
            report.append("-" * 20)
            for framework, stats in frameworks.items():
                report.append(f"{framework}: {stats['passed']}/{stats['total']} passed")
            report.append("")
            
            report.append("DETAILED RESULTS")
            report.append("-" * 20)
            for result in self.session_results:
                report.append(f"Scenario: {result.get('scenario_name', result.get('scenario_id', 'Unknown'))}")
                report.append(f"  Status: {result.get('status', 'unknown')}")
                report.append(f"  Framework: {result.get('framework', 'unknown')}")
                report.append(f"  Duration: {result.get('total_execution_time_seconds', 0):.1f}s")
                if result.get('overall_feedback'):
                    report.append(f"  Feedback: {result['overall_feedback']}")
                report.append("")
            
            return "\n".join(report)


async def main():
    """Main command-line interface"""
    parser = argparse.ArgumentParser(description="Assisted Testing Runner")
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    parser.add_argument("--category", help="Filter scenarios by category")
    parser.add_argument("--framework", choices=["all", "general", "voice"], default="all", help="Framework to use")
    parser.add_argument("--scenario", help="Run a specific scenario")
    parser.add_argument("--run-category", help="Run all scenarios in a category")
    parser.add_argument("--run-all", action="store_true", help="Run all scenarios")
    parser.add_argument("--tester", help="Name of the tester")
    parser.add_argument("--output-dir", help="Output directory for results")
    parser.add_argument("--report", choices=["text", "json"], default="text", help="Report format")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Initialize runner
    runner = AssistedTestRunner(args.output_dir)
    
    try:
        if args.list:
            # List scenarios
            scenarios = runner.list_scenarios(args.category, args.framework)
            
            if not scenarios:
                print("No scenarios found")
                return
            
            print(f"Available Scenarios ({len(scenarios)}):")
            print("=" * 60)
            
            for scenario in scenarios:
                print(f"ID: {scenario['id']}")
                print(f"Name: {scenario['name']}")
                print(f"Description: {scenario['description']}")
                print(f"Category: {scenario['category']}")
                print(f"Framework: {scenario['framework']}")
                print(f"Duration: ~{scenario['duration']} minutes")
                print(f"Difficulty: {scenario['difficulty']}")
                print("-" * 60)
        
        elif args.scenario:
            # Run specific scenario
            print(f"Running scenario: {args.scenario}")
            result = await runner.run_scenario(args.scenario, args.tester)
            
            print("\nResult:")
            print(f"Status: {result['status']}")
            print(f"Duration: {result['total_execution_time_seconds']:.1f}s")
            if result.get('overall_feedback'):
                print(f"Feedback: {result['overall_feedback']}")
        
        elif args.run_category:
            # Run category
            print(f"Running category: {args.run_category}")
            results = await runner.run_category(args.run_category, args.tester, args.framework)
            
            # Generate report
            print("\n" + runner.generate_report(args.report))
        
        elif args.run_all:
            # Run all scenarios
            print("Running all scenarios")
            results = await runner.run_all(args.tester, args.framework)
            
            # Generate report
            print("\n" + runner.generate_report(args.report))
        
        else:
            # Interactive mode
            print("Assisted Testing Runner - Interactive Mode")
            print("=" * 50)
            
            # Show available scenarios
            scenarios = runner.list_scenarios()
            
            if not scenarios:
                print("No scenarios available")
                return
            
            print("Available Scenarios:")
            for i, scenario in enumerate(scenarios, 1):
                print(f"{i}. {scenario['name']} ({scenario['category']})")
            
            # Get user choice
            try:
                choice = int(input("\nSelect a scenario (number): ")) - 1
                if 0 <= choice < len(scenarios):
                    selected_scenario = scenarios[choice]
                    print(f"\nRunning: {selected_scenario['name']}")
                    result = await runner.run_scenario(selected_scenario['id'], args.tester)
                    
                    print("\nResult:")
                    print(f"Status: {result['status']}")
                    print(f"Duration: {result['total_execution_time_seconds']:.1f}s")
                    if result.get('overall_feedback'):
                        print(f"Feedback: {result['overall_feedback']}")
                else:
                    print("Invalid selection")
            except ValueError:
                print("Invalid input")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())