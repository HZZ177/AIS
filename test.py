from crewai import Agent, Task, Crew, Process, LLM
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource


content = "Users name is John. He is 30 years old and lives in San Francisco."
pdf_source = PDFKnowledgeSource(
    file_paths=["findcarQA.pdf",]
)

# Create an LLM with a temperature of 0 to ensure deterministic outputs
llm = LLM(
    model="deepseek/deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key="sk-f90f833388614e509da4e80528285dc2"
)

# Create an agent with the knowledge store
agent = Agent(
    role="About User",
    goal="You know everything about the user.",
    backstory="""You are a master at understanding people and their preferences.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
)
task = Task(
    description="Answer the following questions about the user: {question}",
    expected_output="An answer to the question.",
    agent=agent,
)

crew = Crew(
    agents=[agent],
    tasks=[task],
    verbose=True,
    process=Process.sequential,
    knowledge_sources=[pdf_source],
)

result = crew.kickoff(inputs={"question": "车位状态变化很慢"})