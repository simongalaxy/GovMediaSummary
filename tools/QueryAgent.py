from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_classic.agents import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit   

from pprint import pformat
import os
from dotenv import load_dotenv
load_dotenv()

# from tools.logger import Logger

class QueryAgent:
    def __init__(self):
        # set up logger.
        # self.logger = logger
        
        # set up db connection.
        self.username = os.getenv("username")
        self.password = os.getenv("password")
        self.host = os.getenv("host")
        self.port = os.getenv("port")
        self.database = os.getenv("db_name")
        self.conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        self.db = SQLDatabase.from_uri(self.conn_str)
        
        # set up LLM.
        self.modelName = os.getenv("llm_model")
        self.llm = ChatOllama(model=os.getenv("llm_model"))
        
        # set up agent.
        self.toolkits = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.agent_executor = create_sql_agent(llm=self.llm, toolkit=self.toolkits, verbose=True)
        
    def query_to_db(self, question: str) -> str:
        print(f"QueryAgent received question: {question}")
        response = self.agent_executor.run(question)
        print("QueryAgent response: \n%s", pformat(response))
        return response
        
        
if __name__ == "__main__":
    query_agent = QueryAgent()
    while True:
        question = input("Enter your question to query the database (or 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        answer = query_agent.query_to_db(question)
        