from pprint import pformat
import os
from dotenv import load_dotenv
load_dotenv()
import ast

from langchain_ollama import ChatOllama
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_classic.prompts import PromptTemplate

class ReportGenerator:
    def __init__(self, logger):
        
        # declaring logger.
        self.logger = logger
        
        # declare database connection parameters.
        self.username = os.getenv("username")
        self.password = os.getenv("password")
        self.host = os.getenv("host")
        self.port = os.getenv("port")
        self.db_name = os.getenv("db_name")
        self.db_uri = f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        self.db = SQLDatabase.from_uri(self.db_uri)
        
        # set up llm.
        self.model_name = os.getenv("OLLAMA_LLM_MODEL")
        self.llm = ChatOllama(model=self.model_name, temperature=0.7)
        
        # set up prompt template for generating report.
        self.report_prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            You are media research analyst. Summarize the content and group them by organization(s) or topic. 
            Use only the data provided in the content.
            
            content:
            {content}
            """
        )
        self.logger.info("Report Generator initiated.")
    
    
    def query_to_db(self, query: dict):
        
        # classify question by query key.
        if query.keys == "date":
            self.logger.info(query.values)
            query_str = """SELECT content FROM public.news WHERE pub_date::date = '{query.values}'"""
        elif query.keys == "organization":
            pattern = f"%{query.values}%"
            query_str = f"""SELECT content FROM public.news WHERE organization LIKE '{pattern}' OR keywords LIKE '{pattern}'"""
        else:
            pattern = f"%{query.values}%"
            query_str = f"""SELECT content FROM public.news WHERE keywords LIKE '{pattern}'"""
        
        # query to DB.
        result = self.db.run(query_str)
        content = "\n".join(t[0] for t in ast.literal_eval(result) if t[0] is not None)
        
        return content
    
      
    def generate_report(self, query:dict):
        
        content = self.query_to_db(query=query)
        
        # set up llm chain.
        report_chain = self.report_prompt | self.llm
        report = report_chain.invoke({"content": content})
        
        self.logger.info(report.content)
        
        return
    
    