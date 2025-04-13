# Developer Guidelines

This document provides guidelines for developers working on the SensorPy project. It covers best practices for writing code, modifying the codebase, and using the provided development tools.

## 1. Code Style and Conventions

- **PEP8 Compliance:**  
  Write code that adheres to [PEP8](https://www.python.org/dev/peps/pep-0008/). Use tools like [Black](https://black.readthedocs.io/) and [isort](https://pycqa.github.io/isort/) to format and sort your code automatically.

- **Naming Conventions:**  
  - **Classes:** Use PascalCase (e.g., `SensorManager`, `STC31CSensor`).
  - **Functions/Variables:** Use snake_case (e.g., `initialize_sensor`, `read_data`).
  - **Constants:** Use UPPER_SNAKE_CASE (e.g., `SENSOR_TIMEOUT`).

- **File Organization:**  
  Maintain clear separation between modules:
  - **`sensorpy/`** contains the library code.
  - **`drivers_c/`** holds the C driver sources and build files.
  - **`tests/`** includes unit tests.
  - **`docs/`** is reserved for documentation (this file and others).

## 2. Writing Docstrings and Comments

- **Module-Level Docstrings:**  
  Each Python file should start with a module-level docstring that explains its purpose.

- **Public API Documentation:**  
  All public classes, functions, and methods should have docstrings in [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html) that describe parameters, return types, side effects, and any raised exceptions.

- **Inline Comments:**  
  Use inline comments sparingly to explain non-obvious logic. Comments should be clear and up-to-date.

## 3. Error Handling and Exceptions

- **Custom Exceptions:**  
  Use the custom exceptions defined in `sensorpy/exceptions.py` (e.g., `InitializationError`, `ReadError`) for sensor-specific error conditions.

- **Catching and Logging Errors:**  
  Always log exceptions at an appropriate level (e.g., `ERROR` or `WARNING`) without silently suppressing errors.

## 4. Development Tools and Best Practices

### Code Formatting and Static Analysis

- **Black:**  
  Run Black to auto-format code:
  ```bash
  black sensorpy tests examples
  ```
- **isort:**  
  Sort imports using isort:
  ```bash
  isort sensorpy tests examples
  ```
- **mypy:**  
  Run mypy for static type checking:
  ```bash
  mypy sensorpy tests examples
  ```

### Testing

- **Pytest:**  
  Run tests with pytest:
  ```bash
  pytest --cov-config=.coveragerc --cov=sensorpy --cov-report term-missing
  ```
- **Writing Tests:**  
  - Keep tests small and focused.
  - Use fixtures and mocks to isolate functionality.
  - Cover edge cases, including error conditions.

### Version Control

- **Git Workflow:**  
  - Create feature branches for new functionality.
  - Write clear commit messages.
  - Ensure tests pass before merging to the main branch.
  - Follow the repository’s style for submodule updates (e.g., the C drivers in `drivers_c/`).

## 5. General Documentation Best Practices

- **Keep Documentation Up-to-Date:**  
  Update documentation when modifying APIs or adding new features.

- **Examples and Tutorials:**  
  Include examples (like `examples/basic_usage.py`) and step-by-step tutorials for using the sensors.

- **Consistent Style:**  
  Use Markdown for documentation files. Organize content with headers, lists, and code blocks.

- **Tooling:**  
  Consider using tools like [Sphinx](https://www.sphinx-doc.org/) or [MkDocs](https://www.mkdocs.org/) for generating HTML documentation from Markdown files.