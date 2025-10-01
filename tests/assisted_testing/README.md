# Assisted Testing Framework

## Overview

The Assisted Testing Framework provides interactive testing scenarios for components that cannot be fully automated, particularly voice input/output functionality. This framework guides users through manual testing steps while collecting structured feedback and results.

## Features

- **Interactive Test Scenarios**: Step-by-step guided testing with user prompts
- **Voice-Specific Testing**: Comprehensive scenarios for voice input, output, and workflows
- **Result Collection**: Structured collection of test results and user feedback
- **Flexible Framework**: Extensible system for creating custom test scenarios
- **Multiple Output Formats**: JSON and text reports for test results

## Installation

The assisted testing framework is included in the voice-rag-system project. No additional installation is required.

## Quick Start

### 1. List Available Scenarios

```bash
cd voice-rag-system
python -m tests.assisted_testing.runner --list
```

### 2. Run a Specific Scenario

```bash
python -m tests.assisted_testing.runner --scenario voice_input_comprehensive
```

### 3. Run All Voice Tests

```bash
python -m tests.assisted_testing.runner --run-all --framework voice
```

### 4. Interactive Mode

```bash
python -m tests.assisted_testing.runner
```

## Available Test Scenarios

### Voice Input Testing

#### `voice_input_comprehensive`
- **Description**: Test voice input functionality with real microphone input and transcription
- **Duration**: ~10 minutes
- **Difficulty**: Medium
- **Steps**:
  1. Microphone setup verification
  2. Basic voice recording test
  3. Voice transcription accuracy test
  4. Noise handling test
  5. Overall quality assessment

### Voice Output Testing

#### `voice_output_comprehensive`
- **Description**: Test text-to-speech output quality, clarity, and different voice options
- **Duration**: ~12 minutes
- **Difficulty**: Medium
- **Steps**:
  1. Audio output setup verification
  2. Basic TTS functionality test
  3. Different voice options test
  4. Speech speed variations test
  5. Long text processing test
  6. Overall quality assessment

### Voice Workflow Testing

#### `voice_workflow_complete`
- **Description**: Test complete voice workflow: speech → text → processing → speech
- **Duration**: ~15 minutes
- **Difficulty**: Hard
- **Steps**:
  1. Workflow setup (input/output devices)
  2. Voice to text conversion
  3. Transcription validation
  4. Text processing
  5. Text to voice conversion
  6. Complete workflow validation

### Voice UI Integration Testing

#### `voice_ui_integration`
- **Description**: Test voice functionality integrated with the user interface
- **Duration**: ~10 minutes
- **Difficulty**: Medium
- **Steps**:
  1. UI navigation to voice interface
  2. Voice button functionality test
  3. Voice recording UI indicators test
  4. Voice playback UI indicators test
  5. Voice settings UI test
  6. Overall UI integration assessment

### Voice Error Handling Testing

#### `voice_error_handling`
- **Description**: Test how the system handles various voice-related errors
- **Duration**: ~12 minutes
- **Difficulty**: Hard
- **Steps**:
  1. Microphone permission denied test
  2. No audio input test
  3. Unrecognized speech test
  4. Network connectivity issues test
  5. Overall error handling assessment

## Command Line Interface

### Basic Commands

```bash
# List all available scenarios
python -m tests.assisted_testing.runner --list

# List scenarios by category
python -m tests.assisted_testing.runner --list --category voice_input

# Run a specific scenario
python -m tests.assisted_testing.runner --scenario voice_input_comprehensive

# Run all scenarios in a category
python -m tests.assisted_testing.runner --run-category voice_input

# Run all scenarios
python -m tests.assisted_testing.runner --run-all

# Interactive mode
python -m tests.assisted_testing.runner
```

### Advanced Options

```bash
# Specify tester name
python -m tests.assisted_testing.runner --scenario voice_input_comprehensive --tester "John Doe"

# Custom output directory
python -m tests.assisted_testing.runner --run-all --output-dir ./custom_results

# Generate JSON report
python -m tests.assisted_testing.runner --run-all --report json

# Verbose output
python -m tests.assisted_testing.runner --run-all --verbose

# Filter by framework
python -m tests.assisted_testing.runner --list --framework voice
```

## Test Results

### Result Structure

Each test scenario generates a structured result with the following information:

