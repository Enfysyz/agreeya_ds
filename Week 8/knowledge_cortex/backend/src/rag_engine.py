import os
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_ollama import OllamaEmbeddings  
from langchain_community.llms import Ollama
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

DOCS_DIR = "./docs"
DB_DIR = "./chroma_db" 

embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://ollama:11434")
llm = Ollama(model="llama3", base_url="http://ollama:11434")

cross_encoder = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
compressor = CrossEncoderReranker(model=cross_encoder, top_n=3)

vectorstore = None
bm25_retriever = None

def ingest_documents():
    global vectorstore, bm25_retriever 
    
    print("Indexing documents...")
    loader = PyPDFDirectoryLoader(DOCS_DIR)
    docs = loader.load()
    
    if not docs:
        print("No documents found in ./docs.")
        return
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    for split in splits:
        clean_metadata = {}
        # Only keep the exact two fields we need for citations, force them to clean types
        if "source" in split.metadata:
            clean_metadata["source"] = str(split.metadata["source"])
        if "page" in split.metadata:
            clean_metadata["page"] = int(split.metadata["page"])
            
        # Overwrite the dirty PDF metadata with our clean dictionary
        split.metadata = clean_metadata
    
    # Update Dense Vector Store (Chroma)
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=DB_DIR)
    
    # Update Sparse Store (BM25)
    bm25_retriever = BM25Retriever.from_documents(splits)
    bm25_retriever.k = 5
    
    print("Indexing complete. Memory updated.")

ingest_documents()

def get_rag_chain():
    if vectorstore is None or bm25_retriever is None:
        raise ValueError("No documents are currently indexed.")
        
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5]
    )
    
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=ensemble_retriever
    )
    
    prompt = ChatPromptTemplate.from_template("""
    Answer the following question based only on the provided context. 
    If the answer is not in the context, say "I don't know based on the provided documents."
    
    Context:
    {context}
    
    Question: {input}
    """)
    
    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(compression_retriever, document_chain)
    
    return retrieval_chain