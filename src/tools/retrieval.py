import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from src.config import DATA_DIR, CHROMA_DB_DIR, OPENAI_API_KEY
from src.llm_factory import get_embeddings

class PolicyRetriever:
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        # Initialize immediately if env vars are present
        self.reinitialize()

    def reinitialize(self):
        """Re-initializes the vector store with current environment variables."""
        self.embeddings = get_embeddings()
        if not self.embeddings:
            print("Warning: API Key not found. RAG will not work.")
            self.vector_store = None
            return

        if os.path.exists(CHROMA_DB_DIR) and os.listdir(CHROMA_DB_DIR):
            self.vector_store = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=self.embeddings)
        else:
            self._index_documents()

    def _index_documents(self):
        print("Indexing policy documents...")
        if not os.path.exists(DATA_DIR):
            print(f"Data directory {DATA_DIR} does not exist. Skipping index.")
            return

        loader = DirectoryLoader(DATA_DIR, glob="**/*.md", loader_cls=TextLoader)
        docs = loader.load()
        
        if not docs:
            print("No documents found to index.")
            return

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(docs)
        
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=CHROMA_DB_DIR
        )
        print("Indexing complete.")

    def search(self, query: str, k: int = 5):
        if not self.vector_store:
            # Try to re-init just in case
            self.reinitialize()
            if not self.vector_store:
                return [{"content": "Retrieval unavailable (No API Key or Index)", "source": "N/A"}]
        
        results = self.vector_store.similarity_search(query, k=k)
        return [{"content": doc.page_content, "source": doc.metadata.get("source", "Unknown")} for doc in results]

# Singleton instance
policy_retriever = PolicyRetriever()

def retrieve_policy(query: str) -> list:
    """Tool function to retrieve policy evidence."""
    return policy_retriever.search(query)
