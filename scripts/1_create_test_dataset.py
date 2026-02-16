"""
Script para extrair perguntas e respostas do Manual RFB
e criar dataset de teste estruturado para experimentos RAG

Fonte: Manual_Padrao_RFB_PeR_Tributacao_Cotin_V.19.12.2025.pdf

TODO: Melhorar métricas de metadata no futuro:
    - Adicionar detecção de requisitos temporais (prazos, vigência)
    - Implementar análise de dependências entre leis
    - Extrair porcentagens e alíquotas de forma estruturada
    - Classificar automaticamente a jurisdição (federal, estadual, municipal)
    - Detectar sujeitos passivos e ativos da obrigação tributária
    - Identificar fases processuais mencionadas
    - Mapear conceitos jurídicos específicos (ex: fato gerador, base de cálculo)

Uso:
    python scripts/create_test_dataset.py --pdf data/raw/Manual_Padrao_RFB_PeR_Tributacao_Cotin_V.19.12.2025.pdf
    
    Opcional:
    python scripts/create_test_dataset.py --pdf data/raw/Manual_Padrao_RFB_PeR_Tributacao_Cotin_V.19.12.2025.pdf --output data/processed/test_dataset.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
import re
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.extractors.pdf_extractor import PDFExtractor


def extract_qa_pairs(text: str) -> List[Dict]:
    """
    Extrai pares de perguntas e respostas do texto.
    
    Estratégia melhorada:
    - Filtrar sumário/índice (páginas 2-4) 
    - Começar captura após primeira RESPOSTA real (não sumário)
    - Identificar padrões de perguntas numeradas (ex: "4. A distribuição...")
    - Capturar resposta até próxima pergunta numerada
    - Limpar cabeçalhos/rodapés (URLs, números de página isolados)
    
    Args:
        text: Texto completo do documento
        
    Returns:
        Lista de dicionários com 'question' e 'answer'
    """
    qa_pairs = []
    
    # 1. Pular sumário e começar na primeira RESPOSTA real
    # A questão 1 tem resposta começando com "A Lei nº 15.270, de 2025, decorre..."
    # Vamos procurar a primeira pergunta seguida de resposta (não de "...")
    start_marker = "A Lei nº 15.270, de 2025, decorre"
    start_idx = text.find(start_marker)
    
    if start_idx == -1:
        # Fallback: procurar resposta da questão 4
        start_marker = "Com a edição da Lei nº 15.270"
        start_idx = text.find(start_marker)
    
    if start_idx != -1:
        # Voltar para encontrar a pergunta correspondente (cerca de 500 chars antes)
        search_start = max(0, start_idx - 800)
        text_section = text[search_start:]
        
        # Procurar a pergunta antes desta resposta
        # Padrão: "1. Quais os objetivos da Lei nº 15.270, de 2025?"
        question_match = re.search(r'(\d+)\.\s+([^\n]+\?\s*)\n', text_section)
        if question_match:
            # Usar texto a partir da pergunta encontrada
            text = text_section[question_match.start():]
        else:
            # Se não encontrar, usar a partir da resposta mesmo
            text = text[start_idx:]
    
    # 2. Limpar cabeçalhos/rodapés comuns
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Ignorar linhas vazias
        if not line:
            continue
        
        # Ignorar rodapés (números de página + URL)
        if re.match(r'^\d+\s*$', line):  # Só número de página
            continue
        if 'www.gov.br/receitafederal' in line.lower():
            continue
        
        # Ignorar cabeçalhos de seção repetitivos
        if line == start_marker:
            continue
        if line.startswith('Lucros e dividendos pagos a não residente'):
            continue
        if line.startswith('Lucros e dividendos pagos a pessoa física residente no País'):
            continue
        if line.startswith('Aspectos gerais da Lei'):
            continue
            
        cleaned_lines.append(line)
    
    # 3. Regex para identificar INÍCIO de perguntas numeradas (ex: "5. Qual..." ou "15. A distribuição...")
    question_start_pattern = r'^(\d+)\.\s+(.+)$'
    
    # 4. Processar linhas limpas - juntar linhas para formar perguntas completas
    current_question_num = None
    current_question_parts = []
    current_answer = []
    in_question = False
    
    for i, line in enumerate(cleaned_lines):
        # Detectar INÍCIO de pergunta numerada
        match = re.match(question_start_pattern, line)
        if match:
            # Salvar Q&A anterior
            if current_question_parts and current_answer:
                question_text = ' '.join(current_question_parts).strip()
                answer_text = ' '.join(current_answer).strip()
                # Limpar resposta de fragmentos de URLs/rodapés que escaparam
                answer_text = re.sub(r'\d+\s+www\.gov\.br/receitafederal', '', answer_text)
                # Remover cabeçalhos de seção que escaparam
                answer_text = re.sub(r'Lucros e dividendos pagos a (pessoa física residente no País|não residente no País)$', '', answer_text)
                answer_text = re.sub(r'Aspectos gerais da Lei.*?de 2025$', '', answer_text)
                answer_text = answer_text.strip()
                
                if answer_text and question_text.endswith('?'):  # Só adicionar se pergunta termina com ?
                    qa_pairs.append({
                        'question': question_text,
                        'answer': answer_text
                    })
            
            # Iniciar nova pergunta
            current_question_num = match.group(1)
            current_question_parts = [match.group(2)]
            current_answer = []
            in_question = True
            
            # Se a linha já termina com ?, pergunta está completa
            if line.endswith('?'):
                in_question = False
                
        elif in_question:
            # Continuar acumulando partes da pergunta até encontrar '?'
            current_question_parts.append(line)
            if line.endswith('?'):
                in_question = False
                
        elif current_question_parts:
            # Acumular resposta (ignorar fragmentos muito curtos que podem ser ruído)
            if len(line) > 3:  # Ignorar fragmentos de 1-3 caracteres
                current_answer.append(line)
    
    # Adicionar última Q&A
    if current_question_parts and current_answer:
        question_text = ' '.join(current_question_parts).strip()
        answer_text = ' '.join(current_answer).strip()
        answer_text = re.sub(r'\d+\s+www\.gov\.br/receitafederal', '', answer_text)
        # Remover cabeçalhos de seção que escaparam
        answer_text = re.sub(r'Lucros e dividendos pagos a (pessoa física residente no País|não residente no País)$', '', answer_text)
        answer_text = re.sub(r'Aspectos gerais da Lei.*?de 2025$', '', answer_text)
        answer_text = answer_text.strip()
        
        if answer_text and question_text.endswith('?'):
            qa_pairs.append({
                'question': question_text,
                'answer': answer_text
            })
    
    return qa_pairs


def classify_category(question: str) -> str:
    """
    Classifica pergunta em categoria baseada em palavras-chave.
    
    Args:
        question: Texto da pergunta
        
    Returns:
        Nome da categoria
    """
    keywords = {
        'obrigatoriedade': ['obrigado', 'obrigada', 'obrigatório', 'obrigação', 'deve declarar'],
        'deducoes': ['dedução', 'deduzir', 'abater', 'despesa', 'desconto'],
        'dependentes': ['dependente', 'filho', 'cônjuge', 'companheiro', 'alimentando'],
        'rendimentos': ['rendimento', 'renda', 'salário', 'trabalho', 'aposentadoria'],
        'prazo': ['prazo', 'data', 'quando', 'período', 'entrega'],
        'penalidades': ['multa', 'penalidade', 'sanção', 'infração'],
        'isencao': ['isento', 'isenção', 'dispensado', 'não tributado'],
        'aliquota': ['alíquota', 'percentual', 'taxa', 'imposto'],
        'retificacao': ['retificar', 'corrigir', 'alterar', 'retificadora'],
        'restituicao': ['restituição', 'restituir', 'devolver', 'receber de volta']
    }
    
    question_lower = question.lower()
    for category, words in keywords.items():
        if any(word in question_lower for word in words):
            return category
    
    return 'outros'


def normalize_law_name(law: str) -> str:
    """Normaliza o nome da lei para evitar duplicatas."""
    # Remove vírgulas e normaliza espaços
    law = re.sub(r'\s+', ' ', law.strip())
    # Padrão: "Lei nº 15.270/25" -> "Lei nº 15.270, de 2025"
    # Mas manter o formato original se já estiver completo
    return law


def extract_laws_and_articles(text: str) -> List[Dict]:
    """
    Extrai referências a leis e artigos do texto fornecido de forma estruturada.
    Retorna uma lista de objetos: [{"law": "Lei nº 15.270", "articles": ["16-A", "70"]}, ...]
    """
    law_pattern = r'Lei\s*n[oº]?\s*(?:\.?\s*n\.?\s*)?(\d+[\d\./\s]*)(?:,?\s*de\s*\d{4})?'
    art_pattern = r'\b(?:artigo|art\.?|art|§)\s*(?:n[ºo]?\s*)?(\d+[A-Za-z0-9\-ºª]*)'

    found_laws = {}
    current_law = None

    # Abordagem simplificada: Iterar por palavras/tokens ou apenas encontrar leis e seus contextos
    # Vamos encontrar todas as leis primeiro para definir os "blocos" de contexto
    law_matches = list(re.finditer(law_pattern, text, flags=re.IGNORECASE))
    
    if not law_matches:
        # Se não houver lei explícita, buscar artigos soltos
        arts = sorted(list(set(m.group(1).strip() for m in re.finditer(art_pattern, text, flags=re.IGNORECASE))))
        if arts:
            return [{"law": "Legislação Citada", "articles": arts}]
        return []

    last_pos = 0
    for i, m in enumerate(law_matches):
        law_name = m.group(0).strip().rstrip('.,;')
        law_name = re.sub(r'\s+', ' ', law_name)
        
        # O contexto de uma lei vai até a próxima lei ou fim do texto
        end_pos = law_matches[i+1].start() if i+1 < len(law_matches) else len(text)
        context = text[m.start():end_pos]
        
        arts = sorted(list(set(am.group(1).strip() for am in re.finditer(art_pattern, context, flags=re.IGNORECASE))))
        
        if law_name in found_laws:
            found_laws[law_name].update(arts)
        else:
            found_laws[law_name] = set(arts)

    return [{"law": l, "articles": sorted(list(a))} for l, a in found_laws.items()]


def identify_question_type(question: str) -> str:
    """Identifica o tipo de pergunta."""
    q = question.lower()
    if any(w in q for w in ['como', 'proceder', 'forma', 'prazo', 'quando', 'onde']):
        return 'procedimental'
    if any(w in q for w in ['quais', 'quem', 'qual a lei', 'o que diz']):
        return 'factual'
    if any(w in q for w in ['por que', 'motivo', 'razão', 'explicação']):
        return 'conceitual'
    return 'geral'


def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extrai entidades estruturadas por tipo."""
    entities = {
        'organizations': [],
        'tax_types': [],
        'monetary_values': [],
        'dates': []
    }
    
    # Órgãos e sistemas
    orgs = ['RFB', 'Receita Federal', 'PGFN', 'e-CAC', 'DARF', 'Simples Nacional']
    entities['organizations'] = sorted(list(set(kw for kw in orgs if kw in text)))
    
    # Tipos de imposto
    taxes = ['IRRF', 'IRPF', 'IRPJ', 'COFINS', 'PIS', 'Imposto de Renda']
    entities['tax_types'] = sorted(list(set(kw for kw in taxes if kw in text)))
    
    # Valores monetários
    import re
    values = re.findall(r'R\$\s*[\d.,]+', text)
    entities['monetary_values'] = sorted(list(set(values)))
    
    # Datas e períodos
    dates = re.findall(r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}|\d{4}|ano-calendário\s+de\s+\d{4}', text)
    entities['dates'] = sorted(list(set(dates)))
    
    # Remover chaves vazias
    return {k: v for k, v in entities.items() if v}


