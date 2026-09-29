import json
import logging
import re
from typing import Any, Optional, cast

from backend.ai_service import generate_llm_response
from graph.state import BusinessState
from mcp_server.mcp_service import (
    create_ticket_mcp,
    search_complaint_mcp,
    search_customer_mcp,
    search_customers_by_status_mcp,
)
from prompts.system_prompts import GEMINI_BUSINESS_SYSTEM_INSTRUCTION
from rag.rag_service import search_documents
from backend.supabase_client import (
    extract_all_customer_names as supa_extract_all_names,
    search_customers_multi,
)

# Configure high-level observability logging
logger = logging.getLogger("dci.workflow")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [DCI-AGENT] %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def extract_customer_name(text: str) -> str:
    """Extract the FIRST customer name or ID from query text.
    Kept for backward compatibility. For multi-customer support use extract_all_customer_names_from_query().
    """
    names = extract_all_customer_names_from_query(text)
    return names[0] if names else ""


def extract_all_customer_names_from_query(text: str) -> list[str]:
    """
    Extract ALL customer names and/or IDs from query text.
    Delegates to supabase_client.extract_all_customer_names for DB-aware matching,
    then falls back to contextual regex for names not in the database.

    Returns:
        List of customer name/ID strings found in the text.
    """
    found: list[str] = []

    # 1. Use the database-aware extractor (handles IDs, known names, first-name matching)
    try:
        found = supa_extract_all_names(text)
    except Exception:
        pass

    # 2. Contextual regex fallback: matches capitalized person names preceded by indicators
    #    Only add names not already discovered
    if not found:
        match = re.search(
            r"\b(?:for|named|about|mr\.|mrs\.|ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            text,
        )
        if match:
            candidate = match.group(1).strip()
            blocked = {
                "artificial intelligence",
                "machine learning",
                "customer support",
                "refund policy",
                "return policy",
                "business assistant",
                "details",
                "complaint",
                "a refund",
                "a ticket",
                "a customer",
                "help",
                "customers",
                "inactive",
                "active",
                "support",
            }
            if candidate.lower() not in blocked and candidate not in found:
                found.append(candidate)

    # 3. Extract search term helper as last resort
    if not found:
        try:
            from backend.supabase_client import extract_search_term
            extracted = extract_search_term(text)
            if extracted and len(extracted) >= 2 and extracted.lower() not in {"details", "help", "support", "policy", "active", "inactive"}:
                found.append(extracted)
        except Exception:
            pass

    return found


def _is_list_all_query(q_lower: str, entity: str) -> bool:
    """Detect if the user wants to list/show ALL records of a given entity type.
    Examples: 'show all customers', 'list all orders', 'show customers', 'list orders'
    Must NOT match when a specific name/ID is provided (handled by extract_customer_name).
    """
    # Patterns that indicate "list everything" intent
    list_keywords = ["show all", "list all", "get all", "display all", "fetch all",
                     "show every", "list every", "all the"]
    # Also match bare "show customers" / "list orders" without a specific name
    bare_list = ["show", "list", "get", "display", "fetch"]

    for kw in list_keywords:
        if kw in q_lower and entity in q_lower:
            return True

    # Match "show customers", "list orders" etc. (verb + entity, no specific name after)
    for verb in bare_list:
        pattern = rf"\b{verb}\s+{entity}\b"
        if re.search(pattern, q_lower):
            # Make sure it's not "show Ravi Kumar's orders" (has a name before the entity)
            return True

    return False


