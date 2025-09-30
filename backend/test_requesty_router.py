"""
Test script for Requesty Router integration
Run this to verify your ROUTER_API_KEY is working correctly
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

ROUTER_API_KEY = os.getenv("ROUTER_API_KEY")

if not ROUTER_API_KEY:
    print("❌ ROUTER_API_KEY not found in .env file")
    print("Please add your Requesty Router API key to the .env file")
    exit(1)

print("✓ ROUTER_API_KEY found")
print("Testing Requesty Router connection...\n")

try:
    # Initialize OpenAI client with Requesty Router
    client = OpenAI(
        api_key=ROUTER_API_KEY,
        base_url="https://router.requesty.ai/v1",
        default_headers={"Authorization": f"Bearer {ROUTER_API_KEY}"}
    )
    
    # Test request
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'Hello from Requesty Router!' if you can hear me."}]
    )
    
    # Check response
    if response.choices:
        print("✅ SUCCESS! Requesty Router is working!")
        print(f"\nResponse: {response.choices[0].message.content}")
        print(f"\nUsage: {response.usage.total_tokens} tokens")
    else:
        print("❌ No response received")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease check:")
    print("1. Your ROUTER_API_KEY is valid")
    print("2. You have credits available at https://requesty.ai")
    print("3. Your internet connection is working")
