# nlip_web

![Status](https://img.shields.io/badge/status-active-success)
![Documentation](https://img.shields.io/badge/docs-complete-success)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

A NLIP web server with a JavaScript client for displaying products and handling multimodal chat interactions.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Overview

nlip_web is a web application that demonstrates the NLIP (Natural Language Interface Protocol) through three main features:

1. Product Search: Search products across multiple e-commerce stores simultaneously
2. Text Chat: Conversational interface using local LLMs via Ollama
3. Image Chat: Multimodal chat interface supporting text and image inputs

The project uses FastAPI for the backend, React/Vite for modern frontends, and vanilla JavaScript for simple chat interfaces. All communication uses the NLIP protocol for structured message exchange.

## Features

- Website Modules: Product search modules for various stores
- Product Display: Product tables and cards
- Multi-Store Support: Amazon, Walmart, Staples, Newegg, etc.
- Text Chat: Text chat interface
- Image Chat: Multimodal chat with image support
- Session Management: Conversation state tracking

## Quick Start

### Prerequisites

- Python 3.10+
- Poetry (Python package manager)
- Node.js 18+ (for React client, if using)
- Ollama running locally (for chat features)
- Chrome/Chromium (for web scraping)

### Installation

```bash
# Clone the repository
git clone https://github.com/nlip-project/nlip_web.git
cd nlip_web

# Install Python dependencies
poetry install
poetry add beautifulsoup4 selenium requests

# Install client dependencies (if using React frontend)
cd client
npm install
```

### Running the Application

Text Chat Server (Port 8010):
```bash
poetry run python scripts.py chat --port 8010
# Or: poetry run python nlip_web/text_chat.py
# Access at http://localhost:8010
```

Image Chat Server (Port 8020):
```bash
poetry run python scripts.py image --port 8020
# Or: poetry run python nlip_web/image_chat.py
# Access at http://localhost:8020
```

Product Search (CLI):
```bash
./run_main_module.sh
# Or: python3 -m website_modules.main_module "search term"
```

### Access the Application

- Text Chat: `http://localhost:8010` or `http://localhost:8010/static/text_chat.html`
- Image Chat: `http://localhost:8020` or `http://localhost:8020/static/image_chat.html`

## Documentation

Documentation is available for all major components:

- [Text Chat Development Guide](TEXT_CHAT_DEVELOPMENT_GUIDE.md) ![Complete](https://img.shields.io/badge/status-complete-success) - Development guide for text chat interface
- [Image Chat Development Guide](IMAGE_CHAT_DEVELOPMENT_GUIDE.md) ![Complete](https://img.shields.io/badge/status-complete-success) - Development guide for image chat interface
- [Website Modules](website_modules/WEB_MODULES.md) ![Complete](https://img.shields.io/badge/status-complete-success) - Guide for creating and using store modules
- [Architecture](ARCHITECTURE.md) ![Complete](https://img.shields.io/badge/status-complete-success) - System architecture overview
- [Contributing](CONTRIBUTING.md) ![Complete](https://img.shields.io/badge/status-complete-success) - Guidelines for contributors

## Core Functionality

The primary goal is to display products nicely on screen. The system receives JSON product data, parses it, and renders product tables and cards.

## Project Structure

```
nlip_web/
├── nlip_web/              # Python backend modules
│   ├── genai.py          # Ollama client interface
│   ├── text_chat.py      # Text chat server (port 8010)
│   ├── image_chat.py     # Image chat server (port 8020)
│   ├── vite_chat.py      # Product search server (port 8030)
│   └── nlip_ext.py       # NLIP extensions and session management
│
├── website_modules/       # E-commerce scraping modules
│   ├── main_module.py    # Orchestrates all store searches
│   ├── staples_ca_module.py
│   ├── newegg_ca_module.py
│   └── ... (other store modules)
│
├── static/                # Static HTML/JS files
│   ├── text_chat.html    # Text chat interface
│   ├── image_chat.html   # Image chat interface
│   ├── chat_script.js    # Text chat client
│   ├── image_script.js   # Image chat client
│   └── nlip.js          # NLIP protocol library
│
├── client/               # React frontend (if exists)
│   └── src/              # React components
│
└── Documentation files
    ├── README.md         # This file
    ├── ARCHITECTURE.md   # Architecture overview
    └── CONTRIBUTING.md   # Contributing guidelines
```

## Architecture

The system consists of three main applications:

1. Text Chat: Simple HTML interface connecting to Ollama for text conversations
2. Image Chat: HTML interface supporting text and image inputs for multimodal AI
3. Product Search: Web scraping system that searches multiple e-commerce stores in parallel

All applications use the NLIP protocol for structured communication and maintain session state through correlator tokens.

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_PORT` | `8010` (text), `8020` (image), `8030` (products) | Server port |
| `CHAT_MODEL` | `granite3-moe` (text), `llava` (image) | Ollama model name |
| `CHAT_HOST` | `localhost` | Ollama server host |
| `CHAT_PORT` | `11434` | Ollama server port |

### Ollama Setup

Before using chat features, ensure Ollama is running:

```bash
# Install Ollama (if not already installed)
# Visit https://ollama.ai/ for installation instructions

# Pull required models
ollama pull granite3-moe  # For text chat
ollama pull llava          # For image chat

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

## Contributing

We welcome contributions. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Code style and standards
- How to submit pull requests
- Adding new store modules
- Improving documentation
- Reporting issues

## License

Apache-2.0 License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [NLIP Server](https://github.com/nlip-project/nlip_server) - Required dependency
- [NLIP SDK](https://github.com/nlip-project/nlip_sdk) - Development tools

## Support

For questions, issues, or contributions:

- Open an issue on GitHub
- Review the documentation in each component's directory
- Check the troubleshooting sections in component documentation
