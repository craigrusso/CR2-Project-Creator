# Testing the CLAUSE PROJECT CREATOR

This directory contains tests for the CLAUSE PROJECT CREATOR application. The tests are designed to ensure that the application works correctly and to help identify and fix bugs.

## Available Tests

- **test_save_structure.py**: Tests for the save structure functionality
- **test_template_editor.py**: Tests for the template editor
- **test_structure_editor_integration.py**: Integration tests for structure editor and template manager
- **manual_test_structure_editor.py**: A manual test harness for the structure editor

## Running the Tests

### Running All Tests

The easiest way to run all tests is to use the `run_all_tests.py` script:

```bash
cd /path/to/CLAUSE\ PROJECT\ CREATOR/V4
python3 tests/run_all_tests.py
```

This will:
1. Discover and run all unit tests
2. Prompt you to run manual interactive tests
3. Prompt you to run the main application
4. Generate a test report in the `tests/reports` directory

### Running Individual Tests

You can also run individual test files:

```bash
cd /path/to/CLAUSE\ PROJECT\ CREATOR/V4
python3 -m unittest tests/test_save_structure.py
python3 -m unittest tests/test_template_editor.py
python3 -m unittest tests/test_structure_editor_integration.py
```

### Running the Manual Test Harness

The manual test harness allows you to interactively test the structure editor:

```bash
cd /path/to/CLAUSE\ PROJECT\ CREATOR/V4
python3 tests/manual_test_structure_editor.py
```

This will open a GUI window where you can create new structure editors or edit existing ones.

## Writing New Tests

When adding new tests:

1. Create a new file with the prefix `test_` (e.g., `test_my_feature.py`)
2. Subclass `unittest.TestCase`
3. Add test methods with names starting with `test_`
4. Run your tests to make sure they work

Example:

```python
import unittest

class TestMyFeature(unittest.TestCase):
    def test_something(self):
        self.assertEqual(1 + 1, 2)

if __name__ == '__main__':
    unittest.main()
```

## Test Reports

Test reports are generated in the `tests/reports` directory when you run the `run_all_tests.py` script. These reports include:

- The date and time the tests were run
- A summary of the test results
- The status of each type of test (unit tests, manual tests, main application)

## Tips for Testing

- Make sure to clean up after your tests (closing dialogs, removing temporary files, etc.)
- Use the `setUp` and `tearDown` methods for setup and cleanup
- Use mocks for complex dependencies
- Test edge cases and error conditions
- Keep tests independent of each other 