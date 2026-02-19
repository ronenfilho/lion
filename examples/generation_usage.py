"""
Exemplo de uso do sistema de geração com múltiplos provedores
"""

import os
import sys
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from generation import create_llm_client, GenerationConfig, LLMFactory


def example_basic_usage():
    """Exemplo básico de uso."""
    print("🔹 EXEMPLO 1: Uso básico (provedor padrão)")
    print("=" * 60)
    
    # Criar cliente usando provedor padrão do .env
    llm = create_llm_client()
    
    print(f"Provedor: {llm.provider_name}")
    print(f"Modelo: {llm.model_name}")
    
    # Gerar resposta simples
    result = llm.generate("O que é IRPF?")
    
    print(f"\n💬 Resposta:")
    print(result.text[:200] + "..." if len(result.text) > 200 else result.text)
    print(f"\n📊 Tokens: {result.tokens_used} | Tempo: {result.generation_time:.2f}s")


def example_specific_provider():
    """Exemplo especificando provedor."""
    print("\n\n🔹 EXEMPLO 2: Especificar provedor")
    print("=" * 60)
    
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  Exemplo requer GEMINI_API_KEY")
        print("Código:")
        print("  llm = create_llm_client(")
        print("      provider='gemini',")
        print("      model_name='gemini-2.0-flash-exp'")
        print("  )")
        return
    
    # Criar cliente Gemini explicitamente
    llm = create_llm_client(
        provider='gemini',
        model_name='gemini-2.0-flash-exp'
    )
    
    print(f"Provedor: {llm.provider_name}")
    print(f"Modelo: {llm.model_name}")


def example_custom_config():
    """Exemplo com configuração customizada."""
    print("\n\n🔹 EXEMPLO 3: Configuração customizada")
    print("=" * 60)
    
    # Configuração mais criativa
    config = GenerationConfig(
        temperature=0.7,  # Mais criativo
        max_tokens=1000,  # Respostas mais longas
        top_p=0.95
    )
    
    print(f"Configuração:")
    print(f"  • Temperature: {config.temperature}")
    print(f"  • Max tokens: {config.max_tokens}")
    print(f"  • Top-p: {config.top_p}")
    
    print("\nCódigo para criar cliente:")
    print("  config = GenerationConfig(temperature=0.7, max_tokens=1000)")
    print("  llm = create_llm_client(config=config)")


def example_rag_generation():
    """Exemplo de geração com contexto RAG."""
    print("\n\n🔹 EXEMPLO 4: Geração RAG")
    print("=" * 60)
    
    llm = create_llm_client()
    
    # Simular chunks recuperados
    context_chunks = [
        "Art. 68. São permitidas deduções de despesas com educação até R$ 3.561,50.",
        "§ 1º As deduções devem ser comprovadas documentalmente.",
        "Art. 69. Despesas médicas podem ser deduzidas integralmente."
    ]
    
    query = "Quais deduções são permitidas no IRPF?"
    
    result = llm.generate_with_context(
        query=query,
        context_chunks=context_chunks,
        system_instruction="Você é um assistente especializado em IRPF."
    )
    
    print(f"💬 Resposta:")
    print(result.text[:300] + "..." if len(result.text) > 300 else result.text)


def example_chat():
    """Exemplo de conversação multi-turno."""
    print("\n\n🔹 EXEMPLO 5: Conversação multi-turno")
    print("=" * 60)
    
    llm = create_llm_client()
    
    messages = [
        {'role': 'user', 'content': 'O que é IRPF?'},
        {'role': 'assistant', 'content': 'IRPF é o Imposto de Renda Pessoa Física...'},
        {'role': 'user', 'content': 'E quem precisa declarar?'}
    ]
    
    result = llm.chat(
        messages=messages,
        system_instruction="Você é um assistente de IRPF."
    )
    
    print(f"💬 Resposta do chat:")
    print(result.text[:200] + "..." if len(result.text) > 200 else result.text)


def example_list_providers():
    """Listar provedores disponíveis."""
    print("\n\n🔹 EXEMPLO 6: Provedores disponíveis")
    print("=" * 60)
    
    providers = LLMFactory.list_providers()
    
    print(f"Provedores suportados:")
    for provider in providers:
        print(f"  • {provider}")
    
    print("\n💡 Para adicionar mais provedores, implementar:")
    print("  - OpenAIProvider (GPT-4, GPT-3.5)")
    print("  - AnthropicProvider (Claude)")
    print("  - OllamaProvider (modelos locais)")


def example_switch_providers():
    """Exemplo de como trocar de provedor facilmente."""
    print("\n\n🔹 EXEMPLO 7: Trocar de provedor facilmente")
    print("=" * 60)
    
    print("Via .env:")
    print("  LLM_PROVIDER=gemini")
    print("  LLM_MODEL=gemini-2.0-flash-exp")
    print("  GEMINI_API_KEY=sua_chave")
    
    print("\nVia código:")
    print("  # Gemini")
    print("  llm = create_llm_client(provider='gemini')")
    print()
    print("  # OpenAI (quando implementado)")
    print("  llm = create_llm_client(provider='openai', model_name='gpt-4')")
    print()
    print("  # Anthropic (quando implementado)")
    print("  llm = create_llm_client(provider='anthropic', model_name='claude-3-opus')")
    
    print("\n✅ Mesmo código de geração funciona com qualquer provedor!")


def main():
    """Executa todos os exemplos."""
    print("🚀 EXEMPLOS DE USO - SISTEMA DE GERAÇÃO")
    print("=" * 60)
    print("Sistema flexível com suporte a múltiplos provedores\n")
    
    # Verificar se tem API key
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  GEMINI_API_KEY não configurada")
        print("Configure no .env para executar os exemplos com chamadas reais\n")
    
    try:
        # Exemplos que não precisam de API key
        example_specific_provider()
        example_custom_config()
        example_list_providers()
        example_switch_providers()
        
        # Exemplos que precisam de API key
        if os.getenv('GEMINI_API_KEY'):
            example_basic_usage()
            example_rag_generation()
            example_chat()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
