#!/usr/bin/env python3
"""
Test script for the Agentic AI trading system
Tests the coordination between DataAgent, AnalyseAgent, and DecisionAgent
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Agentic AI system
from master_agent.agents.agentic_ai import AgenticAI, process_trading_request

async def test_individual_agents():
    """Test each agent individually"""
    print("🧪 Testing Individual Agents")
    print("=" * 50)
    
    try:
        ai_system = AgenticAI()
        
        # Test DataAgent
        print("\n📊 Testing DataAgent...")
        btc_price = ai_system.data_agent.get_current_price('BTC/USDT')
        print(f"✅ Current BTC price: ${btc_price}")
        
        ohlcv_data = ai_system.data_agent.fetch_ohlcv_data('BTC/USDT', '1h', 10)
        print(f"✅ Fetched {len(ohlcv_data)} OHLCV records")
        
        # Test AnalyseAgent
        print("\n📈 Testing AnalyseAgent...")
        analysis = ai_system.analyse_agent.comprehensive_analysis('BTC/USDT', ['1h'])
        print(f"✅ Analysis completed for BTC/USDT")
        print(f"   Overall sentiment: {analysis.get('overall_sentiment', {}).get('overall_sentiment', 'N/A')}")
        
        # Test DecisionAgent
        print("\n🎯 Testing DecisionAgent...")
        decision = ai_system.decision_agent.make_trading_decision('BTC/USDT', 10000)
        print(f"✅ Trading decision: {decision.get('action', 'N/A')}")
        print(f"   Confidence: {decision.get('confidence', 0):.2f}")
        print(f"   Recommendation: {decision.get('recommendation', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing individual agents: {e}")
        return False

async def test_agentic_ai_system():
    """Test the LangGraph-based Agentic AI system with various user prompts"""
    print("\n🤖 Testing LangGraph Agentic AI System")
    print("=" * 50)
    
    test_prompts = [
        "Analyze BTC/USDT for me",
        "Should I buy SOL right now?", 
        "Give me a market overview",
        "What's the risk level for ETH?",
        "How is my portfolio performing?",
        "What are the current trading opportunities?"
    ]
    
    ai_system = AgenticAI()
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🔍 Test {i}: '{prompt}'")
        try:
            response = await ai_system.process_user_request(prompt, f"test_session_{i}")
            
            print(f"   Type: {response.get('type', 'Unknown')}")
            print(f"   Status: {response.get('status', 'Unknown')}")
            
            if response.get('status') == 'success':
                if response.get('summary'):
                    print(f"   Summary: {response['summary'][:100]}...")
                elif response.get('explanation'):
                    print(f"   Explanation: {response['explanation'][:100]}...")
                elif response.get('response'):
                    print(f"   Response: {response['response'][:100]}...")
                elif response.get('overview'):
                    print(f"   Overview: {response['overview'][:100]}...")
                elif response.get('risk_summary'):
                    print(f"   Risk Summary: {response['risk_summary'][:100]}...")
                print("   ✅ Success")
            else:
                print(f"   ❌ Error: {response.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

async def test_convenience_function():
    """Test the convenience function"""
    print("\n⚡ Testing Convenience Function")
    print("=" * 50)
    
    try:
        response = await process_trading_request("Analyze BTC for trading", "convenience_test")
        print(f"✅ Convenience function works")
        print(f"   Response type: {response.get('type')}")
        print(f"   Status: {response.get('status')}")
        
    except Exception as e:
        print(f"❌ Convenience function error: {e}")

async def test_system_status():
    """Test system status and capabilities"""
    print("\n🔧 Testing System Status")
    print("=" * 50)
    
    try:
        ai_system = AgenticAI()
        status = ai_system.get_system_status()
        
        print(f"✅ System Status: {status['status']}")
        print(f"   Active Agents: {list(status['agents'].keys())}")
        print(f"   Supported Symbols: {len(status['supported_symbols'])} symbols")
        print(f"   Capabilities: {len(status['capabilities'])} features")
        
    except Exception as e:
        print(f"❌ System status error: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting Agentic AI System Tests")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test individual agents
    agents_ok = await test_individual_agents()
    
    if agents_ok:
        # Test the full system
        await test_agentic_ai_system()
        
        # Test convenience function
        await test_convenience_function()
        
        # Test system status
        await test_system_status()
    
    print("\n" + "=" * 60)
    print("🏁 Tests Completed")
    
    if agents_ok:
        print("✅ Agentic AI System is operational!")
    else:
        print("❌ Some tests failed. Check configuration and dependencies.")

if __name__ == "__main__":
    # Check if we have required environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY environment variable is required")
        sys.exit(1)
    
    # Run the tests
    asyncio.run(main())