def estimate_difficulty(question: str, answer: str) -> str:
    """
    Estima dificuldade da pergunta baseada em heurísticas.
    
    Args:
        question: Texto da pergunta
        answer: Texto da resposta
        
    Returns:
        'facil', 'medio', ou 'dificil'
    """
    # Perguntas curtas e diretas = fácil
    if len(question.split()) < 10 and len(answer.split()) < 50:
        return 'facil'
    
    # Respostas longas ou com múltiplas condições = difícil
    if len(answer.split()) > 150 or answer.count('desde que') > 1 or answer.count('exceto') > 1:
        return 'dificil'
    
    # Palavras técnicas/jurídicas = difícil
    technical_terms = ['cômputo', 'não obstante', 'ressalvado', 'ex vi', 'ipso facto']
    if any(term in answer.lower() for term in technical_terms):
        return 'dificil'
    
    return 'medio'


def extract_source_metadata(text: str) -> Dict:
    """
    Extrai metadados de fonte (artigos, parágrafos) do texto.
    
    Args:
        text: Texto da resposta
        
    Returns:
        Dicionário com metadados
    """
    metadata = {}
    
    # Buscar artigos (ex: "art. 3º", "artigo 12")
    art_match = re.search(r'art(?:igo)?\.?\s*(\d+)[ºª°]?', text, re.IGNORECASE)
    if art_match:
        metadata['article'] = art_match.group(1)
    
    # Buscar parágrafos (ex: "§ 2º")
    para_match = re.search(r'§\s*(\d+)[ºª°]?', text)
    if para_match:
        metadata['paragraph'] = para_match.group(1)
    
    # Buscar incisos (ex: "inciso II")
    inc_match = re.search(r'inciso\s+([IVX]+)', text, re.IGNORECASE)
    if inc_match:
        metadata['clause'] = inc_match.group(1)
    
    return metadata


