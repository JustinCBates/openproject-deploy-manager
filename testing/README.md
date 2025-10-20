# Testing Framework - Deploy Manager# Testing Framework Documentation



This directory contains the comprehensive testing framework for the deploy-manager component.Welcome to the OpenProject Configuration Manager testing framework! This directory contains comprehensive testing infrastructure organized for maintainability and clarity.



## 🎯 **Testing Philosophy**## 📁 Directory Structure



We use a structured approach to testing with clear separation of concerns:```

- **Unit Tests**: Test individual deployment components in isolationtesting/

- **Integration Tests**: Test deployment workflows and Docker interactions  ├── unit/                    # Fast unit tests for individual components

- **End-to-End Tests**: Test complete deployment scenarios and rollback workflows├── integration/             # Integration tests for multiple components

├── e2e/                     # End-to-end workflow tests

## 📁 **Directory Structure**├── scripts/                 # Test runner utilities

├── config/                  # Test configuration files

```├── results/                 # Test output and reports (gitignored)

testing/├── documentation/           # Testing guides and documentation

├── unit/                    # Unit tests (fast, isolated)└── env/                     # Virtual environment (gitignored)

│   ├── conftest.py         # Unit test fixtures```

│   └── __init__.py

├── integration/            # Integration tests (components working together)## 🚀 Quick Start

│   ├── conftest.py         # Integration test fixtures

│   └── __init__.py### Run All Tests

├── e2e/                    # End-to-end tests (full workflows)```bash

│   ├── conftest.py         # E2E test fixturescd /opt/openproject/external/config-manager

│   └── __init__.pypython testing/scripts/run_all_tests.py

├── scripts/                # Test execution scripts```

│   ├── run_unit_tests.py   # Run only unit tests

│   ├── run_integration_tests.py  # Run only integration tests  ### Run Specific Test Types

│   ├── run_e2e_tests.py    # Run only e2e tests```bash

│   └── run_all_tests.py    # Run complete test suite# Unit tests only (fast)

├── config/                 # Test configurationpython testing/scripts/run_unit_tests.py

│   └── pytest.ini         # Pytest configuration

├── results/                # Test results and reports# Integration tests only

├── documentation/          # Testing guides and documentationpython testing/scripts/run_integration_tests.py

│   ├── testing_guide.md    # Comprehensive testing guide

│   └── framework_overview.md  # Testing framework overview# End-to-end tests only

└── README.md              # This filepython testing/scripts/run_e2e_tests.py

``````



## 🚀 **Quick Start**### Run Tests with Pytest Directly

```bash

### Run All Tests# All tests

```bashpytest testing/

cd testing

python scripts/run_all_tests.py# Specific test type

```pytest testing/unit/

pytest testing/integration/

### Run Specific Test Typespytest testing/e2e/

```bash

# Unit tests only (fast)# With coverage

python scripts/run_unit_tests.pypytest testing/ --cov=openproject_config_manager --cov-report=html

```

# Integration tests only

python scripts/run_integration_tests.py## 📋 Test Categories



# End-to-end tests only### Unit Tests (`testing/unit/`)

python scripts/run_e2e_tests.py- **Purpose**: Test individual components in isolation

```- **Speed**: Fast (< 1 second per test)

- **Dependencies**: Minimal, heavily mocked

### Run Tests with Pytest Directly- **Files**:

```bash  - `test_core_config.py` - Configuration model tests

# From project root  - `test_ui_console.py` - UI component tests

pytest testing/unit/ -v                    # Unit tests  - `test_discovery_environment.py` - Environment discovery tests

pytest testing/integration/ -v             # Integration tests    - `test_export_cfg_writer.py` - Configuration export tests

pytest testing/e2e/ -v                     # E2E tests  - `test_validation_validator.py` - Validation logic tests

pytest testing/ -v                         # All tests

```### Integration Tests (`testing/integration/`)

- **Purpose**: Test multiple components working together

## 📊 **Current Test Coverage**- **Speed**: Medium (1-10 seconds per test)

- **Dependencies**: Real components, some external dependencies

- **Unit Tests**: Deployment orchestration, template rendering, health checking- **Files**:

- **Integration Tests**: TBD - Docker Compose workflows, container lifecycle management  - `test_integration.py` - Cross-component integration

- **E2E Tests**: TBD - Complete deployment scenarios, rollback workflows  - `test_collector_interactive.py` - Interactive collection flows

  - `test_main_cli.py` - CLI interface integration

## 🔧 **Adding New Tests**

### End-to-End Tests (`testing/e2e/`)

### Unit Tests- **Purpose**: Test complete user workflows

- Add to `testing/unit/`- **Speed**: Slow (10+ seconds per test)

- Focus on testing individual deployment functions/classes- **Dependencies**: Full system, real file I/O

- Use mocks for Docker API and external dependencies- **Files**:

- Should run in <1 second each  - `test_e2e_ui_workflows.py` - Complete configuration workflows



### Integration Tests  ## 🔧 Configuration

- Add to `testing/integration/`

- Test deployment component interactions- **pytest.ini**: Located in `testing/config/pytest.ini`

- May use Docker containers and compose files- **pyproject.toml**: Main project config also contains pytest settings

- Acceptable to run in <30 seconds each- **conftest.py**: Shared fixtures in each test directory



### End-to-End Tests## 📊 Coverage and Reporting

- Add to `testing/e2e/`

- Test complete deployment workflowsTest results and coverage reports are stored in `testing/results/` and are automatically ignored by git.

- May take several minutes to run

- Test real deployment and rollback scenarios## 🏃‍♂️ CI/CD Integration



## 📋 **Test Standards**The GitHub Actions workflow automatically runs all test types in the correct sequence:

1. Unit tests (fast feedback)

1. **Naming**: Test files must start with `test_`2. Integration tests (component interaction)

2. **Documentation**: Each test should have a clear docstring3. E2E tests (full workflows)

3. **Isolation**: Tests should not depend on each other

4. **Cleanup**: Tests should clean up Docker resources they create## 📚 Best Practices

5. **Assertions**: Use descriptive assertion messages

1. **Write unit tests first** - Fast feedback loop

## 🔗 **Related Documentation**2. **Mock external dependencies** in unit tests

3. **Use real components** in integration tests

- [`documentation/testing_guide.md`](documentation/testing_guide.md) - Comprehensive testing guide4. **Test real user scenarios** in E2E tests

- [`documentation/framework_overview.md`](documentation/framework_overview.md) - Framework architecture5. **Keep tests independent** - No test dependencies

- [`config/pytest.ini`](config/pytest.ini) - Pytest configuration details6. **Use descriptive test names** - Clear intent

7. **Maintain test fixtures** in conftest.py files

This testing framework ensures reliability and maintainability of the deploy-manager component.
## 🐛 Debugging Tests

```bash
# Run with verbose output
pytest testing/ -v -s

# Run specific test
pytest testing/unit/test_core_config.py::TestConfiguration::test_basic_config

# Debug with pdb
pytest testing/ --pdb

# See coverage gaps
pytest testing/ --cov=openproject_config_manager --cov-report=html
open htmlcov/index.html
```

---

For more detailed information, see the individual documentation files in this directory.
