"""
Test directo de Azure OpenAI
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_openai_direct():
    """Test directo con Azure OpenAI"""
    print("🧪 Test directo de Azure OpenAI")
    print("=" * 40)
    
    api_key = os.getenv('OPENAI_API_KEY')
    endpoint = os.getenv('OPENAI_ENDPOINT')
    deployment = os.getenv('OPENAI_DEPLOYMENT_NAME')
    
    print(f"API Key: {api_key[:20]}...")
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")
    
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-12-01-preview"
        )
        
        print("\n✅ Cliente Azure OpenAI creado exitosamente")
        
        # Test simple
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "user", "content": "Hola, ¿cómo estás?"}
            ],
            max_tokens=50
        )
        
        print("✅ Respuesta recibida:")
        print(f"🤖 {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_openai_direct()