def enrich_qa_metadata(qa_pairs: List[Dict], source_name: str) -> List[Dict]:
    """
    Enriquece pares Q&A com metadados objetivos e não redundantes.
    """
    enriched = []
    
    for i, qa in enumerate(qa_pairs, 1):
        # 1. Extração separada de base legal (pergunta vs resposta)
        question_legal = extract_laws_and_articles(qa['question'])
        answer_legal = extract_laws_and_articles(qa['answer'])
        
        # 2. Informações de contexto
        full_text = f"{qa['question']} {qa['answer']}"
        entities = extract_entities(full_text)
        
        # 3. Classificar complexidade da pergunta de forma mais precisa
        q_words = len(qa['question'].split())
        q_complexity = 'simple' if q_words <= 12 else 'medium' if q_words <= 25 else 'complex'
        
        # 4. Análise semântica da resposta
        answer_analysis = {
            'has_examples': any(indicator in qa['answer'].lower() for indicator in ['exemplo', 'por exemplo', 'ex:', 'como:', 'no caso']),
            'has_conditions': any(indicator in qa['answer'].lower() for indicator in ['desde que', 'exceto', 'salvo', 'ressalvado', 'caso', 'hipótese']),
            'has_enumerations': any(indicator in qa['answer'] for indicator in ['i.', 'ii.', 'iii.', '1.', '2.', '3.']),
            'has_references': 'art.' in qa['answer'].lower() or 'artigo' in qa['answer'].lower()
        }
        
        metadata = {
            'legal_references': {
                'in_question': question_legal,
                'in_answer': answer_legal
            },
            'entities': entities,
            'question_analysis': {
                'type': identify_question_type(qa['question']),
                'length_chars': len(qa['question']),
                'length_words': q_words,
                'complexity': q_complexity
            },
            'answer_analysis': {
                'length_chars': len(qa['answer']),
                'length_words': len(qa['answer'].split()),
                **answer_analysis
            }
        }

        # 5. Adicionar posição específica se encontrada
        pos = extract_source_metadata(qa['answer'])
        if pos:
            metadata['legal_references']['cited_in_answer'] = pos

        enriched.append({
            'id': f'q{i:03d}',
            'question': qa['question'],
            'ground_truth': qa['answer'],
            'category': classify_category(qa['question']),
            'difficulty': estimate_difficulty(qa['question'], qa['answer']),
            'source': source_name,
            'metadata': metadata
        })
    
    return enriched


