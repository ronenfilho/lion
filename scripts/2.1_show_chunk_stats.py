"""Script para estatísticas dos chunks no ChromaDB"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.vector_store import VectorStore
from dotenv import load_dotenv
import os
from collections import Counter

load_dotenv()

PERSIST_DIR = "./data/embeddings/chroma_db"
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "irpf_2025")

# Inicializar Vector Store
vector_store = VectorStore(
    persist_directory=PERSIST_DIR,
    collection_name=COLLECTION_NAME
)

# Buscar todos os documentos
results = vector_store.collection.get(
    include=["documents", "metadatas"]
)

print(f"\n{'='*80}")
print(f"📊 ESTATÍSTICAS DOS CHUNKS - Coleção: {COLLECTION_NAME}")
print(f"{'='*80}\n")

# Estatísticas gerais
total_chunks = len(results['documents'])
sizes = [len(doc) for doc in results['documents']]
methods = [meta.get('chunk_method', 'unknown') for meta in results['metadatas']]
sections = [meta.get('section', 'unknown') for meta in results['metadatas']]

print(f"📈 TAMANHOS DOS CHUNKS:")
print(f"   • Total de chunks: {total_chunks}")
print(f"   • Tamanho mínimo: {min(sizes)} caracteres")
print(f"   • Tamanho máximo: {max(sizes)} caracteres")
print(f"   • Tamanho médio: {sum(sizes) / len(sizes):.1f} caracteres")
print(f"   • Tamanho total: {sum(sizes):,} caracteres")

print(f"\n🔧 MÉTODOS DE CHUNKING:")
method_counts = Counter(methods)
for method, count in method_counts.most_common():
    percentage = (count / total_chunks) * 100
    print(f"   • {method}: {count} chunks ({percentage:.1f}%)")

print(f"\n📑 SEÇÕES DO DOCUMENTO:")
section_counts = Counter(sections)
for section, count in section_counts.most_common(15):
    print(f"   • {section[:60]}: {count} chunk(s)")

if len(section_counts) > 15:
    print(f"   ... e mais {len(section_counts) - 15} seções")

# Distribuição de tamanhos
print(f"\n📊 DISTRIBUIÇÃO DE TAMANHOS:")
ranges = [
    (0, 200, "Muito pequeno"),
    (200, 500, "Pequeno"),
    (500, 800, "Médio"),
    (800, 1000, "Grande"),
    (1000, float('inf'), "Muito grande")
]

for min_size, max_size, label in ranges:
    count = sum(1 for s in sizes if min_size <= s < max_size)
    if count > 0:
        percentage = (count / total_chunks) * 100
        bar = "█" * int(percentage / 2)
        print(f"   {label:15} [{min_size:4}-{max_size if max_size != float('inf') else '∞':4}]: {bar} {count} ({percentage:.1f}%)")

print(f"\n{'='*80}\n")