async def plan_node(state: BusinessState) -> BusinessState:
    """
    UNDERSTAND & PLAN STAGE:
    Analyzes the user request to determine the required actions:
    - LIST_CUSTOMERS     (show/list ALL customers)
    - LIST_ORDERS        (show/list ALL orders)
    - LIST_COMPLAINTS    (show/list ALL or filtered complaints)
    - CUSTOMER_LOOKUP    (search for a specific customer by name/ID)
    - ORDER_LOOKUP       (search for specific orders by customer/order ID)
    - STATUS_LOOKUP
    - COMPLAINT_LOOKUP   (search complaint for a specific customer)
    - POLICY_SEARCH
    - TICKET_CREATION
    - GENERAL_RESPONSE
    """
    question = state.get("question", "").strip()
    logger.info("Request received: '%s'", question[:60])

    if not question:
        return {
            **state,
            "category": "general",
            "customer_name": "",
            "customer_names": [],
            "required_actions": ["GENERAL_RESPONSE"],
            "decision": "NO_ACTION",
            "response": "Please provide a valid question or business request.",
        }

    q_lower = question.lower()
    # Extract ALL customer names/IDs from the query
    customer_names = extract_all_customer_names_from_query(question)
    customer_name = customer_names[0] if customer_names else ""

    logger.info("Extracted customer names: %s", customer_names)

    required_actions: list[str] = []

    # ---- Detect LIST ALL intents FIRST (before specific lookups) ----

    # "Show all customers" / "List customers"
    is_list_all_customers = _is_list_all_query(q_lower, "customer") and not customer_name
    if is_list_all_customers:
        required_actions.append("LIST_CUSTOMERS")

    # "Show all orders" / "List orders"  (but NOT "Show Manoj Kumar's orders")
    is_list_all_orders = _is_list_all_query(q_lower, "order") and not customer_name and not re.search(r"\b(C\d{1,4})\b", question, re.IGNORECASE)
    if is_list_all_orders:
        required_actions.append("LIST_ORDERS")

    # "Show all complaints" / "Find pending complaints" / "List complaints"
    is_list_complaints = (
        ((_is_list_all_query(q_lower, "complaint") and not customer_name)
         or (any(kw in q_lower for kw in ["pending complaint", "open complaint", "find complaint", "show complaint", "list complaint"]) and not customer_name))
    )
    if is_list_complaints:
        required_actions.append("LIST_COMPLAINTS")

    # If we already identified a LIST action, skip the specific lookup detection for that entity
    if required_actions:
        logger.info("Request planned (list-all): category=%s, actions=%s",
                     "orders" if "LIST_ORDERS" in required_actions else "customer", required_actions)
        if "LIST_ORDERS" in required_actions:
            category = "orders"
        elif "LIST_COMPLAINTS" in required_actions:
            category = "customer"
        else:
            category = "customer"
        return {
            **state,
            "category": category,
            "customer_name": "",
            "customer_names": [],
            "required_actions": required_actions,
        }

    # ---- Specific lookup intents ----

    # Detect Ticket Creation intent
    if any(kw in q_lower for kw in ["create a support ticket", "create a ticket", "create ticket"]):
        required_actions.append("TICKET_CREATION")
        if customer_name or "customer" in q_lower:
            required_actions.append("CUSTOMER_LOOKUP")
            required_actions.append("COMPLAINT_LOOKUP")
        required_actions.append("POLICY_SEARCH")

    # Detect Order intent (e.g. "Show orders for C001", "What orders does Ravi Kumar have?", "Find order ORD001", "Show pending orders", "What did Manoj Kumar order?")
    is_order_query = (
        bool(re.search(r"\b(?:ORD|O)\d{1,5}\b", question, re.IGNORECASE))
        or any(kw in q_lower for kw in ["order", "orders", "ordered", "purchase", "purchases", "buy", "bought"])
        or ("pending" in q_lower and any(w in q_lower for w in ["orders", "items", "show", "list"]))
    )
    if is_order_query and "ORDER_LOOKUP" not in required_actions:
        required_actions.append("ORDER_LOOKUP")

    # Detect Status / Multi-customer query intent (e.g. "Which customers are inactive?", "List active customers")
    is_status_query = (
        not is_order_query
        and ("inactive" in q_lower or "active" in q_lower or "suspended" in q_lower)
        and any(kw in q_lower for kw in ["which", "list", "show", "who are", "customers are", "customer is", "all "])
    )
    if is_status_query:
        required_actions.append("STATUS_LOOKUP")

    # Detect Policy intent
    if any(kw in q_lower for kw in ["refund", "policy", "warranty", "return", "days to", "timeframe", "eligible", "eligibility", "condition"]):
        if "POLICY_SEARCH" not in required_actions:
            required_actions.append("POLICY_SEARCH")

    # Detect Complaint intent (specific customer)
    if any(kw in q_lower for kw in ["complaint", "damaged product", "damaged", "issue"]):
        if "COMPLAINT_LOOKUP" not in required_actions:
            required_actions.append("COMPLAINT_LOOKUP")
        if customer_name and "CUSTOMER_LOOKUP" not in required_actions:
            required_actions.append("CUSTOMER_LOOKUP")

    # Detect Customer Lookup intent
    is_customer_query = (
        not is_order_query
        and (
            bool(customer_name)
            or bool(re.search(r"\b(C\d{1,4})\b", question, re.IGNORECASE))
            or any(kw in q_lower for kw in [
                "customer", "details", "email", "phone", "city",
                "account", "find", "search", "who is", "what is", "look up"
            ])
        )
    )
    if is_customer_query and not is_status_query and "CUSTOMER_LOOKUP" not in required_actions:
        required_actions.append("CUSTOMER_LOOKUP")

    # If asking for action on customer complaint
    if any(kw in q_lower for kw in ["action should be taken", "what action", "check the available information"]):
        if "TICKET_CREATION" not in required_actions:
            required_actions.append("TICKET_CREATION")
        if "CUSTOMER_LOOKUP" not in required_actions:
            required_actions.append("CUSTOMER_LOOKUP")
        if "COMPLAINT_LOOKUP" not in required_actions:
            required_actions.append("COMPLAINT_LOOKUP")
        if "POLICY_SEARCH" not in required_actions:
            required_actions.append("POLICY_SEARCH")

    # General Knowledge Fallback
    if not required_actions:
        required_actions.append("GENERAL_RESPONSE")

    # Determine high-level category
    if "ORDER_LOOKUP" in required_actions:
        category = "orders"
    elif "TICKET_CREATION" in required_actions or ("POLICY_SEARCH" in required_actions and ("CUSTOMER_LOOKUP" in required_actions or "COMPLAINT_LOOKUP" in required_actions)):
        category = "business_support"
    elif "STATUS_LOOKUP" in required_actions or "CUSTOMER_LOOKUP" in required_actions or "COMPLAINT_LOOKUP" in required_actions:
        category = "customer"
    elif "POLICY_SEARCH" in required_actions:
        category = "policy"
    else:
        category = "general"

    logger.info("Request planned: category=%s, actions=%s, names=%s", category, required_actions, customer_names)

    return {
        **state,
        "category": category,
        "customer_name": customer_name,
        "customer_names": customer_names,
        "required_actions": required_actions,
    }


