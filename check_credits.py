"""
OpenRouter API Key Credits Checker
Quick utility to check your API key status and remaining credits.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_openrouter_credits():
    """Check OpenRouter API key status and credits."""
    
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env file!")
        return
    
    print(f"🔑 API Key: {api_key[:15]}...{api_key[-4:]}")
    print("-" * 50)
    
    # Check key validity
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # 1. Check key info
    print("\n📋 Checking API Key Status...")
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            print(f"   ✅ Key Status: Valid")
            print(f"   📛 Label: {data.get('label', 'N/A')}")
            print(f"   💰 Credits Used: ${data.get('usage', 0):.4f}")
            print(f"   📊 Limit: ${data.get('limit', 'Unlimited')}")
            print(f"   🔢 Rate Limit: {data.get('rate_limit', {}).get('requests', 'N/A')} req/interval")
        elif response.status_code == 401:
            error = response.json().get("error", {})
            print(f"   ❌ Key Status: Invalid")
            print(f"   📛 Error: {error.get('message', 'Unknown error')}")
            print("\n⚠️  Your API key is not valid. Please:")
            print("   1. Go to https://openrouter.ai/keys")
            print("   2. Create a new API key")
            print("   3. Update your .env file with the new key")
            return
        else:
            print(f"   ⚠️ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Network Error: {e}")
        return
    
    # 2. Check credits/limits
    print("\n💳 Checking Credits & Limits...")
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/credits",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            total_credits = data.get("total_credits", 0)
            total_usage = data.get("total_usage", 0)
            remaining = total_credits - total_usage if total_credits else "Unlimited"
            
            print(f"   💵 Total Credits: ${total_credits:.4f}" if total_credits else "   💵 Total Credits: Pay-as-you-go")
            print(f"   📈 Total Usage: ${total_usage:.4f}")
            if isinstance(remaining, (int, float)):
                print(f"   💰 Remaining: ${remaining:.4f}")
        else:
            # Credits endpoint might not exist for all accounts
            print(f"   ℹ️ Credits info not available (status: {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Could not fetch credits: {e}")
    
    # 3. List available models (sample)
    print("\n🤖 Testing Model Access...")
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json().get("data", [])
            print(f"   ✅ Access to {len(models)} models")
            # Show a few popular models
            popular = ["qwen/qwen3-32b", "anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-pro-1.5"]
            print("   📌 Popular models available:")
            for model in models[:5]:
                model_id = model.get("id", "")
                pricing = model.get("pricing", {})
                prompt_cost = float(pricing.get("prompt", 0)) * 1000000  # per 1M tokens
                completion_cost = float(pricing.get("completion", 0)) * 1000000
                print(f"      • {model_id}: ${prompt_cost:.2f}/$1M in, ${completion_cost:.2f}/$1M out")
        else:
            print(f"   ⚠️ Could not fetch models: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Could not fetch models: {e}")
    
    print("\n" + "=" * 50)
    print("✅ API Key check complete!")


if __name__ == "__main__":
    check_openrouter_credits()
