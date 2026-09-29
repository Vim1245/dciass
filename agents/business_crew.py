# pyrefly: ignore [missing-import]
from crewai import Crew, Process

from agents.crew_agents import (
    customer_agent,
    policy_agent,
    analysis_agent,
    report_agent
)

from agents.crew_tasks import (
    customer_task,
    policy_task,
    analysis_task,
    report_task
)


business_crew = Crew(
    agents=[
        customer_agent,
        policy_agent,
        analysis_agent,
        report_agent
    ],

    tasks=[
        customer_task,
        policy_task,
        analysis_task,
        report_task
    ],

    process=Process.sequential,

    verbose=True
)


def run_business_crew(request: str):

    result = business_crew.kickoff(
        inputs={
            "request": request
        }
    )

    return result