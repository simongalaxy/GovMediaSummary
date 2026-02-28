from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools.DataProcessor import date_to_unix, transform_text_to_date, transform_text_to_time

from pprint import pformat
from datetime import datetime, date, time

import os
from dotenv import load_dotenv
load_dotenv()


class DocumentGenerator:
    def __init__(self, logger):
        self.logger = logger
        
        # text_splitter config.
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n"],
            chunk_size=2000,
            chunk_overlap=0
        )
        
        self.logger.info(f"{DocumentGenerator.__name__} initiated.")
    
    
    # split text.
    def _split_text_from_news(self, content: str):
        all_splits = self.text_splitter.split_text(text=content)
        self.logger.info(f"{DocumentGenerator.__name__}: Split content into {len(all_splits)} sub-texts.")
        
        for i, split in enumerate(all_splits):
            self.logger.info(f"Split No. {i}: \n{split}")
        self.logger.info("-"*50)
        
        return all_splits
    
    
    def generate_documents(self, data, result): 
        url = result.url
        news_id = url.split("/")[-1].split(".")[0]
        title = result.metadata["title"]
        date_str=result.markdown.split("\n")[-4].split(", ", 1)[-1].strip()
        time_str=result.markdown.split("\n")[-3].split(" ")[-2]
        
        # get all splitted text from news content.
        all_splits = self._split_text_from_news(content=result.markdown)
       
        # generate document ids and metadatas for each splitted text.
        ids = []
        metadatas = []
    
        for i, split in enumerate(all_splits):
            id=f"{news_id}#chunk={i}"
            metadata={
                "news_id": news_id,
                "pub_date": date_to_unix(date_str=date_str),
                "pub_time": transform_text_to_time(time_str=time_str, logger=self.logger),
                "title": result.metadata["title"],
                "summary": data.get("summary"),
                "keywords": data.get("keywords"),
                "organizations": data.get("organizations"),
                "url": url,
                "chunk": i
            }
            ids.append(id)
            metadatas.append(metadata)
            
            self.logger.info(f"id: {id}")
            self.logger.info(f"metadata: \n%s", pformat(metadata))
            
            self.logger.info(f"Total {len(all_splits)} splited documents for Press Release - Title: {result.metadata["title"]}, news_id: {news_id} created.")
            self.logger.info("-"*50)
        
        return ids, metadatas, all_splits
    
    

 