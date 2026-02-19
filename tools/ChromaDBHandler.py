import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pprint import pformat
from datetime import datetime
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
        
        # text_splitter config.
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n"],
            chunk_size=2000,
            chunk_overlap=0
        )
        
        self.logger.info(f"{ChromaDBHandler.__name__} initiated.")
    
    
    # split text.
    def _split_text_from_news(self, content: str):
        all_splits = self.text_splitter.split_text(text=content)
        self.logger.info(f"{ChromaDBHandler.__name__}: Split content into {len(all_splits)} sub-texts.")
        
        for i, split in enumerate(all_splits):
            self.logger.info(f"Split No. {i}: \n{split}")
        self.logger.info("-"*50)
        
        return all_splits
    
   
    # save splits to chromaDB.   
    def _add_splits_to_db(self, ids, documents, metadatas):
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        self.logger.info(f"{ChromaDBHandler.__name__}: added {len(documents)} new chunks for id={metadatas[0]["news_id"]}")

        return
    
    
    # prepare ids, splited_docs and metadatas from result.
    def create_and_save_result_to_db(self, data, result):
        # prepare splitted documents.
        all_splits = self._split_text_from_news(content=result.markdown)
        news_id = result.url.split("/")[-1].split(".")[0]
        
        ids = []
        metadatas = []
    
        for i, split in enumerate(all_splits):
            id=f"{news_id}#chunk={i}"
            metadata={
                "news_id": news_id,
                "url": result.url,
                "title": data.get("title"), #result.metadata["title"],
                "pub_date": data.get("pub_date"), #transform_text_to_date(date_str=result.markdown.split("\n")[-4].split(", ", 1)[-1].strip()),
                "pub_time": data.get("pub_time"), #transform_text_to_time(time_str=result.markdown.split("\n")[-3].split(" ")[-2]),
                "organization": data.get("organization"),
                "keywords": data.get("keywords"),
                "summary": data.get("summary"),
                "chunk": i
            }
            ids.append(id)
            metadatas.append(metadata)
            
            self.logger.info(f"id: {id}")
            self.logger.info(f"metadata: \n%s", pformat(metadata))
        
        self.logger.info(f"Total {len(all_splits)} splited documents for Press Release - Title: {result.metadata["title"]}, news_id: {news_id} created.")
        self.logger.info("-"*50)
        
        #save data to chromadb.
        self._add_splits_to_db(
            ids=ids,
            documents=all_splits,
            metadatas=metadatas
        )
        
        return
    
       # def _transform_text_to_date(self, date_str: str) -> str:
    #     try:
    #         date_obj = datetime.strptime(date_str, "%B %d, %Y")
    #         return date_obj.strftime("%Y-%m-%d")
    #     except ValueError as e:
    #         self.logger.error(f"Date conversion error for '{date_str}': {e}")
    #         return date_str


    # def _transform_text_to_time(self, time_str: str) -> str:
    #     try:
    #         time_obj = datetime.strptime(time_str, "%H:%M")
    #         return time_obj.strftime("%H:%M:%S")
    #     except ValueError as e:
    #         self.logger.error(f"Time conversion error for '{time_str}': {e}")
    #         return time_str
    
    # retriever.
    
    