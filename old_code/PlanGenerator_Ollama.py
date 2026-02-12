from ollama import chat
from pydantic import BaseModel, Field
from typing import List

from datetime import date, time, datetime
from devtools import debug
import os
from dotenv import load_dotenv
load_dotenv()


class Instruction(BaseModel):
    start_date: date = Field(description="start date in the query")
    end_date: date = Field(description="end date in the query")
    topic: str | None = Field(description="topic specified in the query, state 'None' if no topic specified.")
    organziation: List[str] | None = Field(description="subject organization concerned in the query, state 'None' if no organization specified")
    action: str = Field(description="summarize all the actions in the query")
    

class PlanGenerator:
    def __init__(self):
        self.model = os.getenv("OLLAMA_LLM_MODEL")
        self.prompt = """Extract the items from query. Only use the information from the query."""
    
    def chat_loop(self):
        while True:
            query = input("Enter the query to the Gov News or type 'q' for exit: ")
            if query.lower() == "q":
                break
            
            response = chat(
                model = self.model,
                messages = [
                    {
                        "role": "system",
                        "content": self.prompt
                    },
                    {
                        "role": "user",
                        "content": query
                    },
                ],
                format=Instruction.model_json_schema(),
            )
            instruct_dict = Instruction.model_validate_json(response.message.content)
            debug(instruct_dict)
        
        return
    
# testing.
generator = PlanGenerator()
generator.chat_loop()
