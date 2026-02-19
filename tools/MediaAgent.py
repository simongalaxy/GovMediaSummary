from langchain_ollama.chat_models import ChatOllama
from langchain_community.tools import StructuredTool
from langchain_classic.agents import initialize_agent, AgentType, load_tools
from langchain_classic.load.dump import dumps


from tools.NewsCrawler import NewsCrawler
from tools.ChromaDBHandler import ChromaDBHandler
from tools.logger import Logger


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
        self.tools = [
            StructuredTool.from_function(
                func=self.Crawler.fetch_news_by_dates,
                name="crawl_news",
                description="crawl news from startDate to endDate. startDate and endDate are in 'YYYYMMDD' string format, e.g. '20260801'"
            ),
            
        ] # add more tools, e.g. retriever, summary generator.
        
        self.agent = initialize_agent(
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            return_intermediate_steps=True,
            handling_parsing_errors=True,
            tools=self.tools
        )
        
    def chat_loop(self) -> None:
        while True:
            query = input("Enter the query or type 'q' to exit: ")
            if query.lower() == "q":
                break
            response = self.agent.invoke({"input": query})
            print(dumps(response["intermediate_steps"], pretty=True))
            
        return
        