# Contributing Guidelines

Thank you for your interest in contributing to SQLActive! Please take a
moment to review this document before submitting a pull request.

## Why should you read these guidelines?

Following these guidelines ensures that your contributions align with
the project's standards, respect the time of maintainers, and facilitate
a smooth collaboration process.

## Ground Rules

### Responsibilities

- Ensure **cross-platform compatibility** for all changes (Windows, macOS,
  Debian, and Ubuntu Linux).
- Follow the **[PEP 8](https://www.python.org/dev/peps/pep-0008/)** style
  guide and use single quotes (`'`) for strings.
- Adhere to **clean code principles**, such as **SOLID**, **DRY**, and
  **KISS**. Avoid unnecessary complexity.
- Use **Active Record** patterns for database interactions where applicable.
- Keep contributions small and focused. One feature or fix per pull request.
- Discuss significant changes or enhancements transparently by opening an
  issue first.
- Be respectful and welcoming. Follow the
  [Python Community Code of Conduct](https://www.python.org/psf/codeofconduct/).

### Tools and Workflow

- Use **Ruff** as the linter and formatter (**Black** could be an alternative).
- Write **NumPy-style docstrings** for all public functions, classes, attributes,
  and properties.
- Commit messages and pull requests must follow specific prefixes described
  [here](#commit-message-format).

## Your First Pull Request

### Getting Started

If this is your first pull request:

- Watch the [How to Contribute to an Open Source Project on GitHub](https://egghead.io/courses/how-to-contribute-to-an-open-source-project-on-github)
  video series.
- Search for existing discussions to ensure your contribution doesn't duplicate
  ongoing efforts.

### Setup Instructions

1. Fork the repository.
2. Clone your fork to your local machine.
3. Set up a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # on Windows: venv\Scripts\activate
    ```
4. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5. Run tests and `Ruff` linter to confirm the setup:
    ```bash
    python -m unittest discover -s tests -t .
    python -m ruff check .
    ```

## Reporting Issues

### Security Issues

For security vulnerabilities, **do not open an issue**. Instead,
email [dairoandres123@gmail.com](mailto:dairoandres123@gmail.com).

In order to determine whether you are dealing with a security issue, ask
yourself these two questions:

* Can I access something that's not mine, or something I shouldn't have
  access to?
* Can I disable something for other people?

If the answer to either of those two questions are "yes", then you're probably
dealing with a security issue.
Note that even if you answer "no" to both questions, you may still be dealing
with a security issue, so if you're unsure, just email
[dairoandres123@gmail.com](mailto:dairoandres123@gmail.com).

### Filing a Bug Report

When reporting a bug, please include:

1. Python version.
2. Operating system and architecture.
3. Steps to reproduce the issue.
4. Expected behavior.
5. Actual behavior, including error messages and stack traces.

General questions should go to the
[python-discuss mailing list](https://www.python.org/community/lists/)
instead of the issue tracker. The Pythonists there will answer or ask you
to file an issue if you have tripped over a bug.

## Suggesting Features or Enhancements

To suggest a feature:

1. Open an issue on the GitHub issues page.
2. Clearly describe the desired feature, its purpose, and its expected behavior.
3. If possible, include examples or PseudoCode.

## Code Conventions

### Code Style

- Follow **PEP 8** guidelines, enforced by **Ruff** and **Black**.
- Use single quotes (`'`) for strings unless escaping becomes cumbersome.
- Write docstrings in **NumPy style**. Example:
    ```python
    def add(a: int, b: int) -> int:
        """
        Add two integers.

        Parameters
        ----------
        a : int
            First integer.
        b : int
            Second integer.

        Returns
        -------
        int
            Sum of the integers.

        Examples
        --------
        >>> add(1, 2)
        3
        """
        return a + b
    ```

### Commit Message Format

Use the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
format for commit messages. It says that the commit message consists of a
**header**, a **body** and a **footer**. The header has a special format that
includes a [**type**](#types), an **optional scope** and a **subject**:

```
<type>(<optional scope>): <subject>
<BLANK LINE>
<optional body>
<BLANK LINE>
<optional footer>
```

Any line of the commit message cannot be longer 100 characters! This allows the
message to be easier to read on GitHub as well as in various git tools.

The footer should contain a [closing reference to an issue](https://help.github.com/articles/closing-issues-via-commit-messages/)
if any.

#### Types

- `build`: Changes that affect the build system or external dependencies.
  Example: "build: Update build-backend in pyproject.toml".
- `ci`: Changes to the CI configuration files and scripts.
  Example: "ci: Add GitHub Actions workflow for testing".
- `docs`: Documentation only changes.
  Example: "docs: Add documentation for new feature".
- `feat`: A new feature.
  Example: "feat: Add support for PostgreSQL database connections".
- `fix`: A bug fix.
  Example: "fix: Resolve issue with incorrect date display".
- `perf`: A code change that improves performance.
  Example: "perf: Optimize database query for faster response times".
- `refactor`: A code change that neither fixes a bug nor adds a feature,
  for example, renaming a variable.
  Example: "refactor: Extract user profile component".
- `revert`: Described [below](#revert).
- `style`: Changes that do not affect the meaning of the code
  (white-space, formatting, missing semi-colons, etc).
  Example: "style: Apply code formatting according to PEP 8".
- `test`: Adding missing tests or correcting existing tests.
  Example: "test: Add unit tests for user service".
- `chore`: Other changes that don't modify src or test files.
  Example: "chore: Update dependencies to latest versions".

#### Revert

If the commit reverts a previous commit, it should begin with `revert:`,
followed by the header of the reverted commit. In the body it should say:
"This reverts commit <hash> because of <reason>.", where the hash is the SHA of
the commit being reverted.

Example:
```
revert: feat: Add support for PostgreSQL database connections

This reverts commit 1234567890abcdef1234567890abcdef12345678 because it
caused a breaking change.
```

### Pull Request Checklist

Before submitting a pull request:

1. Add or update tests for your changes.
2. Ensure all tests pass:
    ```bash
    python -m unittest discover -s tests -t .
    ```
3. Check code linting:
    ```bash
    python -m ruff check .
    ```
4. Update the documentation, if necessary.
5. Provide a clear and descriptive pull request title and description.

Pull requests titles should be short and descriptive, and should not exceed
72 characters. Also, must follow the specified [commit message format](#commit-message-format).
