from langchain_ollama import ChatOllama
from langchain_classic.prompts import PromptTemplate

import os
import json
from dotenv import load_dotenv
load_dotenv()


class ReportGenerator:
    def __init__(self, logger):
        
        # declaring logger.
        self.logger = logger
        
        # set up llm.
        self.model_name = os.getenv("OLLAMA_LLM_MODEL")
        self.llm = ChatOllama(model=self.model_name, temperature=0.2)
        
        # set up prompt template.
        self.template = PromptTemplate(
            input_variables=["sql", "rows"], 
            template="""
            You are an expert analyst. 
            
            SQL query: 
            {sql} 
            
            Query results: 
            {rows} 
            
            Tasks: 
            1. Group by organization(s) or topic(s). 
            2. Summaries ≤ 500 words per group. 
            3. Provide cross-group patterns. 
            4. Provide follow-up analyses. 
            
            Output sections: 
            - Grouped Summaries 
            - Cross-Group Patterns 
            - Suggested Follow-Ups 
            
            """ ) 
        
        self.logger.info("Report Generator initiated.")


    async def generate_report(self, sql: str, rows): 
        prompt = self.template.format(
            sql=sql, 
            rows=json.dumps(rows, indent=2) 
        ) 
        return await self.llm.ainvoke(prompt)
    
    
        
        
        
        
## old code
      
    # def generate_report(self, query:dict) -> str:
        
    #     content = self.query_to_db(query=query)
        
    #     # set up llm chain.
    #     report_chain = self.report_prompt | self.llm
    #     report = report_chain.invoke({"content": content})
    #     self.logger.info(f"Summary: \n%s", report.content)
        
    #     return report.content
    

                
    