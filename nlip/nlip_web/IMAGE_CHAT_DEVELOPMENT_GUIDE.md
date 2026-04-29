# Image Chat Development Guide

![Status](https://img.shields.io/badge/status-complete-success)

This guide provides documentation for the Image Chat interface in the NLIP Web project. The image chat page enables multimodal conversations where users can send both text messages and images, receiving text responses that describe or analyze the images.

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

The Image Chat interface is a web-based multimodal chat application that enables conversations with both text and images. It uses the NLIP (Natural Language Interface Protocol) for structured message exchange and maintains conversation state through session correlators.

### Features

- Multimodal conversations: Send text messages with attached images
- Image analysis: AI describes and analyzes uploaded images
- Text-only mode: Can also work as text-only chat when no image is attached
- Session management: Maintains conversation history across messages
- Ollama integration: Uses vision-capable LLM models via Ollama
- NLIP protocol: Structured message exchange using NLIP
- FastAPI backend
- Vanilla JavaScript with no framework dependencies

### Use Cases

- Image description and analysis
- Visual question answering
- Document analysis
- Diagram explanation
- Photo interpretation
- Visual content understanding

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Poetry (install from python-poetry.org)
- Ollama (install from ollama.ai)
- Vision-capable model: Ollama model that supports image input (e.g., `llava`)
- Modern web browser with File API support

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
   # Pull a vision-capable model
   ollama pull llava
   # Other vision models: llava:13b, bakllava, etc.
   ```

4. Verify installation:
   ```bash
   poetry run python --version
   ollama list  # Should show llava or other vision model
   ```

### Project Structure

```
nlip_web/
├── nlip_web/
│   ├── image_chat.py      # Image chat backend server
│   ├── genai.py           # Ollama client interface (with multimodal support)
│   ├── nlip_ext.py        # NLIP extensions and session management
│   └── env.py             # Environment variable utilities
│
├── static/
│   ├── image_chat.html    # Image chat HTML interface
│   ├── image_script.js    # JavaScript client logic
│   ├── nlip.js            # NLIP protocol library
│   └── styles.css         # Shared CSS styles
│
├── scripts.py             # Helper scripts for running servers
└── pyproject.toml         # Poetry configuration
```

---

## Running the Server

### Option 1: Using Helper Script

```bash
# Start image chat server on port 8020
poetry run python scripts.py image --port 8020
```

### Option 2: Direct Python Execution

```bash
# Set environment variables
export LOCAL_PORT=8020
export CHAT_MODEL=llava
export CHAT_HOST=localhost
export CHAT_PORT=11434

# Run the server
poetry run python nlip_web/image_chat.py
```

### Option 3: Using Poetry Scripts

If configured in `pyproject.toml`:
```bash
poetry run image
```

### Access the Application

Once the server is running, open your browser to:
- Image Chat Interface: `http://localhost:8020`
- Direct HTML file: `http://localhost:8020/static/image_chat.html`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_PORT` | `8020` | Port for the image chat server |
| `CHAT_MODEL` | `llava` | Ollama model name (must support vision) |
| `CHAT_HOST` | `localhost` | Ollama server hostname |
| `CHAT_PORT` | `11434` | Ollama server port |

---

## How It Works

### Architecture Overview

```
User Browser
     ↓
image_chat.html (HTML interface)
     ↓
image_script.js (JavaScript client)
     ↓
NLIPClient.sendWithImage() or sendMessage()
     ↓
FastAPI /nlip/ endpoint (port 8020)
     ↓
image_chat.py ChatSession
     ↓
StatefulGenAI.chat_multimodal()
     ↓
Ollama API with images (localhost:11434)
     ↓
Response back through chain
```

### Frontend Flow

1. User types a message in the text input field
2. User optionally selects an image file to attach
3. Selected file name is displayed in file list
4. JavaScript intercepts form submission
5. Message creation:
   - If image attached: NLIPClient creates NLIP message with text and binary image data
   - If no image: NLIPClient creates text-only message
6. Message is sent via POST to `/nlip/` endpoint
7. Server response is displayed in the chat box
8. Conversation history is maintained in the DOM

### Backend Flow

1. FastAPI server receives NLIP message at `/nlip/` endpoint
2. ChatSession extracts text and binary (image) data from message
3. Images are extracted from binary field list (already in base64)
4. Session correlator is used to retrieve or create conversation state
5. StatefulGenAI sends multimodal message to Ollama with images and conversation history
6. Response is formatted as NLIP message and returned
7. Conversation history is updated in StatefulGenAI instance

### Session Management

- Each conversation gets a unique **correlator token**
- Correlator is stored in NLIPClient and sent with each message
- Backend uses correlator to retrieve conversation history
- History is maintained in StatefulGenAI instance
- Images are included in conversation context
- Session state persists for the duration of the server process

### Image Processing

- Images are selected via HTML file input
- JavaScript reads file using FileReader API
- Images are converted to base64 encoding
- Base64 data is included in NLIP message binary field
- Backend extracts base64 images and sends to Ollama
- Ollama processes images with vision model

---

## Testing Guide

### Quick Testing Checklist

1. Start the server:
   ```bash
   poetry run python scripts.py image --port 8020
   ```

2. Verify Ollama is running with vision model:
   ```bash
   curl http://localhost:11434/api/tags
   ollama list  # Should show llava or other vision model
   ```

3. Open the interface:
   - Navigate to `http://localhost:8020` in your browser
   - You should see the image chat interface with file upload option

4. Test basic functionality:
   - Type a text-only message and click Send
   - Upload an image and send a message
   - Verify responses appear in chat box
   - Send multiple messages to test conversation history

### Test Scenarios

**Text-Only Message**:
- Send: "Hello, how are you?" (no image)
- Expected: Normal text response
- Verify: Response appears in bot-box div

**Image with Question**:
- Upload an image (JPG, PNG, etc.)
- Send: "What's in this picture?"
- Expected: Description of image contents
- Verify: Response describes the image

**Follow-up Questions**:
- Upload an image and ask: "What is this?"
- Send: "Tell me more about it"
- Expected: Second message should reference the image
- Verify: Conversation context includes image

**Multiple Images** (if supported):
- Upload multiple images
- Send: "Compare these images"
- Expected: Comparison or analysis
- Verify: All images are processed

**Error Handling**:
- Stop Ollama server
- Send a message with image
- Expected: Error message displayed
- Verify: "Error connecting to chat engine" appears

**Invalid File Types**:
- Try uploading non-image file (e.g., .txt, .pdf)
- Expected: Either rejection or error message
- Verify: Appropriate error handling

### Browser Console Testing

```javascript
// Check NLIP client
console.log(window.NLIPClient);

// Check if client is initialized
const client = new NLIPClient();
console.log(client);

// Test file reading
const fileInput = document.getElementById('file-input');
console.log(fileInput.files);

// Test message sending with image
const file = fileInput.files[0];
if (file) {
  client.sendWithImage("Test message", file).then(console.log);
}
```

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)
- BMP (.bmp)

