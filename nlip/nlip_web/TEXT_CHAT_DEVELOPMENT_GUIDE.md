# Text Chat Development Guide

![Status](https://img.shields.io/badge/status-complete-success)

This guide provides documentation for the Text Chat interface in the NLIP Web project. The text chat page enables text-only conversations between users and an AI chat bot powered by Ollama.

## Table of Contents

1. [Overview](#overview)
2. [Setup & Installation](#setup--installation)
3. [Running the Server](#running-the-server)
4. [How It Works](#how-it-works)
5. [Testing Guide](#testing-guide)
6. [Code Architecture](#code-architecture)
7. [Adding New Features](#adding-new-features)
8. [Common Issues & Solutions](#common-issues--solutions)
9. [Development Workflow](#development-workflow)

## Overview

The Text Chat interface is a web-based chat application that enables text-only conversations with an AI assistant. It uses the NLIP (Natural Language Interface Protocol) for structured message exchange and maintains conversation state through session correlators.

### Features

- Text-only conversations with simple interface
- Session management maintains conversation history
- Ollama integration for local LLM models
- NLIP protocol for structured message exchange
- FastAPI backend
- Vanilla JavaScript with no framework dependencies

### Use Cases

- General Q&A conversations
- Coding assistance
- Information lookup
- Casual chat interactions

## Setup & Installation

### Prerequisites

- Python 3.10+
- Poetry (install from python-poetry.org)
- Ollama (install from ollama.ai)
- Modern web browser

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/nlip-project/nlip_web.git
   cd nlip_web
   ```

2. Install Python dependencies:
   ```bash
   poetry install
   ```

3. Install and setup Ollama:
   ```bash
   # Install Ollama (visit https://ollama.ai/ for installation instructions)
   # Pull a text chat model
   ollama pull granite3-moe
   # Or use another model like llama3, mistral, etc.
   ```

4. Verify installation:
   ```bash
   poetry run python --version
   ollama list  # Should show your installed models
   ```

### Project Structure

```
nlip_web/
├── nlip_web/
│   ├── text_chat.py      # Text chat backend server
│   ├── genai.py          # Ollama client interface
│   ├── nlip_ext.py       # NLIP extensions and session management
│   └── env.py            # Environment variable utilities
│
├── static/
│   ├── text_chat.html    # Text chat HTML interface
│   ├── chat_script.js    # JavaScript client logic
│   ├── nlip.js           # NLIP protocol library
│   └── styles.css        # Shared CSS styles
│
├── scripts.py            # Helper scripts for running servers
└── pyproject.toml        # Poetry configuration
```

## Running the Server

### Option 1: Using Helper Script

```bash
# Start text chat server on port 8010
poetry run python scripts.py chat --port 8010
```

### Option 2: Direct Python Execution

```bash
# Set environment variables
export LOCAL_PORT=8010
export CHAT_MODEL=granite3-moe
export CHAT_HOST=localhost
export CHAT_PORT=11434

# Run the server
poetry run python nlip_web/text_chat.py
```

### Option 3: Using Poetry Scripts

If configured in `pyproject.toml`:
```bash
poetry run chat
```

### Access the Application

Once the server is running, open your browser to:
- Text Chat Interface: `http://localhost:8010`
- Direct HTML file: `http://localhost:8010/static/text_chat.html`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_PORT` | `8010` | Port for the text chat server |
| `CHAT_MODEL` | `granite3-moe` | Ollama model name for text chat |
| `CHAT_HOST` | `localhost` | Ollama server hostname |
| `CHAT_PORT` | `11434` | Ollama server port |

## How It Works

### Architecture Overview

```
User Browser
     ↓
text_chat.html (HTML interface)
     ↓
chat_script.js (JavaScript client)
     ↓
NLIPClient.sendMessage()
     ↓
FastAPI /nlip/ endpoint (port 8010)
     ↓
text_chat.py ChatSession
     ↓
StatefulGenAI.chat()
     ↓
Ollama API (localhost:11434)
     ↓
Response back through chain
```

### Frontend Flow

1. User types a message in the text input field
2. JavaScript intercepts form submission
3. NLIPClient creates a NLIP text message
4. Message is sent via POST to `/nlip/` endpoint
5. Server response is displayed in the chat box
6. Conversation history is maintained in the DOM

### Backend Flow

1. FastAPI server receives NLIP message at `/nlip/` endpoint
2. ChatSession extracts text and retrieves session correlator
3. Session correlator is used to retrieve or create conversation state
4. StatefulGenAI sends message to Ollama with conversation history
5. Response is formatted as NLIP message and returned
6. Conversation history is updated in StatefulGenAI instance

### Session Management

- Each conversation gets a unique correlator token
- Correlator is stored in NLIPClient and sent with each message
- Backend uses correlator to retrieve conversation history
- History is maintained in StatefulGenAI instance
- Session state persists for the duration of the server process

## Testing Guide

### Quick Testing Checklist

1. Start the server:
   ```bash
   poetry run python scripts.py chat --port 8010
   ```

2. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. Open the interface:
   - Navigate to `http://localhost:8010` in your browser
   - You should see the text chat interface

4. Test basic functionality:
   - Type a message and click Send
   - Verify response appears in chat box
   - Send multiple messages to test conversation history
   - Check browser console for errors

### Test Scenarios

Basic Conversation:
- Send: "Hello, how are you?"
- Expected: Friendly greeting response
- Verify: Response appears in bot-box div

Follow-up Questions:
- Send: "What is Python?"
- Send: "Tell me more about that"
- Expected: Second message should reference previous conversation
- Verify: Conversation context is maintained

Error Handling:
- Stop Ollama server
- Send a message
- Expected: Error message displayed
- Verify: "Error connecting to chat engine" appears

Multiple Sessions:
- Open interface in two browser tabs
- Send different messages in each
- Expected: Each tab maintains separate conversation
- Verify: Different correlators are used

### Browser Console Testing

```javascript
// Check NLIP client
console.log(window.NLIPClient);

// Check if client is initialized
const client = new NLIPClient(window.location.origin);
console.log(client);

// Test message sending manually
client.sendMessage("Test message").then(console.log);
```

### Server Logs

Monitor server output for:
- Session creation messages
- Request/response logging
- Error messages
- Connection status

## Code Architecture

### Frontend Structure

HTML (`static/text_chat.html`):
- Simple structure with description container, chat container, and form
- Links to `styles.css` for styling
- Loads `chat_script.js` as ES6 module

JavaScript (`static/chat_script.js`):
- Imports NLIPClient from `nlip.js`
- Handles form submission
- Creates message pairs (user bubble + bot box)
- Manages chat display and scrolling
- Error handling for connection issues

Key Frontend Components:
```javascript
// NLIPClient initialization
const client = new NLIPClient(window.location.origin);

// Form submission handler
form.addEventListener('submit', async (e) => {
  // Prevent default form submission
  // Create message pair UI
  // Send message via NLIPClient
  // Display response
});
```

### Backend Structure

Main Server (`nlip_web/text_chat.py`):

ChatApplication Class:
- Extends `SafeStatefulApplication`
- Manages server configuration (port, model, host)
- Creates and stores chat sessions
- Handles session data storage

ChatSession Class:
- Extends `StatefulSession`
- Processes incoming NLIP messages
- Extracts text from messages
- Retrieves StatefulGenAI instance using correlator
- Sends messages to Ollama and returns responses

Key Backend Components:
```python
# ChatApplication setup
class ChatApplication(nlip_ext.SafeStatefulApplication):
    def create_stateful_session(self) -> server.NLIP_Session:
        genAI = StatefulGenAI(self.host, self.port, self.model)
        session = ChatSession()
        session.set_correlator()
        self.store_session_data(session.get_correlator(), genAI)
        return session

# ChatSession message processing
class ChatSession(nlip_ext.StatefulSession):
    def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        text = msg.extract_text()
        chat_server = self.nlip_app.retrieve_session_data(self.get_correlator())
        response = chat_server.chat(text)
        return nlip.NLIP_Factory.create_text(response)
```

### Supporting Modules

StatefulGenAI (`nlip_web/genai.py`):
- Manages connection to Ollama
- Maintains conversation history
- Handles chat API calls
- Processes responses

NLIP Extensions (`nlip_web/nlip_ext.py`):
- Provides SafeStatefulApplication base class
- Manages session state
- Handles correlator generation
- WebApplication setup utilities

NLIP Client (`static/nlip.js`):
- NLIP protocol implementation
- Message creation and parsing
- HTTP client for API communication
- Session correlator management

## Adding New Features

### Adding UI Elements

1. Modify HTML (`static/text_chat.html`):
   ```html
   <!-- Add new elements to the HTML structure -->
   <div id="new-feature">...</div>
   ```

2. Update JavaScript (`static/chat_script.js`):
   ```javascript
   // Add event listeners and functionality
   const newFeature = document.getElementById('new-feature');
   // ... implement feature
   ```

3. Style with CSS (`static/styles.css`):
   ```css
   #new-feature {
     /* Add styling */
   }
   ```

### Adding Backend Functionality

1. Modify ChatSession (`nlip_web/text_chat.py`):
   ```python
   class ChatSession(nlip_ext.StatefulSession):
       def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
           # Add custom processing logic
           # Extract additional data from message
           # Process with custom logic
           # Return modified response
   ```

2. Extend StatefulGenAI (`nlip_web/genai.py`):
   ```python
   class StatefulGenAI:
       def custom_method(self, data):
           # Add custom AI processing
           pass
   ```

### Best Practices

- Maintain NLIP Protocol: Always use NLIP messages for communication
- Session Management: Use correlators for session state
- Error Handling: Always handle errors gracefully
- Code Organization: Keep frontend and backend concerns separated
- Testing: Test new features thoroughly before committing

## Common Issues & Solutions

### Server Won't Start

Problem: Server fails to start or port is already in use

Solutions:
- Check if port 8010 is in use: `netstat -ano | findstr :8010` (Windows) or `lsof -i :8010` (Linux/Mac)
- Change port by setting `LOCAL_PORT` environment variable
- Kill process using the port if necessary
- Ensure all dependencies are installed: `poetry install`

### No Response from Chat

Problem: Messages are sent but no response is received

Solutions:
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check if the model is installed: `ollama list`
- Install the model if needed: `ollama pull granite3-moe`
- Check browser console for JavaScript errors
- Check server logs for Python errors
- Verify model name matches environment variable

### Connection Errors

Problem: "Error connecting to chat engine" message appears

Solutions:
- Verify server is running on correct port
- Check CORS settings if accessing from different origin
- Ensure NLIPClient is initialized with correct base URL
- Check network tab in browser developer tools
- Verify firewall isn't blocking connections

### Session Not Persisting

Problem: Conversation history is lost between messages

Solutions:
- Verify correlator is being sent with messages
- Check that StatefulGenAI instance is being stored correctly
- Ensure session data is not being purged prematurely
- Review session storage logic in ChatApplication
- Check browser console for correlator values

### Slow Response Times

Problem: Messages take a long time to get responses

Solutions:
- Check Ollama model size (smaller models are faster)
- Verify Ollama is running locally (not remote)
- Check system resources (CPU, RAM)
- Consider using a faster model
- Check network latency if using remote Ollama

### Model Not Found

Problem: Server reports model not found

Solutions:
- Verify model name is correct: `ollama list`
- Pull the model: `ollama pull granite3-moe`
- Check CHAT_MODEL environment variable matches installed model
- Restart server after pulling new model

## Development Workflow

### Daily Development Process

1. Start development server:
   ```bash
   poetry run python scripts.py chat --port 8010
   ```

2. Make changes:
   - Edit HTML, CSS, or JavaScript files
   - Modify Python backend code
   - Test changes in browser

3. Test thoroughly:
   - Test basic functionality
   - Test error cases
   - Check browser console
   - Verify server logs

4. Commit changes:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```

### Code Review Checklist

- All functionality still works
- No JavaScript errors in console
- No Python errors in server logs
- Error handling is appropriate
- Code follows existing patterns
- Documentation is updated if needed
- Tests pass (if applicable)

### Debugging Tips

Frontend Debugging:
- Use browser developer tools (F12)
- Check Console tab for JavaScript errors
- Use Network tab to inspect API requests
- Use Elements tab to inspect DOM

Backend Debugging:
- Add print statements for debugging
- Check server console output
- Use Python debugger (pdb) if needed
- Review server logs for errors

NLIP Protocol Debugging:
- Log NLIP messages to console
- Inspect message structure
- Verify correlator values
- Check message format matches protocol

## Getting Help

### Resources

- Existing Documentation: 
  - `ARCHITECTURE.md` - System architecture
  - `IMAGE_CHAT_DEVELOPMENT_GUIDE.md` - Image chat development guide
- Code Comments: Check existing code for examples
- Browser Developer Tools: Use F12 to debug issues
- Ollama Documentation: ollama.ai/docs

### Common Commands

```bash
# Start server
poetry run python scripts.py chat --port 8010

# Check Ollama status
curl http://localhost:11434/api/tags

# List Ollama models
ollama list

# Pull a model
ollama pull granite3-moe

# Check port usage
netstat -ano | findstr :8010  # Windows
lsof -i :8010                  # Linux/Mac
```

## Success Criteria

You'll know everything is working when:
- Server starts without errors
- Interface loads in browser
- Messages send successfully
- Responses are received
- Conversation history is maintained
- No errors in browser console
- No errors in server logs
- Multiple messages work correctly
