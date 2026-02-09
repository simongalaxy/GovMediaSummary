import chromadb
# from ollama import embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()


class ChromaDBHandler:
    def __init__(self, logger):
        self.logger = logger
        # embedding config.
        # self.model = os.getenv("OLLAMA_EMBEDDINGS_MODEL")
        
        # chromaDB config.
        self.collection_name = os.getenv("collection_name")
        self.db_path = os.getenv("chromadb_path")
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            # embedding_function=embeddings(self.model)
        )
        
        # text_splitter config.
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n"],
            chunk_size=500,
            chunk_overlap=50
        )
        
        self.logger.info(f"{ChromaDBHandler.__name__} initiated.")
    
    
    # split text.
    def split_text_from_news(self, content: str):
        all_splits = self.text_splitter.split_text(text=content)
        self.logger.info(f"{ChromaDBHandler.__name__}: Split content into {len(all_splits)} sub-texts.")
        
        for i, split in enumerate(all_splits, start=1):
            self.logger.info(f"Split No. {i}: \n{split}")
        self.logger.info("-"*50)
        
        return all_splits
    
    
    def transform_text_to_date(self, date_str: str) -> str:
        try:
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError as e:
            self.logger.error(f"Date conversion error for '{date_str}': {e}")
            return date_str


    def transform_text_to_time(self, time_str: str) -> str:
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.strftime("%H:%M:%S")
        except ValueError as e:
            self.logger.error(f"Time conversion error for '{time_str}': {e}")
            return time_str
    
    # prepare ids, splited_docs and metadatas from result.
    # def create_and_save_result_to_db(self, result):
    #     # prepare all splits from content.
    #     all_splits = self.split_text_from_news(content=result.markdown)
        
    #     # prepare splitted documents.
    #     ids = []
    #     splited_docs = []
    #     metadatas = []
        
    #     news_id = result.url.split("/")[-1].split(".")[0]
        
    #     for i, split in enumerate(all_splits):
    #         id=f"{news_id}#chunk={i}"
    #         metadata={
    #             "news_id": news_id,
    #             "title": result.metadata["title"],
    #             "url": result.url,
    #             "pub_date": transform_text_to_date(date_str=result.markdown.split("\n")[-4].split(", ", 1)[-1].strip()),
    #             "pub_time": transform_text_to_time(time_str=result.markdown.split("\n")[-3].split(" ")[-2]),
    #         }
    #         ids.append(id)
    #         metadatas.append(metadata)
            
    #     self.logger.info(f"{ChromaDBHandler.__name__}: Total {len(all_splits)} splited documents for Press Release - Title: {result.metadata["title"]}, news_id: {news_id} created.")
    #     self.add_splits_to_db(
    #         ids=ids,
    #         splited_docs=splited_docs,
    #         metadatas=metadatas
    #     )
        
    #     return
    

    # save splits to chromaDB.   
    def add_splits_to_db(self, ids, documents, metadatas):
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        self.logger.info(f"{ChromaDBHandler.__name__}: added {len(documents)} new chunks for id={metadatas[0]["news_id"]}")

        return
    
    
    # retriever.
    