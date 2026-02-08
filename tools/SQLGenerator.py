from pydantic import BaseModel
from langchain_classic.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_classic.chains.llm import LLMChain

from pydantic import BaseModel, Field

import os
import json
from dotenv import load_dotenv
load_dotenv()

class SQLQuery(BaseModel):
    sql: str = Field(description="a valid SQL query with no explanation.")


class NL2SQLGenerator:
    def __init__(self, logger):
        # set up logger.
        self.logger = logger
        
        # set up db connection.
        self.username = os.getenv("username")
        self.password = os.getenv("password")
        self.host = os.getenv("host")
        self.port = os.getenv("port")
        self.database = os.getenv("db_name")
        self.conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        self.db = SQLDatabase.from_uri(self.conn_str)
        self.db_schema = self.db.get_table_info(["news"])
        
        self.prompt_template = prompt_template = prompt_template = """
        You are an expert SQL generator. Convert the user's natural language request
        into a valid SQL query. Use ONLY the tables and columns from the schema.

        SCHEMA:
        {schema}

        Return ONLY valid JSON in this format:
        {
        "sql": "<SQL_QUERY>"
        }

        Do NOT add explanations or commentary.
        USER REQUEST:
        {question}
        """

        self.parser = PydanticOutputParser(pydantic_object=SQLQuery)
        self.sql_prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=self.prompt_template,
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
         # set up LLM.
        self.modelName = os.getenv("SQL_LLM_MODEL")
        self.llm = ChatOllama(model=self.modelName, temperature=0)
        self.chain = LLMChain(llm=self.llm, prompt=self.sql_prompt)
        
        self.logger.info("NL2SQLGenerator initiated.")
        
    def generate_sql(self, question: str) -> str:
        """ Generate SQL from a natural language question and return pure SQL. """ 
        raw_output = self.chain.run(schema=self.db_schema, question=question) 
        parsed = self.parser.parse(raw_output) 
        
        return parsed.sql.strip()
