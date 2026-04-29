# Architecture Documentation

![Status](https://img.shields.io/badge/status-complete-success)

This document provides an overview of the nlip_web system architecture, components, and data flow.

## System Overview

nlip_web is a multi-application system that demonstrates the NLIP (Natural Language Interface Protocol) through three distinct interfaces:

1. **Text Chat Application** - Port 8010
2. **Image Chat Application** - Port 8020  
3. **Product Search Application** - Port 8030

All applications share common infrastructure for NLIP protocol handling and session management.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
├─────────────────────────────────────────────────────────────┤
│  HTML/JS Pages          React Frontend      CLI Tools        │
│  (text_chat.html)       (Products.jsx)      (main_module)    │
│  (image_chat.html)      (SearchForm.jsx)                     │
└────────────────────┬──────────────────┬─────────────────────┘
                     │                  │
                     ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    NLIP Protocol Layer                       │
├─────────────────────────────────────────────────────────────┤
│  NLIPClient (JS)          NLIP Messages                      │
│  - Text messages          - Structured format               │
│  - Binary data            - Session correlators             │
│  - JSON data              - Multi-format support            │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Server Layer                       │
├─────────────────────────────────────────────────────────────┤
│  text_chat.py      image_chat.py      vite_chat.py          │
│  (Port 8010)       (Port 8020)        (Port 8030)           │
│                                                              │
│  - ChatSession     - ChatSession      - ChatSession         │
│  - Session Mgmt    - Multimodal       - Product Search      │
└────────────────────┬──────────────────┬────────────────────┘
                     │                  │
                     ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Logic Layer                     │
├─────────────────────────────────────────────────────────────┤
│  StatefulGenAI              Website Modules                  │
│  - Ollama integration       - Store scrapers                 │
│  - Conversation history     - Parallel execution             │
│  - Multimodal support       - JSON aggregation              │
└────────────────────┬──────────────────┬────────────────────┘
                     │                  │
                     ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
├─────────────────────────────────────────────────────────────┤
│  Ollama API              E-commerce Websites                │
│  (localhost:11434)       (Staples, Newegg, etc.)            │
│  - LLM models            - Product data                      │
│  - Vision models         - Web scraping                      │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Text Chat Application

**Purpose**: Provide text-based conversational interface

**Components**:
- Frontend: `static/text_chat.html` + `static/chat_script.js`
- Backend: `nlip_web/text_chat.py`
- Protocol: NLIP text messages
- AI: Ollama with text models (granite3-moe)

**Flow**:
```
User Input → NLIPClient → FastAPI → ChatSession → StatefulGenAI → Ollama
                                                                    ↓
Response ← NLIPClient ← FastAPI ← ChatSession ← StatefulGenAI ←────┘
```

**Session Management**:
- Each conversation gets unique correlator token
- StatefulGenAI maintains conversation history
- Session data stored in memory (purged after 1 hour inactivity)

### 2. Image Chat Application

**Purpose**: Provide multimodal conversational interface (text + images)

**Components**:
- Frontend: `static/image_chat.html` + `static/image_script.js`
- Backend: `nlip_web/image_chat.py`
- Protocol: NLIP messages with binary image data
- AI: Ollama with vision models (llava)

**Flow**:
```
User Input + Image → NLIPClient → FastAPI → ChatSession → StatefulGenAI → Ollama
  (base64 encoded)                                                          ↓
Response ← NLIPClient ← FastAPI ← ChatSession ← StatefulGenAI ←────────────┘
```

**Image Processing**:
- Images converted to base64 in JavaScript
- Sent as binary field in NLIP message
- Extracted and passed to Ollama API
- Vision model processes image + text together

### 3. Product Search Application

**Purpose**: Search products across multiple e-commerce stores

**Components**:
- Frontend: React components (Products.jsx, SearchForm.jsx)
- Backend: `nlip_web/vite_chat.py` + `website_modules/main_module.py`
- Protocol: NLIP JSON messages
- Scraping: Selenium + BeautifulSoup

**Flow**:
```
User Search → React → NLIPClient → FastAPI → ChatSession → main_module
                                                              ↓
Results ← React ← NLIPClient ← FastAPI ← ChatSession ←────────┘
                                                              ↓
                    Parallel Store Scraping
                    ┌──────┬──────┬──────┐
                    │      │      │      │
                  Staples Newegg Dellelce
                    │      │      │      │
                    └──────┴──────┴──────┘
                              ↓
                    Aggregated JSON Results
```

**Parallel Execution**:
- ThreadPoolExecutor runs up to 4 store searches simultaneously
- Each store module runs independently
- Results collected and aggregated into single JSON response

## NLIP Protocol

The NLIP (Natural Language Interface Protocol) provides structured message format:

### Message Structure

```json
{
  "messagetype": null,
  "format": "text",
  "subformat": "english",
  "content": "Hello",
  "label": null,
  "submessages": [
    {
      "format": "token",
      "subformat": "conversation",
      "content": "correlator-uuid",
      "label": null
    }
  ]
}
```

### Supported Formats

- **Text**: Plain text messages
- **Binary**: Images, files (base64 encoded)
- **Structured**: JSON data
- **Token**: Session correlators, authentication

### Session Management

- **Correlator Tokens**: Unique identifiers for conversations
- **Session Storage**: In-memory dictionary with timeout
- **State Preservation**: Conversation history maintained per session

## Data Flow Examples

### Text Chat Flow

1. User types "Hello" in browser
2. JavaScript creates NLIP text message
3. If correlator exists, adds it to message
4. POST to `/nlip/` endpoint
5. Server extracts correlator, retrieves session
6. StatefulGenAI adds message to history
7. Sends to Ollama with full context
8. Response added to history
9. NLIP message returned with correlator
10. JavaScript displays response

### Product Search Flow

1. User enters "laptop" in search form
2. React sends NLIP JSON message
3. Server receives, extracts search term
4. main_module.search_product() called
5. ThreadPoolExecutor distributes to store modules
6. Each module:
   - Opens store website with Selenium
   - Performs search
   - Scrapes product data with BeautifulSoup
   - Returns JSON
7. Results aggregated into single response
8. NLIP JSON message returned
9. React displays products in cards

## Session Management

### Session Lifecycle

1. **Creation**: New correlator generated on first request
2. **Storage**: StatefulGenAI instance stored with correlator
3. **Retrieval**: Subsequent requests use correlator to find session
4. **Update**: Session touched timestamp updated on access
5. **Purge**: Sessions older than 1 hour automatically removed

### Session Data Structure

```python
SessionState(
    session_data=StatefulGenAI(...),  # Conversation state
    touched=timestamp                 # Last access time
)
```

## Error Handling

### Client-Side

- Network errors caught and displayed to user
- Timeout handling (30 second default)
- Graceful degradation for missing features

### Server-Side

- Session not found: Returns error message
- Ollama connection failure: Returns error
- Module scraping failure: Logged, continues with other modules
- Invalid NLIP message: Returns error response

## Scalability Considerations

### Current Limitations

- Session storage in memory (lost on restart)
- Single-threaded server per application
- No load balancing
- No persistent storage

### Future Improvements

- Database-backed session storage
- Redis for distributed sessions
- Multiple worker processes
- Caching for product search results
- Rate limiting

## Security Considerations

### Current State

- No authentication required
- Sessions accessible via correlator token
- No input validation beyond basic checks
- Web scraping may violate some sites' terms of service

### Recommendations

- Add authentication for production use
- Validate and sanitize all inputs
- Implement rate limiting
- Use official APIs where available instead of scraping
- Add CORS configuration for production

## Dependencies

### Python Backend

- FastAPI: Web framework
- nlip-server, nlip-sdk: NLIP protocol
- httpx: HTTP client for Ollama
- Selenium: Web browser automation
- BeautifulSoup4: HTML parsing

### JavaScript Frontend

- Native fetch API: HTTP requests
- ES6 modules: Code organization
- No external dependencies for chat interfaces
- React + Vite for product search (if used)

### External Services

- Ollama: Local LLM server
- Chrome/Chromium: Browser for Selenium
- E-commerce websites: Scraping targets

## Configuration

All configuration via environment variables:

- `LOCAL_PORT`: Server port
- `CHAT_MODEL`: Ollama model name
- `CHAT_HOST`: Ollama server host
- `CHAT_PORT`: Ollama server port

See [README.md](README.md) for detailed configuration options.

## Related Documentation

- [Website Modules](website_modules/WEB_MODULES.md) - Store module architecture
- [Text Chat Development Guide](TEXT_CHAT_DEVELOPMENT_GUIDE.md) - Text chat implementation details
- [Image Chat Development Guide](IMAGE_CHAT_DEVELOPMENT_GUIDE.md) - Image chat implementation details
- [Contributing](CONTRIBUTING.md) - Development guidelines



