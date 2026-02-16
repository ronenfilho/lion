"""
Teste simples do LocalLLMClient.
"""
import sys
sys.path.insert(0, '/home/decode/workspace/lion')

from src.generation.local_llm_client import LocalLLMClient

def test_local_llm():
    print("🔧 Testando LocalLLMClient...")
    print("="*70)
    
    try:
        # Criar cliente TinyLlama (modelo menor)
        print("📦 Carregando TinyLlama (1.1B)...")
        client = LocalLLMClient(model_name='tinyllama', quantize=False)
        
        print(f"✅ Modelo carregado: {client.model_name}")
        print(f"   Device: {client.model.device}")
        print()
        
        # Testar geração simples
        prompt = "Qual é a capital do Brasil?"
        print(f"💬 Prompt: {prompt}")
        print()
        
        print("⏳ Gerando resposta...")
        result = client.generate(prompt, max_tokens=50, temperature=0.7)
        
        print("✅ Resposta gerada!")
        print(f"   Texto: {result.text[:200]}...")
        print(f"   Tokens: {result.tokens_used}")
        print(f"   Tempo: {result.generation_time:.2f}s")
        print(f"   Finish: {result.finish_reason}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_local_llm()
