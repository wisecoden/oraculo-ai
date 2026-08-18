from langchain_community.document_loaders import ( 
    PyPDFLoader,
)

def load_pdf(path):
    loader = PyPDFLoader(path)
    doc_list = loader.load()
    document = '\n\n'.join([doc.page_content for doc in doc_list])
    return document


# documento = load_pdf(path)
# print(documento)