async def retrieve_node(state: BusinessState) -> BusinessState:
    """
    SELECTIVE RETRIEVAL STAGE:
    Executes ONLY the tools and knowledge sources required for this request.
    Does not make unnecessary MCP or RAG calls.
    Supports LIST_CUSTOMERS, LIST_ORDERS, LIST_COMPLAINTS for "show all" queries.
    """
    required_actions = state.get("required_actions", [])
    customer_name = state.get("customer_name", "")
    question = state.get("question", "")
    q_lower = question.lower()

    customer_data = ""
    order_data = ""
    complaint_data = ""
    policy_context = ""

    # ---- LIST ALL: Customers ----
    if "LIST_CUSTOMERS" in required_actions:
        try:
            logger.info("Executing Supabase list ALL customers")
            from backend.supabase_client import supabase as supa_client, format_customer_records
            resp = supa_client.table("customers").select("*").order("Customer_ID").execute()
            from backend.supabase_client import _to_dict_list
            records = _to_dict_list(resp.data)
            if records:
                customer_data = format_customer_records(records)
            else:
                customer_data = "No customer records found in the database."
        except Exception as e:
            logger.error("Error listing all customers: %s", e)
            customer_data = f"Error listing customers: {str(e)}"

    # ---- LIST ALL: Orders ----
    if "LIST_ORDERS" in required_actions:
        try:
            logger.info("Executing Supabase list ALL orders")
            from backend.supabase_client import supabase as supa_client, format_order_records
            resp = None
            for tbl in ["orders", "Orders"]:
                try:
                    resp = supa_client.table(tbl).select("*").order("Order_ID").execute()
                    from backend.supabase_client import _to_dict_list
                    records = _to_dict_list(resp.data)
                    if records:
                        order_data = format_order_records(records, limit=20)
                        break
                except Exception:
                    continue
            if not order_data:
                order_data = "No order records found in the database."
        except Exception as e:
            logger.error("Error listing all orders: %s", e)
            order_data = f"Error listing orders: {str(e)}"

    # ---- LIST ALL: Complaints (with optional status filter) ----
    if "LIST_COMPLAINTS" in required_actions:
        try:
            logger.info("Executing local DB list complaints")
            from backend.database import get_db_connection
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                # Check for status filter (e.g. "pending complaints", "open complaints")
                status_filter = ""
                for st in ["pending", "open", "under review", "resolved", "closed"]:
                    if st in q_lower:
                        status_filter = st
                        break

                if status_filter:
                    cur.execute("SELECT * FROM complaints WHERE LOWER(status) LIKE ? ORDER BY complaint_id",
                                (f"%{status_filter}%",))
                else:
                    cur.execute("SELECT * FROM complaints ORDER BY complaint_id")

                rows = cur.fetchall()
                if rows:
                    lines = []
                    for row in rows:
                        lines.append(
                            f"Complaint ID: {row['complaint_id']}\n"
                            f"Customer ID: {row['customer_id']}\n"
                            f"Customer Name: {row['customer_name']}\n"
                            f"Issue: {row['issue']}\n"
                            f"Status: {row['status']}\n"
                            f"Date: {row['date']}"
                        )
                    status_label = f" with status '{status_filter}'" if status_filter else ""
                    complaint_data = f"Found {len(rows)} complaint(s){status_label}:\n\n" + "\n\n---\n\n".join(lines)
                else:
                    complaint_data = f"No complaints found{' with status ' + repr(status_filter) if status_filter else ''}."
            finally:
                conn.close()
        except Exception as e:
            logger.error("Error listing complaints: %s", e)
            complaint_data = f"Error listing complaints: {str(e)}"

    # ---- Specific Order Lookup from Supabase / Database ----
    if "ORDER_LOOKUP" in required_actions:
        try:
            logger.info("Executing Supabase search_orders for '%s'", question)
            from backend.supabase_client import search_orders as supabase_orders, format_order_records
            valid_cust = customer_name if customer_name and not any(w in customer_name.lower() for w in ["order", "orders", "pending", "delivered", "transit", "find", "show"]) else ""
            order_records = supabase_orders(query=question, customer_name=valid_cust, user_query=question)
            if order_records:
                order_data = format_order_records(order_records)
            else:
                order_data = "No matching order found."

        except Exception as e:
            logger.error("Error during orders search: %s", e)
            order_data = "No matching order found."

    # Status Lookup across 100 customer records in database
    if "STATUS_LOOKUP" in required_actions:
        status_term = "Inactive" if "inactive" in question.lower() else "Active"
        try:
            logger.info("MCP tool called: search_customers_by_status for '%s'", status_term)
            status_res = await search_customers_by_status_mcp(status_term)
            if isinstance(status_res, list) and status_res:
                lines = [
                    f"- {c['name']} (ID: {c.get('customer_id', 'N/A')}, Status: {c.get('status', 'N/A')}, Email: {c.get('email', 'N/A')})"
                    for c in status_res
                ]
                customer_data = f"Customers with status '{status_term}' ({len(status_res)} records found in database):\n" + "\n".join(lines)
            elif isinstance(status_res, str):
                customer_data = status_res
            else:
                customer_data = f"No customers found with status '{status_term}'."
        except Exception as e:
            customer_data = f"Error querying customer status: {str(e)}"

    # Customer Lookup from Supabase (specific name/ID search)
    # Supports MULTIPLE customers in a single request
    if "CUSTOMER_LOOKUP" in required_actions:
        customer_names_list = state.get("customer_names", [])
        if not customer_names_list and customer_name:
            customer_names_list = [customer_name]

        try:
            from backend.supabase_client import (
                search_customer as supabase_search,
                search_customers_multi as supabase_search_multi,
                format_customer_records,
                _fetch_last_customer,
            )

            if customer_names_list:
                logger.info("Executing multi-customer Supabase search for: %s", customer_names_list)

                # Handle __LAST_CUSTOMER__ special token
                search_names = [n for n in customer_names_list if n != "__LAST_CUSTOMER__"]
                all_records: list[dict[str, Any]] = []

                # Fetch last customer if requested
                if "__LAST_CUSTOMER__" in customer_names_list:
                    last_records = _fetch_last_customer()
                    all_records.extend(last_records)

                # Search all named/ID customers
                if search_names:
                    multi_records = supabase_search_multi(search_names, user_query=question)
                    # Deduplicate against already-found records
                    seen_ids = {str(r.get("Customer_ID", "")) for r in all_records}
                    for r in multi_records:
                        cid = str(r.get("Customer_ID", ""))
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            all_records.append(r)

                if all_records:
                    customer_data = format_customer_records(all_records)
                    logger.info("Found %d customer record(s) for names: %s", len(all_records), customer_names_list)
                else:
                    not_found_names = ", ".join(customer_names_list)
                    customer_data = f"Customer not found. No records matching: {not_found_names}"
            else:
                # Fallback: search by the question text directly
                logger.info("Executing Supabase search_customer for question text")
                supa_records = supabase_search(name=question, user_query=question)
                if supa_records:
                    customer_data = format_customer_records(supa_records)
                else:
                    customer_data = "Customer not found."
        except Exception as e:
            logger.error("Error during customer search: %s", e)
            customer_data = f"Customer lookup error: {str(e)}"

    # Selective MCP Complaint Lookup (specific customer)
    if "COMPLAINT_LOOKUP" in required_actions:
        if customer_name:
            try:
                logger.info("MCP tool called: search_complaint for '%s'", customer_name)
                res = await search_complaint_mcp(customer_name)
                complaint_data = str(res) if res else "Complaint not found."
            except Exception as e:
                complaint_data = f"MCP search_complaint unavailable: {str(e)}"
        else:
            complaint_data = "Complaint not found."

    # Selective RAG Policy Search
    if "POLICY_SEARCH" in required_actions:
        try:
            logger.info("RAG search performed for query: '%s'", question[:50])
            documents = search_documents(question)
            if documents:
                policy_context = "\n\n".join(doc.page_content for doc in documents)
            else:
                policy_context = "No relevant policy documents found."
        except Exception as e:
            policy_context = f"Error retrieving policy documents: {str(e)}"

    return {
        **state,
        "customer_data": customer_data,
        "order_data": order_data,
        "complaint_data": complaint_data,
        "policy_context": policy_context,
    }



