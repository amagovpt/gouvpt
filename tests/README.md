## Instructions for testing

# Needs test requirements installed
- pip install -r requirements/test.pip

# Run test suite with
- pytest -v                             # Run tests with output verbose
- pytest -x                             # stop after first failure
- pytest --maxfail=2                    # stop after two failures
- pytest tests/test_gouvpt_saml.py      # Run specific test