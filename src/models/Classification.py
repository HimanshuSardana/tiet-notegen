from pydantic import BaseModel, Field

class Classification(BaseModel):
    """
    Schema for classification of questions of a question paper
    """
    topic: str = Field(description="The subtopic of the question paper")
    questions: list[str] = Field(description="List of questions falling under the specified topic", min_items=1)
