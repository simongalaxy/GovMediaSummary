import instructor
from pydantic import Field, BaseModel
from typing import List

from datetime import date
from devtools import debug


class Instruction(BaseModel):
    start_date: date | None = Field(description="start date in the query")
    end_date: date | None = Field(description="end date in the query")
    topic: List[str] | None = Field(description="topic specified in the query, state 'None' if no topic specified.")
    organziation: List[str] | None = Field(description="subject organization concerned in the query, state 'None' if no organization specified")
    action: List[str] = Field(description="summarize all the actions in the query")


class PlanGenerator:
    def __init__(self):
        self.client = instructor.from_provider("ollama/llama3")
        
    def chat_loop(self):
        while True:
            query = input("Enter the query to the Gov News or type 'q' for exit:")
            if query.lower() == "q":
                break
            
            instruction = self.client.create(
                response_model=Instruction,
                messages=[
                    {
                        "role": "user",
                        "content": """Extract the items from query: {{query}}. Only use the information from the query."""
                    },
                ],
                context={"query": query}
            )
            debug(instruction)
            
        return instruction
        
# testing
generator = PlanGenerator()
instruction = generator.chat_loop()
