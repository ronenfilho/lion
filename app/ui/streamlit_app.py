"""LION Q&A Streamlit UI - Interactive RAG system interface."""

import streamlit as st
import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import pandas as pd

# Page config
st.set_page_config(
    page_title="LION Q&A System",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 500;
    }
    .chunk-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .citation-badge {
        display: inline-block;
        background-color: #fff0b3;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.85rem;
        margin: 0 0.2rem;
    }
</style>
""", unsafe_allow_html=True)


class LIONUIClient:
    """Client for LION Q&A API with Streamlit integration."""

    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/")
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]

    def check_health(self) -> bool:
        """Check if API is available."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def ask(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Send question to API and get response."""
        try:
            payload = {"question": question}
            if context:
                payload["context"] = context

            response = requests.post(
                f"{self.api_url}/ask",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "error": f"Conexão recusada: API não está acessível em {self.api_url}",
                "answer": None,
            }
        except requests.exceptions.Timeout:
            return {
                "error": "Timeout: API levou muito tempo para responder",
                "answer": None,
            }
        except requests.exceptions.HTTPError as e:
            return {
                "error": f"Erro HTTP {e.response.status_code}: {e.response.text}",
                "answer": None,
            }
        except Exception as e:
            return {
                "error": f"Erro inesperado: {str(e)}",
                "answer": None,
            }


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "client" not in st.session_state:
        api_url = st.session_state.get("api_url", "http://127.0.0.1:8001")
        st.session_state.client = LIONUIClient(api_url)

    if "history" not in st.session_state:
        st.session_state.history = []

    if "api_status" not in st.session_state:
        st.session_state.api_status = None


