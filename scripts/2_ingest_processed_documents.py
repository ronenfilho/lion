"""
Script de Ingestão de Documentos Processados - LION
Lê arquivos de chunks JSON de data/processed/chunks/ e carrega no ChromaDB

Uso:
    # Processar todos os arquivos
    python scripts/2_ingest_processed_documents.py
    
    # Processar um arquivo específico
    python scripts/2_ingest_processed_documents.py --file data/processed/json/legislation/pl-1087-25_processed.json
"""

import sys
import os
import argparse
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


def choose_json_file(json_files: list[Path]) -> Path | None:
    """
    Apresenta lista de arquivos JSON e permite ao usuário escolher um
    
    Args:
        json_files: Lista de arquivos JSON encontrados
        
    Returns:
        Caminho do arquivo escolhido ou None se cancelar
    """
    print("\n" + "="*70)
    print("📂 ARQUIVOS JSON DISPONÍVEIS")
    print("="*70)
    
    for i, json_file in enumerate(json_files, 1):
        # Calcular tamanho do arquivo
        size_kb = json_file.stat().st_size / 1024
        # Tentar retornar caminho relativo, caso contrário usar absoluto
        try:
            rel_path = json_file.relative_to(Path.cwd())
        except ValueError:
            rel_path = json_file
        print(f"  [{i}] {rel_path} ({size_kb:.1f} KB)")
    
    print(f"  [0] ➕ Processar TODOS os {len(json_files)} arquivo(s)")
    print("  [C] ❌ Cancelar")
    print("="*70)
    
    while True:
        choice = input("\nDigite o número do arquivo ou opção (0/C): ").strip().upper()
        
        if choice == "C":
            print("❌ Operação cancelada.")
            return None
        elif choice == "0":
            return "ALL"  # Código especial para todos
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(json_files):
                    return json_files[idx]
                else:
                    print(f"❌ Opção inválida. Digite um número entre 1 e {len(json_files)}, 0 ou C.")
            except ValueError:
                print(f"❌ Opção inválida. Digite um número entre 1 e {len(json_files)}, 0 ou C.")


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
            json_files.extend(subdir.glob("*.json"))
    
    return sorted(json_files)


def load_chunks_from_json(json_path: Path) -> list[dict]:
    """
    Carrega chunks de um arquivo JSON
    
    Suporta dois formatos:
    1. {"chunks": [...]} - usado por scripts 1.2 e 1.2c
    2. [...] - lista direta de chunks
    
    Args:
        json_path: Caminho do arquivo JSON
        
    Returns:
        Lista de chunks
    """
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Se for um dicionário com chave 'chunks', extrair a lista
    if isinstance(data, dict) and 'chunks' in data:
        return data['chunks']
    # Se for uma lista, retornar direto
    elif isinstance(data, list):
        return data
    # Caso contrário, retornar lista vazia
    else:
        return []


def main():
    """Pipeline principal de ingestão"""
    
    # Parser de argumentos
    parser = argparse.ArgumentParser(
        description="Ingestão de documentos processados no ChromaDB"
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Processar um arquivo JSON específico (ex: data/processed/json/legislation/pl-1087-25_processed.json)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🦁 LION - Ingestão de Documentos Processados")
    print("="*70)
    
    # Configurações
    CHUNKS_DIR = Path("data/processed/json")
    COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "irpf_2025")
    PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/embeddings/chroma_db")
    
    # Determinar quais arquivos processar
    if args.file:
        # Processar arquivo específico
        json_file = Path(args.file)
        if not json_file.exists():
            print(f"❌ Arquivo não encontrado: {json_file}")
            return
        chunk_files = [json_file]
        print(f"📄 Arquivo específico selecionado: {json_file}")
    else:
        # Buscar chunks processados
        print(f"\n📁 Buscando chunks em: {CHUNKS_DIR}")
        all_chunk_files = find_chunk_files(CHUNKS_DIR)
        
        if not all_chunk_files:
            print("❌ Nenhum arquivo de chunks encontrado")
            print(f"   Procure em: {CHUNKS_DIR.absolute()}")
            print(f"\n💡 Dica: Execute primeiro:")
            print(f"   python scripts/1.1_convert_documents.py")
            print(f"   python scripts/1.2_create_article_chunks.py")
            return
        
        # Permitir ao usuário escolher um arquivo ou processar todos
        selected = choose_json_file(all_chunk_files)
        
        if selected is None:
            return
        elif selected == "ALL":
            chunk_files = all_chunk_files
            print(f"\n✅ {len(chunk_files)} arquivo(s) serão processados")
            # Perguntar se quer zerar o banco
            should_reset = get_user_choice()
        else:
            chunk_files = [selected]
            try:
                display_path = selected.relative_to(Path.cwd())
            except ValueError:
                display_path = selected
            print(f"✅ Arquivo selecionado: {display_path}")
            should_reset = False  # Não zerar quando processa arquivo único
    
    # Inicializar Vector Store
    print(f"\n🗄️  Inicializando ChromaDB...")
    vector_store = VectorStore(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME
    )
    
    # Zerar banco se solicitado (somente em modo múltiplo)
    try:
        if 'should_reset' in locals() and should_reset:
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
    except Exception:
        pass
    
    # Exibir status atual
    try:
        current_docs = vector_store.collection.count()
        print(f"   ✓ Coleção '{COLLECTION_NAME}' carregada ({current_docs} documentos)")
    except:
        print(f"   ✓ Coleção '{COLLECTION_NAME}' carregada")
    
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
        
        def serialize_metadata(meta: dict) -> dict:
            """Serializar valores complexos em metadata para tipos primitivos"""
            result = {}
            for key, value in meta.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    result[key] = value
                elif isinstance(value, (list, dict)):
                    result[key] = str(value)  # Converter listas/dicts em strings
                else:
                    result[key] = str(value)
            return result
        
        ids = [chunk['chunk_id'] for chunk in chunks_data]
        documents = [chunk['content'] for chunk in chunks_data]
        metadatas = [
            serialize_metadata({
                **chunk.get('metadata', {}),
                'document_type': chunk.get('document_type', ''),
                'project_number': chunk.get('project_number', ''),
                'law_number': chunk.get('law_number', ''),
                'law_date': chunk.get('law_date', ''),
                'article_number': chunk.get('article_number', ''),
                'section': chunk.get('section', ''),
                'hierarchy_string': chunk.get('hierarchy_string', ''),
                'source_file': chunk_file.stem
            })
            for chunk in chunks_data
        ]
        
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