Note: Images are automatically converted to base64 encoding before transmission.

---

## Code Architecture

### Frontend Structure

**HTML (`static/image_chat.html`)**:
- Structure with description container, chat container, form, and file list
- File input for image selection
- Links to `styles.css` for styling
- Loads `image_script.js` as ES6 module

**JavaScript (`static/image_script.js`)**:
- Imports NLIPClient from `nlip.js`
- Handles file selection and display
- Handles form submission
- Conditionally sends messages with or without images
- Creates message pairs (user bubble + bot box)
- Manages chat display and scrolling
- Error handling for connection issues

**Key Frontend Components**:
```javascript
// NLIPClient initialization
const client = new NLIPClient();

// File selection handler
file.addEventListener('change', () => {
  // Display selected file names
});

// Form submission handler
form.addEventListener('submit', async (e) => {
  // Check if file is selected
  if (file.files.length > 0) {
    // Send with image
    data = await client.sendWithImage(message, file.files[0]);
  } else {
    // Send text only
    data = await client.sendMessage(message);
  }
});
```

### Backend Structure

**Main Server (`nlip_web/image_chat.py`)**:

**ChatApplication Class**:
- Extends `SafeStatefulApplication`
- Manages server configuration (port, model, host)
- Creates and stores chat sessions
- Handles session data storage

**ChatSession Class**:
- Extends `StatefulSession`
- Processes incoming NLIP messages
- Extracts text and binary (image) data from messages
- Retrieves StatefulGenAI instance using correlator
- Sends multimodal messages to Ollama and returns responses

