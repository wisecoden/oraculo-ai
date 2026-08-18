import tempfile 
import streamlit as st

from langchain_openai.chat_models import ChatOpenAI
from langchain_groq.chat_models import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from app import *


TIPOS_ARQUIVOS_VALIDOS = ["Pdf"]

CONFIG_MODELOS = {
    "OpenAI": {
        "modelos": ["gpt-5.3-codex", "gpt-4o-mini"],
        "chat": ChatOpenAI,
    },
}


if "messages" not in st.session_state:
    st.session_state.messages = []

if "chain" not in st.session_state:
    st.session_state.chain = None

def load_arquivo(tipo_arquivo, arquivo):
    if tipo_arquivo == 'Pdf':
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
            temp.write(arquivo.read())
            name_temp = temp.name
        documento = load_pdf(name_temp)
    return documento

def load_model(provedor, modelo, api_key, tipo_arquivo, arquivo):
    documento = load_arquivo(tipo_arquivo, arquivo)

    system_message = '''Você é um assistente amigável. Você possui acesso às seguintes informações vindas de um documento {}:

    #####
    {}
    #####

    Utilize as informações fornecidas para basear as suas respostas.

    Sempre que houver $ na sua saída, substitua por S.

    '''.format(tipo_arquivo, documento)

    template = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("placeholder", "{chat_history}"),
       ("user", "{input}"),
    ])

    
    chat = CONFIG_MODELOS[provedor]["chat"](model=modelo, api_key=api_key)
    chain = template | chat
    st.session_state["chain"] = chain


def extrair_texto_resposta(resposta):
    content = getattr(resposta, "content", resposta)

    if isinstance(content, list):
        textos = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    textos.append(str(item.get("text", "")))
                elif "text" in item:
                    textos.append(str(item["text"]))
        return "".join(textos)

    if isinstance(content, dict):
        if "text" in content:
            return str(content["text"])
        return ""

    return str(content)


def page_chat():
    st.header("Bem-vindo ao Assistente", divider=True)

    chain = st.session_state.get("chain")

    if chain is None:
        st.error('Carregue um arquivo e inicialize o assistente antes de enviar mensagens.')
        st.stop()

    for mensagem in st.session_state.messages:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    input_user = st.chat_input("Fale com o assistente")

    if input_user:
        st.session_state.messages.append({'role': 'user', 'content': input_user})
        with st.chat_message("user"):
            st.markdown(input_user)

        chat_history = []
        for mensagem in st.session_state.messages[:-1]:
            if mensagem["role"] == "user":
                chat_history.append(HumanMessage(content=mensagem["content"]))
            elif mensagem["role"] == "assistant":
                chat_history.append(AIMessage(content=mensagem["content"]))

        with st.spinner("Pensando..."):
            resposta = chain.invoke({
                "chat_history": chat_history,
                "input": input_user,
            })

        texto_resposta = extrair_texto_resposta(resposta)
        st.session_state.messages.append({'role': 'assistant', 'content': texto_resposta})
        with st.chat_message("assistant"):
            st.markdown(texto_resposta)


def sidebar():
    tabs = st.tabs(["Upload de Arquivos", "Seleção de Modelos"])

    with tabs[0]:
        tipo_arquivo = st.selectbox("Selecione o tipo de arquivo", TIPOS_ARQUIVOS_VALIDOS)
        if tipo_arquivo == "Pdf":
            arquivo = st.file_uploader("Faça o upload do arquivo Pdf", type=["pdf"])

    with tabs[1]:
        provedor = st.selectbox("Selecione o provedor dos modelos", CONFIG_MODELOS.keys())
        modelo = st.selectbox("Selecione o modelo", CONFIG_MODELOS[provedor]["modelos"])
        api_key = st.text_input(
            f"Adicione a api key para o provedor {provedor}",
            value=st.session_state.get(f"api_key_{provedor}"),
        )
        st.session_state[f"api_key_{provedor}"] = api_key

    if st.button("Inicializar Assistente", use_container_width=True):
        load_model(provedor, modelo, api_key, tipo_arquivo, arquivo)
    if st.button("Apagar histórico de mensagens", use_container_width=True):
        st.session_state.messages = []


def main():
    with st.sidebar:
        sidebar()
    page_chat()

if __name__ == "__main__":
    main()