```json
{
  "scenario_id": "voice_input_comprehensive",
  "scenario_name": "Comprehensive Voice Input Testing",
  "status": "passed",
  "step_results": [
    {
      "step_id": "microphone_setup",
      "status": "passed",
      "actual_result": "yes",
      "execution_time_seconds": 5.2,
      "timestamp": "2025-01-15T10:30:00"
    }
  ],
  "overall_feedback": "Voice input worked well with good accuracy",
  "total_execution_time_seconds": 612.5,
  "started_at": "2025-01-15T10:30:00",
  "completed_at": "2025-01-15T10:40:12",
  "tester_name": "John Doe",
  "environment_info": {
    "platform": "Windows",
    "python_version": "3.9.0"
  }
}
```

### Output Files

Test results are saved to `./tests/assisted_testing/results/` with the following files:

- `session_{timestamp}.json`: Complete session results
- `{scenario_id}_{timestamp}.json`: Individual scenario results
- `session_{timestamp}_report.txt`: Human-readable report

## Creating Custom Test Scenarios

### Basic Scenario Structure

```python
from voice_rag_system.tests.assisted_testing.core import (
    TestScenario, TestStep, TestStepType
)

# Create a custom scenario
custom_scenario = TestScenario(
    id="my_custom_test",
    name="My Custom Test",
    description="A custom test scenario",
    category="custom",
    steps=[
        TestStep(
            id="step1",
            name="First Step",
            description="Description of the first step",
            step_type=TestStepType.USER_INPUT,
            instructions="What the user should do",
            user_prompt="Enter your response:",
            expected_result="Expected outcome"
        )
    ],
    estimated_duration_minutes=5,
    difficulty_level="easy"
)

# Add to framework
framework = AssistedTestFramework()
framework.add_scenario(custom_scenario)
```

### Step Types

1. **USER_INPUT**: Collect input from user
2. **SYSTEM_ACTION**: Perform system action with user confirmation
3. **MANUAL_VALIDATION**: User validates something manually
4. **AUTOMATED_CHECK**: Automated validation with custom function
5. **WAIT_FOR_USER**: Wait for user action
6. **RECORD_OBSERVATION**: Record user observations

### Validation Functions

```python
def my_validation_function():
    """Custom validation function"""
    # Perform validation logic
    return True  # or False

step = TestStep(
    id="validation_step",
    name="Validation Step",
    description="Step with custom validation",
    step_type=TestStepType.AUTOMATED_CHECK,
    instructions="Instructions for validation",
    validation_function=my_validation_function
)
```

## Best Practices

### For Testers

1. **Prepare Environment**: Ensure microphone and speakers are working before starting
2. **Follow Instructions**: Read each step carefully and follow instructions precisely
3. **Provide Honest Feedback**: Give accurate and detailed feedback for each step
4. **Document Issues**: Note any problems or unexpected behavior
5. **Take Breaks**: Voice testing can be tiring, take breaks between scenarios

### For Developers

1. **Clear Instructions**: Write clear, concise instructions for each step
2. **Realistic Expectations**: Set appropriate expected results
3. **Error Handling**: Handle errors gracefully and provide helpful messages
4. **Progress Feedback**: Give users clear feedback on progress
5. **Result Analysis**: Analyze results to identify patterns and issues

## Troubleshooting

### Common Issues

1. **Microphone Not Working**:
   - Check microphone connection
   - Verify system microphone permissions
   - Test with other applications

2. **No Audio Output**:
   - Check speaker/headphone connection
   - Verify system audio settings
   - Check volume levels

3. **Permission Errors**:
   - Grant microphone permissions when prompted
   - Run as administrator if needed

4. **Import Errors**:
   - Ensure all dependencies are installed
   - Check Python path configuration
   - Verify voice services are available

### Debug Mode

Run with verbose output for debugging:

```bash
python -m tests.assisted_testing.runner --verbose --scenario voice_input_comprehensive
```

## Integration with CI/CD

While assisted testing requires human interaction, the framework can be integrated into CI/CD pipelines for:

1. **Test Availability**: Verify test scenarios are properly configured
2. **Result Collection**: Collect and analyze human test results
3. **Reporting**: Generate comprehensive test reports
4. **Trend Analysis**: Track test results over time

Example CI integration:

```bash
# Verify test framework is working
python -m tests.assisted_testing.runner --list

# Generate template for manual testing
python -m tests.assisted_testing.runner --scenario voice_input_comprehensive --dry-run
```

## Contributing

To add new test scenarios:

1. Create scenario in appropriate category file
2. Follow existing naming conventions
3. Include clear instructions and expected results
4. Test the scenario thoroughly
5. Update documentation

## Support

For issues or questions about the assisted testing framework:

1. Check this documentation
2. Review existing test scenarios for examples
3. Check log files for error details
4. Contact the development team

## License

This framework is part of the voice-rag-system project and follows the same license terms.