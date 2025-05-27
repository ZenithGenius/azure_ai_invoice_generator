"""
Test script for Gemini client initialization and basic functionality
"""

import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

def test_gemini_initialization():
    """Test Gemini client initialization and basic functionality."""
    print("\n=== Testing Gemini Client Initialization ===\n")
    
    # 1. Test environment setup
    print("1. Testing environment variables...")
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("💡 Make sure to set GOOGLE_API_KEY in your .env file")
        return False
    print("✅ GOOGLE_API_KEY found")

    # 2. Test Gemini import and version
    print("\n2. Testing Gemini package version...")
    try:
        print(f"📦 google.generativeai version: {genai.__version__}")
        print("✅ Successfully imported google.generativeai")
    except Exception as e:
        print(f"❌ Error importing google.generativeai: {str(e)}")
        return False

    # 3. Test Gemini configuration
    print("\n3. Testing Gemini configuration...")
    try:
        # Configure the Gemini client
        genai.configure(api_key=api_key)
        print("✅ Successfully configured Gemini client")
    except AttributeError:
        print("❌ Error: genai.configure() method not found")
        print("💡 You might need to upgrade google-generativeai package")
        print("   Try: pip install --upgrade google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Error configuring Gemini: {str(e)}")
        return False

    # 4. Test model availability
    print("\n4. Testing model availability...")
    try:
        models = genai.list_models()
        gemini_models = [model.name for model in models if 'gemini' in model.name.lower()]
        if gemini_models:
            print("✅ Available Gemini models:")
            for model in gemini_models:
                print(f"   - {model}")
        else:
            print("❌ No Gemini models found")
            return False
    except Exception as e:
        print(f"❌ Error listing models: {str(e)}")
        return False

    # 5. Test basic generation with retry logic
    print("\n5. Testing basic text generation...")
    max_retries = 3
    retry_delay = 15  # seconds
    
    for attempt in range(max_retries):
        try:
            # Using a less resource-intensive model for testing
            model = genai.GenerativeModel('models/gemini-1.5-flash')  # Using flash model which has higher quotas
            response = model.generate_content("Say hello!")
            print("✅ Successfully generated content:")
            print(f"   Response: {response.text}")
            break
        except Exception as e:
            if "429" in str(e):  # Rate limit error
                if attempt < max_retries - 1:
                    print(f"⚠️ Rate limit hit. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    print("❌ Rate limit persists after all retries.")
                    print("💡 Suggestions:")
                    print("   1. Wait a few minutes before trying again")
                    print("   2. Check your API quota at https://ai.google.dev/")
                    print("   3. Consider upgrading to a paid tier if needed")
                    return False
            else:
                print(f"❌ Error generating content: {str(e)}")
                return False

    print("\n=== All tests completed successfully! ===")
    return True

if __name__ == "__main__":
    test_gemini_initialization() 