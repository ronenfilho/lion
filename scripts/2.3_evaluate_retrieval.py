"""Script para avaliação do componente de Retrieval (R) no RAG com dataset de teste"""
import sys
from pathlib import Path
import json
from typing import List, Dict, Any
import csv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.vector_store import VectorStore
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.dense_retriever import DenseRetriever
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Configurações
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/embeddings/chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "irpf_2025")
TOP_K = int(os.getenv("TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
TEST_DATASET_PATH = "data/datasets/test/manual_rfb_test.json"
RESULTS_DIR = Path("data/experiments/results")


def load_test_dataset(path: str) -> Dict[str, Any]:
    """Carrega o dataset de teste"""
    if not Path(path).exists():
        print(f"❌ Dataset não encontrado: {path}")
        return None
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_report(results: Dict, timestamp: str):
    """Salva relatório em JSON"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RESULTS_DIR / f"retrieval_evaluation_{timestamp}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return filepath


def save_csv_report(results: Dict, timestamp: str):
    """Salva relatório resumido em CSV"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RESULTS_DIR / f"retrieval_evaluation_{timestamp}.csv"
    
    rows = []
    for retriever_type in ["dense", "hybrid"]:
        for r in results[retriever_type]:
            if "num_results" in r:
                rows.append({
                    "retriever": retriever_type,
                    "query_id": r.get("query_id", ""),
                    "question": r.get("question", "")[:100],
                    "num_results": r.get("num_results", 0),
                    "top_score": r.get("top_score", 0),
                    "ground_truth_found": r.get("ground_truth_found", False),
                    "ground_truth_position": r.get("ground_truth_position", -1),
                    "ground_truth_score": r.get("ground_truth_score", 0),
                    "time_ms": r.get("time_ms", 0)
                })
    
    if rows:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    return filepath


def save_markdown_report(results: Dict, timestamp: str, metrics: Dict):
    """Salva relatório detalhado em Markdown"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RESULTS_DIR / f"retrieval_evaluation_{timestamp}.md"
    
    md = []
    md.append("# Relatório de Avaliação do Retrieval (R)\n")
    md.append(f"**Data**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    md.append(f"**Timestamp**: {timestamp}\n")
    md.append(f"**Dataset**: {TEST_DATASET_PATH}\n")
    md.append(f"**Collection**: {COLLECTION_NAME}\n")
    md.append(f"**Top-K**: {TOP_K}\n")
    
    # Métricas Resumidas
    md.append("\n## 📊 Resumo de Métricas\n")
    
    for retriever_type in ["dense", "hybrid"]:
        if retriever_type in metrics and metrics[retriever_type]:
            m = metrics[retriever_type]
            md.append(f"\n### {retriever_type.capitalize()} Retriever\n")
            md.append(f"- **Taxa de Recall**: {m['recall']:.1f}%\n")
            md.append(f"- **Queries com Ground Truth**: {m['found_count']}/{m['total_count']}\n")
            md.append(f"- **Posição Média (Ground Truth)**: {m['avg_position']:.1f}\n")
            md.append(f"- **Score Médio (top-1)**: {m['avg_score']:.3f}\n")
            md.append(f"- **Tempo Médio**: {m['avg_time']:.1f}ms\n")
    
    # Detalhes por Query
    md.append("\n## 🔍 Detalhes por Query\n")
    
    dense_results = results.get("dense", [])
    for r in dense_results:
        if "num_results" in r:
            md.append(f"\n### [{r['query_id']}] Dense Retriever\n")
            md.append(f"**Query**: {r['question']}\n\n")
            md.append(f"- Resultados: {r['num_results']}\n")
            md.append(f"- Score Máx: {r['top_score']:.3f}\n")
            md.append(f"- Ground Truth Encontrado: {'✅ Sim' if r['ground_truth_found'] else '❌ Não'}\n")
            if r['ground_truth_found']:
                md.append(f"- Posição: #{r['ground_truth_position']} (score: {r['ground_truth_score']:.3f})\n")
            md.append(f"- Tempo: {r['time_ms']:.1f}ms\n")
    
    # Recomendações
    md.append("\n## 💡 Recomendações\n")
    
    dense_recall = metrics.get("dense", {}).get("recall", 0) if metrics.get("dense") else 0
    
    if dense_recall >= 80:
        md.append("✅ **Retrieval está funcionando muito bem!**\n\n")
        md.append(f"- Taxa de acerto de {dense_recall:.0f}%\n")
        md.append("- Pronto para avançar para teste de Generation (G)\n")
    elif dense_recall >= 60:
        md.append("⚠️ **Retrieval funcionando com taxa moderada**\n\n")
        md.append(f"- Taxa de acerto de {dense_recall:.0f}%\n")
        md.append("- Ações recomendadas:\n")
        md.append("  - Aumentar TOP_K\n")
        md.append("  - Ajustar SIMILARITY_THRESHOLD\n")
        md.append("  - Validar qualidade dos embeddings\n")
    else:
        md.append("❌ **Retrieval com baixa taxa de acerto**\n\n")
        md.append(f"- Taxa de acerto de {dense_recall:.0f}%\n")
        md.append("- Ações necessárias:\n")
        md.append("  - Verificar ChromaDB e embeddings\n")
        md.append("  - Reprocessar documentos\n")
        md.append("  - Analisar qualidade do dataset de teste\n")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    
    return filepath


def evaluate_retrieval_with_dataset():
    """Avalia o retrieval usando dataset de teste com questions e ground_truth"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'='*80}")
    print(f"📊 AVALIAÇÃO DO RETRIEVAL (R) - Com Dataset de Teste")
    print(f"{'='*80}\n")
    
    # 1. Carregar dataset
    print("📂 Carregando dataset de teste...")
    dataset = load_test_dataset(TEST_DATASET_PATH)
    if not dataset:
        return
    
    questions = dataset.get("questions", [])
    print(f"   ✓ {len(questions)} questions carregadas\n")
    
    # 2. Inicializar Vector Store
    print("🔄 Inicializando Vector Store...")
    try:
        vector_store = VectorStore(
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME
        )
        num_docs = vector_store.collection.count()
        print(f"   ✓ ChromaDB carregado ({num_docs} documentos)\n")
    except Exception as e:
        print(f"   ❌ Erro ao carregar ChromaDB: {e}")
        return
    
    # 3. Inicializar Retrievers
    print("🔄 Inicializando Retrievers...")
    try:
        dense_retriever = DenseRetriever(vector_store=vector_store)
        hybrid_retriever = HybridRetriever(vector_store=vector_store)
        print(f"   ✓ Dense Retriever OK")
        print(f"   ✓ Hybrid Retriever OK\n")
    except Exception as e:
        print(f"   ⚠️  Erro ao inicializar retrievers: {e}")
        hybrid_retriever = None
    
    # 4. Executar avaliação
    print(f"{'='*80}")
    print(f"🧪 VALIDAÇÃO DO RETRIEVAL ({len(questions)} questions)")
    print(f"{'='*80}\n")
    
    results = {
        "dense": [],
        "hybrid": []
    }
    
    for i, q_data in enumerate(questions, 1):
        query_id = q_data.get("id", f"q{i}")
        question = q_data.get("question", "")
        ground_truth = q_data.get("ground_truth", "")
        category = q_data.get("category", "unknown")
        difficulty = q_data.get("difficulty", "unknown")
        
        print(f"[{query_id}] {category} ({difficulty})")
        print(f"{'─'*80}")
        print(f"❓ {question[:100]}{'...' if len(question) > 100 else ''}\n")
        
        # Dense Retrieval
        print(f"  [Dense Retriever]")
        start = time.time()
        try:
            dense_results = dense_retriever.retrieve(question, k=TOP_K)
            dense_time = time.time() - start
            
            # Calcular métricas
            ground_truth_found = False
            ground_truth_position = -1
            ground_truth_score = 0
            
            for j, result in enumerate(dense_results, 1):
                content = result['content'][:200]
                score = result['score']
                
                # Verificar se contém ground_truth
                if ground_truth.lower()[:100] in content.lower() or \
                   content.lower() in ground_truth.lower():
                    ground_truth_found = True
                    ground_truth_position = j
                    ground_truth_score = score
            
            status = "✅" if ground_truth_found else "❌"
            print(f"    {status} {len(dense_results)} resultados | Score máx: {dense_results[0]['score']:.3f} | Tempo: {dense_time*1000:.1f}ms")
            
            if ground_truth_found:
                print(f"    → Ground truth encontrado em posição #{ground_truth_position} (score: {ground_truth_score:.3f})")
            
            # Mostrar top 3
            for j, result in enumerate(dense_results[:3], 1):
                doc = result['metadata'].get('document', 'N/A')
                section = result['metadata'].get('section', 'N/A')
                score = result['score']
                preview = result['content'][:80].replace('\n', ' ')
                print(f"      {j}. [{score:.3f}] {doc} > {section}")
            
            results["dense"].append({
                "query_id": query_id,
                "question": question,
                "num_results": len(dense_results),
                "top_score": dense_results[0]['score'] if dense_results else 0,
                "ground_truth_found": ground_truth_found,
                "ground_truth_position": ground_truth_position,
                "ground_truth_score": ground_truth_score,
                "time_ms": dense_time * 1000
            })
        except Exception as e:
            print(f"    ❌ Erro: {e}")
            results["dense"].append({
                "query_id": query_id,
                "error": str(e)
            })
        
        # Hybrid Retrieval
        if hybrid_retriever:
            print(f"\n  [Hybrid Retriever]")
            start = time.time()
            try:
                hybrid_results = hybrid_retriever.retrieve(question, k=TOP_K)
                hybrid_time = time.time() - start
                
                # Calcular métricas
                ground_truth_found = False
                ground_truth_position = -1
                ground_truth_score = 0
                
                for j, result in enumerate(hybrid_results, 1):
                    content = result['content'][:200]
                    score = result['score']
                    
                    if ground_truth.lower()[:100] in content.lower() or \
                       content.lower() in ground_truth.lower():
                        ground_truth_found = True
                        ground_truth_position = j
                        ground_truth_score = score
                
                status = "✅" if ground_truth_found else "❌"
                print(f"    {status} {len(hybrid_results)} resultados | Score máx: {hybrid_results[0]['score']:.3f} | Tempo: {hybrid_time*1000:.1f}ms")
                
                if ground_truth_found:
                    print(f"    → Ground truth encontrado em posição #{ground_truth_position} (score: {ground_truth_score:.3f})")
                
                # Mostrar top 3
                for j, result in enumerate(hybrid_results[:3], 1):
                    doc = result['metadata'].get('document', 'N/A')
                    section = result['metadata'].get('section', 'N/A')
                    score = result['score']
                    preview = result['content'][:80].replace('\n', ' ')
                    print(f"      {j}. [{score:.3f}] {doc} > {section}")
                
                results["hybrid"].append({
                    "query_id": query_id,
                    "question": question,
                    "num_results": len(hybrid_results),
                    "top_score": hybrid_results[0]['score'] if hybrid_results else 0,
                    "ground_truth_found": ground_truth_found,
                    "ground_truth_position": ground_truth_position,
                    "ground_truth_score": ground_truth_score,
                    "time_ms": hybrid_time * 1000
                })
            except Exception as e:
                print(f"    ❌ Erro: {e}")
                results["hybrid"].append({
                    "query_id": query_id,
                    "error": str(e)
                })
        
        print()
    
    # 5. Calcular Métricas
    print(f"{'='*80}")
    print(f"📊 RESUMO DE VALIDAÇÃO")
    print(f"{'='*80}\n")
    
    metrics = {}
    
    # Dense Retriever Metrics
    print("🔍 Dense Retriever:")
    dense_valid = [r for r in results["dense"] if "num_results" in r]
    if dense_valid:
        found_count = sum(1 for r in dense_valid if r.get("ground_truth_found"))
        recall = (found_count / len(dense_valid)) * 100
        
        valid_positions = [r["ground_truth_position"] for r in dense_valid if r.get("ground_truth_found")]
        avg_position = sum(valid_positions) / len(valid_positions) if valid_positions else 0
        
        avg_score = sum(r["top_score"] for r in dense_valid) / len(dense_valid)
        avg_time = sum(r["time_ms"] for r in dense_valid) / len(dense_valid)
        
        metrics["dense"] = {
            "recall": recall,
            "found_count": found_count,
            "total_count": len(dense_valid),
            "avg_position": avg_position,
            "avg_score": avg_score,
            "avg_time": avg_time
        }
        
        print(f"  • Taxa de Recall (Ground Truth Found): {recall:.1f}% ({found_count}/{len(dense_valid)})")
        print(f"  • Posição Média (Ground Truth): {avg_position:.1f}")
        print(f"  • Score Médio (top-1): {avg_score:.3f}")
        print(f"  • Tempo Médio por Query: {avg_time:.1f}ms")
    else:
        print(f"  ❌ Nenhum resultado válido")
    
    # Hybrid Retriever Metrics
    if hybrid_retriever:
        print("\n🔀 Hybrid Retriever:")
        hybrid_valid = [r for r in results["hybrid"] if "num_results" in r]
        if hybrid_valid:
            found_count = sum(1 for r in hybrid_valid if r.get("ground_truth_found"))
            recall = (found_count / len(hybrid_valid)) * 100
            
            valid_positions = [r["ground_truth_position"] for r in hybrid_valid if r.get("ground_truth_found")]
            avg_position = sum(valid_positions) / len(valid_positions) if valid_positions else 0
            
            avg_score = sum(r["top_score"] for r in hybrid_valid) / len(hybrid_valid)
            avg_time = sum(r["time_ms"] for r in hybrid_valid) / len(hybrid_valid)
            
            metrics["hybrid"] = {
                "recall": recall,
                "found_count": found_count,
                "total_count": len(hybrid_valid),
                "avg_position": avg_position,
                "avg_score": avg_score,
                "avg_time": avg_time
            }
            
            print(f"  • Taxa de Recall (Ground Truth Found): {recall:.1f}% ({found_count}/{len(hybrid_valid)})")
            print(f"  • Posição Média (Ground Truth): {avg_position:.1f}")
            print(f"  • Score Médio (top-1): {avg_score:.3f}")
            print(f"  • Tempo Médio por Query: {avg_time:.1f}ms")
        else:
            print(f"  ❌ Nenhum resultado válido")
    
    # 6. Recomendações
    print(f"\n{'='*80}")
    print(f"💡 RECOMENDAÇÕES")
    print(f"{'='*80}\n")
    
    dense_recall = metrics.get("dense", {}).get("recall", 0)
    
    if dense_recall >= 80:
        print("  ✅ Retrieval está funcionando muito bem!")
        print(f"     → {dense_recall:.0f}% das queries encontraram o ground truth")
        print("     → Pronto para avançar para teste de Generation (G)")
    elif dense_recall >= 60:
        print("  ⚠️  Retrieval funcionando com taxa moderada")
        print(f"     → {dense_recall:.0f}% das queries encontraram o ground truth")
        print("     → Considere:")
        print("        - Aumentar TOP_K")
        print("        - Ajustar SIMILARITY_THRESHOLD")
        print("        - Validar qualidade dos embeddings")
    else:
        print("  ❌ Retrieval com baixa taxa de acerto")
        print(f"     → Apenas {dense_recall:.0f}% das queries encontraram o ground truth")
        print("     → Ações necessárias:")
        print("        - Verificar ChromaDB e embeddings")
        print("        - Reprocessar documentos")
        print("        - Analisar qualidade do dataset de teste")
    
    # 7. Salvar Relatórios
    print(f"\n{'='*80}")
    print(f"💾 SALVANDO RELATÓRIOS")
    print(f"{'='*80}\n")
    
    json_file = save_json_report(results, timestamp)
    print(f"  ✓ JSON: {json_file}")
    
    csv_file = save_csv_report(results, timestamp)
    print(f"  ✓ CSV: {csv_file}")
    
    md_file = save_markdown_report(results, timestamp, metrics)
    print(f"  ✓ Markdown: {md_file}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    evaluate_retrieval_with_dataset()

