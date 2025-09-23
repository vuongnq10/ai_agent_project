# Agentic AI Trading System with LangGraph

A comprehensive cryptocurrency trading AI system powered by **LangGraph** that coordinates multiple specialized agents through a structured workflow to provide intelligent market analysis, trading decisions, and risk management.

## 🏗️ Architecture Overview

The system consists of four main components:

### 1. **DataAgent** (`data_agent.py`)

**Role**: Market data collection and preprocessing

- Fetches real-time price data from Binance
- Handles multiple timeframe data collection
- Provides order book analysis
- Calculates volume profiles and market metrics
- Detects price and volume anomalies
- Manages data caching for performance

**Key Methods**:

- `fetch_ohlcv_data()` - Get OHLCV candle data
- `get_current_price()` - Real-time price fetching
- `get_market_overview()` - Multi-symbol market summary
- `detect_anomalies()` - Price/volume anomaly detection

### 2. **AnalyseAgent** (`analyse_agent.py`)

**Role**: Technical analysis and market sentiment

- Comprehensive Smart Money Concepts (SMC) analysis
- Technical indicator calculations (RSI, MACD, EMA, Bollinger Bands)
- Market structure analysis (Higher Highs, Lower Lows)
- Pattern recognition (Double tops/bottoms, triangles)
- Support and resistance level identification
- Risk metrics calculation

**Key Methods**:

- `comprehensive_analysis()` - Full multi-timeframe analysis
- `smart_money_concepts()` - SMC analysis (Order Blocks, FVGs, BOS)
- `calculate_indicators()` - Technical indicators
- `detect_patterns()` - Chart pattern recognition

### 3. **DecisionAgent** (`decision_agent.py`)

**Role**: Trading decisions and risk management

- Makes buy/sell/wait decisions based on analysis
- Calculates position sizing and risk management
- Provides entry/exit strategies
- Evaluates existing positions
- Risk assessment and mitigation

**Key Methods**:

- `make_trading_decision()` - Primary trading decision engine
- `evaluate_exit_strategy()` - Position exit analysis
- `_calculate_risk_management()` - Position sizing and stops

### 4. **AgenticAI** (`agentic_ai.py`)

**Role**: Master coordinator and natural language interface

- Coordinates all specialized agents
- Parses user intent from natural language
- Routes requests to appropriate agents
- Generates human-readable responses
- Manages session memory and context

**Key Methods**:

- `process_user_request()` - Main entry point
- `_parse_user_intent()` - NLP intent classification
- Session management and context tracking

## 🚀 Quick Start

### Prerequisites

```bash
pip install ccxt pandas numpy scipy google-genai python-dotenv
```

### Environment Setup

Create a `.env` file with:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Basic Usage

```python
import asyncio
from master_agent.agents.agentic_ai import AgenticAI

async def main():
    ai_system = AgenticAI()

    # Analyze a cryptocurrency
    response = await ai_system.process_user_request(
        "Analyze BTC/USDT for potential trades",
        session_id="user_123"
    )

    print(response['summary'])

# Run the system
asyncio.run(main())
```

### Convenience Function

```python
from master_agent.agents.agentic_ai import process_trading_request

# Quick one-liner for trading analysis
response = await process_trading_request("Should I buy SOL right now?")
```

## 📊 Supported Request Types

The system automatically classifies user requests into these categories:

### 1. **Market Analysis**

**Trigger words**: analyze, analysis, technical, chart
**Example**: "Analyze BTC/USDT technical indicators"
**Response**: Comprehensive technical analysis with SMC, indicators, and sentiment

### 2. **Trading Decisions**

**Trigger words**: buy, sell, trade, decision, recommend
**Example**: "Should I buy ETH right now?"
**Response**: Buy/Sell/Wait recommendation with confidence scores and risk management

### 3. **Portfolio Review**

**Trigger words**: portfolio, position, holding
**Example**: "How is my portfolio performing?"
**Response**: Position analysis and exit strategy recommendations

### 4. **Market Overview**

**Trigger words**: market, overview, summary
**Example**: "Give me a crypto market overview"
**Response**: Multi-symbol market performance and correlation analysis

### 5. **Risk Assessment**

**Trigger words**: risk, volatility, drawdown
**Example**: "What's the risk level for SOL?"
**Response**: Comprehensive risk metrics and anomaly detection

### 6. **General Queries**

**Fallback**: General trading questions and system capabilities
**Example**: "How does SMC analysis work?"
**Response**: Educational content and system explanations

## 🎯 Key Features

### Smart Money Concepts (SMC) Analysis

- **Order Blocks**: High-volume institutional zones
- **Fair Value Gaps (FVG)**: Price imbalances
- **Break of Structure (BOS)**: Trend change confirmation
- **Change of Character (CHoCH)**: Market sentiment shifts
- **Liquidity Pools**: High-volume accumulation areas

### Technical Indicators

- **RSI**: Momentum oscillator (6, 12, 14, 24 periods)
- **MACD**: Trend following momentum indicator
- **EMA**: Exponential moving averages (7, 20, 50)
- **Bollinger Bands**: Volatility-based bands
- **ATR**: Average True Range for volatility

### Risk Management