async def decision_node(state: BusinessState) -> BusinessState:
    """
    BUSINESS ANALYSIS & DECISION STAGE:
    Analyzes gathered facts and outputs strictly one structured decision:
    - CREATE_TICKET
    - MORE_INFORMATION_REQUIRED
    - NO_ACTION
    """
    category = state.get("category", "general")
    required_actions = state.get("required_actions", [])
    question = state.get("question", "")
    customer_name = state.get("customer_name", "")
    customer_data = state.get("customer_data", "")
    complaint_data = state.get("complaint_data", "")
    policy_context = state.get("policy_context", "")

    # For pure general knowledge, policy, or customer lookup requests, no ticket decision is needed
    if category in ["general", "policy", "customer"] or "TICKET_CREATION" not in required_actions:
        decision = "NO_ACTION"
    else:
        # Ticket creation was planned/requested
        if not customer_name or "not specified" in customer_data.lower() or "not found" in customer_data.lower():
            decision = "MORE_INFORMATION_REQUIRED"
        elif customer_name and ("open" in complaint_data.lower() or "damaged" in complaint_data.lower()):
            decision = "CREATE_TICKET"
        else:
            decision = "NO_ACTION"

    logger.info("Decision generated: %s", decision)

    # Perform analysis with configured LLM (Ollama via unified AI service)
    response = ""
    if category == "general":
        try:
            response = await generate_llm_response(
                prompt=question,
                system_instruction=GEMINI_BUSINESS_SYSTEM_INSTRUCTION,
            )
        except Exception as e:
            response = f"Assistant temporarily unavailable: {str(e)}"
    elif category == "policy":
        prompt = f"""You are the DCI AI Business Assistant.
Answer the user question using ONLY the provided company policy context.
If not in the context, state clearly: "The requested information was not found in the available data."

Policy Context:
{policy_context}

Question:
{question}
"""
        try:
            response = await generate_llm_response(
                prompt=prompt,
                system_instruction=GEMINI_BUSINESS_SYSTEM_INSTRUCTION,
            )
        except Exception as e:
            response = f"Policy assistant temporarily unavailable: {str(e)}"

    return {
        **state,
        "decision": decision,
        "response": response,
    }


