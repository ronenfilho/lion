"""
Teste de Validação - Sistema de Geração
Valida estrutura e funcionamento dos componentes sem chamadas reais à API
"""

import sys
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from generation.prompts import create_prompt_manager
from generation.output_parser import create_output_parser


def test_prompt_manager():
    """Testa gerenciador de prompts."""
    print("🧪 TESTE: Prompt Manager")
    print("=" * 60)
    
    manager = create_prompt_manager()
    
    # Listar templates
    templates = manager.list_templates()
    print(f"\n✓ Templates disponíveis: {len(templates)}")
    for t in templates:
        print(f"   • {t['name']}: {t['description']}")
    
    # Testar detecção automática
    test_queries = [
        ("Quais deduções posso fazer?", "deductions"),
        ("Como calcular o imposto?", "calculation"),
        ("Qual o prazo de entrega?", "deadlines"),
        ("Como declarar aluguel?", "income"),
        ("Posso incluir meu filho?", "dependents")
    ]
    
    print(f"\n✓ Teste de detecção automática:")
    correct = 0
    for query, expected in test_queries:
        detected = manager.detect_query_type(query)
        match = "✓" if detected == expected else "✗"
        print(f"   {match} '{query}' → {detected} (esperado: {expected})")
        if detected == expected:
            correct += 1
    
    print(f"\n📊 Acurácia: {correct}/{len(test_queries)} ({100*correct/len(test_queries):.0f}%)")
    
    # Testar formatação
    print(f"\n✓ Teste de formatação de prompt:")
    query = "Quais deduções são permitidas?"
    context = "[Trecho 1]\nArt. 68. São permitidas deduções de despesas médicas."
    
    system, user_prompt = manager.format_prompt('deductions', query, context)
    
    print(f"   • System instruction: {len(system)} chars")
    print(f"   • User prompt: {len(user_prompt)} chars")
    print(f"   • Context incluído: {'✓' if context in user_prompt else '✗'}")
    print(f"   • Query incluída: {'✓' if query in user_prompt else '✗'}")
    
    return True


def test_output_parser():
    """Testa parser de saídas."""
    print("\n\n🧪 TESTE: Output Parser")
    print("=" * 60)
    
    parser = create_output_parser()
    
    # Teste 1: Resposta com citações
    print(f"\n✓ Teste 1: Resposta com citações e valores")
    test_text = """
    De acordo com o Art. 68, § 1º da Lei, são permitidas deduções de despesas 
    com educação até o limite de R$ 3.561,50 por dependente. A alíquota 
    aplicável é de 27,5% para rendimentos acima de R$ 55.976,16 anuais.
    """
    
    parsed = parser.parse(test_text)
    
    print(f"   • Citações: {len(parsed.citations)}")
    for c in parsed.citations:
        print(f"      - {c.article} {c.paragraph or ''}")
    
    print(f"   • Valores monetários: {parsed.extracted_data.monetary_values}")
    print(f"   • Percentuais: {parsed.extracted_data.percentages}")
    print(f"   • Confiança: {parsed.confidence:.2f}")
    print(f"   • Tem resposta: {parsed.has_answer}")
    print(f"   • Warnings: {len(parsed.warnings)}")
    
    # Teste 2: Resposta sem informação
    print(f"\n✓ Teste 2: Resposta indicando falta de informação")
    test_text2 = "Não encontrei essa informação nos documentos consultados."
    
    parsed2 = parser.parse(test_text2)
    print(f"   • Confiança: {parsed2.confidence:.2f}")
    print(f"   • Tem resposta: {parsed2.has_answer}")
    print(f"   • Warnings: {parsed2.warnings}")
    
    # Teste 3: Resposta pedindo esclarecimento
    print(f"\n✓ Teste 3: Resposta pedindo esclarecimento")
    test_text3 = "Poderia esclarecer qual tipo de dedução você está perguntando?"
    
    parsed3 = parser.parse(test_text3)
    print(f"   • Precisa esclarecimento: {parsed3.needs_clarification}")
    print(f"   • Confiança: {parsed3.confidence:.2f}")
    
    # Teste 4: Formatação para display
    print(f"\n✓ Teste 4: Formatação para exibição")
    formatted = parser.format_for_display(parsed)
    print(f"   • Texto formatado: {len(formatted)} chars")
    print(f"   • Inclui seção de referências: {'📚' in formatted}")
    
    return True


def test_integration():
    """Testa integração entre componentes."""
    print("\n\n🧪 TESTE: Integração Prompts + Parser")
    print("=" * 60)
    
    prompt_mgr = create_prompt_manager()
    parser = create_output_parser()
    
    # Simular fluxo completo
    query = "Quais são as deduções permitidas no IRPF?"
    
    # 1. Detectar template
    template_name = prompt_mgr.detect_query_type(query)
    print(f"\n1. Template detectado: {template_name}")
    
    # 2. Formatar prompt
    context = """[Trecho 1]
Art. 68. São permitidas as seguintes deduções:
I - Despesas médicas de até R$ 3.561,50
II - Despesas com educação
§ 1º As deduções estão sujeitas à comprovação documental."""
    
    system, user_prompt = prompt_mgr.format_prompt(template_name, query, context)
    print(f"2. Prompt formatado: {len(user_prompt)} chars")
    
    # 3. Simular resposta do LLM
    simulated_response = """
    De acordo com o Art. 68, são permitidas deduções de:
    
    • Despesas médicas: até R$ 3.561,50
    • Despesas com educação
    
    O § 1º estabelece que as deduções requerem comprovação documental.
    """
    
    # 4. Parse da resposta
    parsed = parser.parse(simulated_response)
    print(f"3. Resposta parseada:")
    print(f"   • Citações: {len(parsed.citations)}")
    print(f"   • Valores: {parsed.extracted_data.monetary_values}")
    print(f"   • Confiança: {parsed.confidence:.2f}")
    
    # 5. Formatar para display
    formatted = parser.format_for_display(parsed)
    print(f"4. Output final:")
    print("-" * 60)
    print(formatted[:300] + "..." if len(formatted) > 300 else formatted)
    
    return True


def run_all_tests():
    """Executa todos os testes de validação."""
    print("🚀 INICIANDO TESTES DE VALIDAÇÃO")
    print("=" * 60)
    print("Sistema de Geração - LION")
    print("Validação estrutural dos componentes\n")
    
    tests = [
        ("Prompt Manager", test_prompt_manager),
        ("Output Parser", test_output_parser),
        ("Integração", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ ERRO em {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Sumário
    print("\n\n" + "=" * 60)
    print("📊 SUMÁRIO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} testes passaram ({100*passed/total:.0f}%)")
    
    if passed == total:
        print("✅ Todos os testes passaram!")
    else:
        print("⚠️ Alguns testes falharam")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
