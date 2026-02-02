import json
from pydantic import BaseModel
from langchain_classic.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_community.utilities.sql_database import SQLDatabase

import os
import json
from dotenv import load_dotenv
load_dotenv()

class SQLQuery(BaseModel):
    sql: str


class SQLGenerator:
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
        
        # set up LLM.
        self.modelName = os.getenv("SQL_LLM_MODEL")
        self.llm = ChatOllama(model=self.modelName, temperature=0)
        
        # set up max retries
        self.max_retries = 2

        # set up prompt template.
        self.template = PromptTemplate(
            input_variables=["user_question", "schema"],
            template="""
            You are an expert SQL generator. Output must be valid JSON:

            {{
            "sql": "<PostgreSQL SELECT query>"
            }}

            User question:
            {user_question}

            Schema for public.news:
            {schema}

            Rules:
            - Output ONLY valid JSON.
            - The "sql" field must contain a single SELECT query.
            - No explanations, no comments, no markdown.
            """
        )

        self.logger.info("SQL generator initiated.")
        
    def load_schema(self) -> str:
        return self.db.get_table_info(["public.news"])
    
    def query_to_db(self, sql: str):
        return self.db.run(sql)

    async def generate_sql(self, user_question: str) -> str:
        schema = self.load_schema()
        prompt = self.template.format(user_question=user_question, schema=schema)

        for attempt in range(self.max_retries + 1):
            response = await self.llm.ainvoke(prompt)

            try:
                parsed = SQLQuery.model_validate_json(response)
                sql = parsed.sql.strip()
            except Exception:
                if attempt == self.max_retries:
                    raise ValueError("SQL model failed to return valid JSON.")
                prompt += "\nThe previous output was invalid JSON. Fix it."
                continue

            try:
                self.db.run(f"EXPLAIN {sql}")
                return sql
            except Exception:
                if attempt == self.max_retries:
                    raise ValueError("SQL model produced invalid SQL after retries.")
                prompt += "\nThe previous SQL was invalid. Fix it."

        raise RuntimeError("Unexpected SQL generation failure.")