def display_response(response: Dict[str, Any], show_chunks: bool = True):
    """Display formatted response."""
    if "error" in response:
        st.error(f"❌ {response['error']}")
        return

    if not response.get("answer"):
        st.warning("⚠️ Nenhuma resposta foi gerada")
        return

    # Display answer
    with st.container():
        st.subheader("📝 Resposta")
        st.write(response.get("answer", ""))

    # Display metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        confidence = response.get("confidence", 0.0)
        color = "🟢" if confidence > 0.5 else "🟡" if confidence > 0.3 else "🔴"
        st.metric("Confiança", f"{confidence:.4f}", delta=f"{color}")

    with col2:
        st.metric("Fonte", response.get("source", "unknown")[:30])

    with col3:
        citations = response.get("citations", [])
        st.metric("Citações", len(citations))

    # Display citations
    citations = response.get("citations", [])
    if citations:
        st.subheader("🏷️ Citações")
        citation_cols = st.columns(min(len(citations), 5))
        for idx, citation in enumerate(citations):
            with citation_cols[idx % len(citation_cols)]:
                chunk_id = citation.get("chunk_id", "unknown")
                score = citation.get("score", 0.0)
                st.code(f"{chunk_id}\n({score:.4f})", language="text")

    # Display chunks if requested
    if show_chunks and citations:
        st.subheader("📚 Trechos Recuperados")
        
        # Create expandable sections for each chunk
        for idx, citation in enumerate(citations, 1):
            chunk_id = citation.get("chunk_id", "unknown")
            content = citation.get("content", "")
            score = citation.get("score", 0.0)

            with st.expander(f"[{idx}] {chunk_id} ({score:.4f})", expanded=(idx == 1)):
                st.write(content)


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Sidebar configuration
    st.sidebar.title("🦁 LION Q&A System")
    st.sidebar.markdown("---")

    # API Configuration
    with st.sidebar.expander("⚙️ Configuração da API", expanded=False):
        api_url = st.text_input(
            "URL da API",
            value="http://127.0.0.1:8001",
            help="Endereço da API LION Q&A",
        )
        if api_url != st.session_state.get("api_url"):
            st.session_state.api_url = api_url
            st.session_state.client = LIONUIClient(api_url)

        # Check API status
        if st.button("🔍 Verificar Status", key="check_status"):
            with st.spinner("Verificando..."):
                is_healthy = st.session_state.client.check_health()
                st.session_state.api_status = is_healthy
                if is_healthy:
                    st.success("✅ API conectada e funcionando!")
                else:
                    st.error("❌ API não está acessível")

        if st.session_state.api_status is not None:
            status_emoji = "✅" if st.session_state.api_status else "❌"
            st.info(f"Status: {status_emoji}")

    # System settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Configurações do Sistema")

    show_chunks = st.sidebar.checkbox(
        "Mostrar trechos recuperados",
        value=True,
        help="Exibe os documentos/chunks que foram utilizados na resposta",
    )

    show_advanced = st.sidebar.checkbox(
        "Modo avançado",
        value=False,
        help="Ativa opções avançadas de configuração",
    )

    context_enabled = st.sidebar.checkbox(
        "Usar contexto adicional",
        value=False,
        help="Permite fornecer contexto adicional para as perguntas",
    )

    # Advanced settings
    if show_advanced:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 Opções Avançadas")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            temperature = st.slider(
                "Temperatura (criatividade)",
                min_value=0.0,
                max_value=2.0,
                value=0.2,
                step=0.1,
                help="Valores menores = mais determinístico, maiores = mais criativo",
            )

        with col2:
            max_tokens = st.number_input(
                "Máx de tokens",
                min_value=100,
                max_value=2000,
                value=800,
                step=100,
                help="Comprimento máximo da resposta",
            )

        st.sidebar.info(
            f"⚠️ Nota: Estas configurações são apenas informativos. "
            f"Os parâmetros reais são definidos no .env da API."
        )

    # Main content
    st.title("🦁 LION - Sistema de Perguntas e Respostas")
    st.markdown(
        "Sistema baseado em RAG (Retrieval-Augmented Generation) com suporte a citações e transparência"
    )

    # Tabs
    tab1, tab2, tab3 = st.tabs(["💬 Q&A", "📊 Histórico", "ℹ️ Sobre"])

    with tab1:
        # Question input
        st.subheader("Faça uma pergunta")

        question = st.text_area(
            "Pergunta",
            placeholder="Digite sua pergunta aqui...",
            height=100,
            label_visibility="collapsed",
        )

        # Context input (if enabled)
        context = None
        if context_enabled:
            context = st.text_area(
                "Contexto adicional (opcional)",
                placeholder="Forneça contexto adicional se necessário...",
                height=80,
                label_visibility="collapsed",
            )

        # Submit button
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            submit_button = st.button(
                "🔍 Buscar Resposta",
                type="primary",
                use_container_width=True,
            )

        with col2:
            clear_button = st.button("🗑️ Limpar", use_container_width=True)

        with col3:
            save_button = st.button("💾 Salvar", use_container_width=True)

        if clear_button:
            st.rerun()

        # Process question
        if submit_button and question.strip():
            with st.spinner("🤔 Pensando..."):
                response = st.session_state.client.ask(question, context)

                # Store in history
                history_item = {
                    "timestamp": datetime.now().isoformat(),
                    "question": question,
                    "response": response,
                    "context": context,
                }
                st.session_state.history.append(history_item)

                # Display response
                display_response(response, show_chunks=show_chunks)

                # Save button functionality
                if save_button:
                    save_to_json(history_item)
                    st.success("✅ Resposta salva com sucesso!")

        elif submit_button:
            st.warning("⚠️ Por favor, digite uma pergunta")

    with tab2:
        st.subheader("📊 Histórico de Perguntas")

        if not st.session_state.history:
            st.info("Nenhuma pergunta ainda. Vá para a aba 'Q&A' e faça uma pergunta!")
        else:
            # Display history as table
            history_data = []
            for item in st.session_state.history:
                response = item.get("response", {})
                history_data.append(
                    {
                        "Timestamp": item["timestamp"][:19],
                        "Pergunta": item["question"][:50],
                        "Confiança": f"{response.get('confidence', 0):.4f}",
                        "Citações": len(response.get("citations", [])),
                    }
                )

            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Show details of selected item
            st.markdown("---")
            selected_idx = st.selectbox(
                "Selecione um item para ver detalhes",
                range(len(st.session_state.history)),
                format_func=lambda i: f"[{i}] {st.session_state.history[i]['question'][:40]}",
            )

            if selected_idx is not None:
                item = st.session_state.history[selected_idx]
                st.subheader("Detalhes da Pergunta")
                st.write(f"**Pergunta:** {item['question']}")
                if item.get("context"):
                    st.write(f"**Contexto:** {item['context']}")

                st.subheader("Detalhes da Resposta")
                display_response(item["response"], show_chunks=show_chunks)

            # Export history
            if st.button("📥 Exportar Histórico como JSON"):
                export_history()

    with tab3:
        st.subheader("ℹ️ Sobre o Sistema LION")

        st.markdown("""
        ### O que é LION?

        **LION** é um sistema inteligente de Pergunta e Resposta baseado em **RAG** 
        (Retrieval-Augmented Generation) que combina:

        - 🔍 **Retrieval (Busca)**: HybridRetriever combinando embeddings densos + BM25
        - 🤖 **LLM (Geração)**: Groq com llama-3.1-8b-instant
        - 📚 **Fonte de Conhecimento**: Legislação fiscal brasileira (IRPF, etc.)

        ### Funcionalidades

        ✅ **Citações**: Cada resposta inclui referências exatas aos documentos utilizados
        ✅ **Transparência**: Visualize os trechos que fundamentaram a resposta
        ✅ **Histórico**: Acompanhe todas as suas perguntas e respostas
        ✅ **Configurável**: Ajuste parâmetros como temperatura e comprimento máximo
        ✅ **Multi-Modal**: Use via CLI, API REST ou esta interface Streamlit

        ### Componentes Técnicos

        | Componente | Tecnologia |
        |-----------|-----------|
        | **LLM Provider** | Groq (llama-3.1-8b-instant) |
        | **Retrieval** | HybridRetriever (Dense + BM25) |
        | **Embeddings** | Gemini Embeddings |
        | **Vector Store** | ChromaDB |
        | **API Framework** | FastAPI |
        | **CLI** | Python Click |
        | **UI** | Streamlit |

        ### Como Usar

        1. **Configure a API**: Use a seção "⚙️ Configuração da API" na sidebar
        2. **Faça uma pergunta**: Digite na seção "💬 Q&A"
        3. **Veja as citações**: Referências aos documentos aparecem automaticamente
        4. **Explore os trechos**: Expanda "Trechos Recuperados" para ver o contexto completo
        5. **Salve respostas**: Clique "💾 Salvar" para guardar uma resposta

        ### Sobre Citações

        Cada citação segue o formato: `[documento_secao_art_numero]`

        Exemplo: `[L9250compilado_processed_preambulo_art_10]`

        - `L9250compilado`: Lei 9.250 compilada
        - `processed`: Documento processado
        - `preambulo`: Seção do documento
        - `art_10`: Artigo 10

        ### Performance

        - ⚡ Primeira consulta: ~2-3s (inicializa retriever)
        - ⚡ Consultas subsequentes: ~0.5-1s
        - 📊 Confiança: Baseada na média dos scores de relevância dos chunks

        """)

        st.markdown("---")
        st.info(
            "💡 **Dica**: Use o modo avançado para explorar diferentes parâmetros e entender "
            "como afetam as respostas!"
        )


def save_to_json(item: Dict[str, Any]):
    """Save a single response item to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ui_folder = Path(__file__).parent
    filename = ui_folder / f"response_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2, ensure_ascii=False)

    return filename


def export_history():
    """Export entire history as JSON."""
    if not st.session_state.history:
        st.warning("Nenhum histórico para exportar")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ui_folder = Path(__file__).parent
    filename = ui_folder / f"history_export_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(st.session_state.history, f, indent=2, ensure_ascii=False)

    # Provide download
    with open(filename, "r", encoding="utf-8") as f:
        st.download_button(
            label="📥 Baixar Histórico JSON",
            data=f.read(),
            file_name=filename.name,
            mime="application/json",
        )


if __name__ == "__main__":
    main()