**Key Backend Components**:
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
        images = list()
        # Extract binary (image) data
        binary_contents = msg.extract_field_list("binary")
        for base64_content in binary_contents:
            images.append(base64_content)
        
        chat_server = self.nlip_app.retrieve_session_data(self.get_correlator())
        # Send multimodal message
        response = chat_server.chat_multimodal(text, images=images)
        return nlip.NLIP_Factory.create_text(response)
```

### Supporting Modules

**StatefulGenAI (`nlip_web/genai.py`)**:
- Manages connection to Ollama
- Maintains conversation history
- Handles chat API calls (text-only)
- Handles chat_multimodal API calls (text + images)
- Processes responses

**NLIP Extensions (`nlip_web/nlip_ext.py`)**:
- Provides SafeStatefulApplication base class
- Manages session state
- Handles correlator generation
- WebApplication setup utilities

**NLIP Client (`static/nlip.js`)**:
- NLIP protocol implementation
- Message creation and parsing
- HTTP client for API communication
- Session correlator management
- sendWithImage() method for multimodal messages

---

## Adding New Features

### Adding UI Elements

1. **Modify HTML** (`static/image_chat.html`):
   ```html
   <!-- Add new elements to the HTML structure -->
   <div id="new-feature">...</div>
   ```

2. **Update JavaScript** (`static/image_script.js`):
   ```javascript
   // Add event listeners and functionality
   const newFeature = document.getElementById('new-feature');
   // ... implement feature
   ```

3. **Style with CSS** (`static/styles.css`):
   ```css
   #new-feature {
     /* Add styling */
   }
   ```

### Adding Image Processing Features

1. **Image Preview**:
   ```javascript
   // Add image preview before sending
   const reader = new FileReader();
   reader.onload = (e) => {
     const img = document.createElement('img');
     img.src = e.target.result;
     // Display preview
   };
   reader.readAsDataURL(file);
   ```

2. **Image Validation**:
   ```javascript
   // Validate image file type and size
   if (!file.type.startsWith('image/')) {
     alert('Please select an image file');
     return;
   }
   if (file.size > 10 * 1024 * 1024) { // 10MB limit
     alert('Image too large');
     return;
   }
   ```

3. **Multiple Images**:
   ```javascript
   // Support multiple image uploads
   const images = Array.from(fileInput.files);
   for (const image of images) {
     // Process each image
   }
   ```

### Adding Backend Functionality

1. **Modify ChatSession** (`nlip_web/image_chat.py`):
   ```python
   class ChatSession(nlip_ext.StatefulSession):
       def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
           # Add custom image processing
           # Extract additional data from images
           # Process with custom logic
           # Return modified response
   ```

2. **Extend StatefulGenAI** (`nlip_web/genai.py`):
   ```python
   class StatefulGenAI:
       def custom_multimodal_method(self, text, images, extra_data):
           # Add custom multimodal processing
           pass
   ```

### Best Practices

- **Maintain NLIP Protocol**: Always use NLIP messages for communication
- **Session Management**: Use correlators for session state
- **Image Handling**: Validate images before processing
- **Error Handling**: Always handle errors gracefully
- **Code Organization**: Keep frontend and backend concerns separated
- **Testing**: Test with various image formats and sizes

---

## Common Issues & Solutions

### Server Won't Start

**Problem**: Server fails to start or port is already in use

**Solutions**:
- Check if port 8020 is in use: `netstat -ano | findstr :8020` (Windows) or `lsof -i :8020` (Linux/Mac)
- Change port by setting `LOCAL_PORT` environment variable
- Kill process using the port if necessary
- Ensure all dependencies are installed: `poetry install`

### No Response from Chat

**Problem**: Messages are sent but no response is received

**Solutions**:
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check if vision model is installed: `ollama list`
- Install vision model if needed: `ollama pull llava`
- Verify model supports vision capabilities
- Check browser console for JavaScript errors
- Check server logs for Python errors
- Verify model name matches environment variable

### Image Not Processing

**Problem**: Image is attached but not recognized by the model

**Solutions**:
- Verify image file is valid and not corrupted
- Check image file size (very large images may cause issues)
- Ensure model supports vision (use `llava` or similar)
- Check that image is being converted to base64 correctly
- Review browser console for file reading errors
- Verify image format is supported (JPEG, PNG, etc.)

### Connection Errors

**Problem**: "Error connecting to chat engine" message appears

**Solutions**:
- Verify server is running on correct port
- Check CORS settings if accessing from different origin
- Ensure NLIPClient is initialized correctly
- Check network tab in browser developer tools
- Verify Ollama API is accessible

### Large Image Issues

**Problem**: Large images cause timeouts or errors

**Solutions**:
- Resize images before uploading
- Use compressed image formats (JPEG instead of PNG)
- Increase timeout settings in NLIPClient
- Consider implementing client-side image compression
- Check Ollama model memory requirements
- Reduce image quality/size before sending

### Session Not Persisting

**Problem**: Conversation history is lost between messages

**Solutions**:
- Verify correlator is being sent with messages
- Check that StatefulGenAI instance is being stored correctly
- Ensure session data is not being purged prematurely
- Review session storage logic in ChatApplication
- Check browser console for correlator values
- Verify images are included in conversation context

### Model Not Found or Wrong Model

**Problem**: Server reports model not found or uses wrong model

**Solutions**:
- Verify vision model is installed: `ollama list`
- Pull the correct model: `ollama pull llava`
- Check CHAT_MODEL environment variable matches installed model
- Restart server after pulling new model
- Verify model supports vision (not all models do)

---

## Development Workflow

### Daily Development Process

1. **Start development server**:
   ```bash
   poetry run python scripts.py image --port 8020
   ```

2. **Make changes**:
   - Edit HTML, CSS, or JavaScript files
   - Modify Python backend code
   - Test changes in browser

3. **Test thoroughly**:
   - Test with text-only messages
   - Test with images
   - Test with various image formats
   - Test error cases
   - Check browser console
   - Verify server logs

4. **Commit changes**:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```

