import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part

from .data_agent import DataAgent
from .analyse_agent import AnalyseAgent
from .decision_agent import DecisionAgent

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))
memory = InMemorySaver()

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

class AgenticAI:
    """
    LangGraph-based Agentic AI System that coordinates all specialized agents using a state machine workflow:
    - DataAgent: Market data collection and preprocessing
    - AnalyseAgent: Technical analysis and market sentiment
    - DecisionAgent: Trading decisions and risk management
    - Master coordination through LangGraph state management
    """
    
    def __init__(self):
        # Initialize all specialized agents
        self.data_agent = DataAgent()
        self.analyse_agent = AnalyseAgent()
        self.decision_agent = DecisionAgent()
        
        # System configuration
        self.supported_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT']
        self.default_timeframes = ['1h', '4h', '1d']
        self.session_memory = {}
        
        # Build LangGraph workflow
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for agent coordination"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes for each step in the workflow
        workflow.add_node("parse_intent", self._parse_intent_node)
        workflow.add_node("collect_data", self._collect_data_node)
        workflow.add_node("analyze_market", self._analyze_market_node)
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("parse_intent")
        
        # Add conditional edges based on intent type and success/failure
        workflow.add_conditional_edges(
            "parse_intent",
            self._route_based_on_intent,
            {
                "collect_data": "collect_data",
                "generate_response": "generate_response",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "collect_data",
            self._check_data_collection,
            {
                "analyze": "analyze_market",
                "decision": "make_decision",
                "response": "generate_response",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "analyze_market",
            self._check_analysis_completion,
            {
                "decision": "make_decision",
                "response": "generate_response",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("make_decision", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile(checkpointer=memory)
    
    def _parse_intent_node(self, state: AgentState) -> AgentState:
        """Parse user intent and extract parameters"""
        try:
            user_prompt = state["user_prompt"]
            
            # Use existing intent parsing logic
            intent = asyncio.run(self._parse_user_intent_sync(user_prompt))
            
            state["intent"] = intent
            state["step_count"] = state.get("step_count", 0) + 1
            
            print(f"🎯 Intent parsed: {intent['type']} for symbols: {intent.get('symbols', [])}")
            
        except Exception as e:
            state["error_message"] = f"Intent parsing failed: {str(e)}"
            print(f"❌ Intent parsing error: {e}")
        
        return state
    
    def _collect_data_node(self, state: AgentState) -> AgentState:
        """Collect market data based on intent"""
        try:
            intent = state["intent"]
            symbols = intent.get('symbols', ['BTC/USDT'])
            
            market_data = {}
            
            for symbol in symbols:
                # Get current price
                current_price = self.data_agent.get_current_price(symbol)
                
                # Get OHLCV data for multiple timeframes
                timeframes = intent.get('timeframes', self.default_timeframes)
                ohlcv_data = self.data_agent.fetch_multiple_timeframes(symbol, timeframes)
                
                # Get additional market data if needed
                if intent['type'] in ['MARKET_OVERVIEW', 'RISK_ASSESSMENT']:
                    order_book = self.data_agent.get_order_book(symbol)
                    volume_profile = self.data_agent.get_volume_profile(symbol)
                    anomalies = self.data_agent.detect_anomalies(symbol)
                    
                    market_data[symbol] = {
                        'current_price': current_price,
                        'ohlcv_data': ohlcv_data,
                        'order_book': order_book,
                        'volume_profile': volume_profile,
                        'anomalies': anomalies
                    }
                else:
                    market_data[symbol] = {
                        'current_price': current_price,
                        'ohlcv_data': ohlcv_data
                    }
            
            state["market_data"] = market_data
            state["step_count"] = state.get("step_count", 0) + 1
            
            print(f"📊 Data collected for {len(symbols)} symbol(s)")
            
        except Exception as e:
            state["error_message"] = f"Data collection failed: {str(e)}"
            print(f"❌ Data collection error: {e}")
        
        return state
    
    def _analyze_market_node(self, state: AgentState) -> AgentState:
        """Perform market analysis using AnalyseAgent"""
        try:
            intent = state["intent"]
            market_data = state["market_data"]
            
            analysis_results = {}
            
            for symbol, data in market_data.items():
                timeframes = intent.get('timeframes', self.default_timeframes)
                
                # Perform comprehensive analysis
                analysis = self.analyse_agent.comprehensive_analysis(symbol, timeframes)
                analysis_results[symbol] = analysis
                
                # Store in session for reference
                session_id = state.get("session_id", "default")
                if session_id not in self.session_memory:
                    self.session_memory[session_id] = {'last_analysis': {}}
                
                self.session_memory[session_id]['last_analysis'][symbol] = analysis
            
            state["analysis_results"] = analysis_results
            state["step_count"] = state.get("step_count", 0) + 1
            
            print(f"📈 Analysis completed for {len(analysis_results)} symbol(s)")
            
        except Exception as e:
            state["error_message"] = f"Market analysis failed: {str(e)}"
            print(f"❌ Analysis error: {e}")
        
        return state
    
    def _make_decision_node(self, state: AgentState) -> AgentState:
        """Make trading decisions using DecisionAgent"""
        try:
            intent = state["intent"]
            analysis_results = state["analysis_results"]
            
            trading_decisions = {}
            
            for symbol, analysis in analysis_results.items():
                account_balance = intent.get('account_balance', 10000)
                risk_tolerance = intent.get('risk_tolerance', 0.02)
                
                # Make trading decision
                decision = self.decision_agent.make_trading_decision(
                    symbol=symbol,
                    account_balance=account_balance,
                    custom_risk_tolerance=risk_tolerance
                )
                
                trading_decisions[symbol] = decision
            
            state["trading_decision"] = trading_decisions
            state["step_count"] = state.get("step_count", 0) + 1
            
            print(f"🎯 Trading decisions made for {len(trading_decisions)} symbol(s)")
            
        except Exception as e:
            state["error_message"] = f"Decision making failed: {str(e)}"
            print(f"❌ Decision error: {e}")
        
        return state
    
    def _generate_response_node(self, state: AgentState) -> AgentState:
        """Generate final response based on workflow results"""
        try:
            intent = state["intent"]
            intent_type = intent.get('type', 'GENERAL_QUERY')
            
            if intent_type == 'MARKET_ANALYSIS':
                response = self._format_analysis_response(state)
            elif intent_type == 'TRADING_DECISION':
                response = self._format_decision_response(state)
            elif intent_type == 'PORTFOLIO_REVIEW':
                response = self._format_portfolio_response(state)
            elif intent_type == 'MARKET_OVERVIEW':
                response = self._format_market_overview_response(state)
            elif intent_type == 'RISK_ASSESSMENT':
                response = self._format_risk_assessment_response(state)
            else:
                response = self._format_general_response(state)
            
            state["final_response"] = response
            state["step_count"] = state.get("step_count", 0) + 1
            
            print(f"✅ Response generated for {intent_type}")
            
        except Exception as e:
            state["error_message"] = f"Response generation failed: {str(e)}"
            state["final_response"] = {
                'type': 'ERROR',
                'message': f"Failed to generate response: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
            print(f"❌ Response generation error: {e}")
        
        return state
    
    def _handle_error_node(self, state: AgentState) -> AgentState:
        """Handle errors and generate error response"""
        error_message = state.get("error_message", "Unknown error occurred")
        
        state["final_response"] = {
            'type': 'ERROR',
            'message': error_message,
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'step_count': state.get("step_count", 0)
        }
        
        print(f"🚨 Error handled: {error_message}")
        
        return state
    
    def _route_based_on_intent(self, state: AgentState) -> str:
        """Route workflow based on parsed intent"""
        if state.get("error_message"):
            return "error"
        
        intent_type = state.get("intent", {}).get('type', 'GENERAL_QUERY')
        
        if intent_type in ['MARKET_ANALYSIS', 'TRADING_DECISION', 'RISK_ASSESSMENT']:
            return "collect_data"
        elif intent_type in ['PORTFOLIO_REVIEW', 'MARKET_OVERVIEW']:
            return "collect_data"
        else:
            return "generate_response"
    
    def _check_data_collection(self, state: AgentState) -> str:
        """Check data collection status and route accordingly"""
        if state.get("error_message"):
            return "error"
        
        intent_type = state.get("intent", {}).get('type', 'GENERAL_QUERY')
        
        if intent_type in ['MARKET_ANALYSIS', 'RISK_ASSESSMENT']:
            return "analyze"
        elif intent_type == 'TRADING_DECISION':
            return "analyze"
        elif intent_type in ['PORTFOLIO_REVIEW', 'MARKET_OVERVIEW']:
            return "response"
        else:
            return "response"
    
    def _check_analysis_completion(self, state: AgentState) -> str:
        """Check analysis completion and route accordingly"""
        if state.get("error_message"):
            return "error"
        
        intent_type = state.get("intent", {}).get('type', 'GENERAL_QUERY')
        
        if intent_type == 'TRADING_DECISION':
            return "decision"
        else:
            return "response"
    
    async def process_user_request(self, user_prompt: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Main entry point for processing user requests using LangGraph workflow
        """
        
        # Initialize session if new
        if session_id not in self.session_memory:
            self.session_memory[session_id] = {
                'conversation_history': [],
                'last_analysis': {},
                'active_positions': {},
                'preferences': {}
            }
        
        # Initial state
        initial_state = {
            "user_prompt": user_prompt,
            "intent": {},
            "market_data": {},
            "analysis_results": {},
            "trading_decision": {},
            "final_response": {},
            "session_id": session_id,
            "error_message": "",
            "step_count": 0,
            "max_steps": 10
        }
        
        # Configuration for checkpointing
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            print(f"🚀 Processing request: '{user_prompt[:50]}...'")
            
            # Run the workflow
            final_state = self.graph.invoke(initial_state, config=config)
            
            response = final_state.get("final_response", {
                'type': 'ERROR',
                'message': 'No response generated',
                'status': 'error'
            })
            
            # Update session memory
            session = self.session_memory[session_id]
            session['conversation_history'].append({
                'timestamp': datetime.now().isoformat(),
                'user_prompt': user_prompt,
                'intent': final_state.get("intent", {}),
                'response': response,
                'step_count': final_state.get("step_count", 0)
            })
            
            print(f"✅ Request completed in {final_state.get('step_count', 0)} steps")
            
            return response
            
        except Exception as e:
            print(f"❌ Workflow execution error: {e}")
            return {
                'type': 'ERROR',
                'message': f"Workflow execution failed: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
    
    async def _parse_user_intent(self, user_prompt: str) -> Dict[str, Any]:
        """
        Parse user intent using Gemini to understand what the user wants
        """
        
        system_prompt = """
        You are an AI assistant that analyzes user prompts for cryptocurrency trading intentions.
        
        Classify the user's request into one of these categories:
        - MARKET_ANALYSIS: User wants technical analysis of a specific symbol
        - TRADING_DECISION: User wants trading recommendations (buy/sell/wait)
        - PORTFOLIO_REVIEW: User wants to review existing positions
        - MARKET_OVERVIEW: User wants general market overview
        - RISK_ASSESSMENT: User wants risk analysis
        - GENERAL_QUERY: General questions about trading, markets, or system capabilities
        
        Extract relevant parameters:
        - symbols: List of cryptocurrency symbols mentioned
        - timeframes: Any specific timeframes mentioned
        - account_balance: If mentioned
        - risk_tolerance: If mentioned
        
        Respond in JSON format:
        {
            "type": "CATEGORY",
            "symbols": ["SYMBOL1", "SYMBOL2"],
            "timeframes": ["1h", "4h"],
            "account_balance": 10000,
            "risk_tolerance": 0.02,
            "confidence": 0.9
        }
        """
        
        try:
            contents = [
                Content(role="user", parts=[Part.from_text(text=f"{system_prompt}\n\nUser prompt: {user_prompt}")])
            ]
            
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=GenerateContentConfig()
            )
            
            # Parse JSON response
            import json
            intent_data = json.loads(response.text)
            
            # Validate and set defaults
            intent = {
                'type': intent_data.get('type', 'GENERAL_QUERY'),
                'symbols': intent_data.get('symbols', []),
                'timeframes': intent_data.get('timeframes', self.default_timeframes),
                'account_balance': intent_data.get('account_balance', 10000),
                'risk_tolerance': intent_data.get('risk_tolerance', 0.02),
                'confidence': intent_data.get('confidence', 0.5),
                'raw_prompt': user_prompt
            }
            
            return intent
            
        except Exception as e:
            print(f"Error parsing intent: {e}")
            # Fallback to simple keyword matching
            return self._fallback_intent_parsing(user_prompt)
    
    def _fallback_intent_parsing(self, user_prompt: str) -> Dict[str, Any]:
        """Fallback intent parsing using keyword matching"""
        
        prompt_lower = user_prompt.lower()
        
        # Extract symbols
        symbols = []
        for symbol in self.supported_symbols:
            symbol_variants = [symbol, symbol.replace('/', ''), symbol.split('/')[0]]
            if any(variant.lower() in prompt_lower for variant in symbol_variants):
                symbols.append(symbol)
        
        # Determine intent type
        if any(word in prompt_lower for word in ['analyze', 'analysis', 'technical', 'chart']):
            intent_type = 'MARKET_ANALYSIS'
        elif any(word in prompt_lower for word in ['buy', 'sell', 'trade', 'decision', 'recommend']):
            intent_type = 'TRADING_DECISION'
        elif any(word in prompt_lower for word in ['portfolio', 'position', 'holding']):
            intent_type = 'PORTFOLIO_REVIEW'
        elif any(word in prompt_lower for word in ['market', 'overview', 'summary']):
            intent_type = 'MARKET_OVERVIEW'
        elif any(word in prompt_lower for word in ['risk', 'volatility', 'drawdown']):
            intent_type = 'RISK_ASSESSMENT'
        else:
            intent_type = 'GENERAL_QUERY'
        
        return {
            'type': intent_type,
            'symbols': symbols if symbols else ['BTC/USDT'],  # Default to BTC
            'timeframes': self.default_timeframes,
            'account_balance': 10000,
            'risk_tolerance': 0.02,
            'confidence': 0.7,
            'raw_prompt': user_prompt
        }
    
    async def _handle_market_analysis(self, intent: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle market analysis requests"""
        
        symbol = intent['symbols'][0] if intent['symbols'] else 'BTC/USDT'
        timeframes = intent['timeframes']
        
        try:
            # Get comprehensive analysis from AnalyseAgent
            analysis = self.analyse_agent.comprehensive_analysis(symbol, timeframes)
            
            # Store in session for reference
            session['last_analysis'][symbol] = analysis
            
            # Generate natural language summary
            summary = await self._generate_analysis_summary(analysis, symbol)
            
            return {
                'type': 'MARKET_ANALYSIS',
                'symbol': symbol,
                'analysis': analysis,
                'summary': summary,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'type': 'ERROR',
                'message': f"Failed to analyze {symbol}: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
    
    async def _handle_trading_decision(self, intent: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trading decision requests"""
        
        symbol = intent['symbols'][0] if intent['symbols'] else 'BTC/USDT'
        account_balance = intent['account_balance']
        risk_tolerance = intent['risk_tolerance']
        
        try:
            # Get trading decision from DecisionAgent
            decision = self.decision_agent.make_trading_decision(
                symbol=symbol,
                account_balance=account_balance,
                custom_risk_tolerance=risk_tolerance
            )
            
            # Generate natural language explanation
            explanation = await self._generate_decision_explanation(decision, symbol)
            
            return {
                'type': 'TRADING_DECISION',
                'symbol': symbol,
                'decision': decision,
                'explanation': explanation,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'type': 'ERROR',
                'message': f"Failed to generate trading decision for {symbol}: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
    
    async def _handle_portfolio_review(self, intent: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle portfolio review requests"""
        
        active_positions = session.get('active_positions', {})
        
        if not active_positions:
            return {
                'type': 'PORTFOLIO_REVIEW',
                'message': "No active positions found. Would you like to analyze some symbols for potential trades?",
                'suggestions': self.supported_symbols[:3],
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
        
        try:
            portfolio_analysis = {}
            
            for symbol, position in active_positions.items():
                # Get exit strategy evaluation
                exit_evaluation = self.decision_agent.evaluate_exit_strategy(
                    symbol=symbol,
                    entry_price=position['entry_price'],
                    position_side=position['side'],
                    current_pl_percentage=position.get('current_pl', 0)
                )
                portfolio_analysis[symbol] = exit_evaluation
            
            # Generate portfolio summary
            summary = await self._generate_portfolio_summary(portfolio_analysis)
            
            return {
                'type': 'PORTFOLIO_REVIEW',
                'portfolio_analysis': portfolio_analysis,
                'summary': summary,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'type': 'ERROR',
                'message': f"Failed to review portfolio: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
    
    async def _handle_market_overview(self, intent: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle market overview requests"""
        
        try:
            # Get market overview from DataAgent
            symbols = intent['symbols'] if intent['symbols'] else self.supported_symbols[:5]
            market_data = self.data_agent.get_market_overview(symbols)
            
            # Get correlation analysis
            correlation_data = self.data_agent.get_correlation_matrix(symbols)
            
            # Generate natural language overview
            overview = await self._generate_market_overview(market_data, correlation_data)
            
            return {
                'type': 'MARKET_OVERVIEW',
                'market_data': market_data,
                'correlation_data': correlation_data,
                'overview': overview,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'type': 'ERROR',
                'message': f"Failed to generate market overview: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
    
    async def _handle_risk_assessment(self, intent: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle risk assessment requests"""
        
        symbol = intent['symbols'][0] if intent['symbols'] else 'BTC/USDT'
        
        try:
            # Get data and detect anomalies
            anomalies = self.data_agent.detect_anomalies(symbol)
            
            # Get risk metrics from analysis
            analysis = self.analyse_agent.comprehensive_analysis(symbol)
            risk_metrics = {}
            
            for timeframe, tf_analysis in analysis['timeframe_analysis'].items():
                risk_metrics[timeframe] = tf_analysis.get('risk_metrics', {})
            
            # Generate risk assessment summary
            risk_summary = await self._generate_risk_assessment(anomalies, risk_metrics, symbol)
            
            return {
                'type': 'RISK_ASSESSMENT',
                'symbol': symbol,
                'anomalies': anomalies,
                'risk_metrics': risk_metrics,
                'risk_summary': risk_summary,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'type': 'ERROR',
                'message': f"Failed to assess risk for {symbol}: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
    
    async def _handle_general_query(self, intent: Dict[str, Any], session: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Handle general queries using Gemini"""
        
        try:
            # Get context from recent analysis
            context = self._get_session_context(session)
            
            system_prompt = f"""
            You are Kite, a professional cryptocurrency trading assistant with access to comprehensive market analysis tools.
            
            Based on recent analysis context:
            {context}
            
            Provide helpful, accurate information about cryptocurrency trading, market analysis, or system capabilities.
            Be concise but informative. If the user asks about specific analysis, refer them to use the analysis commands.
            """
            
            contents = [
                Content(role="user", parts=[Part.from_text(text=f"{system_prompt}\n\nUser question: {user_prompt}")])
            ]
            
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=GenerateContentConfig()
            )
            
            return {
                'type': 'GENERAL_QUERY',
                'response': response.text,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'type': 'ERROR',
                'message': f"Failed to process query: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
    
    def _get_session_context(self, session: Dict[str, Any]) -> str:
        """Get relevant context from session for general queries"""
        
        context_parts = []
        
        # Recent analysis
        if session.get('last_analysis'):
            symbols = list(session['last_analysis'].keys())
            context_parts.append(f"Recently analyzed: {', '.join(symbols)}")
        
        # Active positions
        if session.get('active_positions'):
            positions = list(session['active_positions'].keys())
            context_parts.append(f"Active positions: {', '.join(positions)}")
        
        # Recent conversation
        if session.get('conversation_history'):
            recent_intents = [conv['intent']['type'] for conv in session['conversation_history'][-3:]]
            context_parts.append(f"Recent queries: {', '.join(recent_intents)}")
        
        return '\n'.join(context_parts) if context_parts else "No recent analysis context available."
    
    async def _generate_analysis_summary(self, analysis: Dict[str, Any], symbol: str) -> str:
        """Generate natural language summary of analysis"""
        
        overall_sentiment = analysis.get('overall_sentiment', {})
        current_price = analysis.get('current_price', 0)
        
        system_prompt = f"""
        Generate a concise, professional summary of this technical analysis for {symbol}.
        
        Current price: ${current_price}
        Overall sentiment: {overall_sentiment.get('overall_sentiment', 'NEUTRAL')}
        Confidence: {overall_sentiment.get('confidence_score', 0):.2f}
        
        Include key findings from:
        - Market structure and trend
        - Technical indicators (RSI, MACD, etc.)
        - Smart Money Concepts (order blocks, fair value gaps)
        - Support/resistance levels
        - Risk assessment
        
        Keep it under 200 words and focus on actionable insights.
        """
        
        try:
            contents = [
                Content(role="user", parts=[Part.from_text(text=f"{system_prompt}\n\nAnalysis data: {str(analysis)}")])
            ]
            
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=GenerateContentConfig()
            )
            
            return response.text
            
        except Exception as e:
            return f"Analysis complete for {symbol}. Overall sentiment: {overall_sentiment.get('overall_sentiment', 'NEUTRAL')}. Current price: ${current_price}"
    
    async def _generate_decision_explanation(self, decision: Dict[str, Any], symbol: str) -> str:
        """Generate natural language explanation of trading decision"""
        
        action = decision.get('action', 'WAIT')
        confidence = decision.get('confidence', 0)
        recommendation = decision.get('recommendation', '')
        
        system_prompt = f"""
        Generate a clear explanation for this trading decision on {symbol}.
        
        Decision: {action}
        Confidence: {confidence:.2f}
        Setup type: {decision.get('setup_type', 'UNKNOWN')}
        
        Include:
        - Why this decision was made
        - Key factors that influenced it
        - Risk management details if applicable
        - What to watch for next
        
        Be professional but accessible. Keep under 150 words.
        """
        
        try:
            contents = [
                Content(role="user", parts=[Part.from_text(text=f"{system_prompt}\n\nDecision data: {str(decision)}")])
            ]
            
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=GenerateContentConfig()
            )
            
            return response.text
            
        except Exception as e:
            return recommendation if recommendation else f"Trading decision for {symbol}: {action} with {confidence:.0%} confidence."
    
    async def _generate_portfolio_summary(self, portfolio_analysis: Dict[str, Any]) -> str:
        """Generate portfolio summary"""
        
        total_positions = len(portfolio_analysis)
        
        if total_positions == 0:
            return "No active positions to review."
        
        summary_parts = [f"Portfolio Review - {total_positions} active position(s):"]
        
        for symbol, analysis in portfolio_analysis.items():
            exit_decision = analysis.get('exit_decision', {})
            pl_pct = analysis.get('unrealized_pl_percentage', 0)
            action = exit_decision.get('action', 'HOLD')
            
            summary_parts.append(f"• {symbol}: {pl_pct:+.2f}% | Action: {action}")
        
        return '\n'.join(summary_parts)
    
    async def _generate_market_overview(self, market_data: Dict[str, Any], correlation_data: Dict[str, Any]) -> str:
        """Generate market overview summary"""
        
        try:
            performing_well = []
            performing_poorly = []
            
            for symbol, data in market_data.items():
                if data and data.get('change_24h'):
                    change_24h = data['change_24h']
                    if change_24h > 2:
                        performing_well.append(f"{symbol} (+{change_24h:.1f}%)")
                    elif change_24h < -2:
                        performing_poorly.append(f"{symbol} ({change_24h:.1f}%)")
            
            summary_parts = ["📊 Market Overview:"]
            
            if performing_well:
                summary_parts.append(f"🟢 Strong performers: {', '.join(performing_well)}")
            
            if performing_poorly:
                summary_parts.append(f"🔴 Weak performers: {', '.join(performing_poorly)}")
            
            if correlation_data.get('highest_correlation'):
                highest_corr = correlation_data['highest_correlation']
                summary_parts.append(f"📈 Market correlation: {highest_corr:.2f} (High correlation indicates similar movements)")
            
            return '\n'.join(summary_parts)
            
        except Exception as e:
            return "Market overview generated successfully. Check individual symbol data for details."
    
    async def _generate_risk_assessment(self, anomalies: Dict[str, Any], risk_metrics: Dict[str, Any], symbol: str) -> str:
        """Generate risk assessment summary"""
        
        risk_parts = [f"🚨 Risk Assessment for {symbol}:"]
        
        # Anomaly analysis
        if anomalies.get('recent_price_anomaly'):
            risk_parts.append("⚠️ Recent price anomaly detected")
        
        if anomalies.get('recent_volume_spike'):
            risk_parts.append("⚠️ Recent volume spike detected")
        
        # Volatility analysis
        if risk_metrics:
            avg_volatility = sum(tf.get('volatility', 0) for tf in risk_metrics.values()) / len(risk_metrics)
            if avg_volatility > 0.3:
                risk_parts.append(f"⚠️ High volatility: {avg_volatility:.1%}")
            elif avg_volatility > 0.15:
                risk_parts.append(f"📊 Moderate volatility: {avg_volatility:.1%}")
            else:
                risk_parts.append(f"✅ Low volatility: {avg_volatility:.1%}")
        
        if len(risk_parts) == 1:  # Only header added
            risk_parts.append("✅ No significant risk factors detected")
        
        return '\n'.join(risk_parts)
    
    def add_position(self, session_id: str, symbol: str, entry_price: float, side: str, size: float) -> None:
        """Add a position to session tracking"""
        
        if session_id not in self.session_memory:
            self.session_memory[session_id] = {'active_positions': {}}
        
        self.session_memory[session_id]['active_positions'][symbol] = {
            'entry_price': entry_price,
            'side': side,
            'size': size,
            'timestamp': datetime.now().isoformat()
        }
    
    def remove_position(self, session_id: str, symbol: str) -> None:
        """Remove a position from session tracking"""
        
        if session_id in self.session_memory and symbol in self.session_memory[session_id].get('active_positions', {}):
            del self.session_memory[session_id]['active_positions'][symbol]
    
    def _parse_user_intent_sync(self, user_prompt: str) -> Dict[str, Any]:
        """Synchronous version of intent parsing for LangGraph nodes"""
        try:
            return asyncio.run(self._parse_user_intent(user_prompt))
        except Exception as e:
            print(f"Error in sync intent parsing: {e}")
            return self._fallback_intent_parsing(user_prompt)
    
    def _format_analysis_response(self, state: AgentState) -> Dict[str, Any]:
        """Format market analysis response"""
        analysis_results = state.get("analysis_results", {})
        
        if not analysis_results:
            return {
                'type': 'ERROR',
                'message': 'No analysis results available',
                'status': 'error'
            }
        
        symbol = list(analysis_results.keys())[0]
        analysis = analysis_results[symbol]
        
        # Generate summary using existing method
        try:
            summary = asyncio.run(self._generate_analysis_summary(analysis, symbol))
        except Exception as e:
            summary = f"Analysis completed for {symbol}"
        
        return {
            'type': 'MARKET_ANALYSIS',
            'symbol': symbol,
            'analysis': analysis,
            'summary': summary,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    
    def _format_decision_response(self, state: AgentState) -> Dict[str, Any]:
        """Format trading decision response"""
        trading_decisions = state.get("trading_decision", {})
        
        if not trading_decisions:
            return {
                'type': 'ERROR',
                'message': 'No trading decisions available',
                'status': 'error'
            }
        
        symbol = list(trading_decisions.keys())[0]
        decision = trading_decisions[symbol]
        
        # Generate explanation using existing method
        try:
            explanation = asyncio.run(self._generate_decision_explanation(decision, symbol))
        except Exception as e:
            explanation = f"Trading decision: {decision.get('action', 'WAIT')}"
        
        return {
            'type': 'TRADING_DECISION',
            'symbol': symbol,
            'decision': decision,
            'explanation': explanation,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    
    def _format_portfolio_response(self, state: AgentState) -> Dict[str, Any]:
        """Format portfolio review response"""
        session_id = state.get("session_id", "default")
        session = self.session_memory.get(session_id, {})
        active_positions = session.get('active_positions', {})
        
        if not active_positions:
            return {
                'type': 'PORTFOLIO_REVIEW',
                'message': "No active positions found. Would you like to analyze some symbols for potential trades?",
                'suggestions': self.supported_symbols[:3],
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
        
        # Generate portfolio analysis
        portfolio_analysis = {}
        for symbol, position in active_positions.items():
            exit_evaluation = self.decision_agent.evaluate_exit_strategy(
                symbol=symbol,
                entry_price=position['entry_price'],
                position_side=position['side'],
                current_pl_percentage=position.get('current_pl', 0)
            )
            portfolio_analysis[symbol] = exit_evaluation
        
        try:
            summary = asyncio.run(self._generate_portfolio_summary(portfolio_analysis))
        except Exception as e:
            summary = f"Portfolio with {len(portfolio_analysis)} positions"
        
        return {
            'type': 'PORTFOLIO_REVIEW',
            'portfolio_analysis': portfolio_analysis,
            'summary': summary,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    
    def _format_market_overview_response(self, state: AgentState) -> Dict[str, Any]:
        """Format market overview response"""
        intent = state.get("intent", {})
        symbols = intent.get('symbols', self.supported_symbols[:5])
        
        # Get market data
        market_data = self.data_agent.get_market_overview(symbols)
        correlation_data = self.data_agent.get_correlation_matrix(symbols)
        
        try:
            overview = asyncio.run(self._generate_market_overview(market_data, correlation_data))
        except Exception as e:
            overview = "Market overview completed"
        
        return {
            'type': 'MARKET_OVERVIEW',
            'market_data': market_data,
            'correlation_data': correlation_data,
            'overview': overview,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    
    def _format_risk_assessment_response(self, state: AgentState) -> Dict[str, Any]:
        """Format risk assessment response"""
        intent = state.get("intent", {})
        symbol = intent.get('symbols', ['BTC/USDT'])[0]
        market_data = state.get("market_data", {})
        
        # Get anomalies and risk metrics
        anomalies = market_data.get(symbol, {}).get('anomalies', {})
        
        analysis_results = state.get("analysis_results", {})
        risk_metrics = {}
        if symbol in analysis_results:
            analysis = analysis_results[symbol]
            for timeframe, tf_analysis in analysis.get('timeframe_analysis', {}).items():
                risk_metrics[timeframe] = tf_analysis.get('risk_metrics', {})
        
        try:
            risk_summary = asyncio.run(self._generate_risk_assessment(anomalies, risk_metrics, symbol))
        except Exception as e:
            risk_summary = f"Risk assessment completed for {symbol}"
        
        return {
            'type': 'RISK_ASSESSMENT',
            'symbol': symbol,
            'anomalies': anomalies,
            'risk_metrics': risk_metrics,
            'risk_summary': risk_summary,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    
    def _format_general_response(self, state: AgentState) -> Dict[str, Any]:
        """Format general query response"""
        user_prompt = state.get("user_prompt", "")
        session_id = state.get("session_id", "default")
        session = self.session_memory.get(session_id, {})
        
        # Get context and generate response
        context = self._get_session_context(session)
        
        system_prompt = f"""
        You are Kite, a professional cryptocurrency trading assistant with access to comprehensive market analysis tools.
        
        Based on recent analysis context:
        {context}
        
        Provide helpful, accurate information about cryptocurrency trading, market analysis, or system capabilities.
        Be concise but informative. If the user asks about specific analysis, refer them to use the analysis commands.
        """
        
        try:
            contents = [
                Content(role="user", parts=[Part.from_text(text=f"{system_prompt}\n\nUser question: {user_prompt}")])
            ]
            
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=GenerateContentConfig()
            )
            
            response_text = response.text
        except Exception as e:
            response_text = "I'm here to help with cryptocurrency trading analysis. Please ask about market analysis, trading decisions, or portfolio management."
        
        return {
            'type': 'GENERAL_QUERY',
            'response': response_text,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and capabilities"""
        
        return {
            'status': 'operational',
            'workflow': 'langgraph',
            'agents': {
                'data_agent': 'active',
                'analyse_agent': 'active', 
                'decision_agent': 'active'
            },
            'supported_symbols': self.supported_symbols,
            'supported_timeframes': self.default_timeframes,
            'capabilities': [
                'Market Analysis',
                'Trading Decisions',
                'Portfolio Review',
                'Risk Assessment',
                'Market Overview',
                'Natural Language Interaction',
                'LangGraph Workflow Management'
            ],
            'session_count': len(self.session_memory),
            'timestamp': datetime.now().isoformat()
        }

# Convenience function for quick access
async def process_trading_request(user_prompt: str, session_id: str = "default") -> Dict[str, Any]:
    """
    Convenience function to process trading requests without manual initialization
    """
    ai_system = AgenticAI()
    return await ai_system.process_user_request(user_prompt, session_id)
