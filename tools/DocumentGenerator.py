from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from datetime import datetime
from typing import List



class DocumentGenerator:
    def __init__(self, logger):
        self.logger = logger
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n"],
            chunk_size=400,
            chunk_overlap=80
        )
        
        self.logger.info("DocumentGenerator intiated.")
        
         
    def split_text_from_news(self, content: str):
        all_splits = self.text_splitter.split_text(text=content)
        self.logger.info(f"{DocumentGenerator.__name__}: Split content into {len(all_splits)} sub-texts.")
        
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
    
    
    def create_Documents_from_news(self, result):
        # prepare all splits from content.
        all_splits = self.split_text_from_news(content=result.markdown)
        
        # prepare splitted documents.
        splited_documents = []
        
        for i, split in enumerate(all_splits):
            news_id = result.url.split("/")[-1].split(".")[0]
            doc = Document(
                page_content=split,
                metadata={
                    "news_id": news_id,
                    "title": result.metadata["title"],
                    "url": result.url,
                    "pub_date": self.transform_text_to_date(result.markdown.split("\n")[-4].split(", ", 1)[-1].strip()),
                    "pub_time": self.transform_text_to_time(result.markdown.split("\n")[-3].split(" ")[-2]),
                },
                id=f"{news_id}#chunk={i}"
            )
            splited_documents.append(doc)

        self.logger.info(f"{DocumentGenerator.__name__}: Total {len(splited_documents)} splited documents for Press Release - Title: {result.metadata["title"]} created.")

        return splited_documents
    
    
    