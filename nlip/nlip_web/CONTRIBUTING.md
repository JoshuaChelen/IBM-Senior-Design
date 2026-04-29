# Contributing to nlip_web

![Status](https://img.shields.io/badge/status-complete-success)

Thank you for your interest in contributing to nlip_web. This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)
- [Testing](#testing)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/nlip_web.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10+
- Poetry
- Node.js 18+ (if working on React frontend)
- Ollama (for testing chat features)
- Chrome/Chromium (for testing web scraping)

### Setup Steps

```bash
# Install Python dependencies
poetry install
poetry add beautifulsoup4 selenium requests

# Install development dependencies (if any)
poetry add --group dev pytest black flake8

# Install client dependencies (if working on frontend)
cd client
npm install
```

## Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

1. Bug Fixes: Fix issues in existing code
2. New Features: Add new functionality
3. Documentation: Improve or add documentation
4. Store Modules: Add support for new e-commerce stores
5. Code Improvements: Refactor, optimize, or improve code quality
6. Testing: Add or improve tests

### Before You Start

- Check existing issues to see if your idea is already being worked on
- For major changes, open an issue first to discuss
- Ensure your changes align with the project's goals

## Code Style

### Python

- Follow PEP 8 style guide
- Use type hints where appropriate
- Keep functions focused and small
- Add docstrings for public functions and classes

Example:

```python
def search_product(product_name: str) -> str:
    """
    Search for products on the store's website.
    
    Args:
        product_name: The search query
        
    Returns:
        JSON string with product results
    """
    # Implementation
    pass
```

### JavaScript

- Use ES6+ features
- Follow consistent naming conventions
- Add comments for complex logic
- Keep functions focused

Example:

```javascript
/**
 * Sends a message to the chat server
 * @param {string} message - The message text
 * @returns {Promise<string>} Server response
 */
async function sendMessage(message) {
    // Implementation
}
```

### Markdown Documentation

- Use clear headings and structure
- Include code examples where helpful
- Keep language simple and direct
- Update table of contents when adding sections

## Submitting Changes

### Commit Messages

Write clear, descriptive commit messages:

```
Add support for Best Buy store module

- Implement search_product() function
- Add CSS selectors for product data
- Update main_module.py to include new module
- Add documentation for Best Buy module
```

### Pull Request Process

1. Update Documentation: If your change affects functionality, update relevant docs
2. Add Tests: Include tests for new features (if test framework exists)
3. Check Compatibility: Ensure changes work with existing code
4. Update CHANGELOG: Document your changes (if CHANGELOG exists)

### Pull Request Template

When creating a PR, include:

- Description of changes
- Related issues (if any)
- Testing performed
- Screenshots (if UI changes)
- Checklist of completed items

## Documentation

### When to Update Documentation

- Adding new features
- Changing existing behavior
- Fixing bugs that affect user experience
- Adding new store modules
- Changing configuration options

### Documentation Standards

- Use clear, simple language
- Include code examples
- Add troubleshooting sections for complex features
- Keep documentation up to date with code changes

### Documentation Files

- `README.md`: Main project overview
- `ARCHITECTURE.md`: System architecture
- `CONTRIBUTING.md`: This file
- Component-specific docs in their directories

## Adding New Store Modules

If you're adding a new e-commerce store module:

1. Create new module file: `website_modules/store_name_module.py`
2. Implement `search_product()` function
3. Follow existing module patterns
4. Test with various search terms
5. Add to `main_module.py` search_modules list
6. Update `website_modules/WEB_MODULES.md` status table
7. Document any special requirements

See [Website Modules Documentation](website_modules/WEB_MODULES.md) for detailed instructions.

## Testing

### Manual Testing

Before submitting, test your changes:

- Text Chat: Start server, test conversations
- Image Chat: Test with various image types
- Product Search: Test with different search terms
- Store Modules: Test scraping with multiple queries

### Testing Checklist

- Code runs without errors
- No console errors in browser
- All features work as expected
- Error handling works correctly
- Documentation is updated

## Reporting Issues

When reporting bugs or requesting features:

1. Check if issue already exists
2. Use clear, descriptive title
3. Include steps to reproduce
4. Provide environment details (OS, Python version, etc.)
5. Include error messages or logs
6. Add screenshots if relevant

## Code Review Process

- All PRs require review before merging
- Address review comments promptly
- Be open to feedback and suggestions
- Ask questions if something is unclear

## Questions?

- Open an issue with the "question" label
- Check existing documentation
- Review code comments and examples

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md (if exists)
- Release notes
- Project documentation

Thank you for contributing to nlip_web!
