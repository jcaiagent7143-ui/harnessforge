---
name: add-unit-test
description: Write a unit test using the project's existing test framework, matching its conventions.
version: 1.0.0
when_to_use: After adding or changing any non-trivial function. Always.
inputs:
  - {name: target_function, type: string, required: true}
  - {name: behavior_under_test, type: string, required: true}
outputs:
  - {name: test_file, type: path}
---

# Add unit test

## Steps

1. **Find an existing test** for a similar function. Match its style — class-based vs functional, parametrize vs loop, mocking style.
2. **Locate the test file**. Conventions vary: `tests/test_foo.py`, `test_foo.py` next to `foo.py`, or `src/foo/_test.py`. Don't invent a new one.
3. **Test the public behavior**, not implementation details. Edge cases first: empty input, boundary values, error paths.
4. **Avoid mocking yfinance / requests / DB clients** by isolating logic from I/O — pass dataframes/dicts to pure functions and let the network boundary live in one place.
5. **Run only the new test first** (`pytest -k test_<name>` or `python -m unittest test_module.TestClass.test_method`) to confirm it actually exercises the change.
6. **Then run the full suite** with `{{ profile.test_command if profile and profile.test_command else "the project test_command" }}`.

## Failure modes to avoid

- Adding pytest fixtures when the project uses plain unittest.
- Testing the test framework instead of the function ("assert test runner works").
- Mocking the world — if you're mocking 5 things to test one function, refactor.
- Writing tests that pass only with the implementation in front of you (write the test first if you can).
