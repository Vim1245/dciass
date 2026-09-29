"""
DCI AI Business Assistant - Crew AI Agents
"""

# pyrefly: ignore [missing-import]
import ollama
from backend.config import OLLAMA_MODEL


# pyrefly: ignore [missing-import]
from crewai import Agent, LLM


llm = LLM(
    model=f"ollama/{OLLAMA_MODEL}",
    base_url="http://localhost:11434"
)


customer_agent = Agent(
    role="Customer Data Analyst",
    goal="Analyze customer information accurately.",
    backstory="""
    You are responsible for understanding customer
    information and identifying important details.
    """,
    llm=llm,
    verbose=True
)


policy_agent = Agent(
    role="Policy Researcher",
    goal="Analyze company policies and identify relevant rules.",
    backstory="""
    You are a business policy specialist.
    You carefully examine available policy information.
    """,
    llm=llm,
    verbose=True
)


analysis_agent = Agent(
    role="Business Analyst",
    goal="Analyze customer information and policy information together.",
    backstory="""
    You combine business data and policy information
    to produce useful conclusions.
    """,
    llm=llm,
    verbose=True
)


report_agent = Agent(
    role="Business Report Generator",
    goal="Create a concise professional business report.",
    backstory="""
    You convert analysis into a clear report that
    business users can understand.
    """,
    llm=llm,
    verbose=True
)