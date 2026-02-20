import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pprint import pformat
from datetime import datetime, date
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
    
    def _generate_documents(self, data, result): 
        url = result.url
        all_splits = self._split_text_from_news(content=result.markdown)
        news_id = url.split("/")[-1].split(".")[0]
        
        ids = []
        metadatas = []
    
        for i, split in enumerate(all_splits):
            id=f"{news_id}#chunk={i}"
            metadata={
                "news_id": news_id,
                "url": url,
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
        
        return ids, metadatas, all_splits
    
    
    # prepare ids, splited_docs and metadatas from result.
    def create_and_save_result_to_db(self, data, result):
        # prepare splitted documents.
        ids, metadatas, all_splits = self._generate_documents(
            data=data,
            result=result
        )
        
        #save data to chromadb.
        self._add_splits_to_db(
            ids=ids,
            documents=all_splits,
            metadatas=metadatas
        )
        
        return

    # retriever.
    def check_records_by_dates(self, start_date: str, end_date: str):
        return self.collection.get(
             where={
                "pub_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            },
            include=["documents"]
        )
    
    
    def check_records_by_organizations(self, organizations: list[str]):
        return self.collection.get(
            include=["documents"],
            where={"organizations": {"$in": organizations}}
        )
    
      
    def check_records_by_topics(self, keywords: list[str]):
       return self.collection.get(
           include=["documents"],
           where={
               "keywords": {
                    "$in": keywords
               }
           }
       )

        
    def check_records_by_organizations_dates(
        self,
        organizations: list[str],
        start_date: str,
        end_date: str
    ):
        # First filter by date
        date_filtered = self.collection.get(
            where={
                "pub_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            },
            include=["documents", "metadatas"]
        )

        # Now manually apply the organization filter
        results = {
            "ids": [],
            "documents": [],
            "metadatas": []
        }

        for doc_id, doc, meta in zip(
            date_filtered["ids"],
            date_filtered["documents"],
            date_filtered["metadatas"]
        ):
            orgs = meta.get("organizations", [])
            if any(org in orgs for org in organizations):
                results["ids"].append(doc_id)
                results["documents"].append(doc)
                results["metadatas"].append(meta)

        return results
