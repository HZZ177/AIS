from crewai import LLM
from pydantic import BaseModel


class Dog(BaseModel):
    name: str
    age: int
    breed: str
    description: str
    mom: str


llm = LLM(
    # openrouter
    model="openrouter/google/gemini-2.0-flash-001",
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    response_format=Dog
)

response = llm.call(
    "分析以下信息" 
    "认识一下科纳！她今年3 岁，是一只黑色的德国牧羊犬"
    "中文回答"
)
print(response)

# Output:
# Dog(name='Kona', age=3, breed='black german shepherd')