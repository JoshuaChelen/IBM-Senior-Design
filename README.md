# nlip-stress-testing-agent

An AI-driven performance stress-testing platform built on the NLIP protocol.

The system allows user to describe their application in plain English, automatically generate workload simulations, and identify potential bottlenecks.

![Screenshot of Running the NLIP Stress Testing Agent](application.png)

## Features

- Natural language to application description generation via Ollama
- Queue network modeling from application graphs
- Synthetic workload and latency simulation
- Bottleneck and what-if scenario analysis
- Web UI with NLIP support and follow-up Q&A

## Quick Start

### Prerequisites

- Python 3.10+
- Poetry (Python package manager)
- Ollama

### Installation

```bash
# Clone the repository
git clone https://github.com/JoshuaChelen/nlip-stress-testing-agent.git

# Clone submodules
git submodule update --init --recursive

# Install Python dependencies
poetry --directory nlip\nlip_web install
```

#### Set up Ollama

```bash
# Start ollama
ollama serve

# (Optional) Verify ollama is running
curl http://localhost:11434/api/tags

# Pull required base models
ollama pull granite3-moe
ollama pull llava

# Creating the project models
ollama create nlip-sys-desc -f model/NLIP-sys-desc.Modelfile
ollama create nlip-follow-up -f model/NLIP-follow-up.Modelfile
```

### Running the Application

Run from root:

#### Windows

```bash
.\run_web.bat
# Visit http://localhost:8030/
```

#### macOS

```bash
.\run_web.sh
# Visit http://localhost:8030/

```

## Resources

- [NLIP Documentation](https://nlip-project.org/#/)
- NLIP Repository
  - [NLIP Web](https://github.com/nlip-project/nlip_web)
  - [NLIP Server](https://github.com/nlip-project/nlip_server)
  - [NLIP SDK](https://github.com/nlip-project/nlip_sdk)
