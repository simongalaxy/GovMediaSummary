from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

import os
from dotenv import load_dotenv
load_dotenv()


class ChromaDBHandler:
    def __init__(self, logger):
        self.logger = logger
        self.model = os.getenv("OLLAMA_EMBEDDINGS_MODEL")
        self.embeddings = OllamaEmbeddings(model=self.model)
        self.vector_store = Chroma(
            collection_name=os.getenv("collection_name"),
            embedding_function=self.embeddings,
            persist_directory=os.getenv("chromadb_path"),
        )
     
    # save splits to chromaDB.   
    def add_splits_to_db(self, documents):
        news_id = documents[0].metadata["news_id"]
        # self.logger.info(f"News id: {news_id}")
        # existing = self.collection.query()
        # )
        
        # # check whether the documents have already exist and delete it if exists.
        # if existing["ids"]:
        #     self.vector_store.delete(ids=existing["ids"])
        #     self.logger.info(f"{ChromaDBHandler.__name__}: Removed {len(existing["ids"])} old chunks for id={id}")
        
        # insert new chunks.
        news_ids = [doc.id for doc in documents]
        self.vector_store.add_documents(documents=documents, ids=news_ids)
        self.logger.info(f"{ChromaDBHandler.__name__}: added {len(news_ids)} new chunks for id={news_id}")
        # self.logger.info(f"{ChromaDBHandler.__name__}: Added {len(existing["ids"])} new chunks for id={id}")
       
        return
    
    # retriever.
    def retrieve_documents_from_chromadb(self):
        return self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 10,
                "fetch_k": 20
            }
        )
    
    def get_unique_ids_from_metadata(self):
        results = self.vector_store.get()
        all_ids = [item["news_id"] for item in results["metadatas"]]
        
        return list(set(all_ids))
    
    
    def get_all_splits_by_id(self, metadata_id: str):
        results = self.vector_store.get(where={"id": metadata_id})
        
        return [
            {
                "chunk_id": chunk_id,
                "content": content,
                "metadata": meta
            }
            for chunk_id, content, meta in zip(results["ids"], results["documents"], results["metadatas"])
        ]