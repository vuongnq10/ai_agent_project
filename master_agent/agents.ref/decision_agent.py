import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part

from .data_agent import DataAgent
from .analyse_agent import AnalyseAgent

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))

class DecisionAgent:
    """
    Decision Agent responsible for:
    - Making trading decisions based on analysis
    - Risk management and position sizing
    - Entry and exit strategies
    - Trade execution recommendations
    - Portfolio management
    - Risk assessment and mitigation
    """
    
    def __init__(self):
        self.data_agent = DataAgent()
        self.analyse_agent = AnalyseAgent()
        self.risk_tolerance = 0.02  # 2% max risk per trade
        self.max_position_size = 0.1  # 10% of portfolio max
        
    def make_trading_decision(self, symbol: str, account_balance: float = 10000, 
                            custom_risk_tolerance: float = None) -> Dict[str, Any]:
        """
        Make a comprehensive trading decision for a given symbol
        """
        if custom_risk_tolerance:
            self.risk_tolerance = custom_risk_tolerance
            
        # Get comprehensive analysis
        analysis = self.analyse_agent.comprehensive_analysis(symbol)
        current_price = analysis['current_price']
        
        # Evaluate trading opportunity
        decision = self._evaluate_trading_opportunity(analysis, current_price, account_balance)
        
        # Calculate position sizing and risk management
        if decision['action'] in ['BUY', 'SELL']:
            risk_management = self._calculate_risk_management(
                current_price, decision, account_balance
            )
            decision.update(risk_management)
        
        # Add timestamp and metadata
        decision.update({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'current_price': current_price,
            'account_balance': account_balance,
            'analysis_summary': self._create_analysis_summary(analysis)
        })
        
        return decision
    
    def _evaluate_trading_opportunity(self, analysis: Dict[str, Any], 
                                    current_price: float, account_balance: float) -> Dict[str, Any]:
        """
        Evaluate whether to enter a trade and in which direction
        """
        overall_sentiment = analysis['overall_sentiment']
        timeframe_analysis = analysis['timeframe_analysis']
        
        # Initialize scoring system
        bullish_score = 0
        bearish_score = 0
        confidence_factors = []
        
        # Analyze each timeframe
        for timeframe, tf_analysis in timeframe_analysis.items():
            weight = self._get_timeframe_weight(timeframe)
            
            # SMC Analysis scoring
            smc_score = self._score_smc_analysis(tf_analysis.get('smc_analysis', {}))
            
            # Technical indicators scoring
            indicators_score = self._score_technical_indicators(tf_analysis.get('technical_indicators', {}))
            
            # Market structure scoring
            structure_score = self._score_market_structure(tf_analysis.get('market_structure', {}))
            
            # Pattern scoring
            pattern_score = self._score_patterns(tf_analysis.get('patterns', {}))
            
            # Combine scores for this timeframe
            tf_bullish = (smc_score['bullish'] + indicators_score['bullish'] + 
                         structure_score['bullish'] + pattern_score['bullish']) * weight
            tf_bearish = (smc_score['bearish'] + indicators_score['bearish'] + 
                         structure_score['bearish'] + pattern_score['bearish']) * weight
            
            bullish_score += tf_bullish
            bearish_score += tf_bearish
            
            confidence_factors.extend([
                f"{timeframe}: SMC {smc_score['reason']}",
                f"{timeframe}: Indicators {indicators_score['reason']}",
                f"{timeframe}: Structure {structure_score['reason']}"
            ])
        
        # Risk assessment
        risk_assessment = self._assess_market_risk(timeframe_analysis)
        
        # Make final decision
        decision = self._make_final_decision(
            bullish_score, bearish_score, risk_assessment, confidence_factors
        )
        
        return decision
    
    def _get_timeframe_weight(self, timeframe: str) -> float:
        """Get weight for different timeframes"""
        weights = {
            '1h': 0.25,
            '4h': 0.40,
            '1d': 0.35
        }
        return weights.get(timeframe, 0.1)
    
    def _score_smc_analysis(self, smc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Score Smart Money Concepts analysis"""
        bullish_score = 0
        bearish_score = 0
        reasons = []
        
        # Market structure trend
        market_structure = smc_analysis.get('market_structure', {})
        trend = market_structure.get('trend', 'SIDEWAYS')
        
        if trend == 'BULLISH':
            bullish_score += 0.4
            reasons.append('Bullish trend')
        elif trend == 'BEARISH':
            bearish_score += 0.4
            reasons.append('Bearish trend')
        
        # Break of Structure
        bos = smc_analysis.get('break_of_structure', {})
        if bos.get('detected'):
            if bos.get('type') == 'BULLISH':
                bullish_score += 0.3
                reasons.append('Bullish BOS')
            elif bos.get('type') == 'BEARISH':
                bearish_score += 0.3
                reasons.append('Bearish BOS')
        
        # Order Blocks
        order_blocks = smc_analysis.get('order_blocks', [])
        if order_blocks:
            recent_ob = order_blocks[0]  # Most significant order block
            if recent_ob.get('type') == 'BULLISH':
                bullish_score += 0.2
                reasons.append('Bullish OB')
            elif recent_ob.get('type') == 'BEARISH':
                bearish_score += 0.2
                reasons.append('Bearish OB')
        
        # Fair Value Gaps
        fvgs = smc_analysis.get('fair_value_gaps', [])
        if fvgs:
            recent_fvg = fvgs[-1]  # Most recent FVG
            if recent_fvg.get('type') == 'BULLISH':
                bullish_score += 0.1
                reasons.append('Bullish FVG')
            elif recent_fvg.get('type') == 'BEARISH':
                bearish_score += 0.1
                reasons.append('Bearish FVG')
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'reason': ', '.join(reasons) if reasons else 'No clear SMC signals'
        }
    
    def _score_technical_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Score technical indicators"""
        bullish_score = 0
        bearish_score = 0
        reasons = []
        
        # RSI Analysis
        rsi_14 = indicators.get('rsi_14', 50)
        if rsi_14 < 30:
            bullish_score += 0.3
            reasons.append('RSI oversold')
        elif rsi_14 > 70:
            bearish_score += 0.3
            reasons.append('RSI overbought')
        elif 40 <= rsi_14 <= 60:
            reasons.append('RSI neutral')
        
        # MACD Analysis
        macd = indicators.get('macd', {})
        if macd.get('histogram', 0) > 0:
            bullish_score += 0.2
            reasons.append('MACD bullish')
        else:
            bearish_score += 0.2
            reasons.append('MACD bearish')
        
        # Moving Average Analysis
        ema_7 = indicators.get('ema_7')
        ema_20 = indicators.get('ema_20')
        if ema_7 and ema_20:
            if ema_7 > ema_20:
                bullish_score += 0.2
                reasons.append('EMA bullish')
            else:
                bearish_score += 0.2
                reasons.append('EMA bearish')
        
        # Bollinger Bands
        bb = indicators.get('bollinger_bands', {})
        if bb:
            current_price = indicators.get('current_price', 0)
            if current_price and current_price < bb.get('lower', 0):
                bullish_score += 0.2
                reasons.append('Price below BB lower')
            elif current_price and current_price > bb.get('upper', 0):
                bearish_score += 0.2
                reasons.append('Price above BB upper')
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'reason': ', '.join(reasons) if reasons else 'Indicators neutral'
        }
    
    def _score_market_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Score market structure"""
        bullish_score = 0
        bearish_score = 0
        reasons = []
        
        overall = structure.get('overall', 'NEUTRAL')
        
        if overall in ['STRONG_BULLISH', 'BULLISH']:
            bullish_score += 0.4 if overall == 'STRONG_BULLISH' else 0.3
            reasons.append(f'{overall.lower()} structure')
        elif overall in ['STRONG_BEARISH', 'BEARISH']:
            bearish_score += 0.4 if overall == 'STRONG_BEARISH' else 0.3
            reasons.append(f'{overall.lower()} structure')
        else:
            reasons.append('Neutral structure')
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'reason': ', '.join(reasons) if reasons else 'Structure neutral'
        }
    
    def _score_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Score chart patterns"""
        bullish_score = 0
        bearish_score = 0
        reasons = []
        
        if patterns.get('double_bottom'):
            bullish_score += 0.3
            reasons.append('Double bottom')
        
        if patterns.get('double_top'):
            bearish_score += 0.3
            reasons.append('Double top')
        
        if patterns.get('ascending_triangle'):
            bullish_score += 0.2
            reasons.append('Ascending triangle')
        
        if patterns.get('descending_triangle'):
            bearish_score += 0.2
            reasons.append('Descending triangle')
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'reason': ', '.join(reasons) if reasons else 'No significant patterns'
        }
    
    def _assess_market_risk(self, timeframe_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall market risk"""
        total_volatility = 0
        risk_factors = []
        
        for timeframe, analysis in timeframe_analysis.items():
            risk_metrics = analysis.get('risk_metrics', {})
            volatility = risk_metrics.get('volatility', 0)
            total_volatility += volatility
            
            if volatility > 0.3:  # High volatility threshold
                risk_factors.append(f'High volatility in {timeframe}')
            
            max_drawdown = risk_metrics.get('max_drawdown', 0)
            if max_drawdown < -0.15:  # High drawdown
                risk_factors.append(f'High drawdown risk in {timeframe}')
        
        avg_volatility = total_volatility / len(timeframe_analysis)
        
        if avg_volatility > 0.4:
            risk_level = 'HIGH'
        elif avg_volatility > 0.2:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'risk_level': risk_level,
            'average_volatility': avg_volatility,
            'risk_factors': risk_factors
        }
    
    def _make_final_decision(self, bullish_score: float, bearish_score: float, 
                           risk_assessment: Dict[str, Any], confidence_factors: List[str]) -> Dict[str, Any]:
        """Make the final trading decision"""
        
        net_score = bullish_score - bearish_score
        confidence = abs(net_score)
        
        # Risk adjustment
        risk_multiplier = {
            'LOW': 1.0,
            'MEDIUM': 0.8,
            'HIGH': 0.6
        }.get(risk_assessment['risk_level'], 0.5)
        
        adjusted_confidence = confidence * risk_multiplier
        
        # Decision thresholds
        if net_score > 0.6 and adjusted_confidence > 0.5:
            action = 'BUY'
            setup_type = 'STRONG_BULLISH'
        elif net_score > 0.3 and adjusted_confidence > 0.3:
            action = 'BUY'
            setup_type = 'MODERATE_BULLISH'
        elif net_score < -0.6 and adjusted_confidence > 0.5:
            action = 'SELL'
            setup_type = 'STRONG_BEARISH'
        elif net_score < -0.3 and adjusted_confidence > 0.3:
            action = 'SELL'
            setup_type = 'MODERATE_BEARISH'
        else:
            action = 'WAIT'
            setup_type = 'NO_CLEAR_SETUP'
        
        return {
            'action': action,
            'setup_type': setup_type,
            'confidence': min(adjusted_confidence, 1.0),
            'bullish_score': bullish_score,
            'bearish_score': bearish_score,
            'net_score': net_score,
            'risk_assessment': risk_assessment,
            'confidence_factors': confidence_factors,
            'recommendation': self._generate_recommendation(action, setup_type, adjusted_confidence)
        }
    
    def _calculate_risk_management(self, current_price: float, decision: Dict[str, Any], 
                                 account_balance: float) -> Dict[str, Any]:
        """Calculate position sizing and risk management parameters"""
        
        action = decision['action']
        confidence = decision['confidence']
        
        # Base position size on confidence and risk tolerance
        risk_amount = account_balance * self.risk_tolerance
        confidence_multiplier = min(confidence * 1.5, 1.0)  # Scale with confidence
        position_value = min(risk_amount * confidence_multiplier, account_balance * self.max_position_size)
        
        # Calculate stop loss and take profit based on ATR or percentage
        atr_estimate = current_price * 0.02  # 2% ATR estimate if not available
        
        if action == 'BUY':
            # For long positions
            stop_loss = current_price - (atr_estimate * 2)  # 2 ATR stop loss
            take_profit_1 = current_price + (atr_estimate * 2)  # 2:1 RR
            take_profit_2 = current_price + (atr_estimate * 3)  # 3:1 RR
            
            # Calculate position size based on stop loss distance
            stop_distance = current_price - stop_loss
            position_size = risk_amount / stop_distance if stop_distance > 0 else 0
            
        else:  # SELL
            # For short positions
            stop_loss = current_price + (atr_estimate * 2)  # 2 ATR stop loss
            take_profit_1 = current_price - (atr_estimate * 2)  # 2:1 RR
            take_profit_2 = current_price - (atr_estimate * 3)  # 3:1 RR
            
            # Calculate position size based on stop loss distance
            stop_distance = stop_loss - current_price
            position_size = risk_amount / stop_distance if stop_distance > 0 else 0
        
        # Ensure position size doesn't exceed maximum
        max_size = position_value / current_price
        position_size = min(position_size, max_size)
        
        return {
            'position_size': round(position_size, 6),
            'position_value': round(position_size * current_price, 2),
            'risk_amount': round(risk_amount, 2),
            'stop_loss': round(stop_loss, 4),
            'take_profit_1': round(take_profit_1, 4),
            'take_profit_2': round(take_profit_2, 4),
            'risk_reward_ratio': 2.0,
            'max_loss_percentage': self.risk_tolerance * 100
        }
    
    def _generate_recommendation(self, action: str, setup_type: str, confidence: float) -> str:
        """Generate human-readable recommendation"""
        
        confidence_text = "high" if confidence > 0.7 else "moderate" if confidence > 0.4 else "low"
        
        recommendations = {
            'BUY': {
                'STRONG_BULLISH': f"Strong BUY signal with {confidence_text} confidence. All indicators align for a bullish move.",
                'MODERATE_BULLISH': f"Moderate BUY signal with {confidence_text} confidence. Some bullish indicators present."
            },
            'SELL': {
                'STRONG_BEARISH': f"Strong SELL signal with {confidence_text} confidence. All indicators align for a bearish move.",
                'MODERATE_BEARISH': f"Moderate SELL signal with {confidence_text} confidence. Some bearish indicators present."
            },
            'WAIT': {
                'NO_CLEAR_SETUP': f"WAIT for better setup. Current market conditions don't provide clear directional bias with sufficient confidence."
            }
        }
        
        return recommendations.get(action, {}).get(setup_type, "No clear recommendation available.")
    
    def _create_analysis_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the analysis for decision context"""
        
        overall_sentiment = analysis.get('overall_sentiment', {})
        timeframes = list(analysis.get('timeframe_analysis', {}).keys())
        
        # Get key levels from 4h timeframe (most important for decisions)
        key_analysis = analysis.get('timeframe_analysis', {}).get('4h', {})
        support_resistance = key_analysis.get('support_resistance', {})
        
        return {
            'overall_sentiment': overall_sentiment.get('overall_sentiment', 'NEUTRAL'),
            'confidence_score': overall_sentiment.get('confidence_score', 0),
            'analyzed_timeframes': timeframes,
            'key_support_levels': support_resistance.get('support', [])[:3],
            'key_resistance_levels': support_resistance.get('resistance', [])[:3],
            'primary_trend': key_analysis.get('smc_analysis', {}).get('market_structure', {}).get('trend', 'SIDEWAYS')
        }
    
    def evaluate_exit_strategy(self, symbol: str, entry_price: float, position_side: str, 
                             current_pl_percentage: float) -> Dict[str, Any]:
        """
        Evaluate whether to exit an existing position
        """
        
        # Get current analysis
        analysis = self.analyse_agent.comprehensive_analysis(symbol)
        current_price = analysis['current_price']
        
        # Calculate current position metrics
        if position_side.upper() == 'LONG':
            unrealized_pl = ((current_price - entry_price) / entry_price) * 100
        else:
            unrealized_pl = ((entry_price - current_price) / entry_price) * 100
        
        # Check for exit conditions
        exit_decision = self._evaluate_exit_conditions(
            analysis, entry_price, current_price, position_side, unrealized_pl
        )
        
        return {
            'symbol': symbol,
            'entry_price': entry_price,
            'current_price': current_price,
            'position_side': position_side,
            'unrealized_pl_percentage': round(unrealized_pl, 2),
            'exit_decision': exit_decision,
            'timestamp': datetime.now().isoformat()
        }
    
    def _evaluate_exit_conditions(self, analysis: Dict[str, Any], entry_price: float, 
                                current_price: float, position_side: str, unrealized_pl: float) -> Dict[str, Any]:
        """Evaluate conditions for exiting a position"""
        
        # Get current market sentiment
        overall_sentiment = analysis.get('overall_sentiment', {})
        sentiment = overall_sentiment.get('overall_sentiment', 'NEUTRAL')
        
        exit_reasons = []
        exit_action = 'HOLD'
        
        # Profit taking conditions
        if unrealized_pl > 4:  # 4% profit
            exit_reasons.append('Significant profit reached')
            exit_action = 'PARTIAL_EXIT'
        elif unrealized_pl > 8:  # 8% profit
            exit_reasons.append('Strong profit - consider full exit')
            exit_action = 'FULL_EXIT'
        
        # Stop loss conditions
        if unrealized_pl < -2:  # 2% loss
            exit_reasons.append('Stop loss triggered')
            exit_action = 'FULL_EXIT'
        
        # Sentiment reversal conditions
        if position_side.upper() == 'LONG' and sentiment in ['BEARISH', 'STRONGLY_BEARISH']:
            exit_reasons.append('Sentiment turned bearish')
            if exit_action == 'HOLD':
                exit_action = 'CONSIDER_EXIT'
        elif position_side.upper() == 'SHORT' and sentiment in ['BULLISH', 'STRONGLY_BULLISH']:
            exit_reasons.append('Sentiment turned bullish')
            if exit_action == 'HOLD':
                exit_action = 'CONSIDER_EXIT'
        
        # Technical break conditions
        key_analysis = analysis.get('timeframe_analysis', {}).get('4h', {})
        smc_analysis = key_analysis.get('smc_analysis', {})
        bos = smc_analysis.get('break_of_structure', {})
        
        if bos.get('detected'):
            if (position_side.upper() == 'LONG' and bos.get('type') == 'BEARISH') or \
               (position_side.upper() == 'SHORT' and bos.get('type') == 'BULLISH'):
                exit_reasons.append('Break of structure against position')
                exit_action = 'FULL_EXIT'
        
        return {
            'action': exit_action,
            'reasons': exit_reasons,
            'recommendation': self._generate_exit_recommendation(exit_action, exit_reasons, unrealized_pl)
        }
    
    def _generate_exit_recommendation(self, action: str, reasons: List[str], pl_percentage: float) -> str:
        """Generate exit recommendation text"""
        
        recommendations = {
            'HOLD': f"Continue holding position. Current P/L: {pl_percentage:.2f}%",
            'PARTIAL_EXIT': f"Consider taking partial profits. Current P/L: {pl_percentage:.2f}%. Reasons: {', '.join(reasons)}",
            'FULL_EXIT': f"Exit position immediately. Current P/L: {pl_percentage:.2f}%. Reasons: {', '.join(reasons)}",
            'CONSIDER_EXIT': f"Monitor closely and consider exit. Current P/L: {pl_percentage:.2f}%. Reasons: {', '.join(reasons)}"
        }
        
        return recommendations.get(action, f"No clear exit signal. Current P/L: {pl_percentage:.2f}%")
