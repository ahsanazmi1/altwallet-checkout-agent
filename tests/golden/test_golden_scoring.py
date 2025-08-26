"""Golden tests for AltWallet Checkout Agent scoring."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

import pytest

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"
INPUTS_DIR = GOLDEN_DIR / "inputs"
OUTPUTS_DIR = GOLDEN_DIR / "outputs"


def normalize_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize JSON for comparison by sorting keys and removing trace_id."""
    # Remove trace_id as it's dynamic
    if "trace_id" in data:
        del data["trace_id"]

    # Recursively sort all dictionary keys
    def sort_dict(d):
        if isinstance(d, dict):
            return {k: sort_dict(v) for k, v in sorted(d.items())}
        elif isinstance(d, list):
            return [sort_dict(item) for item in d]
        else:
            return d

    return sort_dict(data)


def run_scorer_on_input(input_file: Path) -> Dict[str, Any]:
    """Run the scorer CLI on an input file and return the JSON result."""
    try:
        # Run the CLI command
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "altwallet_agent",
                "score",
                "--input",
                str(input_file),
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            check=True,
        )

        # Extract the JSON output from the last line (after log messages)
        lines = result.stdout.strip().split("\n")
        json_line = lines[-1]  # Last line should be the JSON output

        return json.loads(json_line)

    except subprocess.CalledProcessError as e:
        pytest.fail(f"CLI command failed: {e.stderr}")
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse JSON output: {e}")


def get_test_cases():
    """Get all test cases from the inputs directory."""
    test_cases = []

    for input_file in INPUTS_DIR.glob("*.json"):
        test_name = input_file.stem
        output_file = OUTPUTS_DIR / f"{test_name}.json"

        if output_file.exists():
            test_cases.append((test_name, input_file, output_file))
        else:
            pytest.skip(f"No expected output file for {test_name}")

    return test_cases


@pytest.mark.parametrize("test_name,input_file,output_file", get_test_cases())
def test_golden_scoring(test_name: str, input_file: Path, output_file: Path):
    """Test that scoring produces expected golden output."""

    # Load expected output
    with open(output_file) as f:
        expected = json.load(f)

    # Run scorer on input
    actual = run_scorer_on_input(input_file)

    # Normalize both for comparison
    expected_normalized = normalize_json(expected)
    actual_normalized = normalize_json(actual)

    # Compare normalized JSON
    assert actual_normalized == expected_normalized, (
        f"Golden test failed for {test_name}\n"
        f"Expected: {json.dumps(expected_normalized, indent=2)}\n"
        f"Actual: {json.dumps(actual_normalized, indent=2)}"
    )


def test_golden_test_structure():
    """Test that the golden test directory structure is correct."""
    assert INPUTS_DIR.exists(), f"Inputs directory not found: {INPUTS_DIR}"
    assert OUTPUTS_DIR.exists(), f"Outputs directory not found: {OUTPUTS_DIR}"

    input_files = list(INPUTS_DIR.glob("*.json"))
    output_files = list(OUTPUTS_DIR.glob("*.json"))

    assert len(input_files) > 0, "No input files found"
    assert len(output_files) > 0, "No output files found"

    # Check that each input has a corresponding output
    input_names = {f.stem for f in input_files}
    output_names = {f.stem for f in output_files}

    missing_outputs = input_names - output_names
    assert not missing_outputs, f"Missing output files for: {missing_outputs}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
