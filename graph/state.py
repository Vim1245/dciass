from typing import TypedDict


class BusinessState(TypedDict, total=False):

    question: str
    category: str
    customer_name: str
    customer_names: list[str]  # Supports multiple customer lookups in one request
    required_actions: list[str]
    customer_data: str
    order_data: str
    complaint_data: str
    policy_context: str
    context: str
    decision: str
    ticket_result: str
    response: str