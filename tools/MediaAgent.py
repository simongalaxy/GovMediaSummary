from langchain_ollama.chat_models import ChatOllama
from langchain_community.tools import StructuredTool, tool
from langchain_classic.agents import initialize_agent, AgentType
from langchain_classic.load.dump import dumps


from tools.NewsCrawler import NewsCrawler
from tools.ChromaDBHandler import ChromaDBHandler
from tools.logger import Logger

from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()


class MediaAgent:
    def __init__(self): 
        self.model_name = os.getenv("ollama_llm_model")
        self.llm = ChatOllama(
            model=self.model_name,
            temperature=0.1
            )
        self.Logger = Logger(__name__).get_logger()
        self.DBHandler = ChromaDBHandler(logger=self.Logger)
        self.Crawler = NewsCrawler(
            logger=self.Logger, 
            db_handler=self.DBHandler
            )
        self.tools = [self.get_current_date]
        self.structuredtools = [
            StructuredTool.from_function(
                func=self.Crawler.fetch_news_by_dates,
                name="fetch_news_by_dates",
                description="crawl news from startDate to endDate. startDate and endDate are in 'YYYYMMDD' string format, e.g. '20260801'"
            ),
            StructuredTool.from_function(
                func=self.DBHandler.check_records_by_dates,
                name="check_records_by_dates",
                description="check any records from startDate to endDate in ChromaDB"
            ),
            StructuredTool.from_function(
                func=self.DBHandler.check_records_by_organizations,
                name="check_records_by_organizations",
                description="check any records by organizations in ChromaDB"
            ),
            StructuredTool.from_function(
                func=self.DBHandler.check_records_by_topics,
                name="check_records_by_topics",
                description="check any records by topics in ChromaDB"
            ),
            StructuredTool.from_function(
                func=self.DBHandler.check_records_by_organizations_dates,
                name="check_records_by_organizations_dates",
                description="check any records by organizations and dates in ChromaDB"
            )
        ] # add more tools, e.g. retriever, summary generator.
        
        self.agent = initialize_agent(
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            return_intermediate_steps=True,
            handling_parsing_errors=True,
            tools=self.structuredtools + self.tools
        )
    
    @tool
    def get_current_date(_:str = "") -> str:
        """Return today's date in ISO format (YYYY-MM-DD)."""
        return date.today().isoformat()
     
     
    def chat_loop(self) -> None:
        while True:
            query = input("Enter the query or type 'q' to exit: ")
            if query.lower() == "q":
                break
            response = self.agent.invoke({"input": query})
            print(dumps(response["intermediate_steps"], pretty=True))
            
        return
    