### Code Review Checklist

- [ ] All functionality still works
- [ ] Text-only mode works
- [ ] Image upload works
- [ ] No JavaScript errors in console
- [ ] No Python errors in server logs
- [ ] Error handling is appropriate
- [ ] Code follows existing patterns
- [ ] Documentation is updated if needed
- [ ] Tests pass (if applicable)

### Debugging Tips

**Frontend Debugging**:
- Use browser developer tools (F12)
- Check Console tab for JavaScript errors
- Use Network tab to inspect API requests
- Use Elements tab to inspect DOM
- Check file input for selected files
- Verify base64 encoding of images

**Backend Debugging**:
- Add print statements for debugging
- Check server console output
- Log image data (be careful with large base64 strings)
- Use Python debugger (pdb) if needed
- Review server logs for errors

**Image Processing Debugging**:
- Log image file information (name, size, type)
- Verify base64 encoding is correct
- Check image data in NLIP message
- Verify images are extracted correctly in backend
- Test with different image formats

**NLIP Protocol Debugging**:
- Log NLIP messages to console
- Inspect message structure
- Verify binary field contains image data
- Check correlator values
- Verify message format matches protocol

---

## Getting Help

### Resources

- **Existing Documentation**: 
  - `TEXT_CHAT_DEVELOPMENT_GUIDE.md` - Text chat development guide
  - `ARCHITECTURE.md` - System architecture
- **Code Comments**: Check existing code for examples
- **Browser Developer Tools**: Use F12 to debug issues
- **Ollama Documentation**: [ollama.ai/docs](https://ollama.ai/docs)

### Common Commands

```bash
# Start server
poetry run python scripts.py image --port 8020

# Check Ollama status
curl http://localhost:11434/api/tags

# List Ollama models
ollama list

# Pull vision model
ollama pull llava

# Check port usage
netstat -ano | findstr :8020  # Windows
lsof -i :8020                  # Linux/Mac

# Test image processing
# Upload an image through the interface and check logs
```

---

## Success Criteria

You'll know everything is working when:
- Server starts without errors
- Interface loads in browser
- Text-only messages work
- Image upload works
- Messages with images send successfully
- Responses are received (both text and image queries)
- Conversation history is maintained
- Images are included in conversation context
- No errors in browser console
- No errors in server logs
- Multiple messages work correctly

---

This guide should help you understand, develop, and maintain the Image Chat interface.

