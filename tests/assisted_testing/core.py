"""
Core Assisted Testing Framework

Provides the main framework for interactive testing scenarios that cannot be fully automated.
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import inquirer
from loguru import logger


class TestStepType(Enum):
    """Types of test steps in assisted testing"""
    USER_INPUT = "user_input"
    AUTOMATED_CHECK = "automated_check"
    MANUAL_VALIDATION = "manual_validation"
    SYSTEM_ACTION = "system_action"
    WAIT_FOR_USER = "wait_for_user"
    RECORD_OBSERVATION = "record_observation"


@dataclass
class TestStep:
    """Individual step in an assisted test scenario"""
    id: str
    name: str
    description: str
    step_type: TestStepType
    instructions: str
    expected_result: Optional[str] = None
    validation_function: Optional[Callable] = None
    timeout_seconds: int = 60
    required: bool = True
    user_prompt: Optional[str] = None
    choices: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "step_type": self.step_type.value,
            "instructions": self.instructions,
            "expected_result": self.expected_result,
            "timeout_seconds": self.timeout_seconds,
            "required": self.required,
            "user_prompt": self.user_prompt,
            "choices": self.choices
        }


@dataclass
class TestScenario:
    """A complete assisted testing scenario"""
    id: str
    name: str
    description: str
    category: str
    steps: List[TestStep]
    setup_instructions: Optional[str] = None
    cleanup_instructions: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    estimated_duration_minutes: int = 10
    difficulty_level: str = "medium"  # easy, medium, hard
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "steps": [step.to_dict() for step in self.steps],
            "setup_instructions": self.setup_instructions,
            "cleanup_instructions": self.cleanup_instructions,
            "prerequisites": self.prerequisites,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "difficulty_level": self.difficulty_level
        }


@dataclass
class TestResult:
    """Result of a test step or scenario"""
    step_id: str
    status: str  # passed, failed, skipped, error
    actual_result: Optional[str] = None
    user_feedback: Optional[str] = None
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    observations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "step_id": self.step_id,
            "status": self.status,
            "actual_result": self.actual_result,
            "user_feedback": self.user_feedback,
            "execution_time_seconds": self.execution_time_seconds,
            "error_message": self.error_message,
            "observations": self.observations,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ScenarioResult:
    """Result of a complete test scenario"""
    scenario_id: str
    scenario_name: str
    status: str  # passed, failed, partially_completed, error
    step_results: List[TestResult] = field(default_factory=list)
    overall_feedback: Optional[str] = None
    total_execution_time_seconds: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    tester_name: Optional[str] = None
    environment_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "status": self.status,
            "step_results": [result.to_dict() for result in self.step_results],
            "overall_feedback": self.overall_feedback,
            "total_execution_time_seconds": self.total_execution_time_seconds,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tester_name": self.tester_name,
            "environment_info": self.environment_info
        }


class AssistedTestFramework:
    """
    Main framework for conducting assisted testing scenarios.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or "./tests/assisted_testing/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scenarios: Dict[str, TestScenario] = {}
        self.results: List[ScenarioResult] = []
        self.current_scenario: Optional[TestScenario] = None
        self.current_result: Optional[ScenarioResult] = None
        
        # Load built-in scenarios
        self._load_builtin_scenarios()
    
    def _load_builtin_scenarios(self):
        """Load built-in assisted testing scenarios"""
        # Voice Input Testing Scenarios
        self.scenarios["voice_input_basic"] = TestScenario(
            id="voice_input_basic",
            name="Basic Voice Input Testing",
            description="Test basic voice input functionality with real microphone input",
            category="voice_input",
            steps=[
                TestStep(
                    id="setup_microphone",
                    name="Setup Microphone",
                    description="Ensure microphone is connected and working",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Please ensure your microphone is connected and working. Test it by saying something and checking if you can hear yourself.",
                    user_prompt="Is your microphone working properly? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="test_voice_recording",
                    name="Test Voice Recording",
                    description="Record a short voice sample",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will now test voice recording. Please speak clearly into your microphone when prompted.",
                    user_prompt="Press Enter when ready to record a 5-second voice sample",
                    expected_result="Voice should be recorded successfully"
                ),
                TestStep(
                    id="validate_recording_quality",
                    name="Validate Recording Quality",
                    description="Check if the recording quality is acceptable",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Listen to the recorded audio and assess its quality.",
                    user_prompt="How would you rate the recording quality? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="Recording quality should be at least 'fair'"
                )
            ],
            estimated_duration_minutes=5,
            difficulty_level="easy"
        )
        
        # Voice Output Testing Scenarios
        self.scenarios["voice_output_quality"] = TestScenario(
            id="voice_output_quality",
            name="Voice Output Quality Testing",
            description="Test text-to-speech output quality and clarity",
            category="voice_output",
            steps=[
                TestStep(
                    id="setup_audio_output",
                    name="Setup Audio Output",
                    description="Ensure speakers/headphones are working",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Please ensure your speakers or headphones are connected and working.",
                    user_prompt="Can you hear audio from your system? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="test_tts_basic",
                    name="Test Basic TTS",
                    description="Generate and play basic TTS audio",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will generate speech from text and play it back.",
                    user_prompt="Press Enter to generate and play 'Hello, this is a test of the text-to-speech system.'",
                    expected_result="Speech should be clear and understandable"
                ),
                TestStep(
                    id="test_different_voices",
                    name="Test Different Voices",
                    description="Test multiple voice options",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="We will test different voice options available in the system.",
                    user_prompt="Press Enter to test different voice options (alloy, echo, fable, onyx, nova, shimmer)",
                    expected_result="All voices should work and sound different from each other"
                ),
                TestStep(
                    id="validate_voice_quality",
                    name="Validate Voice Quality",
                    description="Assess overall voice quality",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Listen to all voice samples and provide feedback on quality.",
                    user_prompt="How would you rate the overall voice quality? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="Voice quality should be at least 'good'"
                )
            ],
            estimated_duration_minutes=8,
            difficulty_level="easy"
        )
        
        # Voice Workflow Testing
        self.scenarios["voice_workflow_complete"] = TestScenario(
            id="voice_workflow_complete",
            name="Complete Voice Workflow Testing",
            description="Test complete voice workflow: speech -> text -> processing -> speech",
            category="voice_workflow",
            steps=[
                TestStep(
                    id="workflow_setup",
                    name="Workflow Setup",
                    description="Prepare for complete voice workflow test",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Ensure both microphone and speakers/headphones are working.",
                    user_prompt="Are both input (microphone) and output (speakers) audio devices ready? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="voice_input_test",
                    name="Voice Input Test",
                    description="Speak a test phrase for transcription",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Please speak clearly: 'What is artificial intelligence and how does it work?'",
                    user_prompt="Press Enter when ready to speak, then say the phrase clearly",
                    expected_result="Speech should be transcribed accurately"
                ),
                TestStep(
                    id="validate_transcription",
                    name="Validate Transcription",
                    description="Check if transcription is accurate",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Review the transcribed text and compare it with what you said.",
                    user_prompt="Is the transcription accurate? (yes/no)",
                    choices=["yes", "no"],
                    expected_result="Transcription should be reasonably accurate"
                ),
                TestStep(
                    id="process_response",
                    name="Process Response",
                    description="Generate response to transcribed text",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="The system will now process your question and generate a response.",
                    user_prompt="Press Enter to generate a response to your question",
                    expected_result="System should generate a relevant response"
                ),
                TestStep(
                    id="voice_output_test",
                    name="Voice Output Test",
                    description="Convert response back to speech",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="The system will now convert the response back to speech.",
                    user_prompt="Press Enter to hear the response as speech",
                    expected_result="Response should be spoken clearly"
                ),
                TestStep(
                    id="validate_complete_workflow",
                    name="Validate Complete Workflow",
                    description="Assess the complete voice workflow experience",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Consider the entire workflow from speech input to speech output.",
                    user_prompt="How would you rate the complete voice workflow experience? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="Complete workflow should be at least 'good'"
                )
            ],
            estimated_duration_minutes=15,
            difficulty_level="medium"
        )
        
        # UI Interaction Testing
        self.scenarios["ui_interaction_voice"] = TestScenario(
            id="ui_interaction_voice",
            name="Voice UI Interaction Testing",
            description="Test voice user interface interactions and usability",
            category="ui_interaction",
            steps=[
                TestStep(
                    id="ui_setup",
                    name="UI Setup",
                    description="Navigate to voice interface",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Please navigate to the voice interface in your browser or application.",
                    user_prompt="Are you on the voice interface page? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="test_voice_button",
                    name="Test Voice Button",
                    description="Test the voice input button functionality",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Click the voice input button and observe the interface behavior.",
                    user_prompt="Click the voice input button and describe what happens",
                    expected_result="Interface should show recording state or prompt for microphone access"
                ),
                TestStep(
                    id="test_voice_controls",
                    name="Test Voice Controls",
                    description="Test various voice control options",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Test different voice controls like play, stop, volume, etc.",
                    user_prompt="Test the available voice controls and describe their functionality",
                    expected_result="All voice controls should work as expected"
                ),
                TestStep(
                    id="test_voice_settings",
                    name="Test Voice Settings",
                    description="Test voice settings and configuration options",
                    step_type=TestStepType.SYSTEM_ACTION,
                    instructions="Navigate to voice settings and test different options.",
                    user_prompt="Test voice settings (voice selection, speed, etc.) and describe the experience",
                    expected_result="Settings should be accessible and functional"
                ),
                TestStep(
                    id="validate_ui_usability",
                    name="Validate UI Usability",
                    description="Assess overall UI usability",
                    step_type=TestStepType.MANUAL_VALIDATION,
                    instructions="Consider the overall usability of the voice interface.",
                    user_prompt="How would you rate the voice interface usability? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    expected_result="UI should be at least 'good' in usability"
                )
            ],
            estimated_duration_minutes=12,
            difficulty_level="medium"
        )
    
    def add_scenario(self, scenario: TestScenario):
        """Add a custom test scenario"""
        self.scenarios[scenario.id] = scenario
        logger.info(f"Added custom scenario: {scenario.name}")
    
    def get_scenario(self, scenario_id: str) -> Optional[TestScenario]:
        """Get a scenario by ID"""
        return self.scenarios.get(scenario_id)
    
    def list_scenarios(self, category: Optional[str] = None) -> List[TestScenario]:
        """List available scenarios, optionally filtered by category"""
        scenarios = list(self.scenarios.values())
        if category:
            scenarios = [s for s in scenarios if s.category == category]
        return scenarios
    
    async def run_scenario(self, scenario_id: str, tester_name: Optional[str] = None) -> ScenarioResult:
        """Run a complete assisted testing scenario"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")
        
        logger.info(f"Starting assisted test scenario: {scenario.name}")
        
        self.current_scenario = scenario
        self.current_result = ScenarioResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            status="in_progress",
            tester_name=tester_name,
            environment_info=self._get_environment_info()
        )
        
        start_time = time.time()
        
        try:
            # Display scenario information
            self._display_scenario_info(scenario)
            
            # Check prerequisites
            if scenario.prerequisites:
                if not await self._check_prerequisites(scenario.prerequisites):
                    self.current_result.status = "failed"
                    self.current_result.error_message = "Prerequisites not met"
                    return self.current_result
            
            # Run setup instructions
            if scenario.setup_instructions:
                await self._display_instructions("Setup", scenario.setup_instructions)
                if not await self._get_user_confirmation("Ready to proceed?"):
                    self.current_result.status = "skipped"
                    return self.current_result
            
            # Execute test steps
            for step in scenario.steps:
                step_result = await self._execute_step(step)
                self.current_result.step_results.append(step_result)
                
                # If a required step fails, ask if user wants to continue
                if step.required and step_result.status == "failed":
                    continue_test = await self._get_user_confirmation(
                        f"Required step '{step.name}' failed. Continue anyway?"
                    )
                    if not continue_test:
                        self.current_result.status = "failed"
                        break
            
            # Run cleanup instructions
            if scenario.cleanup_instructions:
                await self._display_instructions("Cleanup", scenario.cleanup_instructions)
            
            # Collect overall feedback
            self.current_result.overall_feedback = await self._get_user_feedback(
                "Overall feedback for this test scenario:"
            )
            
            # Determine final status
            self._determine_final_status()
            
        except Exception as e:
            logger.error(f"Error running scenario {scenario_id}: {e}")
            self.current_result.status = "error"
            self.current_result.error_message = str(e)
        
        finally:
            # Complete the result
            self.current_result.completed_at = datetime.now()
            self.current_result.total_execution_time_seconds = time.time() - start_time
            
            # Save result
            self._save_result(self.current_result)
            self.results.append(self.current_result)
            
            logger.info(f"Completed scenario: {scenario.name} - Status: {self.current_result.status}")
        
        return self.current_result
    
    def _display_scenario_info(self, scenario: TestScenario):
        """Display scenario information to the user"""
        print("\n" + "="*60)
        print(f"SCENARIO: {scenario.name}")
        print("="*60)
        print(f"Description: {scenario.description}")
        print(f"Category: {scenario.category}")
        print(f"Duration: ~{scenario.estimated_duration_minutes} minutes")
        print(f"Difficulty: {scenario.difficulty_level}")
        print(f"Steps: {len(scenario.steps)}")
        print("="*60)
    
    async def _check_prerequisites(self, prerequisites: List[str]) -> bool:
        """Check if prerequisites are met"""
        print("\nPrerequisites:")
        for prereq in prerequisites:
            response = await self._get_user_confirmation(f"{prereq} (yes/no)")
            if not response:
                print(f"Prerequisite not met: {prereq}")
                return False
        return True
    
    async def _display_instructions(self, title: str, instructions: str):
        """Display instructions to the user"""
        print(f"\n{title.upper()}")
        print("-" * len(title))
        print(instructions)
        await self._get_user_confirmation("Press Enter when ready to continue...")
    
    async def _execute_step(self, step: TestStep) -> TestResult:
        """Execute a single test step"""
        print(f"\nSTEP: {step.name}")
        print("-" * len(step.name))
        print(f"Description: {step.description}")
        print(f"Instructions: {step.instructions}")
        
        if step.expected_result:
            print(f"Expected: {step.expected_result}")
        
        step_result = TestResult(step_id=step.id, status="in_progress")
        start_time = time.time()
        
        try:
            if step.step_type == TestStepType.USER_INPUT:
                await self._handle_user_input_step(step, step_result)
            elif step.step_type == TestStepType.SYSTEM_ACTION:
                await self._handle_system_action_step(step, step_result)
            elif step.step_type == TestStepType.MANUAL_VALIDATION:
                await self._handle_manual_validation_step(step, step_result)
            elif step.step_type == TestStepType.AUTOMATED_CHECK:
                await self._handle_automated_check_step(step, step_result)
            elif step.step_type == TestStepType.WAIT_FOR_USER:
                await self._handle_wait_step(step, step_result)
            elif step.step_type == TestStepType.RECORD_OBSERVATION:
                await self._handle_observation_step(step, step_result)
            else:
                step_result.status = "error"
                step_result.error_message = f"Unknown step type: {step.step_type}"
        
        except Exception as e:
            step_result.status = "error"
            step_result.error_message = str(e)
            logger.error(f"Error executing step {step.id}: {e}")
        
        finally:
            step_result.execution_time_seconds = time.time() - start_time
            print(f"Step completed: {step_result.status}")
        
        return step_result
    
    async def _handle_user_input_step(self, step: TestStep, result: TestResult):
        """Handle user input step"""
        if step.choices:
            # Use inquirer for choice selection
            try:
                answer = inquirer.prompt([
                    inquirer.List('choice',
                               message=step.user_prompt or step.name,
                               choices=step.choices)
                ])
                result.actual_result = answer['choice']
                result.status = "passed"
            except Exception as e:
                result.status = "error"
                result.error_message = f"Choice selection failed: {e}"
        else:
            # Simple text input
            answer = input(f"{step.user_prompt or step.name}: ")
            result.actual_result = answer
            result.status = "passed"
    
    async def _handle_system_action_step(self, step: TestStep, result: TestResult):
        """Handle system action step"""
        print(f"\n⚡  System Action: {step.name}")
        print("Please perform the action described above.")
        
        # For system actions, we typically wait for user confirmation
        await self._get_user_confirmation("Press Enter when the action is complete...")
        
        # Get user feedback on the action
        feedback = input("How did the action complete? (success/failed/partial): ")
        result.actual_result = feedback
        result.user_feedback = input("Any additional observations? ")
        
        if feedback.lower() in ["success", "passed"]:
            result.status = "passed"
        elif feedback.lower() in ["failed", "error"]:
            result.status = "failed"
        else:
            result.status = "partial"
    
    async def _handle_manual_validation_step(self, step: TestStep, result: TestResult):
        """Handle manual validation step"""
        if step.choices:
            try:
                answer = inquirer.prompt([
                    inquirer.List('validation',
                               message=step.user_prompt or "How would you rate this?",
                               choices=step.choices)
                ])
                result.actual_result = answer['validation']
                
                # Determine status based on expected result
                if step.expected_result and "at least" in step.expected_result.lower():
                    # This is a quality threshold check
                    if answer['validation'] in step.choices[-2:]:  # Last two choices are acceptable
                        result.status = "passed"
                    else:
                        result.status = "failed"
                else:
                    result.status = "passed"
                    
            except Exception as e:
                result.status = "error"
                result.error_message = f"Validation selection failed: {e}"
        else:
            feedback = input(f"{step.user_prompt or 'Provide validation feedback'}: ")
            result.actual_result = feedback
            result.status = "passed"
    
    async def _handle_automated_check_step(self, step: TestStep, result: TestResult):
        """Handle automated check step"""
        if step.validation_function:
            try:
                check_result = step.validation_function()
                result.actual_result = str(check_result)
                result.status = "passed" if check_result else "failed"
            except Exception as e:
                result.status = "error"
                result.error_message = f"Automated check failed: {e}"
        else:
            # No validation function provided
            result.status = "skipped"
            result.actual_result = "No validation function provided"
    
    async def _handle_wait_step(self, step: TestStep, result: TestResult):
        """Handle wait step"""
        print(f"Waiting for {step.timeout_seconds} seconds...")
        await asyncio.sleep(step.timeout_seconds)
        result.status = "passed"
        result.actual_result = "Wait completed"
    
    async def _handle_observation_step(self, step: TestStep, result: TestResult):
        """Handle observation recording step"""
        print("Please record your observations:")
        
        observations = []
        while True:
            obs = input("Observation (or press Enter to finish): ")
            if not obs.strip():
                break
            observations.append(obs.strip())
        
        result.observations = observations
        result.actual_result = f"Recorded {len(observations)} observations"
        result.status = "passed"
    
    async def _get_user_confirmation(self, message: str) -> bool:
        """Get user confirmation (yes/no)"""
        while True:
            response = input(f"{message} (yes/no): ").strip().lower()
            if response in ["yes", "y", "no", "n"]:
                return response in ["yes", "y"]
            print("Please enter 'yes' or 'no'")
    
    async def _get_user_feedback(self, message: str) -> str:
        """Get user feedback"""
        return input(f"{message}\nFeedback: ")
    
    def _determine_final_status(self):
        """Determine the final status of the scenario"""
        if not self.current_result:
            return
        
        step_results = self.current_result.step_results
        
        # Count different statuses
        passed = sum(1 for r in step_results if r.status == "passed")
        failed = sum(1 for r in step_results if r.status == "failed")
        errors = sum(1 for r in step_results if r.status == "error")
        skipped = sum(1 for r in step_results if r.status == "skipped")
        
        # Required steps that failed
        required_steps = [s for s in self.current_scenario.steps if s.required]
        required_failed = sum(1 for i, r in enumerate(step_results) 
                          if i < len(required_steps) and required_steps[i].required and r.status in ["failed", "error"])
        
        if required_failed > 0:
            self.current_result.status = "failed"
        elif errors > 0:
            self.current_result.status = "error"
        elif failed > 0 and passed == 0:
            self.current_result.status = "failed"
        elif failed > 0:
            self.current_result.status = "partially_completed"
        else:
            self.current_result.status = "passed"
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            "timestamp": datetime.now().isoformat(),
            "platform": os.name,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "working_directory": os.getcwd(),
            "user": os.getenv("USER", os.getenv("USERNAME", "unknown"))
        }
    
    def _save_result(self, result: ScenarioResult):
        """Save test result to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result.scenario_id}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        
        logger.info(f"Saved test result to: {filepath}")
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Get summary of all test results"""
        if not self.results:
            return {"message": "No test results available"}
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        partially_completed = sum(1 for r in self.results if r.status == "partially_completed")
        errors = sum(1 for r in self.results if r.status == "error")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        
        # Category breakdown
        categories = {}
        for result in self.results:
            scenario = self.scenarios.get(result.scenario_id)
            if scenario:
                category = scenario.category
                if category not in categories:
                    categories[category] = {"total": 0, "passed": 0, "failed": 0}
                categories[category]["total"] += 1
                if result.status == "passed":
                    categories[category]["passed"] += 1
                elif result.status == "failed":
                    categories[category]["failed"] += 1
        
        return {
            "total_scenarios": total,
            "passed": passed,
            "failed": failed,
            "partially_completed": partially_completed,
            "errors": errors,
            "skipped": skipped,
            "success_rate": passed / total if total > 0 else 0,
            "category_breakdown": categories,
            "average_execution_time": sum(r.total_execution_time_seconds for r in self.results) / total if total > 0 else 0
        }


# Convenience function for quick scenario execution
async def run_assisted_test(scenario_id: str, tester_name: Optional[str] = None):
    """Quick function to run a single assisted test scenario"""
    framework = AssistedTestFramework()
    return await framework.run_scenario(scenario_id, tester_name)