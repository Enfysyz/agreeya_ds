import os
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_ollama import OllamaEmbeddings  
from langchain_community.llms import Ollama
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

DOCS_DIR = "./docs"
DB_DIR = "./chroma_db" 

embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://ollama:11434")
llm = Ollama(model="llama3", base_url="http://ollama:11434")

cross_encoder = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")

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
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    for split in splits:
        clean_metadata = {}
        if "source" in split.metadata:
            clean_metadata["source"] = str(split.metadata["source"])
        if "page" in split.metadata:
            clean_metadata["page"] = int(split.metadata["page"])
            
        split.metadata = clean_metadata
    
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=DB_DIR)
    
    bm25_retriever = BM25Retriever.from_documents(splits)
    bm25_retriever.k = 5
    
    print("Indexing complete. Memory updated.")

ingest_documents()

# --- NEW TRANSPARENT FUNCTION ---
def ask_with_transparency(query: str):
    if vectorstore is None or bm25_retriever is None:
        raise ValueError("No documents are currently indexed.")
        
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5]
    )
    
    # 1. Fetch Top 10 Raw Documents (5 BM25 + 5 Vector)
    raw_docs = ensemble_retriever.invoke(query)
    
    # 2. Manually Score all 10 using the Cross-Encoder
    text_pairs = [[query, doc.page_content] for doc in raw_docs]
    scores = cross_encoder.score(text_pairs)
    
    # 3. Attach the scores to the documents and sort them (Highest to Lowest)
    for doc, score in zip(raw_docs, scores):
        doc.metadata["rerank_score"] = float(score)
        
    raw_docs.sort(key=lambda x: x.metadata["rerank_score"], reverse=True)
    
    # 4. Slice the Top 3 to use as the actual context for the LLM
    top_3_docs = raw_docs[:3]
    
    # 5. Generate the Answer
    # prompt = ChatPromptTemplate.from_template("""
    # Answer the following question based only on the provided context. 
    # If the answer is not in the context, say "I don't know based on the provided documents". Avoid mentioning that the information was sourced from the context.
    
    # Context:
    # {context}
    
    # Question: {input}
    # """)

    # 5. Generate the Answer
    prompt = ChatPromptTemplate.from_template("""
        Answer the following question based only on the provided context. 

        Guidelines:
        - If you don't know the answer, simply state that you don't know.
        - If you're unsure, seek clarification.
        - Avoid mentioning that the information was sourced from the context.
        - Respond in accordance with the language of the user's question.

        Context:
        {context}

        Question: {input}
        """)
    
    document_chain = create_stuff_documents_chain(llm, prompt)
    answer = document_chain.invoke({"context": top_3_docs, "input": query})
    
    return {
        "answer": answer,
        "citations": top_3_docs,           # The 3 used by the LLM
        "all_retrieved_docs": raw_docs     # All 10 found by Hybrid Search
    }

def get_indexed_files():
    """Returns a list of all unique files currently inside the Vector Database."""
    if vectorstore is None:
        return []
    
    # .get() pulls data directly from the underlying Chroma collection
    # We only request 'metadatas' to save memory and speed
    collection_data = vectorstore.get(include=['metadatas'])
    metadatas = collection_data.get('metadatas', [])
    
    unique_sources = set()
    for meta in metadatas:
        if meta and "source" in meta:
            unique_sources.add(meta["source"])
            
    return list(unique_sources)