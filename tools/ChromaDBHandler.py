import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

from tools.DataProcessor import date_to_unix

from typing import List
from pprint import pformat
from datetime import datetime, date, time
import os
from dotenv import load_dotenv
load_dotenv()


class ChromaDBHandler:
    def __init__(self, logger):
        self.logger = logger
        
        # embedding config.
        self.embedding_model = os.getenv("ollama_embedding_model")
        self.embedding_function = OllamaEmbeddingFunction(
            url="http://localhost:11434",
            model_name=self.embedding_model
        )
        
        # chromaDB config.
        self.collection_name = os.getenv("collection_name")
        self.db_path = os.getenv("chromadb_path")
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Collection to store government press releases."}
        )
        self.logger.info(f"{ChromaDBHandler.__name__} initiated.")
    
    
    # save splits to chromaDB.   
    def add_documents_to_chromadb(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        self.logger.info(f"{ChromaDBHandler.__name__}: added {len(documents)} new chunks for id={metadatas[0]["news_id"]}")

        return
    

    # query retriever.
    def check_records_by_dates(self, start_date: str, end_date: str):
        return self.collection.get(
            include=["documents"],
            where={
                "$and": [
                    {"pub_date": {"$gte": date_to_unix(start_date)} },
                    {"pub_date": {"$lte": date_to_unix(end_date)} }
                ]
            }
        )
    
    
    def check_records_by_keyword(self, keyword: str):
        return self.collection.query(
            query_texts=[keyword],
            include=["documents"],
            where={ "summary": {"$contains": keyword} }
        )
    
      
    def check_records_by_keyword_and_dates(self, keyword: str, start_date: str, end_date: str):
        return self.collection.query(
            query_texts=[keyword],
            include=["documents"],
            where={
                "$and": [
                    {"pub_date": {"$gte": date_to_unix(start_date)} },
                    {"pub_date": {"$lte": date_to_unix(end_date)} },
                    {"summary": {"$contains": keyword} }
                ]
            }
        )
