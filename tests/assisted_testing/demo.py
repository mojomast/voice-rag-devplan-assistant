"""
Assisted Testing Framework Demo

Demonstrates the assisted testing framework with a simple example.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from voice_rag_system.tests.assisted_testing.core import (
    TestScenario, TestStep, TestStepType, AssistedTestFramework
)
from voice_rag_system.tests.assisted_testing.voice_scenarios import VoiceAssistedTestFramework


def create_demo_scenario():
    """Create a simple demo scenario for demonstration"""
    return TestScenario(
        id="demo_basic_workflow",
        name="Demo: Basic Assisted Testing Workflow",
        description="A simple demonstration of the assisted testing framework",
        category="demo",
        steps=[
            TestStep(
                id="setup_check",
                name="Setup Check",
                description="Verify basic setup requirements",
                step_type=TestStepType.USER_INPUT,
                instructions="This is a demo step to show how the framework works.",
                user_prompt="Are you ready to start the demo? (yes/no)",
                choices=["yes", "no"],
                required=True
            ),
            TestStep(
                id="user_interaction",
                name="User Interaction Demo",
                description="Demonstrate user input collection",
                step_type=TestStepType.USER_INPUT,
                instructions="Please provide some feedback about the demo.",
                user_prompt="What do you think about this assisted testing framework?",
                expected_result="User provides feedback"
            ),
            TestStep(
                id="manual_validation",
                name="Manual Validation Demo",
                description="Demonstrate manual validation",
                step_type=TestStepType.MANUAL_VALIDATION,
                instructions="This step demonstrates manual validation with predefined choices.",
                user_prompt="How would you rate this demo? (excellent/good/fair/poor)",
                choices=["excellent", "good", "fair", "poor"],
                expected_result="User provides rating"
            ),
            TestStep(
                id="observation_recording",
                name="Observation Recording Demo",
                description="Demonstrate observation recording",
                step_type=TestStepType.RECORD_OBSERVATION,
                instructions="Please record any observations about the demo process.",
                expected_result="User records observations"
            ),
            TestStep(
                id="final_feedback",
                name="Final Feedback",
                description="Collect final feedback",
                step_type=TestStepType.USER_INPUT,
                instructions="Thank you for trying the demo! Please provide any final feedback.",
                user_prompt="Any final thoughts or suggestions for improvement?",
                expected_result="User provides final feedback"
            )
        ],
        setup_instructions="This is a demo scenario to show how the assisted testing framework works.",
        cleanup_instructions="No cleanup required for this demo.",
        estimated_duration_minutes=3,
        difficulty_level="easy"
    )


async def run_demo():
    """Run the demo scenario"""
    print("🎯 Assisted Testing Framework Demo")
    print("=" * 50)
    print("This demo will show you how the assisted testing framework works.")
    print("You'll be guided through a series of interactive steps.")
    print()
    
    # Get user consent
    consent = input("Would you like to continue with the demo? (yes/no): ").strip().lower()
    if consent not in ["yes", "y"]:
        print("Demo cancelled. Goodbye!")
        return
    
    print("\n🚀 Starting demo scenario...")
    
    # Initialize framework
    framework = AssistedTestFramework()
    
    # Add demo scenario
    demo_scenario = create_demo_scenario()
    framework.add_scenario(demo_scenario)
    
    # Run the demo
    try:
        result = await framework.run_scenario("demo_basic_workflow", "Demo User")
        
        # Display results
        print("\n" + "=" * 50)
        print("📊 Demo Results")
        print("=" * 50)
        print(f"Scenario: {result.scenario_name}")
        print(f"Status: {result.status}")
        print(f"Duration: {result.total_execution_time_seconds:.1f} seconds")
        print(f"Steps completed: {len(result.step_results)}")
        
        if result.overall_feedback:
            print(f"\n💬 Overall Feedback:")
            print(f"  {result.overall_feedback}")
        
        print("\n📋 Step Results:")
        for step_result in result.step_results:
            print(f"  • {step_result.step_id}: {step_result.status}")
            if step_result.actual_result:
                print(f"    Result: {step_result.actual_result}")
        
        print(f"\n📁 Results saved to: {framework.output_dir}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


async def run_voice_demo():
    """Run a voice testing demo (simplified)"""
    print("🎤 Voice Testing Demo")
    print("=" * 50)
    print("This demo shows how voice testing scenarios work.")
    print("Note: This is a simulation - actual voice services may not be available.")
    print()
    
    consent = input("Would you like to try the voice testing demo? (yes/no): ").strip().lower()
    if consent not in ["yes", "y"]:
        print("Voice demo cancelled. Goodbye!")
        return
    
    print("\n🎤 Starting voice demo...")
    
    # Initialize voice framework
    voice_framework = VoiceAssistedTestFramework()
    
    # Get available voice scenarios
    voice_scenarios = voice_framework.list_scenarios()
    
    if not voice_scenarios:
        print("❌ No voice scenarios available")
        return
    
    print(f"\n📋 Available Voice Scenarios ({len(voice_scenarios)}):")
    for i, scenario in enumerate(voice_scenarios, 1):
        print(f"{i}. {scenario.name} ({scenario.estimated_duration_minutes} min)")
    
    try:
        choice = int(input("\nSelect a scenario to demo (number): ")) - 1
        if 0 <= choice < len(voice_scenarios):
            selected_scenario = voice_scenarios[choice]
            print(f"\n🚀 Running: {selected_scenario.name}")
            print("Note: This is a simulation of voice testing")
            
            result = await voice_framework.run_scenario(selected_scenario.id, "Voice Demo User")
            
            # Display results
            print("\n" + "=" * 50)
            print("📊 Voice Demo Results")
            print("=" * 50)
            print(f"Scenario: {result.scenario_name}")
            print(f"Status: {result.status}")
            print(f"Duration: {result.total_execution_time_seconds:.1f} seconds")
            
            if result.overall_feedback:
                print(f"\n💬 Overall Feedback:")
                print(f"  {result.overall_feedback}")
            
        else:
            print("❌ Invalid selection")
    
    except ValueError:
        print("❌ Invalid input")
    except KeyboardInterrupt:
        print("\n\n⚠️  Voice demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Voice demo failed: {e}")


async def main():
    """Main demo function"""
    print("🎯 Assisted Testing Framework - Demo Suite")
    print("=" * 60)
    print("Choose a demo to run:")
    print("1. Basic Framework Demo")
    print("2. Voice Testing Demo")
    print("3. Both Demos")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await run_demo()
        elif choice == "2":
            await run_voice_demo()
        elif choice == "3":
            await run_demo()
            print("\n" + "=" * 60)
            await run_voice_demo()
        elif choice == "4":
            print("Goodbye!")
        else:
            print("❌ Invalid choice. Please run again.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())