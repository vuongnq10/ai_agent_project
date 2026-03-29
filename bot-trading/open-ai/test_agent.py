#!/usr/bin/env python3
"""
Test script for OpenAI Agentic Agent
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def test_simple_query():
    """Test the OpenAI agent with a simple query"""
    print("Testing OpenAI Agentic Agent...")
    print("=" * 50)
    
    try:
        import sys
        import os
        
        # Add the current directory to the path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from agents_openai.agentic_agent import MasterOpenAI
        
        # Initialize the agent
        master_agent = MasterOpenAI()
        
        # Test with a simple query
        query = "Hello, what can you do?"
        print(f"Query: {query}")
        print("Response:")
        print("-" * 30)
        
        for chunk in master_agent(query):
            print(chunk, end="")
        
        print("\n" + "=" * 50)
        print("Simple test completed!")
        
    except Exception as e:
        print(f"Error in simple test: {e}")
        import traceback
        traceback.print_exc()

def test_trading_query():
    """Test the OpenAI agent with a trading-related query"""
    print("\nTesting with trading query...")
    print("=" * 50)
    
    try:
        from open_ai.agents_openai.agentic_agent import MasterOpenAI
        
        # Initialize the agent
        master_agent = MasterOpenAI()
        
        # Test with a trading query
        query = "Can you analyze BTC/USDT on 1h timeframe?"
        print(f"Query: {query}")
        print("Response:")
        print("-" * 30)
        
        for chunk in master_agent(query):
            print(chunk, end="")
        
        print("\n" + "=" * 50)
        print("Trading test completed!")
        
    except Exception as e:
        print(f"Error in trading test: {e}")
        import traceback
        traceback.print_exc()

def test_tools():
    """Test the tools directly"""
    print("\nTesting tools directly...")
    print("=" * 50)
    
    try:
        # Add the current directory to the path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from tools.openai_tools import OpenAITools
        
        tools = OpenAITools()
        
        print("Available tools:")
        for tool in tools.tools:
            print(f"- {tool['function']['name']}: {tool['function']['description']}")
        
        print("\nTesting get_ticker function...")
        result = tools.get_ticker("BTCUSDT", "1h")
        print(f"Result: {type(result)} - {len(str(result))} characters")
        
        print("\n" + "=" * 50)
        print("Tools test completed!")
        
    except Exception as e:
        print(f"Error in tools test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("OpenAI Agentic Trading Agent Test Suite")
    print("=" * 60)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        sys.exit(1)
    else:
        print("✅ OPENAI_API_KEY found")
    
    # Run tests
    test_tools()
    test_simple_query()
    # test_trading_query()  # Uncomment this for full trading test
    
    print("\n" + "=" * 60)
    print("All tests completed!")
