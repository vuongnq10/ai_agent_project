#!/usr/bin/env python3
"""
Test script for Django streaming endpoints

This script tests the streaming functionality in Django views
by making HTTP requests to the streaming endpoints.
"""

import requests
import time

def test_simple_streaming():
    """Test the simple streaming endpoint"""
    print("=" * 60)
    print("🚀 Testing Simple Streaming Endpoint")
    print("=" * 60)
    
    url = "http://localhost:8000/chatbot/"  # Adjust URL as needed
    params = {"query": "What is Bitcoin?"}
    
    try:
        response = requests.get(url, params=params, stream=True)
        
        if response.status_code == 200:
            print("✅ Connected to streaming endpoint")
            print("📡 Streaming response:")
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        chunk = decoded_line[6:]  # Remove 'data: ' prefix
                        if chunk == '[DONE]':
                            print("\n✅ Stream completed")
                            break
                        else:
                            print(chunk, end='', flush=True)
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_tools_streaming():
    """Test the streaming endpoint with tools"""
    print("\n" + "=" * 60)
    print("🚀 Testing Tools Streaming Endpoint")
    print("=" * 60)
    
    url = "http://localhost:8000/chatbot/chat_with_tools_stream"  # Adjust URL as needed
    params = {"query": "Calculate the square root of 144", "max_iterations": 5}
    
    try:
        response = requests.get(url, params=params, stream=True)
        
        if response.status_code == 200:
            print("✅ Connected to tools streaming endpoint")
            print("📡 Streaming response:")
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        chunk = decoded_line[6:]  # Remove 'data: ' prefix
                        if chunk == '[DONE]':
                            print("\n✅ Stream completed")
                            break
                        else:
                            print(chunk, end='', flush=True)
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_curl_command():
    """Provide curl commands for manual testing"""
    print("\n" + "=" * 60)
    print("🧪 Manual Testing with cURL")
    print("=" * 60)
    print("Test simple streaming:")
    print('curl -N "http://localhost:8000/chatbot/?query=What+is+Bitcoin%3F"')
    print("\nTest tools streaming:")
    print('curl -N "http://localhost:8000/chatbot/chat_with_tools_stream?query=Calculate+the+square+root+of+144"')
    print("\nNote: -N flag disables buffering for real-time streaming")

if __name__ == "__main__":
    print("🧪 Django Streaming Endpoints Test")
    print("Make sure your Django server is running (python manage.py runserver)")
    print("Press Ctrl+C to stop\n")
    
    try:
        test_simple_streaming()
        time.sleep(1)
        test_tools_streaming()
        test_curl_command()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
