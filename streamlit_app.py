import tempfile
import streamlit as st
from app import answer, build_rag_chain, build_vector_store, load_and_split_pdf, load_settings


MAX_HISTORY_DISPLAY = 50  

def _init_session():
    defaults = {
        "messages": [],
        "chain": None,
        "retriever": None,
        "doc_name": None,
        "doc_chunks": 0,
        "settings": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session()

def sidebar():
    st.header("⚙️ Configuração")

    if st.session_state.chain is not None:
        st.success(
            f"📄 **{st.session_state.doc_name}**\n\n"
            f"{st.session_state.doc_chunks} chunks · "
            f"{len(st.session_state.messages) // 2} turnos de conversa",
        )
    else:
        st.info("Nenhum documento carregado.", icon="📂")

    st.divider()

    arquivo = st.file_uploader(
        "Upload de PDF",
        type=["pdf"],
        help="Selecione um arquivo PDF para análise.",
    )

    col1, col2 = st.columns(2)

    with col1:
        init_clicked = st.button(
            "◈ Inicializar",
            use_container_width=True,
            type="primary",
            disabled=(arquivo is None),
        )

    with col2:
        clear_clicked = st.button(
            "🗑️ Limpar chat",
            use_container_width=True,
            disabled=(len(st.session_state.messages) == 0),
        )

    if init_clicked:
        _initialize_assistant(arquivo)

    if clear_clicked:
        st.session_state.messages = []
        st.rerun()

    st.divider()
    settings = st.session_state.get("settings")
    if settings:
        st.caption(
            f"🤖 `{settings.model_name}` · embeddings: `{settings.embedding_model}`\n\n"
            f"🔒 Configurado via variáveis de ambiente."
        )
    else:
        st.caption("🔒 Modelo configurado via variáveis de ambiente.")


def _initialize_assistant(arquivo):
    """Load the PDF, build vector store and RAG chain, store in session state."""
    with st.spinner("Carregando configurações..."):
        try:
            settings = load_settings()
        except ValueError as exc:
            st.error(f"**Erro de configuração:** {exc}", icon="🔑")
            st.stop()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(arquivo.read())
        tmp_path = tmp.name

    progress = st.progress(0, text="Lendo documento...")
    try:
        chunks = load_and_split_pdf(tmp_path, settings)
        progress.progress(40, text=f"{len(chunks)} chunks criados. Gerando embeddings...")

        vector_store = build_vector_store(chunks, settings)
        progress.progress(80, text="Construindo chain RAG...")

        chain, retriever = build_rag_chain(vector_store, settings)
        progress.progress(100, text="Pronto!")
    except Exception as exc:
        progress.empty()
        st.error(f"**Erro ao processar documento:** {exc}", icon="❌")
        return

    progress.empty()
    st.session_state.chain = chain
    st.session_state.retriever = retriever
    st.session_state.settings = settings
    st.session_state.messages = []
    st.session_state.doc_name = arquivo.name
    st.session_state.doc_chunks = len(chunks)
    st.rerun()

def _render_sources(sources: list[dict]) -> None:
    """Render a collapsible expander listing the document pages used."""
    if not sources:
        return
    pages = ", ".join(f"p. {s['page']}" for s in sources)
    with st.expander(f"📄 Fonte: documento interno · {pages}", expanded=False):
        for s in sources:
            st.markdown(f"**Página {s['page']}**")
            st.caption(f"_{s['snippet']}…_")
            st.divider()

def page_chat():
    st.title("◈ Oráculo.AI")
    st.caption("Assistente inteligente para análise de documentos")

    chain = st.session_state.get("chain")
    retriever = st.session_state.get("retriever")
    settings = st.session_state.get("settings")

    if chain is None or retriever is None:
        st.markdown("---")
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            st.markdown(
                """
                <div style="text-align:center; padding: 3rem 0;">
                    <div style="font-size:4rem;">📂</div>
                    <h3>Nenhum documento carregado</h3>
                    <p style="color:gray;">
                        Faça o upload de um PDF na barra lateral<br>
                        e clique em <strong>Inicializar</strong> para começar.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    n_pairs = len(st.session_state.messages) // 2
    max_pairs = settings.max_history_pairs
    if n_pairs >= max_pairs:
        st.warning(
            f"As mensagens mais antigas estão sendo descartadas do contexto "
            f"(limite: {max_pairs} turnos). Use **Limpar chat** para reiniciar.",
            icon="⚠️",
        )

    for mensagem in st.session_state.messages:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])
    input_user = st.chat_input(
        f"Pergunte sobre '{st.session_state.doc_name}'..."
        if st.session_state.doc_name
        else "Faça uma pergunta sobre o documento..."
    )

    if input_user:
        st.session_state.messages.append({"role": "user", "content": input_user})
        with st.chat_message("user"):
            st.markdown(input_user)

        history = st.session_state.messages[:-1]

        with st.chat_message("assistant"):
            with st.spinner("Consultando documento..."):
                try:
                    resposta, sources = answer(
                        chain,
                        retriever,
                        input_user,
                        history,
                        max_history_pairs=max_pairs,
                    )
                except Exception as exc:
                    resposta = f"⚠️ Erro ao gerar resposta: {exc}"
                    sources = []
            st.markdown(resposta)
            _render_sources(sources)

        st.session_state.messages.append({"role": "assistant", "content": resposta})


def main():
    st.set_page_config(
        page_title="Oráculo.AI",
        page_icon="◈",
        layout="wide",
    )

    with st.sidebar:
        sidebar()

    page_chat()


if __name__ == "__main__":
    main()