# Streaming Response Implementation for Agent

This document explains the streaming functionality implemented in `chatbot/tools/agent.py`.

## Overview

The Agent class now supports streaming responses, allowing text to be processed and displayed as it's generated rather than waiting for the complete response. This improves user experience by providing real-time feedback.

## Features Added

### 1. Streaming Callback Support

- Added `streaming_callback` property to the Agent class
- When set, the callback function receives text chunks as they're generated
- Automatic streaming detection in `_generate_response` method

### 2. Three Streaming Methods

#### `set_streaming_callback(callback)`

Set a callback function to receive streaming chunks:

```python
def my_callback(chunk: str):
    print(f"Received: {chunk}", end="", flush=True)

agent = Agent()
agent.set_streaming_callback(my_callback)
response = agent.call_agent("What is Bitcoin?")
```

#### `call_agent_simple_stream(prompt)`

Simple streaming without tools - returns a generator:

```python
agent = Agent()
for chunk in agent.call_agent_simple_stream("Explain blockchain"):
    print(chunk, end="", flush=True)
```

#### `call_agent_stream(prompt, max_iterations=20)`

Full agent streaming with tools support:

```python
agent = Agent()
for chunk in agent.call_agent_stream("Calculate 10 + 20"):
    print(chunk, end="", flush=True)
```

### 3. Internal Streaming Implementation

#### `_generate_streaming_response(contents, state)`

- Uses `client.models.generate_content_stream()` for streaming
- Calls the streaming callback for each text chunk
- Accumulates complete response for further processing
- Maintains compatibility with tool calling workflow

## Usage Examples

### Basic Streaming

```python
from chatbot.tools.agent import Agent

agent = Agent()

# Method 1: Simple streaming
for chunk in agent.call_agent_simple_stream("What is cryptocurrency?"):
    print(chunk, end="", flush=True)

# Method 2: Callback-based streaming
def stream_handler(chunk):
    print(chunk, end="", flush=True)

agent.set_streaming_callback(stream_handler)
response = agent.call_agent("Explain Bitcoin mining")
```

### Advanced Streaming with Tools

```python
# Stream responses that may involve tool calls
agent = Agent()

def my_callback(chunk: str):
    # Handle each chunk (e.g., send to websocket, update UI)
    print(f"Streaming: {chunk}")

agent.set_streaming_callback(my_callback)
result = agent.call_agent("Calculate the square root of 144")
```

### Web Application Integration

```python
# Example for Django views or FastAPI endpoints
from django.http import StreamingHttpResponse
import json

def stream_chat_response(request):
    agent = Agent()
    prompt = request.POST.get('message')

    def generate():
        for chunk in agent.call_agent_simple_stream(prompt):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingHttpResponse(generate(), content_type='text/plain')
```

## Technical Details

### Streaming Flow

1. User calls streaming method
2. Agent sets internal streaming callback
3. `_generate_response` detects callback and uses `_generate_streaming_response`
4. Text chunks are streamed via `generate_content_stream()`
5. Each chunk triggers the callback function
6. Complete response is assembled for tool processing
7. Tool execution continues normally (non-streaming)
8. Final response combines all iterations

### Compatibility

- Backward compatible - existing `call_agent()` works unchanged
- Tool calling workflow preserved
- LangGraph state management maintained
- Error handling includes streaming scenarios

### Performance Considerations

- Streaming reduces perceived latency
- Memory usage stays constant (chunks processed immediately)
- Network efficiency for real-time applications
- CPU overhead minimal (callback execution)

## Integration Examples

### With Django Views

```python
# In chatbot/views.py
from django.http import StreamingHttpResponse
from .tools.agent import Agent

def stream_response(request):
    agent = Agent()
    prompt = request.POST.get('prompt')

    def generate():
        for chunk in agent.call_agent_simple_stream(prompt):
            yield chunk

    return StreamingHttpResponse(generate(), content_type='text/plain')
```

### With WebSockets

```python
import asyncio
import websockets
from chatbot.tools.agent import Agent

async def websocket_handler(websocket, path):
    agent = Agent()

    async for message in websocket:
        # Stream response back to client
        for chunk in agent.call_agent_simple_stream(message):
            await websocket.send(chunk)
```

### With Server-Sent Events (SSE)

```python
# FastAPI example
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from chatbot.tools.agent import Agent

app = FastAPI()

@app.post("/chat/stream")
async def stream_chat(prompt: str):
    agent = Agent()

    def generate():
        for chunk in agent.call_agent_simple_stream(prompt):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/plain")
```

## Error Handling

The streaming implementation includes proper error handling:

- Network interruptions during streaming
- Invalid callback functions
- Tool execution errors during streaming
- API rate limiting scenarios

## Testing

Use the provided `example_streaming_usage.py` script to test streaming functionality:

```bash
python example_streaming_usage.py
```

This demonstrates all three streaming methods and shows expected output patterns.

## Migration Guide

### From Non-Streaming to Streaming

**Before:**

```python
agent = Agent()
response = agent.call_agent("What is Bitcoin?")
print(response)
```

**After (Simple Streaming):**

```python
agent = Agent()
print("Response: ", end="", flush=True)
for chunk in agent.call_agent_simple_stream("What is Bitcoin?"):
    print(chunk, end="", flush=True)
print()  # New line after complete response
```

**After (Callback Streaming):**

```python
agent = Agent()

def handle_chunk(chunk):
    print(chunk, end="", flush=True)

agent.set_streaming_callback(handle_chunk)
response = agent.call_agent("What is Bitcoin?")
# Chunks are automatically streamed via callback
```

## Troubleshooting

### Common Issues

1. **No streaming output**: Ensure the callback is set before calling the agent
2. **Partial responses**: Check network connectivity and API limits
3. **Tool calling not working**: Use `call_agent_stream` instead of `call_agent_simple_stream`
4. **Memory issues**: Streaming should reduce memory usage, check callback implementation

### Debug Mode

Enable debug output by checking the console for streaming messages:

- `🔄 Starting streaming response...`
- `📝 Streaming chunk: [text]`
- `✅ Streaming complete. Total text: [accumulated]`
