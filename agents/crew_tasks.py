"""
DCI AI Business Assistant - Crew AI Tasks
"""

from agents.crew_agents import (
    customer_agent,
    policy_agent,
    analysis_agent,
    report_agent
)


# pyrefly: ignore [missing-import]
from crewai import Task


customer_task = Task(
    description="""
    Analyze the customer request:

    {request}

    Identify the customer name and summarize
    the customer-related information.
    """,
    expected_output="""
    A concise customer information summary.
    """,
    agent=customer_agent
)


policy_task = Task(
    description="""
    Analyze the following business request:

    {request}

    Identify what company policy information
    is relevant to this request.
    """,
    expected_output="""
    A concise policy analysis.
    """,
    agent=policy_agent
)


analysis_task = Task(
    description="""
    Review the customer analysis and policy analysis provided in the previous tasks.
    Determine the relevant business action.
    """,
    expected_output="""
    A clear business decision analysis.
    """,
    agent=analysis_agent,
    context=[customer_task, policy_task]
)


report_task = Task(
    description="""
    Create a final professional report based on the customer analysis, policy analysis, and business decision analysis from the previous tasks.
    Keep the report concise and factual.
    """,
    expected_output="""
    A professional final business support report.
    """,
    agent=report_agent,
    context=[customer_task, policy_task, analysis_task]
)