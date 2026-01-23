from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session, select, inspect
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY


from pprint import pformat
import os
from dotenv import load_dotenv
load_dotenv()


class News(SQLModel, table=True):
    id: str = Field(primary_key=True, unique=True) # 👈 Enforce uniqueness
    url: str
    title: str = Field(description="title of the news article.")
    date: Optional[str] = Field(default=None, description="publish date of the news article.")
    time: Optional[str] = Field(default=None, description="publish time of the news article.")  
    content: Optional[str] = Field(default=None, description="Raw data of news article.")
    summary: Optional[str] = Field(default=None, description="summary of the news article.")
    

class PostgresDBHandler:
    def __init__(self, logger):
        self.logger=logger
        self.username = os.getenv("username")
        self.password = os.getenv("password")
        self.host = os.getenv("host")
        self.port = os.getenv("port")
        self.db_name = os.getenv("db_name")
        self.postgres_url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        self.engine=create_engine(self.postgres_url)
        
        self.logger.info(f"Class - {PostgresDBHandler.__name__} initiated.")
        
        
    def check_and_create_table(self) -> None:
        inspector = inspect(self.engine)
        if inspector.has_table(self.db_name):
            self.logger.info(f"Table {self.db_name} already exists.")
        else:
            self.logger.info(f"Table {self.db_name} does not exist, creating it now.")
            SQLModel.metadata.create_all(self.engine)
            self.logger.info(f"Table {self.db_name} created.")
        
        return None


    def create_News(self, news_item: News) -> None:
        with Session(self.engine) as session:
            statement = select(News).where(News.id == news_item.id)
            existing = session.exec(statement=statement).first()
            if not existing:
                session.add(news_item)
                session.commit()
                session.refresh(news_item)
                self.logger.info(f"News - id: {news_item.id}) saved to sqlite3.")
            else:
                self.logger.info(f"News - id: {news_item.id} item already existed in database. No saving action taken.")   
        
        return None

    def list_all_News(self):
        with Session(self.engine) as session:
            return session.exec(select(News)).all()
    
    
    def save_News_to_db(self, news_list) -> None:
        # save all crawled data:
        self.logger.info("Save crawled data into Postgresql DB.")
        for news in news_list:
            news_item = News(**news)
            self.logger.info(f"news_item: \n%s", pformat(news_item.model_dump(), indent=2))
            self.create_News(news_item=news_item)
        
        self.logger.info(f"Saved total {len(news_list)} news into Postgresql.")
        
        return None

    # def update_News(self, id: str, update_data: dict):
    #     with Session(self.engine) as session:
    #         db_News = session.get(News, id)
    #         if not db_News:
    #             return None
    #         for key, value in update_data.items():
    #             setattr(db_News, key, value)
    #         session.add(db_News)
    #         session.commit()
    #         session.refresh(db_News)

    #         return

    # def delete_News(self, id: str):
    #     with Session(self.engine) as session:
    #         db_News = session.get(News, id)
    #         if db_News:
    #             session.delete(db_News)
    #             session.commit()
    #             return True
    #         return False


 
            
