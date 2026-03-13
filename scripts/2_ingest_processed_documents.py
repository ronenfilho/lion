"""
Script de Ingestão de Documentos Processados - LION
Lê arquivos de chunks JSON de data/processed/chunks/ e carrega no ChromaDB
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.chunking.structural_chunker import StructuralChunker
from src.ingestion.embeddings_pipeline import EmbeddingsPipeline
from src.ingestion.vector_store import VectorStore
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


def get_user_choice() -> bool:
    """
    Pergunta ao usuário se quer zerar o banco ou incrementar
    
    Returns:
        True para zerar, False para incrementar
    """
    print("\n" + "="*70)
    print("🗄️  CONFIGURAÇÃO DO BANCO DE DADOS")
    print("="*70)
    print("\nEscolha uma opção:")
    print("  [1] 🗑️  Zerar e recriar o banco (apaga todos os dados existentes)")
    print("  [2] ➕ Incrementar (adiciona novos documentos)")
    print("="*70)
    
    while True:
        choice = input("\nDigite sua escolha (1 ou 2): ").strip()
        if choice == "1":
            confirm = input("\n⚠️  ATENÇÃO: Todos os dados serão apagados. Confirma? (S/N): ").strip().upper()
            if confirm == "S":
                return True
            print("❌ Operação cancelada.")
            continue
        elif choice == "2":
            return False
        else:
            print("❌ Opção inválida. Digite 1 ou 2.")


def find_chunk_files(chunks_dir: Path) -> list[Path]:
    """
    Busca todos os arquivos JSON de chunks
    
    Args:
        chunks_dir: Diretório com chunks processados
        
    Returns:
        Lista de caminhos dos arquivos JSON
    """
    if not chunks_dir.exists():
        print(f"⚠️  Diretório não encontrado: {chunks_dir}")
        return []
    
    json_files = []
    # Busca em legislation e qa_reference
    for subdir in chunks_dir.iterdir():
        if subdir.is_dir():
            # Exclui arquivos de stats
            json_files.extend([f for f in subdir.glob("*.json") if "_stats" not in f.name])
    
    return sorted(json_files)


def load_chunks_from_json(json_path: Path) -> list[dict]:
    """
    Carrega chunks de um arquivo JSON
    
    Args:
        json_path: Caminho do arquivo JSON
        
    Returns:
        Lista de chunks
    """
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Se é um dicionário com chave 'chunks', extrai a lista
        if isinstance(data, dict) and 'chunks' in data:
            return data['chunks']
        # Caso contrário, assume que é uma lista de chunks
        return data if isinstance(data, list) else [data]


def main():
    """Pipeline principal de ingestão"""
    
    print("\n" + "="*70)
    print("🦁 LION - Ingestão de Documentos Processados")
    print("="*70)
    
    # Configurações
    CHUNKS_DIR = Path("data/processed/json")
    COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "irpf_2025")
    PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/vectorstore/chroma_db")
    
    # Perguntar ao usuário sobre zerar ou incrementar
    should_reset = get_user_choice()
    
    # Buscar chunks processados
    print(f"\n📁 Buscando chunks em: {CHUNKS_DIR}")
    chunk_files = find_chunk_files(CHUNKS_DIR)
    
    if not chunk_files:
        print("❌ Nenhum arquivo de chunks encontrado")
        print(f"   Procure em: {CHUNKS_DIR.absolute()}")
        print(f"\n💡 Dica: Execute primeiro:")
        print(f"   python scripts/2.1_convert_documents.py")
        print(f"   python scripts/2.2_create_chunks.py")
        return
    
    print(f"✅ Encontrados {len(chunk_files)} arquivo(s):")
    for chunk_file in chunk_files:
        print(f"   - {chunk_file.parent.name}/{chunk_file.name}")
    
    # Inicializar Vector Store
    print(f"\n🗄️  Inicializando ChromaDB...")
    vector_store = VectorStore(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME
    )
    
    # Zerar banco se solicitado
    if should_reset:
        print("\n🗑️  Zerando banco de dados...")
        try:
            vector_store.client.delete_collection(name=COLLECTION_NAME)
            print("   ✓ Coleção anterior removida")
            
            # Recriar coleção
            vector_store.collection = vector_store.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            print("   ✓ Nova coleção criada")
        except Exception as e:
            print(f"   ⚠️  Erro ao zerar: {e}")
    
    # Inicializar componentes
    print("\n🔧 Inicializando componentes...")
    
    embeddings_pipeline = EmbeddingsPipeline(
        batch_size=100,
        rate_limit_delay=0.1
    )
    print("   ✓ Pipeline de embeddings configurado")
    
    # Processar cada arquivo de chunks
    print(f"\n📊 Processando {len(chunk_files)} arquivo(s) de chunks...")
    print("="*70)
    
    total_chunks = 0
    
    for chunk_file in chunk_files:
        print(f"\n📄 Processando: {chunk_file.parent.name}/{chunk_file.name}")
        
        # 1. Carregar chunks do JSON
        print("   [1/3] Carregando chunks...")
        chunks_data = load_chunks_from_json(chunk_file)
        print(f"         ✓ {len(chunks_data)} chunks carregados")
        
        # 2. Gerar embeddings
        print("   [2/3] Gerando embeddings...")
        # Extrair conteúdo dos chunks
        chunk_contents = [chunk['content'] for chunk in chunks_data]
        
        # Criar objetos Chunk temporários para o pipeline
        from dataclasses import dataclass
        @dataclass
        class TempChunk:
            chunk_id: str
            content: str
            metadata: dict
        
        temp_chunks = [
            TempChunk(
                chunk_id=chunk['chunk_id'],
                content=chunk['content'],
                metadata=chunk.get('metadata', {})
            )
            for chunk in chunks_data
        ]
        
        embeddings = embeddings_pipeline.generate_embeddings(
            chunks=temp_chunks,
            task_type="retrieval_document",
            show_progress=False
        )
        print(f"         ✓ {len(embeddings)} embeddings gerados ({embeddings[0].shape[0]}d)")
        
        # 3. Armazenar no ChromaDB
        print("   [3/3] Armazenando no ChromaDB...")
        ids = [chunk['chunk_id'] for chunk in chunks_data]
        
        # Combinar hierarchy_string com content
        documents = [
            f"{chunk.get('hierarchy_string', '')}\n\n{chunk['content']}" if chunk.get('hierarchy_string') 
            else chunk['content']
            for chunk in chunks_data
        ]
        
        # Usar metadados do chunk JSON
        metadatas = []
        for chunk in chunks_data:
            meta = {
                **chunk.get('metadata', {}),
                'chunk_id': chunk['chunk_id'],
                'source_file': chunk.get('source_file', chunk_file.stem),
                'article_number': chunk.get('article_number', ''),
                'section': chunk.get('section', ''),
                'hierarchy_string': chunk.get('hierarchy_string', ''),
                'document': chunk_file.stem
            }
            # Converter qualquer valor de lista para string (ChromaDB não suporta listas)
            for key, value in meta.items():
                if isinstance(value, list):
                    meta[key] = ', '.join(str(v) for v in value)
                elif not isinstance(value, (str, int, float, bool)):
                    meta[key] = str(value)
            metadatas.append(meta)
        
        vector_store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print(f"         ✓ {len(chunks_data)} chunks armazenados")
        
        total_chunks += len(chunks_data)
    
    # Resumo final
    print("\n" + "="*70)
    print("✅ INGESTÃO CONCLUÍDA")
    print("="*70)
    print(f"📊 Total de chunks processados: {total_chunks}")
    print(f"🗄️  Coleção: {COLLECTION_NAME}")
    print(f"📁 Persistido em: {PERSIST_DIR}")
    print(f"🔍 Total de documentos no banco: {vector_store.collection.count()}")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
