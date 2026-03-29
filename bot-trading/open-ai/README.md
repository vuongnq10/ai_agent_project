# OpenAI Agentic Trading Agent

A sophisticated agentic AI system built with OpenAI GPT-4 mini that can analyze cryptocurrency markets, make trading decisions, and execute trades through multiple specialized agents.

## Overview

This OpenAI agentic trading agent implements a multi-agent system that mirrors the Gemini implementation but uses OpenAI's GPT-4 mini model. The system consists of multiple specialized agents working together:

- **Master Agent**: Orchestrates the entire workflow and routes requests to appropriate agents
- **Tools Agent**: Handles market data retrieval and order execution
- **Analysis Agent**: Performs technical analysis using Smart Money Concepts
- **Decision Agent**: Makes trading decisions based on analysis
- **Response Generator**: Provides final responses to users

## Features

### 🤖 Multi-Agent Architecture

- State-based workflow using LangGraph
- Intelligent routing between specialized agents
- Memory persistence across conversations

### 📊 Advanced Market Analysis

- Smart Money Concepts (SMC) analysis
- Technical indicators (RSI, EMA, Bollinger Bands)
- Swing point detection and structure analysis
- Fair Value Gap identification
- Break of Structure (BOS) and Change of Character (CHoCH) detection

### 🛠 Trading Tools

- Real-time market data from Binance
- Automated trade setup creation
- Risk management with stop-loss and take-profit
- 20x leverage support

### 🔄 Tool Calling Capabilities

- Native OpenAI function calling
- Real-time data fetching
- Dynamic tool execution based on context

## Architecture

```
┌─────────────────┐
│   User Query    │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Master Agent   │ ◄─── Routes requests and orchestrates workflow
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tools Agent   │    │ Analysis Agent  │    │ Decision Agent  │
│                 │    │                 │    │                 │
│ • Market Data   │    │ • SMC Analysis  │    │ • Trade Logic   │
│ • Order Creation│    │ • Indicators    │    │ • Risk Mgmt     │
│ • API Calls     │    │ • Pattern Rec   │    │ • Execution     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │ Response Gen    │
                         └─────────────────┘
```

## Installation & Setup

### 1. Prerequisites

```bash
# Install required dependencies
pip install openai langgraph langchain fastapi uvicorn ccxt pandas numpy python-dotenv
```

### 2. Environment Configuration

Create or update the `.env` file in the bot-trading directory:

```env
# OpenAI Configuration
OPENAI_API_KEY="your-openai-api-key-here"

# Binance Configuration (for live trading)
BINANCE_API_KEY="your-binance-api-key"
BINANCE_SECRET_KEY="your-binance-secret-key"
BINANCE_BASE_URL=""  # Leave empty for production

# Other existing configurations...
```

### 3. API Key Setup

1. Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/)
2. Ensure you have sufficient credits for API usage
3. Update the `OPENAI_API_KEY` in your `.env` file

## Usage

### Direct Testing

```bash
# Run the test suite
cd bot-trading
python open-ai/test_agent.py
```

### API Integration

```python
from open_ai.agents_openai.agentic_agent import MasterOpenAI

# Initialize the agent
agent = MasterOpenAI()

# Query the agent
for response_chunk in agent("Analyze BTC/USDT on 1h timeframe"):
    print(response_chunk, end="")
```

### FastAPI Endpoints

The agent is integrated with FastAPI endpoints:

- `GET /openai/stream` - Streaming response endpoint
- `GET /openai/test` - Simple test endpoint

## Available Tools

### 1. SMC Analysis (`smc_analysis`)

Performs comprehensive Smart Money Concepts analysis:

- **Parameters**: `symbol`, `timeframe`, `limit`
- **Returns**: Complete technical analysis including:
  - Current price and ATR
  - Swing highs/lows and order blocks
  - Fair Value Gaps (bullish/bearish)
  - Break of Structure points
  - Bollinger Bands (14, 20, 50 periods)
  - EMA (9, 20, 50 periods)
  - RSI (7, 14, 21 periods)

### 2. Create Order (`create_order`)

Creates leveraged trading setups:

- **Parameters**: `symbol`, `side`, `entry`, `stop_loss`, `take_profit`
- **Features**: 20x leverage, automatic risk management

### 3. Get Ticker (`get_ticker`)

Fetches real-time market data:

- **Parameters**: `symbol`, `timeframe`
- **Returns**: OHLCV data for analysis

## Agent Workflow

1. **Query Reception**: Master Agent receives and classifies user queries
2. **Tool Execution**: Tools Agent fetches required market data
3. **Analysis Phase**: Analysis Agent performs technical analysis
4. **Decision Making**: Decision Agent evaluates trading opportunities
5. **Response Generation**: Final response with recommendations

## Configuration

### Model Settings

- **Model**: `gpt-4o-mini` (configurable in `OpenAIAgent`)
- **Temperature**: `0.7` (balanced creativity/consistency)
- **Max Tokens**: `1000` (sufficient for most responses)

### Workflow Parameters

- **Max Steps**: `10` (prevents infinite loops)
- **Session Management**: Supports multiple concurrent sessions
- **Memory**: Persistent conversation history

## Error Handling

The system includes comprehensive error handling:

- API quota management
- Network timeout handling
- Invalid parameter validation
- Graceful fallbacks for failed operations

## Testing

### Test Coverage

- ✅ Tool functionality validation
- ✅ Agent initialization
- ✅ API integration
- ✅ Error handling
- ✅ Memory management

### Running Tests

```bash
# Basic functionality test
python open-ai/test_agent.py

# Tools-only test (no API quota required)
# Edit test_agent.py and comment out agent tests
```

## Comparison with Gemini Version

| Feature          | OpenAI Version       | Gemini Version        |
| ---------------- | -------------------- | --------------------- |
| Model            | GPT-4 mini           | Gemini Pro            |
| Function Calling | Native OpenAI format | Google GenAI format   |
| Tool Integration | Direct execution     | Gemini-specific tools |
| Response Format  | Standard OpenAI      | Gemini Content/Parts  |
| Performance      | Fast, reliable       | Fast, reliable        |

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all `__init__.py` files are present
2. **API Quota**: Check OpenAI billing and usage limits
3. **Environment Variables**: Verify `.env` file configuration
4. **Dependencies**: Install all required packages

### Debug Mode

Enable detailed logging by setting environment variable:

```bash
export OPENAI_LOG_LEVEL=debug
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive error handling
3. Include tests for new features
4. Update documentation

## License

This project follows the same license as the main bot-trading project.

---

**Note**: This implementation provides feature parity with the Gemini version while leveraging OpenAI's robust function calling capabilities and GPT-4 mini's excellent reasoning abilities.
