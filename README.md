# ◈ Oráculo.AI

> **Assistente inteligente para análise e consulta de documentos PDF com Recuperação Aumentada por Geração (RAG)**

---

##  1. Descrição Geral do Projeto

O **Oráculo.AI** é uma aplicação interativa que permite a análise, exploração e extração de informações de documentos PDF por meio de perguntas em linguagem natural.

Utilizando a técnica de **RAG (Retrieval-Augmented Generation)**, o sistema processa documentos, indexa seu conteúdo e recupera os fragmentos mais relevantes para responder às dúvidas do usuário com precisão, utilizando modelos de linguagem (LLMs) da OpenAI.

[Evidências da Aplicação em Uso](docs/evidence/)

### Principais Funcionalidades

- **Upload e Indexação de PDF**: Carregamento dinâmico de documentos com divisão inteligente em fragmentos de texto (*chunks*).
- **Recuperação Semântica**: Busca vetorial por similaridade utilizando embeddings e índice FAISS em memória.
- **Respostas Baseadas em Evidências**: O modelo responde exclusivamente com base no contexto fornecido no documento, indicando as páginas e trechos de origem consultados.
- **Histórico de Conversa com Janela Deslizante**: Gerenciamento de contexto mantendo as interações mais recentes para evitar estouro de tokens em chats extensos.
- **Interface Intuitiva**: Interface de chat moderna e responsiva construída com Streamlit.

---

##  2. Arquitetura da Solução

A solução foi projetada de forma modular, separando a camada de interface gráfica da lógica de processamento e recuperação de dados:



### Fluxo de Funcionamento

1. **Ingestão e Divisão (*Chunking*)**: O PDF recebido é processado via `PyPDFLoader` e fatiado em blocos menores com sobreposição (*chunk overlap*) pelo `RecursiveCharacterTextSplitter`.
2. **Geração de Embeddings e Armazenamento**: Os blocos de texto são convertidos em vetores densos através do modelo `text-embedding-3-small` e armazenados no banco vetorial **FAISS**.
3. **Consulta e Recuperação**: Ao enviar uma pergunta, o `retriever` localiza os $k$ trechos com maior similaridade semântica em relação à dúvida.
4. **Construção de Contexto e Geração**: Os trechos recuperados, o histórico de turnos anteriores e a nova pergunta são estruturados no prompt do sistema e enviados ao `ChatOpenAI` para geração da resposta com rastreabilidade de páginas.

---

##  3. Tecnologias e Ferramentas Utilizadas


- **Linguagem**: Python 3.10+
- **Framework**: Streamlit
- **Orquestração**: LangChain
- **Modelo de Linguagem**: OpenAI API
- **Banco de Dados Vetorial**: FAISS
- **Leitura de PDF**: pypdf
- **Utilitários**: python-dotenv

---

##  4. Instruções para Execução do Projeto

### Pré-requisitos

- **Python 3.10** ou superior instalado.
- Chave de API da OpenAI

---

### Passo a Passo de Instalação

#### 1. Clonar ou Baixar o Repositório
```bash
git clone https://github.com/seu-usuario/oraculo.git
cd oraculo
```

#### 2. Criar e Ativar um Ambiente Virtual

- **No Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

- **No Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

#### 4. Configurar as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com base no arquivo de exemplo `.env.example`:

- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
- **Linux / macOS:**
  ```bash
  cp .env.example .env
  ```

Edite o arquivo `.env` e insira sua chave de API da OpenAI:

```env
OPENAI_API_KEY=sk-sua-chave-openai-aqui
```


---

### Executando a Aplicação

Inicie o servidor do Streamlit:

```bash
streamlit run streamlit_app.py
```

O navegador abrirá automaticamente no endereço: `http://localhost:8501`.

---

### Como Utilizar

1. **Upload do Documento**: Na barra lateral à esquerda, selecione o arquivo PDF desejado através do botão de upload.
2. **Inicialização**: Clique no botão **◈ Inicializar** para que o documento seja fatiado e os embeddings gerados.
3. **Conversação**: Utilize o campo de mensagem na parte inferior para fazer perguntas ao assistente.
4. **Consulta de Fontes**: Abra o bloco expansível abaixo de cada resposta para conferir os trechos e números de página utilizados como referência.
5. **Limpeza**: Caso queira reiniciar a conversa, utilize o botão **🗑️ Limpar chat** na barra lateral.

# Exemplos de Perguntas e Respostas

## Exemplo 1

### Pergunta

> Em uma situação em que o sistema do Banco Aurora detecta uma transação com comportamento suspeito, quais procedimentos devem ser adotados para prevenir uma possível fraude?

### Resposta

Procedimentos (conforme o documento):

- **Identificar sinais de suspeita**: novo dispositivo, troca de senha, alteração cadastral, mudança de padrão e transação atípica.
- **Aplicar mecanismos de fricção adicionais** quando o risco for elevado (sem transformar todo cliente em suspeito).
- **Elevar o nível de autenticação** e, quando necessário, restringir ou bloquear operações de alto risco.
- **Validar a legitimidade do cliente** por canal confiável; não solicitar senha, token ou código de autenticação durante essa validação.
- **Bloqueio preventivo, investigação, preservação de evidências e comunicação** conforme aplicável.
- **Revogar sessões e credenciais comprometidas** e restaurar fatores de autenticação seguros.
Revisar operações recentes e contas/beneficiários relacionados à transação suspeita.
Registrar evidências e classificar o caso como fraude confirmada, tentativa ou falso positivo.
Manter registros diários de ocorrências de fraude/tentativa e relatório consolidado mensal com as medidas adotadas, conforme obrigações regulatórias quando aplicável.

## Exemplo 2

### Pergunta

> Qual é a diferença entre uma vulnerabilidade de segurança e um incidente de segurança comunicável envolvendo dados pessoais, segundo a politica do Banco Aurora?

### Resposta

Segundo o documento:

- **Vulnerabilidade de segurança**: a existência de uma vulnerabilidade, por si só, não implica que haja um incidente de segurança comunicável.

- **Incidente de segurança comunicável envolvendo dados pessoais**: exige avaliação e presença dos critérios aplicáveis -- em particular, envolvimento confirmado de dados pessoais e possibilidade de risco ou dano relevante. Nesses casos, conforme orientação da ANPD, o controlador deve realizar as comunicações exigidas. 

A Aurora deve manter um procedimento de triagem, avaliação jurídica e decisão documentada para distinguir vulnerabilidades de incidentes comunicáveis e decidir sobre as comunicações.

>Fonte: documento interno-p.2, p.4,p. 11 ‣
---
