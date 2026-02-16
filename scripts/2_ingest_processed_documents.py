"""
Script de Ingestão de Documentos Processados - LION
Lê arquivos .md da pasta data/processed/ e carrega no ChromaDB
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


def find_processed_documents(processed_dir: Path) -> list[Path]:
    """
    Busca todos os arquivos .md na pasta processed
    
    Args:
        processed_dir: Diretório com documentos processados
        
    Returns:
        Lista de caminhos dos arquivos .md
    """
    if not processed_dir.exists():
        print(f"⚠️  Diretório não encontrado: {processed_dir}")
        return []
    
    md_files = list(processed_dir.glob("*.md"))
    return sorted(md_files)


def load_markdown_content(md_path: Path) -> str:
    """
    Carrega conteúdo de um arquivo Markdown
    
    Args:
        md_path: Caminho do arquivo .md
        
    Returns:
        Conteúdo do arquivo
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    """Pipeline principal de ingestão"""
    
    print("\n" + "="*70)
    print("🦁 LION - Ingestão de Documentos Processados")
    print("="*70)
    
    # Configurações
    PROCESSED_DIR = Path("data/processed")
    COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "irpf_2025")
    PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/embeddings/chroma_db")
    
    # Perguntar ao usuário sobre zerar ou incrementar
    should_reset = get_user_choice()
    
    # Buscar documentos processados
    print(f"\n📁 Buscando documentos em: {PROCESSED_DIR}")
    md_files = find_processed_documents(PROCESSED_DIR)
    
    if not md_files:
        print("❌ Nenhum arquivo .md encontrado na pasta processed/")
        print(f"   Procure em: {PROCESSED_DIR.absolute()}")
        return
    
    print(f"✅ Encontrados {len(md_files)} arquivo(s):")
    for md_file in md_files:
        print(f"   - {md_file.name}")
    
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
    chunker = StructuralChunker(
        max_chunk_size=1000,
        overlap=200,
        min_chunk_size=100
    )
    print("   ✓ Structural Chunker configurado")
    
    embeddings_pipeline = EmbeddingsPipeline(
        batch_size=100,
        rate_limit_delay=0.1
    )
    print("   ✓ Pipeline de embeddings configurado")
    
    # Processar cada documento
    print(f"\n📊 Processando {len(md_files)} documento(s)...")
    print("="*70)
    
    total_chunks = 0
    
    for md_file in md_files:
        print(f"\n📄 Processando: {md_file.name}")
        
        # 1. Carregar conteúdo
        print("   [1/4] Carregando conteúdo...")
        content = load_markdown_content(md_file)
        print(f"         ✓ {len(content)} caracteres")
        
        # 2. Chunking
        print("   [2/4] Criando chunks...")
        chunks = chunker.chunk_markdown(
            content=content,
            source=md_file.stem,
            metadata={
                "filename": md_file.name,
                "processed_from": "markdown",
                "collection": COLLECTION_NAME
            }
        )
        print(f"         ✓ {len(chunks)} chunks criados")
        
        # 3. Gerar embeddings
        print("   [3/4] Gerando embeddings...")
        embeddings = embeddings_pipeline.generate_embeddings(
            chunks=chunks,
            task_type="retrieval_document",
            show_progress=False
        )
        print(f"         ✓ {len(embeddings)} embeddings gerados ({embeddings[0].shape[0]}d)")
        
        # 4. Armazenar no ChromaDB
        print("   [4/4] Armazenando no ChromaDB...")
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        vector_store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print(f"         ✓ {len(chunks)} chunks armazenados")
        
        total_chunks += len(chunks)
    
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
