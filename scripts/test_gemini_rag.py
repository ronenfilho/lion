#!/usr/bin/env python3
"""
Script de teste: Verificar se Gemini está recebendo contexto RAG
"""

import json
import os
from pathlib import Path
from src.generation.llm_client import LLMClient, GenerationConfig
from src.generation.prompts import PromptManager
from src.ingestion.vector_store import create_vector_store
from src.retrieval.bm25_retriever import create_bm25_retriever

print("="*80)
print("🧪 TESTE: Gemini Recebendo Contexto RAG")
print("="*80)

# 1. Carregar dataset
print("\n1️⃣  Carregando dataset...")
dataset_path = Path('data/datasets/test/manual_rfb_test.json')
with open(dataset_path) as f:
    dataset = json.load(f)

question = dataset['questions'][0]['question']
ground_truth = dataset['questions'][0]['ground_truth']

print(f"   ❓ Pergunta: {question}")
print(f"   ✅ Resposta esperada: {ground_truth[:100]}...")

# 2. Recuperar chunks
print("\n2️⃣  Recuperando chunks via BM25...")
vs = create_vector_store()
retriever = create_bm25_retriever(vector_store=vs, top_k=3)
results = retriever.retrieve(question)

chunks = [r.content for r in results]
print(f"   ✓ Recuperados {len(chunks)} chunks")
for i, chunk in enumerate(chunks, 1):
    preview = chunk[:80].replace('\n', ' ')
    print(f"     {i}. {preview}...")

# 3. Gerar prompt com RAG
print("\n3️⃣  Gerando prompt com contexto RAG...")
prompt_manager = PromptManager()
prompt = prompt_manager.generate_rag_prompt(
    question=question,
    context_chunks=chunks
)

print(f"   📝 Tamanho do prompt: {len(prompt)} caracteres")
print(f"   📝 Primeiras 500 caracteres:")
print(f"   {prompt[:500]}...")
print(f"\n   📝 Últimas 200 caracteres:")
print(f"   ...{prompt[-200:]}")

# 4. Enviar para Gemini
gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
print(f"\n4️⃣  Enviando para Gemini ({gemini_model})...")
llm = LLMClient(
    model_name=gemini_model,
    config=GenerationConfig(temperature=0.2, max_tokens=2048)
)

try:
    result = llm.generate(prompt)
    response = result.text
    tokens = result.tokens_used
    
    print(f"   ✅ Resposta recebida ({tokens} tokens)")
    print(f"\n   📤 Resposta completa:")
    print(f"   {response}")
    
    # 5. Análise
    print("\n5️⃣  ANÁLISE:")
    print("="*80)
    
    if "Não encontrei" in response or "não encontrei" in response.lower():
        print("   ⚠️  PROBLEMA DETECTADO: Gemini diz 'não encontrou informação'")
        print("   ⚠️  Possíveis causas:")
        print("      1. Contexto não foi incluído no prompt")
        print("      2. Gemini não está processando o contexto")
        print("      3. Chunks recuperados não contêm resposta relevante")
    elif len(response) < 50:
        print("   ⚠️  RESPOSTA MUITO CURTA: Pode indicar erro de parsing")
    else:
        print("   ✅ Resposta recebida com comprimento apropriado")
        
    # Verificar se mencionou contexto
    if "Lei nº 15.270" in response or "15.270" in response:
        print("   ✅ Resposta menciona Lei nº 15.270 (presente nos chunks)")
    else:
        print("   ⚠️  Resposta NÃO menciona Lei nº 15.270")
        
except Exception as e:
    print(f"   ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Teste concluído")
print("="*80)
