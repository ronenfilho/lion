"""Script para visualizar chunks no ChromaDB"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.vector_store import VectorStore
from dotenv import load_dotenv
import os

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
print(f"📊 CHUNKS NO CHROMADB - Coleção: {COLLECTION_NAME}")
print(f"{'='*80}")
print(f"\n🔢 Total de chunks: {len(results['documents'])}\n")

# Mostrar cada chunk
for i, (doc_id, content, metadata) in enumerate(zip(
    results['ids'], 
    results['documents'], 
    results['metadatas']
), 1):
    print(f"\n{'─'*80}")
    print(f"Chunk #{i}")
    print(f"{'─'*80}")
    print(f"🆔 ID: {doc_id}")
    print(f"📝 Seção: {metadata.get('section', 'N/A')}")
    print(f"📄 Arquivo: {metadata.get('filename', 'N/A')}")
    print(f"🔢 Índice: {metadata.get('chunk_index', 'N/A')}")
    print(f"⚙️  Método: {metadata.get('chunk_method', 'N/A')}")
    print(f"📏 Tamanho: {len(content)} caracteres")
    print(f"\n📄 Conteúdo (primeiros 300 caracteres):")
    print(f"{'─'*80}")
    preview = content[:300] + "..." if len(content) > 300 else content
    print(preview)
    
    if i >= 10:
        print(f"\n... (mostrando apenas 10 primeiros chunks de {len(results['documents'])})")
        break

print(f"\n{'='*80}")
print(f"✅ Visualização concluída")
print(f"{'='*80}\n")