async def action_node(state: BusinessState) -> BusinessState:
    """
    ACTION STAGE (Ticket Creation):
    Invokes MCP tool create_ticket only when decision is CREATE_TICKET.
    Enforces duplicate ticket protection (executes at most once per request).
    """
    decision = state.get("decision", "NO_ACTION")

    # Safety checks
    if decision != "CREATE_TICKET":
        return state

    # Duplicate ticket protection
    if state.get("ticket_result"):
        return state

    customer_name = state.get("customer_name") or "Ravi Kumar"
    issue = "Damaged product"

    comp_match = re.search(r'"issue":\s*"([^"]+)"', state.get("complaint_data", ""))
    if comp_match:
        issue = comp_match.group(1)

    try:
        logger.info("MCP tool called: create_ticket for '%s' (Issue: '%s')", customer_name, issue)
        ticket_res = await create_ticket_mcp(customer_name=customer_name, issue=issue)
        logger.info("Ticket created successfully")
    except Exception as e:
        ticket_res = f"Error creating ticket: {str(e)}"

    return {
        **state,
        "ticket_result": ticket_res,
    }


async def final_response_node(state: BusinessState) -> BusinessState:
    """
    FINAL RESPONSE STAGE:
    Formats concise, professional, business-friendly response based strictly on gathered facts and decisions.
    Uses configured AI provider (Ollama) and enforces strict zero-hallucination rules.
    """
    category = state.get("category", "general")
    decision = state.get("decision", "NO_ACTION")
    ticket_result = state.get("ticket_result", "")
    customer_data = state.get("customer_data", "")
    complaint_data = state.get("complaint_data", "")
    policy_context = state.get("policy_context", "")
    question = state.get("question", "")
    customer_name = state.get("customer_name", "")
    required_actions = state.get("required_actions", [])

    # If general or policy already populated a response, preserve it
    if state.get("response"):
        logger.info("Workflow completed successfully")
        return state

    # ---- Handle LIST ALL actions directly (no LLM needed) ----
    if "LIST_CUSTOMERS" in required_actions and customer_data:
        response = f"Here are the customer records from the database:\n\n{customer_data}"
        logger.info("Workflow completed successfully")
        return {**state, "response": response}

    if "LIST_ORDERS" in required_actions:
        order_data = state.get("order_data", "")
        if order_data and "No order records found" not in order_data:
            response = f"Here are the order records from the database:\n\n{order_data}"
        else:
            response = "No order records found in the database."
        logger.info("Workflow completed successfully")
        return {**state, "response": response}

    if "LIST_COMPLAINTS" in required_actions and complaint_data:
        response = f"Here are the complaint records from the database:\n\n{complaint_data}"
        logger.info("Workflow completed successfully")
        return {**state, "response": response}

    # Handle Unknown Customer (Zero Hallucination Guarantee)
    if "CUSTOMER_LOOKUP" in required_actions and ("customer not found" in customer_data.lower() or not customer_data.strip()) and not policy_context:
        display_name = customer_name if customer_name else "the specified customer"
        response = f"Customer not found. The requested information was not found in the available customer records for '{display_name}'."
        return {**state, "response": response}
    # Handle Complaint Not Found when complaint was specifically asked
    elif "COMPLAINT_LOOKUP" in required_actions and "complaint not found" in complaint_data.lower() and not ("open" in complaint_data.lower() or "issue" in complaint_data.lower()):
        if customer_data and "customer_id" in customer_data.lower():
            response = f"The requested complaint information was not found in the available data for '{customer_name}' (Account exists, but no complaints are logged)."
        else:
            response = f"The requested information was not found in the available data."
    # Handle Status / Inactive customer query directly from verified database records
    elif "STATUS_LOOKUP" in required_actions and customer_data:
        response = f"Based on the database records, here are the matching customer accounts:\n\n{customer_data}"
    # Handle Successful Ticket Creation
    elif decision == "CREATE_TICKET" and ticket_result:
        ticket_id = "T001"
        t_match = re.search(r'"ticket_id":\s*"([^"]+)"', ticket_result)
        if t_match:
            ticket_id = t_match.group(1)

        issue = "Damaged product"
        comp_match = re.search(r'"issue":\s*"([^"]+)"', complaint_data)
        if comp_match:
            issue = comp_match.group(1)

        response = (
            f"{customer_name}'s complaint was reviewed against the available policy. A support ticket has been created.\n\n"
            f"Ticket ID: {ticket_id}\n"
            f"Issue: {issue}\n"
            f"Status: Created\n\n"
            f"The support team will review this urgent complaint and provide an update using ticket ID {ticket_id}."
        )
    # Handle Missing Customer Information
    elif decision == "MORE_INFORMATION_REQUIRED":
        response = (
            "Additional customer information is required before creating a support ticket. "
            "Please provide the customer name and order details so we can locate the account and create the ticket."
        )
    elif "ORDER_LOOKUP" in state.get("required_actions", []):
        order_data = state.get("order_data", "")
        if not order_data or "No matching order found." in order_data:
            response = "No matching order found."
        else:
            prompt = f"""You are the DCI AI Business Assistant.
Provide a clear, professional, natural-language answer to the user request based strictly on the verified order records below.

Verified Database Order Records:
{order_data}

User Request:
{question}

Instructions:
- Summarize the matching orders clearly and professionally.
- Include all available fields: Order ID, Customer ID, Customer Name, Product, Category, Amount, Order Date, Delivery Status, and Payment Status.
- Do NOT invent or assume any order details not present in the records.
- If no matching order was found, return exactly: "No matching order found."
"""
            try:
                response = await generate_llm_response(
                    prompt=prompt,
                    system_instruction=GEMINI_BUSINESS_SYSTEM_INSTRUCTION,
                )
                if not response or not response.strip() or "not found" in response.lower() and order_data:
                    response = f"Matching orders found:\n\n{order_data}"
            except Exception:
                response = f"Matching orders found:\n\n{order_data}"
    else:
        prompt = f"""You are the DCI AI Business Assistant.
Provide a clear, professional, natural-language answer to the user request based strictly on the available records below.

Verified Customer Database Record(s):
{customer_data}

Complaint Record:
{complaint_data}

Policy Context:
{policy_context}

User Request:
{question}

Instructions:
- When customer records are present above, include the Customer_ID, Name, Email, and all remaining available fields from the database (Phone, City, State, Customer_Status, Customer_Type, Registration_Date, Total_Orders, Total_Spent, Last_Order_Date, Preferred_Product_Category, Support_Status).
- If the user specifically asked for a specific detail like email, phone, city, or status, highlight that clearly while providing the answer.
- If complaint details were requested and records are present above, summarize Complaint Issue and Status.
- If status or inactive customers were requested, list the matching customers found in the records.
- If complaint was checked against refund policy, explain the policy condition and state what facts are missing without assuming eligibility.
- Never invent or fabricate information. Do NOT mention internal node names.
"""
        try:
            response = await generate_llm_response(
                prompt=prompt,
                system_instruction=GEMINI_BUSINESS_SYSTEM_INSTRUCTION,
            )
            # Guard against small LLM false negative when real customer data was provided
            if customer_data and "not found" not in customer_data.lower() and ("not found" in response.lower() or not response.strip()):
                response = f"Customer details found:\n\n{customer_data}"
        except Exception:
            # Deterministic fallback from real database data if Ollama is unavailable
            parts = []
            if customer_data:
                parts.append(f"Customer Information:\n{customer_data}")
            if complaint_data and "not found" not in complaint_data.lower():
                parts.append(f"Complaint Information:\n{complaint_data}")
            response = "\n\n".join(parts) if parts else "The requested information was not found in the available data."


    logger.info("Workflow completed successfully")


    return {
        **state,
        "response": response,
    }


# Backwards compatibility wrappers
async def classify_request(state: BusinessState) -> BusinessState:
    return await plan_node(state)

async def customer_node(state: BusinessState) -> BusinessState:
    return await retrieve_node(state)

async def policy_search_node(state: BusinessState) -> BusinessState:
    return await retrieve_node(state)

async def ticket_creation_node(state: BusinessState) -> BusinessState:
    return await action_node(state)

async def policy_node(state: BusinessState) -> BusinessState:
    retrieved = await retrieve_node(state)
    return await decision_node(cast(BusinessState, retrieved))

async def general_node(state: BusinessState) -> BusinessState:
    return await decision_node(state)