def print_statistics(dataset: Dict):
    """Imprime estatísticas do dataset"""
    questions = dataset['questions']
    
    print(f"\n📊 Estatísticas do Dataset")
    print(f"{'='*60}")
    print(f"Total de perguntas: {len(questions)}")
    
    # Distribuição por categoria
    categories = {}
    for q in questions:
        cat = q['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📂 Distribuição por categoria:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        pct = (count / len(questions)) * 100
        print(f"   {cat:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Distribuição por dificuldade
    difficulties = {}
    for q in questions:
        diff = q['difficulty']
        difficulties[diff] = difficulties.get(diff, 0) + 1
    
    print(f"\n📊 Distribuição por dificuldade:")
    for diff in ['facil', 'medio', 'dificil']:
        count = difficulties.get(diff, 0)
        pct = (count / len(questions)) * 100
        print(f"   {diff:10s}: {count:3d} ({pct:5.1f}%)")
    
    # Tamanho médio
    avg_q_len = sum(len(q['question'].split()) for q in questions) / len(questions)
    avg_a_len = sum(len(q['ground_truth'].split()) for q in questions) / len(questions)
    
    print(f"\n📏 Tamanho médio:")
    print(f"   Perguntas: {avg_q_len:.1f} palavras")
    print(f"   Respostas: {avg_a_len:.1f} palavras")


def main():
    parser = argparse.ArgumentParser(
        description='Extrai Q&A do Manual RFB e cria dataset de teste'
    )
    parser.add_argument(
        '--pdf',
        default='data/raw/Manual_Padrao_RFB_PeR_Tributacao_Cotin_V.19.12.2025.pdf',
        help='Caminho do PDF fonte'
    )
    parser.add_argument(
        '--output',
        default='experiments/datasets/manual_rfb_test.json',
        help='Caminho do arquivo JSON de saída'
    )
    parser.add_argument(
        '--min-questions',
        type=int,
        default=20,
        help='Número mínimo de perguntas esperadas'
    )
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf)
    output_path = Path(args.output)
    
    # Verificar se PDF existe
    if not pdf_path.exists():
        print(f"❌ Erro: Arquivo não encontrado: {pdf_path}")
        print(f"\nPor favor, coloque o PDF do Manual RFB em: {pdf_path}")
        sys.exit(1)
    
    # 1. Extrair PDF
    print(f"📄 Extraindo PDF...")
    print(f"   Arquivo: {pdf_path}")
    
    extractor = PDFExtractor()
    doc_data = extractor.extract(str(pdf_path))
    
    print(f"   ✅ Extraído: {len(doc_data['full_text'])} caracteres")
    
    # 2. Extrair Q&A
    print(f"\n🔍 Extraindo pares de perguntas e respostas...")
    qa_pairs = extract_qa_pairs(doc_data['full_text'])
    print(f"   ✅ Encontrados: {len(qa_pairs)} pares Q&A")
    
    if len(qa_pairs) < args.min_questions:
        print(f"\n⚠️  Aviso: Apenas {len(qa_pairs)} perguntas encontradas")
        print(f"   Esperado: pelo menos {args.min_questions}")
        print(f"\n   Possíveis causas:")
        print(f"   - PDF não está no formato de perguntas e respostas")
        print(f"   - Perguntas não terminam com '?'")
        print(f"   - Estrutura do documento diferente do esperado")
    
    # 3. Enriquecer com metadados
    print(f"\n📊 Enriquecendo com metadados...")
    # Usar o nome exato do arquivo processado como 'source'
    enriched_qa = enrich_qa_metadata(qa_pairs, pdf_path.name)
    
    # 4. Criar dataset estruturado
    dataset = {
        'dataset_name': 'manual_rfb_qa_test',
        'version': '1.0',
        'created_at': datetime.now().strftime('%Y-%m-%d'),
        'total_questions': len(enriched_qa),
        'source_document': 'Manual Padrão RFB - Tributação (v.19.12.2025)',
        'source_file': str(pdf_path),
        'description': 'Dataset de teste para experimentos RAG baseado no Manual Padrão RFB de Tributação',
        'questions': enriched_qa
    }
    
    # 5. Salvar JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Dataset criado com sucesso!")
    print(f"   Arquivo: {output_path}")
    
    # 6. Estatísticas
    print_statistics(dataset)
    
    # 7. Mostrar exemplos
    print(f"\n📝 Exemplos de perguntas extraídas:")
    print(f"{'='*60}")
    for i, q in enumerate(enriched_qa[:3], 1):
        print(f"\n{i}. [{q['category']}] [{q['difficulty']}]")
        print(f"   P: {q['question']}")
        print(f"   R: {q['ground_truth'][:100]}...")
    
    print(f"\n{'='*60}")
    print(f"✅ Processo concluído!")
    print(f"\n📋 Próximos passos:")
    print(f"   1. Revisar manualmente o arquivo: {output_path}")
    print(f"   2. Ajustar categorias/dificuldades se necessário")
    print(f"   3. Ingerir Manual RFB no vector store:")
    print(f"      python scripts/ingest_manual_rfb.py")
    print(f"   4. Executar experimentos:")
    print(f"      python scripts/run_experiments.py --dataset {output_path}")


if __name__ == '__main__':
    main()
