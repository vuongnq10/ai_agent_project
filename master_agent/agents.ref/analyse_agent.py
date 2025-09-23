import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part

from .data_agent import DataAgent

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))

class AnalyseAgent:
    """
    Analysis Agent responsible for:
    - Technical analysis of market data
    - Smart Money Concepts (SMC) analysis
    - Pattern recognition
    - Indicator calculations (RSI, EMA, Bollinger Bands, etc.)
    - Market structure analysis
    - Risk assessment
    """
    
    def __init__(self):
        self.data_agent = DataAgent()
        
    def comprehensive_analysis(self, symbol: str, timeframes: List[str] = None) -> Dict[str, Any]:
        """Perform comprehensive technical analysis across multiple timeframes"""
        if timeframes is None:
            timeframes = ['1h', '4h', '1d']
        
        analysis_results = {}
        
        for timeframe in timeframes:
            ohlcv = self.data_agent.fetch_ohlcv_data(symbol, timeframe, 200)
            if ohlcv:
                df = self.data_agent.preprocess_data(ohlcv)
                
                analysis_results[timeframe] = {
                    'smc_analysis': self.smart_money_concepts(df),
                    'technical_indicators': self.calculate_indicators(df),
                    'market_structure': self.analyze_market_structure(df),
                    'support_resistance': self.find_support_resistance(df),
                    'patterns': self.detect_patterns(df),
                    'risk_metrics': self.calculate_risk_metrics(df)
                }
        
        # Overall sentiment based on all timeframes
        overall_sentiment = self.calculate_overall_sentiment(analysis_results)
        
        return {
            'symbol': symbol,
            'timeframe_analysis': analysis_results,
            'overall_sentiment': overall_sentiment,
            'current_price': self.data_agent.get_current_price(symbol)
        }
    
    def smart_money_concepts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze Smart Money Concepts"""
        if df.empty:
            return {}
        
        return {
            'market_structure': self._calculate_market_structure(df),
            'order_blocks': self._identify_order_blocks(df),
            'fair_value_gaps': self._find_fair_value_gaps(df),
            'liquidity_pools': self._identify_liquidity_pools(df),
            'break_of_structure': self._detect_break_of_structure(df),
            'change_of_character': self._detect_change_of_character(df)
        }
    
    def _calculate_market_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate market structure (Higher Highs, Lower Lows, etc.)"""
        swing_highs = []
        swing_lows = []
        
        for i in range(5, len(df) - 5):
            # Swing High: current high is higher than 5 candles before and after
            if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, 6)) and \
               all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, 6)):
                swing_highs.append({'index': i, 'price': df['high'].iloc[i], 'timestamp': df['timestamp'].iloc[i]})
            
            # Swing Low: current low is lower than 5 candles before and after
            if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, 6)) and \
               all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, 6)):
                swing_lows.append({'index': i, 'price': df['low'].iloc[i], 'timestamp': df['timestamp'].iloc[i]})
        
        # Determine trend
        trend = self._determine_trend(swing_highs, swing_lows)
        
        return {
            'swing_highs': swing_highs[-10:],  # Last 10 swing highs
            'swing_lows': swing_lows[-10:],    # Last 10 swing lows
            'trend': trend,
            'latest_swing_high': swing_highs[-1] if swing_highs else None,
            'latest_swing_low': swing_lows[-1] if swing_lows else None
        }
    
    def _determine_trend(self, swing_highs: List[Dict], swing_lows: List[Dict]) -> str:
        """Determine market trend based on swing points"""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return "INSUFFICIENT_DATA"
        
        recent_highs = swing_highs[-2:]
        recent_lows = swing_lows[-2:]
        
        higher_highs = recent_highs[1]['price'] > recent_highs[0]['price']
        higher_lows = recent_lows[1]['price'] > recent_lows[0]['price']
        lower_highs = recent_highs[1]['price'] < recent_highs[0]['price']
        lower_lows = recent_lows[1]['price'] < recent_lows[0]['price']
        
        if higher_highs and higher_lows:
            return "BULLISH"
        elif lower_highs and lower_lows:
            return "BEARISH"
        elif higher_highs and lower_lows:
            return "RANGING_BULLISH_BIAS"
        elif lower_highs and higher_lows:
            return "RANGING_BEARISH_BIAS"
        else:
            return "SIDEWAYS"
    
    def _identify_order_blocks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify order blocks based on volume and price action"""
        order_blocks = []
        avg_volume = df['volume'].mean()
        volume_threshold = avg_volume * 1.5
        
        for i in range(1, len(df) - 1):
            current = df.iloc[i]
            next_candle = df.iloc[i + 1] if i + 1 < len(df) else None
            
            if current['volume'] > volume_threshold and next_candle is not None:
                # Bullish order block
                if (current['close'] > current['open'] and 
                    next_candle['close'] > next_candle['open'] and
                    next_candle['close'] > current['high']):
                    
                    order_blocks.append({
                        'type': 'BULLISH',
                        'timestamp': current['timestamp'],
                        'high': current['high'],
                        'low': current['low'],
                        'volume': current['volume'],
                        'strength': current['volume'] / avg_volume
                    })
                
                # Bearish order block
                elif (current['close'] < current['open'] and 
                      next_candle['close'] < next_candle['open'] and
                      next_candle['close'] < current['low']):
                    
                    order_blocks.append({
                        'type': 'BEARISH',
                        'timestamp': current['timestamp'],
                        'high': current['high'],
                        'low': current['low'],
                        'volume': current['volume'],
                        'strength': current['volume'] / avg_volume
                    })
        
        return sorted(order_blocks, key=lambda x: x['strength'], reverse=True)[:5]
    
    def _find_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify Fair Value Gaps (FVG)"""
        gaps = []
        
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle2 = df.iloc[i-1]
            candle3 = df.iloc[i]
            
            # Bullish FVG: Gap between candle1 high and candle3 low
            if candle3['low'] > candle1['high']:
                gaps.append({
                    'type': 'BULLISH',
                    'timestamp': candle2['timestamp'],
                    'gap_high': candle3['low'],
                    'gap_low': candle1['high'],
                    'size': candle3['low'] - candle1['high'],
                    'filled': False
                })
            
            # Bearish FVG: Gap between candle1 low and candle3 high
            elif candle3['high'] < candle1['low']:
                gaps.append({
                    'type': 'BEARISH',
                    'timestamp': candle2['timestamp'],
                    'gap_high': candle1['low'],
                    'gap_low': candle3['high'],
                    'size': candle1['low'] - candle3['high'],
                    'filled': False
                })
        
        return gaps[-10:]  # Return last 10 gaps
    
    def _identify_liquidity_pools(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify liquidity pools (areas of high volume)"""
        pools = []
        avg_volume = df['volume'].mean()
        high_volume_threshold = avg_volume * 2
        
        for i in range(len(df)):
            if df['volume'].iloc[i] > high_volume_threshold:
                pools.append({
                    'timestamp': df['timestamp'].iloc[i],
                    'price_level': (df['high'].iloc[i] + df['low'].iloc[i]) / 2,
                    'volume': df['volume'].iloc[i],
                    'type': 'HIGH_VOLUME',
                    'strength': df['volume'].iloc[i] / avg_volume
                })
        
        return sorted(pools, key=lambda x: x['strength'], reverse=True)[:5]
    
    def _detect_break_of_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect Break of Structure (BOS)"""
        market_structure = self._calculate_market_structure(df)
        
        if not market_structure['swing_highs'] or not market_structure['swing_lows']:
            return {'detected': False}
        
        current_price = df['close'].iloc[-1]
        latest_swing_high = market_structure['latest_swing_high']
        latest_swing_low = market_structure['latest_swing_low']
        
        bullish_bos = latest_swing_high and current_price > latest_swing_high['price']
        bearish_bos = latest_swing_low and current_price < latest_swing_low['price']
        
        return {
            'detected': bullish_bos or bearish_bos,
            'type': 'BULLISH' if bullish_bos else 'BEARISH' if bearish_bos else None,
            'broken_level': latest_swing_high['price'] if bullish_bos else latest_swing_low['price'] if bearish_bos else None
        }
    
    def _detect_change_of_character(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect Change of Character (CHoCH)"""
        if len(df) < 50:
            return {'detected': False}
        
        # Use EMA crossover as a proxy for character change
        ema_fast = df['close'].ewm(span=10).mean()
        ema_slow = df['close'].ewm(span=20).mean()
        
        # Recent crossover detection
        recent_cross_up = (ema_fast.iloc[-1] > ema_slow.iloc[-1] and 
                          ema_fast.iloc[-2] <= ema_slow.iloc[-2])
        recent_cross_down = (ema_fast.iloc[-1] < ema_slow.iloc[-1] and 
                            ema_fast.iloc[-2] >= ema_slow.iloc[-2])
        
        return {
            'detected': recent_cross_up or recent_cross_down,
            'type': 'BULLISH' if recent_cross_up else 'BEARISH' if recent_cross_down else None,
            'confidence': abs(ema_fast.iloc[-1] - ema_slow.iloc[-1]) / df['close'].iloc[-1] * 100
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators"""
        if df.empty:
            return {}
        
        indicators = {}
        
        # Moving Averages
        indicators['ema_7'] = df['close'].ewm(span=7).mean().iloc[-1]
        indicators['ema_20'] = df['close'].ewm(span=20).mean().iloc[-1]
        indicators['ema_50'] = df['close'].ewm(span=50).mean().iloc[-1] if len(df) >= 50 else None
        indicators['sma_200'] = df['close'].rolling(window=200).mean().iloc[-1] if len(df) >= 200 else None
        
        # RSI
        indicators['rsi_14'] = self._calculate_rsi(df, 14)
        indicators['rsi_6'] = self._calculate_rsi(df, 6)
        
        # MACD
        macd_line, signal_line, histogram = self._calculate_macd(df)
        indicators['macd'] = {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        }
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df)
        indicators['bollinger_bands'] = {
            'upper': bb_upper,
            'middle': bb_middle,
            'lower': bb_lower
        }
        
        # ATR (Average True Range)
        indicators['atr'] = self._calculate_atr(df)
        
        return indicators
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate RSI"""
        if len(df) < period + 1:
            return 50.0  # Neutral RSI
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _calculate_macd(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        """Calculate MACD"""
        if len(df) < 26:
            return 0.0, 0.0, 0.0
        
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        
        return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(df) < period:
            price = df['close'].iloc[-1]
            return price * 1.02, price, price * 0.98
        
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        
        return upper.iloc[-1], sma.iloc[-1], lower.iloc[-1]
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(df) < period + 1:
            return 0.0
        
        high_low = df['high'] - df['low']
        high_close_prev = abs(df['high'] - df['close'].shift(1))
        low_close_prev = abs(df['low'] - df['close'].shift(1))
        
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0.0
    
    def analyze_market_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall market structure"""
        if df.empty:
            return {}
        
        current_price = df['close'].iloc[-1]
        
        # Price position relative to moving averages
        ema_20 = df['close'].ewm(span=20).mean().iloc[-1]
        ema_50 = df['close'].ewm(span=50).mean().iloc[-1] if len(df) >= 50 else current_price
        
        structure = {
            'price_above_ema20': current_price > ema_20,
            'price_above_ema50': current_price > ema_50,
            'ema20_above_ema50': ema_20 > ema_50,
            'trend_strength': abs(current_price - ema_20) / current_price * 100
        }
        
        # Determine overall structure
        if structure['price_above_ema20'] and structure['price_above_ema50'] and structure['ema20_above_ema50']:
            structure['overall'] = 'STRONG_BULLISH'
        elif structure['price_above_ema20'] and structure['ema20_above_ema50']:
            structure['overall'] = 'BULLISH'
        elif not structure['price_above_ema20'] and not structure['price_above_ema50'] and not structure['ema20_above_ema50']:
            structure['overall'] = 'STRONG_BEARISH'
        elif not structure['price_above_ema20'] and not structure['ema20_above_ema50']:
            structure['overall'] = 'BEARISH'
        else:
            structure['overall'] = 'NEUTRAL'
        
        return structure
    
    def find_support_resistance(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """Find support and resistance levels"""
        if df.empty:
            return {'support': [], 'resistance': []}
        
        # Use local maxima and minima
        from scipy.signal import argrelextrema
        
        # Find local maxima (resistance)
        resistance_indices = argrelextrema(df['high'].values, np.greater, order=5)[0]
        resistance_levels = [df['high'].iloc[i] for i in resistance_indices]
        
        # Find local minima (support)
        support_indices = argrelextrema(df['low'].values, np.less, order=5)[0]
        support_levels = [df['low'].iloc[i] for i in support_indices]
        
        # Sort and get most recent levels
        resistance_levels.sort(reverse=True)
        support_levels.sort(reverse=True)
        
        return {
            'resistance': resistance_levels[:5],
            'support': support_levels[:5]
        }
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect chart patterns"""
        if len(df) < 20:
            return {}
        
        patterns = {}
        
        # Simple pattern detection
        recent_closes = df['close'].tail(10).values
        
        # Ascending triangle
        if self._is_ascending_triangle(recent_closes):
            patterns['ascending_triangle'] = True
        
        # Descending triangle
        if self._is_descending_triangle(recent_closes):
            patterns['descending_triangle'] = True
        
        # Double top/bottom
        patterns.update(self._detect_double_patterns(df))
        
        return patterns
    
    def _is_ascending_triangle(self, prices: np.ndarray) -> bool:
        """Detect ascending triangle pattern"""
        # Simplified: check if highs are relatively flat and lows are rising
        highs = prices[prices == np.maximum.accumulate(prices)]
        if len(highs) < 3:
            return False
        
        high_slope = np.polyfit(range(len(highs)), highs, 1)[0]
        low_slope = np.polyfit(range(len(prices)), prices, 1)[0]
        
        return abs(high_slope) < 0.001 and low_slope > 0.001
    
    def _is_descending_triangle(self, prices: np.ndarray) -> bool:
        """Detect descending triangle pattern"""
        # Simplified: check if lows are relatively flat and highs are falling
        lows = prices[prices == np.minimum.accumulate(prices)]
        if len(lows) < 3:
            return False
        
        low_slope = np.polyfit(range(len(lows)), lows, 1)[0]
        high_slope = np.polyfit(range(len(prices)), prices, 1)[0]
        
        return abs(low_slope) < 0.001 and high_slope < -0.001
    
    def _detect_double_patterns(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Detect double top/bottom patterns"""
        patterns = {}
        
        if len(df) < 20:
            return patterns
        
        highs = df['high'].tail(20)
        lows = df['low'].tail(20)
        
        # Find peaks and troughs
        from scipy.signal import find_peaks
        
        peak_indices, _ = find_peaks(highs.values, distance=5)
        trough_indices, _ = find_peaks(-lows.values, distance=5)
        
        # Double top: two peaks at similar levels
        if len(peak_indices) >= 2:
            peak_prices = [highs.iloc[i] for i in peak_indices[-2:]]
            if abs(peak_prices[0] - peak_prices[1]) / peak_prices[0] < 0.02:  # Within 2%
                patterns['double_top'] = True
        
        # Double bottom: two troughs at similar levels
        if len(trough_indices) >= 2:
            trough_prices = [lows.iloc[i] for i in trough_indices[-2:]]
            if abs(trough_prices[0] - trough_prices[1]) / trough_prices[0] < 0.02:  # Within 2%
                patterns['double_bottom'] = True
        
        return patterns
    
    def calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate risk metrics"""
        if df.empty:
            return {}
        
        returns = df['close'].pct_change().dropna()
        
        return {
            'volatility': returns.std() * np.sqrt(24),  # Assuming hourly data
            'max_drawdown': self._calculate_max_drawdown(df['close']),
            'sharpe_ratio': returns.mean() / returns.std() if returns.std() > 0 else 0,
            'var_95': np.percentile(returns, 5),  # Value at Risk 95%
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis()
        }
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        peak = prices.expanding(min_periods=1).max()
        drawdown = (prices - peak) / peak
        return drawdown.min()
    
    def calculate_overall_sentiment(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall market sentiment from all timeframes"""
        sentiments = []
        weights = {'1h': 0.3, '4h': 0.4, '1d': 0.3}  # Weight longer timeframes more
        
        for timeframe, analysis in analysis_results.items():
            if timeframe in weights:
                tf_sentiment = self._calculate_timeframe_sentiment(analysis)
                sentiments.append({
                    'timeframe': timeframe,
                    'sentiment': tf_sentiment,
                    'weight': weights[timeframe]
                })
        
        # Weighted average sentiment
        total_score = sum(s['sentiment']['score'] * s['weight'] for s in sentiments)
        
        if total_score > 0.6:
            overall = 'BULLISH'
        elif total_score > 0.4:
            overall = 'SLIGHTLY_BULLISH'
        elif total_score > -0.4:
            overall = 'NEUTRAL'
        elif total_score > -0.6:
            overall = 'SLIGHTLY_BEARISH'
        else:
            overall = 'BEARISH'
        
        return {
            'overall_sentiment': overall,
            'confidence_score': abs(total_score),
            'timeframe_sentiments': sentiments
        }
    
    def _calculate_timeframe_sentiment(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate sentiment for a specific timeframe"""
        score = 0
        factors = []
        
        # Technical indicators sentiment
        indicators = analysis.get('technical_indicators', {})
        if indicators:
            rsi = indicators.get('rsi_14', 50)
            if rsi > 70:
                score -= 0.3
                factors.append('RSI Overbought')
            elif rsi < 30:
                score += 0.3
                factors.append('RSI Oversold')
            
            # MACD sentiment
            macd = indicators.get('macd', {})
            if macd.get('histogram', 0) > 0:
                score += 0.2
                factors.append('MACD Bullish')
            else:
                score -= 0.2
                factors.append('MACD Bearish')
        
        # Market structure sentiment
        structure = analysis.get('market_structure', {})
        if structure.get('overall') in ['STRONG_BULLISH', 'BULLISH']:
            score += 0.4
            factors.append('Bullish Structure')
        elif structure.get('overall') in ['STRONG_BEARISH', 'BEARISH']:
            score -= 0.4
            factors.append('Bearish Structure')
        
        # SMC sentiment
        smc = analysis.get('smc_analysis', {})
        market_struct = smc.get('market_structure', {})
        if market_struct.get('trend') == 'BULLISH':
            score += 0.3
            factors.append('SMC Bullish Trend')
        elif market_struct.get('trend') == 'BEARISH':
            score -= 0.3
            factors.append('SMC Bearish Trend')
        
        return {
            'score': max(-1, min(1, score)),  # Clamp between -1 and 1
            'factors': factors
        }
