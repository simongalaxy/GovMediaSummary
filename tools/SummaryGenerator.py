from langchain_classic.chains.summarize import load_summarize_chain
from langchain_ollama.llms import OllamaLLM
from langchain_community.docstore.document import Document
from langchain_core.prompts import PromptTemplate

from typing import List
import os
from dotenv import load_dotenv
load_dotenv()


class SummaryGenerator:
    def __init__(self, logger):
        # initate logger.
        self.logger = logger
        
        # llm config.
        self.model_name = os.getenv("ollama_llm_model")
        self.llm = OllamaLLM(
            model=self.model_name,
            temperature=0.15
        )
        self.prompt = PromptTemplate(
            input_variables=["documents"],
            template="""
            You are an expert analyst. summarize all documents into a summary based on the tasks and output sections:
            
            documents:
            {documents}

            Tasks: 
            1. Group by organization(s) or topic(s). 
            2. Summaries ≤ 500 words per group. 
            3. Provide cross-group patterns. 
            4. Provide follow-up analyses. 
            
            Output sections: 
            - Grouped Summaries 
            - Cross-Group Patterns 
            - Suggested Follow-Ups 
            
            """
        )
        
        # summarization chain config.
        self.chain = load_summarize_chain(
            llm=self.llm,
            chain_type="map_reduce", # refine
            
        )
        
    def summarize_content(self, documents: List[Document]) -> str:
        response = self.chain.invoke(input=documents)
        return response      