- **Position Sizing**: Based on account balance and risk tolerance
- **Stop Loss/Take Profit**: Automatic calculation using ATR
- **Risk-Reward Ratios**: 2:1 and 3:1 targets
- **Volatility Assessment**: Multi-timeframe risk analysis

### Multi-Timeframe Analysis

- **1 Hour**: Short-term trends and entry timing
- **4 Hour**: Primary trend analysis (40% weight)
- **Daily**: Long-term context and major levels

## 🔧 Configuration

### Supported Symbols

```python
['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT']
```

### Risk Parameters

```python
risk_tolerance = 0.02  # 2% max risk per trade
max_position_size = 0.1  # 10% of portfolio max
```

### Default Timeframes

```python
default_timeframes = ['1h', '4h', '1d']
```

## 🔄 LangGraph Workflow Architecture

The system uses **LangGraph** to orchestrate agent coordination through a structured state machine:

### **Workflow Nodes**

1. **parse_intent** - Parse user request and extract intent
2. **collect_data** - Fetch market data based on requirements
3. **analyze_market** - Perform technical analysis
4. **make_decision** - Generate trading recommendations
5. **generate_response** - Create user-friendly response
6. **handle_error** - Manage errors and fallbacks

### **State Management**

```python
class AgentState(TypedDict):
    user_prompt: str
    intent: Dict[str, Any]
    market_data: Dict[str, Any]
    analysis_results: Dict[str, Any]
    trading_decision: Dict[str, Any]
    final_response: Dict[str, Any]
    session_id: str
    error_message: str
    step_count: int
    max_steps: int
```

### **Conditional Routing**

The workflow intelligently routes based on:

- **Intent Type**: Different paths for analysis vs decisions
- **Success/Failure**: Error handling and recovery
- **Data Requirements**: Conditional data collection

### **Checkpointing**

- **Session Persistence**: InMemorySaver for conversation history
- **State Recovery**: Resume interrupted workflows
- **Thread Management**: Separate sessions per user

## 📈 Decision Making Process

### 1. **Intent Classification**

- Natural language understanding with Gemini
- Extract symbols, timeframes, and parameters
- Route to appropriate workflow path

### 2. **Data Collection** (DataAgent)

- Fetch multi-timeframe OHLCV data
- Get current market prices
- Collect volume and order book data

### 3. **Analysis** (AnalyseAgent)

- Calculate technical indicators
- Perform SMC analysis
- Identify patterns and levels
- Assess market structure

### 4. **Decision Making** (DecisionAgent)

- Weight different timeframes (1h: 25%, 4h: 40%, 1d: 35%)
- Score bullish/bearish factors
- Apply risk adjustments
- Generate confidence levels

### 5. **Response Generation**

- Format analysis results
- Generate natural language explanations
- Include actionable recommendations

### **Decision Thresholds**

- **Strong Buy/Sell**: Net score > 0.6, Confidence > 0.5
- **Moderate Buy/Sell**: Net score > 0.3, Confidence > 0.3
- **Wait**: Below threshold or high risk

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_agentic_ai.py
```

Tests include:

- Individual agent functionality
- Full system integration
- Natural language processing
- Error handling
- System status verification

## 📋 Example Responses

### Market Analysis Response

```json
{
  "type": "MARKET_ANALYSIS",
  "symbol": "BTC/USDT",
  "analysis": {
    "overall_sentiment": "BULLISH",
    "confidence_score": 0.75,
    "current_price": 67500
  },
  "summary": "BTC/USDT shows bullish momentum across timeframes...",
  "status": "success"
}
```

### Trading Decision Response

```json
{
  "type": "TRADING_DECISION",
  "symbol": "BTC/USDT",
  "decision": {
    "action": "BUY",
    "confidence": 0.68,
    "position_size": 0.148,
    "stop_loss": 66150,
    "take_profit_1": 68850,
    "risk_reward_ratio": 2.0
  },
  "explanation": "Strong bullish setup with multiple confirmations...",
  "status": "success"
}
```

## 🔄 Session Management

The system maintains session memory for:

- **Conversation History**: Recent queries and responses
- **Analysis Cache**: Previously analyzed symbols
- **Active Positions**: Tracked trading positions
- **User Preferences**: Custom risk settings

## ⚠️ Important Notes

### Dependencies

- Requires active internet connection for market data
- Gemini API key needed for natural language processing
- CCXT library for exchange connectivity

### Limitations

- **Educational Purpose**: Not financial advice
- **Market Conditions**: Performance varies with market volatility
- **Data Accuracy**: Depends on exchange API reliability

### Risk Disclaimer

This system is for educational and research purposes only. Always conduct your own research and consider consulting with financial advisors before making trading decisions.

## 🛠️ Development

### Adding New Symbols

Modify `supported_symbols` in `AgenticAI.__init__()`

### Extending Analysis

Add new methods to `AnalyseAgent` and update scoring in `DecisionAgent`

### Custom Risk Models

Modify `_calculate_risk_management()` in `DecisionAgent`

## 📞 Support

For issues or questions:

1. Check the test script output for system diagnostics
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Check API rate limits and connectivity

---

**Built with**: Python 3.8+, CCXT, Pandas, NumPy, SciPy, Google GenAI
**License**: Educational Use
**Version**: 1.0.0
