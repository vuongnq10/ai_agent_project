import os
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.genai import Client
from google.genai.types import HttpOptions, GenerateContentConfig, Content, Part

# Import CXConnector for advanced SMC analysis
from broker_bot.tools.cx_connector import CXConnector

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))

class DataAgent:
    """
    Data Agent responsible for:
    - Fetching market data from exchanges
    - Real-time price monitoring
    - Historical data analysis
    - Data preprocessing and cleaning
    - Market data aggregation
    """
    
    def __init__(self):
        self.binance = ccxt.binance({})
        self.supported_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
        self.data_cache = {}
        
        # Initialize CXConnector for advanced SMC analysis
        self.cx_connector = CXConnector()
        
    def fetch_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List]:
        """Fetch OHLCV data for a given symbol and timeframe"""
        try:
            if timeframe not in self.supported_timeframes:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
                
            cache_key = f"{symbol}_{timeframe}_{limit}"
            
            # Check cache for recent data (5 minutes)
            if cache_key in self.data_cache:
                cached_time, cached_data = self.data_cache[cache_key]
                if datetime.now() - cached_time < timedelta(minutes=5):
                    return cached_data
            
            ohlcv = self.binance.fetch_ohlcv(symbol, timeframe, limit=limit)
            self.data_cache[cache_key] = (datetime.now(), ohlcv)
            
            return ohlcv
        except Exception as e:
            print(f"Error fetching OHLCV data: {e}")
            return []
    
    def fetch_multiple_timeframes(self, symbol: str, timeframes: List[str] = None, limit: int = 100) -> Dict[str, List]:
        """Fetch data for multiple timeframes"""
        if timeframes is None:
            timeframes = ['1h', '4h', '1d']
        
        multi_data = {}
        for tf in timeframes:
            multi_data[tf] = self.fetch_ohlcv_data(symbol, tf, limit)
        
        return multi_data
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            ticker = self.binance.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching current price: {e}")
            return 0.0
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Fetch order book data"""
        try:
            order_book = self.binance.fetch_order_book(symbol, limit)
            return {
                'bids': order_book['bids'][:limit],
                'asks': order_book['asks'][:limit],
                'spread': order_book['asks'][0][0] - order_book['bids'][0][0] if order_book['asks'] and order_book['bids'] else 0
            }
        except Exception as e:
            print(f"Error fetching order book: {e}")
            return {'bids': [], 'asks': [], 'spread': 0}
    
    def get_volume_profile(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Dict[str, Any]:
        """Calculate volume profile data"""
        try:
            ohlcv = self.fetch_ohlcv_data(symbol, timeframe, limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate volume-weighted average price (VWAP)
            df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
            
            # Volume analysis
            total_volume = df['volume'].sum()
            avg_volume = df['volume'].mean()
            volume_std = df['volume'].std()
            
            return {
                'total_volume': total_volume,
                'average_volume': avg_volume,
                'volume_volatility': volume_std,
                'current_vwap': df['vwap'].iloc[-1],
                'high_volume_periods': len(df[df['volume'] > avg_volume + volume_std])
            }
        except Exception as e:
            print(f"Error calculating volume profile: {e}")
            return {}
    
    def preprocess_data(self, ohlcv_data: List[List]) -> pd.DataFrame:
        """Clean and preprocess raw OHLCV data"""
        if not ohlcv_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Remove any duplicate timestamps
        df = df.drop_duplicates(subset=['timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Calculate basic indicators
        df['price_change'] = df['close'].pct_change()
        df['volatility'] = df['price_change'].rolling(window=20).std()
        df['true_range'] = np.maximum(df['high'] - df['low'], 
                                     np.maximum(abs(df['high'] - df['close'].shift(1)),
                                              abs(df['low'] - df['close'].shift(1))))
        
        return df
    
    def get_market_overview(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get market overview for multiple symbols"""
        if symbols is None:
            symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
        
        market_data = {}
        for symbol in symbols:
            try:
                ticker = self.binance.fetch_ticker(symbol)
                ohlcv = self.fetch_ohlcv_data(symbol, '1d', 7)  # Last 7 days
                
                if ohlcv:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    week_change = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
                else:
                    week_change = 0
                
                market_data[symbol] = {
                    'current_price': ticker['last'],
                    'change_24h': ticker['percentage'],
                    'change_7d': week_change,
                    'volume_24h': ticker['quoteVolume'],
                    'high_24h': ticker['high'],
                    'low_24h': ticker['low']
                }
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                market_data[symbol] = None
        
        return market_data
    
    def detect_anomalies(self, symbol: str, timeframe: str = '1h', lookback: int = 100) -> Dict[str, Any]:
        """Detect price and volume anomalies"""
        try:
            ohlcv = self.fetch_ohlcv_data(symbol, timeframe, lookback)
            df = self.preprocess_data(ohlcv)
            
            if df.empty:
                return {}
            
            # Price anomalies (using z-score)
            price_mean = df['close'].mean()
            price_std = df['close'].std()
            df['price_zscore'] = (df['close'] - price_mean) / price_std
            
            # Volume anomalies
            volume_mean = df['volume'].mean()
            volume_std = df['volume'].std()
            df['volume_zscore'] = (df['volume'] - volume_mean) / volume_std
            
            anomalies = {
                'price_anomalies': len(df[abs(df['price_zscore']) > 2]),
                'volume_spikes': len(df[df['volume_zscore'] > 2]),
                'recent_price_anomaly': abs(df['price_zscore'].iloc[-1]) > 2,
                'recent_volume_spike': df['volume_zscore'].iloc[-1] > 2,
                'max_price_deviation': df['price_zscore'].max(),
                'max_volume_spike': df['volume_zscore'].max()
            }
            
            return anomalies
        except Exception as e:
            print(f"Error detecting anomalies: {e}")
            return {}
    
    def get_correlation_matrix(self, symbols: List[str], timeframe: str = '1d', limit: int = 30) -> Dict[str, Any]:
        """Calculate correlation matrix between different symbols"""
        try:
            price_data = {}
            
            for symbol in symbols:
                ohlcv = self.fetch_ohlcv_data(symbol, timeframe, limit)
                if ohlcv:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    price_data[symbol] = df['close'].values
            
            if len(price_data) < 2:
                return {}
            
            # Create correlation matrix
            df_corr = pd.DataFrame(price_data)
            correlation_matrix = df_corr.corr()
            
            return {
                'correlation_matrix': correlation_matrix.to_dict(),
                'highest_correlation': correlation_matrix.max().max(),
                'lowest_correlation': correlation_matrix.min().min()
            }
        except Exception as e:
            print(f"Error calculating correlation matrix: {e}")
            return {}
    
    # ==================== CXConnector Integration Methods ====================
    
    def get_smc_analysis(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Dict[str, Any]:
        """
        Perform Smart Money Concepts analysis using CXConnector
        Returns comprehensive SMC analysis including order blocks, FVGs, and market structure
        """
        try:
            result = self.cx_connector.smc_analysis(symbol, timeframe, limit)
            return result.get('result', {})
        except Exception as e:
            print(f"Error performing SMC analysis: {e}")
            return {}
    
    def get_ticker_data(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Get ticker data using CXConnector
        Enhanced version of basic ticker with additional analysis
        """
        try:
            result = self.cx_connector.get_ticker(symbol, timeframe)
            return result.get('result', [])
        except Exception as e:
            print(f"Error fetching ticker data: {e}")
            return {}
    
    def create_trading_order(self, symbol: str, side: str, entry: float, 
                           take_profit: float, stop_loss: float) -> Dict[str, Any]:
        """
        Create trading order using CXConnector with risk management
        Integrates with BinanceConnector for actual order placement
        """
        try:
            result = self.cx_connector.create_order(
                symbol=symbol,
                side=side,
                entry=entry,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            return result.get('result', {})
        except Exception as e:
            print(f"Error creating trading order: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_comprehensive_market_data(self, symbol: str, timeframe: str = '1h', 
                                    limit: int = 100) -> Dict[str, Any]:
        """
        Comprehensive market data collection combining standard data with SMC analysis
        """
        try:
            # Get standard market data
            ohlcv = self.fetch_ohlcv_data(symbol, timeframe, limit)
            current_price = self.get_current_price(symbol)
            order_book = self.get_order_book(symbol)
            volume_profile = self.get_volume_profile(symbol, timeframe, limit)
            
            # Get SMC analysis from CXConnector
            smc_data = self.get_smc_analysis(symbol, timeframe, limit)
            
            # Combine all data
            comprehensive_data = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'current_price': current_price,
                'ohlcv_data': ohlcv,
                'order_book': order_book,
                'volume_profile': volume_profile,
                'smc_analysis': smc_data,
                'data_quality': {
                    'ohlcv_points': len(ohlcv) if ohlcv else 0,
                    'smc_available': bool(smc_data),
                    'order_book_depth': len(order_book.get('bids', [])) + len(order_book.get('asks', []))
                }
            }
            
            return comprehensive_data
        except Exception as e:
            print(f"Error collecting comprehensive market data: {e}")
            return {}
    
    def get_multi_timeframe_smc(self, symbol: str, timeframes: List[str] = None, 
                               limit: int = 100) -> Dict[str, Any]:
        """
        Get SMC analysis across multiple timeframes for comprehensive view
        """
        if timeframes is None:
            timeframes = ['1h', '4h', '1d']
        
        multi_smc = {}
        
        for tf in timeframes:
            try:
                smc_data = self.get_smc_analysis(symbol, tf, limit)
                multi_smc[tf] = smc_data
            except Exception as e:
                print(f"Error getting SMC for {tf}: {e}")
                multi_smc[tf] = {}
        
        # Analyze cross-timeframe confluences
        confluence_analysis = self._analyze_timeframe_confluence(multi_smc)
        
        return {
            'symbol': symbol,
            'timeframes': timeframes,
            'smc_by_timeframe': multi_smc,
            'confluence_analysis': confluence_analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_timeframe_confluence(self, multi_smc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze confluences across different timeframes
        """
        confluence = {
            'bullish_signals': 0,
            'bearish_signals': 0,
            'timeframe_agreement': 0,
            'conflicting_signals': 0,
            'dominant_trend': 'NEUTRAL'
        }
        
        try:
            total_timeframes = len(multi_smc)
            bullish_count = 0
            bearish_count = 0
            
            for tf, smc_data in multi_smc.items():
                if not smc_data:
                    continue
                
                market_structure = smc_data.get('market_structure', {})
                structure_type = market_structure.get('structure', 'UNDEFINED')
                
                if 'BULLISH' in structure_type:
                    bullish_count += 1
                    confluence['bullish_signals'] += 1
                elif 'BEARISH' in structure_type:
                    bearish_count += 1
                    confluence['bearish_signals'] += 1
            
            # Calculate agreement level
            if bullish_count > bearish_count:
                confluence['dominant_trend'] = 'BULLISH'
                confluence['timeframe_agreement'] = bullish_count / total_timeframes
            elif bearish_count > bullish_count:
                confluence['dominant_trend'] = 'BEARISH'
                confluence['timeframe_agreement'] = bearish_count / total_timeframes
            else:
                confluence['dominant_trend'] = 'NEUTRAL'
                confluence['timeframe_agreement'] = 0.5
            
            confluence['conflicting_signals'] = abs(bullish_count - bearish_count)
            
        except Exception as e:
            print(f"Error analyzing timeframe confluence: {e}")
        
        return confluence
    
    def get_enhanced_data_for_analysis(self, symbol: str, timeframes: List[str] = None, 
                                     limit: int = 100) -> Dict[str, Any]:
        """
        Get enhanced data package optimized for trading analysis
        Combines all available data sources including CXConnector SMC analysis
        """
        if timeframes is None:
            timeframes = ['1h', '4h', '1d']
        
        try:
            # Standard multi-timeframe data
            multi_data = self.fetch_multiple_timeframes(symbol, timeframes, limit)
            
            # Current market state
            current_price = self.get_current_price(symbol)
            order_book = self.get_order_book(symbol)
            
            # Multi-timeframe SMC analysis
            multi_smc = self.get_multi_timeframe_smc(symbol, timeframes, limit)
            
            # Market anomalies and correlations
            anomalies = self.detect_anomalies(symbol, timeframes[0], limit)
            
            # Volume profiles for each timeframe
            volume_profiles = {}
            for tf in timeframes:
                volume_profiles[tf] = self.get_volume_profile(symbol, tf, limit)
            
            enhanced_data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_market_state': {
                    'price': current_price,
                    'order_book': order_book,
                    'anomalies': anomalies
                },
                'multi_timeframe_data': multi_data,
                'smc_analysis': multi_smc,
                'volume_profiles': volume_profiles,
                'data_summary': {
                    'timeframes_analyzed': len(timeframes),
                    'total_candles': sum(len(data) for data in multi_data.values() if data),
                    'smc_signals': multi_smc.get('confluence_analysis', {}).get('bullish_signals', 0) + 
                                  multi_smc.get('confluence_analysis', {}).get('bearish_signals', 0),
                    'dominant_trend': multi_smc.get('confluence_analysis', {}).get('dominant_trend', 'NEUTRAL'),
                    'data_quality_score': self._calculate_data_quality_score(multi_data, multi_smc)
                }
            }
            
            return enhanced_data
        except Exception as e:
            print(f"Error getting enhanced data for analysis: {e}")
            return {}
    
    def _calculate_data_quality_score(self, multi_data: Dict, multi_smc: Dict) -> float:
        """
        Calculate a data quality score based on available data completeness
        """
        try:
            score = 0.0
            max_score = 100.0
            
            # OHLCV data completeness (40% of score)
            ohlcv_score = 0
            for tf, data in multi_data.items():
                if data and len(data) > 50:  # At least 50 candles
                    ohlcv_score += 1
            ohlcv_score = (ohlcv_score / len(multi_data)) * 40 if multi_data else 0
            
            # SMC data availability (35% of score)
            smc_score = 0
            smc_by_tf = multi_smc.get('smc_by_timeframe', {})
            for tf, smc_data in smc_by_tf.items():
                if smc_data and isinstance(smc_data, dict):
                    # Check for key SMC components
                    components = ['market_structure', 'liquidity_pools', 'order_blocks', 'fair_value_gaps']
                    available_components = sum(1 for comp in components if comp in smc_data)
                    smc_score += available_components / len(components)
            smc_score = (smc_score / len(smc_by_tf)) * 35 if smc_by_tf else 0
            
            # Confluence analysis (25% of score)
            confluence = multi_smc.get('confluence_analysis', {})
            confluence_score = 0
            if confluence:
                agreement = confluence.get('timeframe_agreement', 0)
                confluence_score = agreement * 25
            
            score = ohlcv_score + smc_score + confluence_score
            return min(score, max_score)
        except Exception as e:
            print(f"Error calculating data quality score: {e}")
            return 0.0
