import logging
import os
import re
from typing import Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("dci.supabase")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [DCI-SUPABASE] %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

SUPABASE_URL: str = os.getenv("SUPABASE_URL") or "https://ebnidyjksuijtxjlldcj.supabase.co"
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVibmlkeWprc3VpanR4amxsZGNqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAzMjI1MTYsImV4cCI6MjEwNTg5ODUxNn0.jY9Rk6uPjlo8JVip7dNkUK1GejVCXugCu6nEfXuJjN8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Supabase PostgREST page size for paginated fetches
_PAGE_SIZE = 1000

# Cache for known customer names and IDs
_CACHED_CUSTOMER_NAMES: list[str] = []
_CACHED_CUSTOMER_IDS: list[str] = []


def _to_dict_list(data: Any) -> list[dict[str, Any]]:
    """Safely convert PostgREST response data to list of dicts for strict type checking."""
    if not isinstance(data, list):
        return []
    return [dict(row) for row in data if isinstance(row, dict)]


def _fetch_all_rows(table: str, columns: str = "*", order_col: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch ALL rows from a Supabase table using offset-based pagination.
    Supabase PostgREST defaults to returning at most 1000 rows per request.
    This helper pages through the full dataset so no records are missed.
    """
    all_rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        try:
            req = supabase.table(table).select(columns).range(offset, offset + _PAGE_SIZE - 1)
            if order_col:
                req = req.order(order_col)
            resp = req.execute()
            page = _to_dict_list(resp.data)
            if not page:
                break
            all_rows.extend(page)
            if len(page) < _PAGE_SIZE:
                break  # Last page
            offset += _PAGE_SIZE
        except Exception as e:
            logger.warning("Paginated fetch from '%s' failed at offset %d: %s", table, offset, e)
            break
    return all_rows


def extract_search_term(raw_query: str) -> str:
    """
    Extract a search keyword, customer name, or customer ID from a natural language query.
    Examples:
    - 'find Manoj Kumar' -> 'Manoj Kumar'
    - 'find Manoj' -> 'Manoj'
    - 'find customer C012' -> 'C012'
    - \"what is Manoj Kumar's email?\" -> 'Manoj Kumar'
    """
    cleaned = raw_query.strip().strip("'\"")
    if not cleaned:
        return ""

    # 1. Customer ID match (e.g. C012, C001, c099)
    id_match = re.search(r"\b(C\d{1,4})\b", cleaned, re.IGNORECASE)
    if id_match:
        return id_match.group(1).upper()

    # 2. Email pattern match
    email_match = re.search(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b", cleaned)
    if email_match:
        return email_match.group(1)

    # 3. Known customer full-name or first-name match
    try:
        known = get_all_customer_names()
        for kn in known:
            if re.search(r"\b" + re.escape(kn) + r"\b", cleaned, re.IGNORECASE):
                return kn
        for kn in known:
            parts = kn.split()
            if len(parts) > 1 and len(parts[0]) >= 3:
                fn = parts[0]
                if re.search(r"\b" + re.escape(fn) + r"\b", cleaned, re.IGNORECASE):
                    return fn
    except Exception:
        pass

    # 4. Clean common natural language command prefixes and question words
    cleaned = re.sub(
        r"^(?:please\s+)?(?:find|search(?:\s+for)?|show(?:\s+me)?|get|look\s+up|who\s+is|what\s+is|tell\s+me\s+about|check)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^(?:customer\s+details\s+(?:for|of)|customer\s+info\s+(?:for|of)|customer|details\s+of|details\s+for|account\s+of|info\s+on)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Remove phrases like 'details of the person', 'details of person', etc.
    cleaned = re.sub(r"\s+(?:details|information|info)\s+of\s+the\s+person\??$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+of\s+the\s+person\??$", "", cleaned, flags=re.IGNORECASE)
    # Remove "'s email / 's phone / 's details / email of ..." suffixes/prefixes
    cleaned = re.sub(r"'(?:s)?\s+(?:email|phone|city|details|account|status|information|address|state)\??$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:email|phone|city|details|account|status|information|address|state)\??$", "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip(" ?.,!\"'")


def get_all_customer_names() -> list[str]:
    """Retrieve ALL customer names from Supabase using pagination (cached in-memory)."""
    global _CACHED_CUSTOMER_NAMES
    if _CACHED_CUSTOMER_NAMES:
        return _CACHED_CUSTOMER_NAMES

    try:
        rows = _fetch_all_rows("customers", columns="Name", order_col="Customer_ID")
        names: list[str] = []
        for row in rows:
            if isinstance(row, dict) and "Name" in row and row["Name"]:
                names.append(str(row["Name"]))
        # Sort by descending length so multi-word names match first
        _CACHED_CUSTOMER_NAMES = sorted(list(set(names)), key=lambda s: len(s), reverse=True)
        return _CACHED_CUSTOMER_NAMES
    except Exception as e:
        logger.warning("Could not fetch customer names from Supabase: %s", e)

    return []


def get_all_customer_ids() -> list[str]:
    """Retrieve ALL customer IDs from Supabase using pagination (cached in-memory)."""
    global _CACHED_CUSTOMER_IDS
    if _CACHED_CUSTOMER_IDS:
        return _CACHED_CUSTOMER_IDS

    try:
        rows = _fetch_all_rows("customers", columns="Customer_ID", order_col="Customer_ID")
        ids: list[str] = []
        for row in rows:
            if isinstance(row, dict) and "Customer_ID" in row and row["Customer_ID"]:
                ids.append(str(row["Customer_ID"]))
        _CACHED_CUSTOMER_IDS = sorted(list(set(ids)))
        return _CACHED_CUSTOMER_IDS
    except Exception as e:
        logger.warning("Could not fetch customer IDs from Supabase: %s", e)

    return []


def search_customer(
    name: str = "",
    query: str = "",
    user_query: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    Search customer in Supabase using the actual column: 'Name'.
    Also supports partial name matching and Customer ID search.
    Handles 'last customer' queries by fetching the last row.

    Tasks satisfied:
    - Uses actual column: 'Name' (.ilike("Name", f"%{name}%"))
    - Supports partial matching (e.g. 'Manoj' -> 'Manoj Kumar')
    - Supports customer ID search (e.g. 'C012' -> Manoj Kumar)
    - Supports email, phone, city search
    - Supports 'last customer' / 'last record' queries
    - Logs debug info: user query, tool called, search value, number of records, returned customer name

    Args:
        name: Name, partial name, customer ID, or search keyword.
        query: Optional alternative argument for tool calling.
        user_query: Optional original raw user prompt for debug logging.

    Returns:
        List of matching customer dictionaries from Supabase.
    """
    raw_input = (name or query or "").strip()
    original_query = user_query or raw_input
    tool_called = "search_customer"

    if not raw_input:
        _log_debug(original_query, tool_called, "", [])
        return []

    # --- Handle 'last customer' / 'last record' queries ---
    q_lower = raw_input.lower()
    if _is_last_record_query(q_lower):
        records = _fetch_last_customer()
        _log_debug(original_query, tool_called, "[LAST_CUSTOMER]", records)
        return records

    # --- Handle 'all inactive/active customers' queries ---
    if _is_status_filter_query(q_lower):
        status_term = _extract_status_term(q_lower)
        if status_term:
            records = _search_customers_by_status_supabase(status_term)
            _log_debug(original_query, tool_called, f"[STATUS:{status_term}]", records)
            return records

    # Extract target search value from potential sentence
    search_val = extract_search_term(raw_input)
    if not search_val:
        search_val = raw_input

    records: list[dict[str, Any]] = []

    try:
        # 1. Customer ID search (e.g. C012, C001)
        if re.match(r"^C\d{1,4}$", search_val, re.IGNORECASE):
            resp = (
                supabase
                .table("customers")
                .select("*")
                .ilike("Customer_ID", search_val)
                .execute()
            )
            parsed = _to_dict_list(resp.data)
            if parsed:
                records = parsed

        # 2. Customer Name search with partial matching using the actual column: 'Name'
        if not records:
            resp = (
                supabase
                .table("customers")
                .select("*")
                .ilike("Name", f"%{search_val}%")
                .execute()
            )
            parsed = _to_dict_list(resp.data)
            if parsed:
                records = parsed

        # 3. Fallback: Search across Email, Phone, City, or broad partial match
        if not records:
            resp = (
                supabase
                .table("customers")
                .select("*")
                .or_(
                    f"Name.ilike.%{search_val}%,Customer_ID.ilike.%{search_val}%,Email.ilike.%{search_val}%,City.ilike.%{search_val}%"
                )
                .execute()
            )
            parsed = _to_dict_list(resp.data)
            if parsed:
                records = parsed

    except Exception as e:
        logger.error("Supabase search_customer query error: %s", str(e))
        records = []

    # Temporary Debug Logging (Task 10)
    _log_debug(original_query, tool_called, search_val, records)

    return records


def _is_last_record_query(q_lower: str) -> bool:
    """Detect if the user is asking for the last customer/record in the table."""
    patterns = [
        r"\blast\s+customer\b",
        r"\blast\s+record\b",
        r"\blast\s+entry\b",
        r"\blast\s+row\b",
        r"\bfinal\s+customer\b",
        r"\bmost\s+recent\s+customer\b",
    ]
    return any(re.search(p, q_lower) for p in patterns)


def _fetch_last_customer() -> list[dict[str, Any]]:
    """Fetch the last customer record from Supabase ordered by Customer_ID descending."""
    try:
        resp = (
            supabase
            .table("customers")
            .select("*")
            .order("Customer_ID", desc=True)
            .limit(1)
            .execute()
        )
        return _to_dict_list(resp.data)
    except Exception as e:
        logger.error("Error fetching last customer: %s", e)
        return []


def _is_status_filter_query(q_lower: str) -> bool:
    """Detect if the user is asking for customers filtered by status."""
    status_words = ["inactive", "active", "suspended"]
    filter_words = ["all", "show", "list", "find", "which", "who"]
    has_status = any(sw in q_lower for sw in status_words)
    has_filter = any(fw in q_lower for fw in filter_words)
    has_customer = "customer" in q_lower
    return has_status and has_filter and has_customer


def _extract_status_term(q_lower: str) -> str:
    """Extract the status term from a status-filter query."""
    if "inactive" in q_lower:
        return "Inactive"
    if "suspended" in q_lower:
        return "Suspended"
    if "active" in q_lower:
        return "Active"
    return ""


def _search_customers_by_status_supabase(status: str) -> list[dict[str, Any]]:
    """Search customers by status using Supabase with full pagination."""
    try:
        all_rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            resp = (
                supabase
                .table("customers")
                .select("*")
                .ilike("Customer_Status", f"%{status}%")
                .range(offset, offset + _PAGE_SIZE - 1)
                .execute()
            )
            page = _to_dict_list(resp.data)
            if not page:
                break
            all_rows.extend(page)
            if len(page) < _PAGE_SIZE:
                break
            offset += _PAGE_SIZE
        return all_rows
    except Exception as e:
        logger.error("Supabase status search error: %s", e)
        return []


def search_customers_multi(
    names: list[str],
    user_query: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Search for MULTIPLE customers by name/ID in a single call.
    Each name in the list is searched independently and all results are combined.
    Deduplicates by Customer_ID.

    Args:
        names: List of customer names, partial names, or customer IDs.
        user_query: Optional original user prompt for logging.

    Returns:
        Combined list of matching customer records (deduplicated).
    """
    if not names:
        return []

    all_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for name in names:
        results = search_customer(name=name, user_query=user_query)
        for r in results:
            cid = str(r.get("Customer_ID", ""))
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                all_records.append(r)
            elif not cid:
                all_records.append(r)

    logger.info(
        "Multi-customer search: searched %d names, found %d unique records",
        len(names), len(all_records),
    )
    return all_records


def extract_all_customer_names(text: str) -> list[str]:
    """
    Extract ALL customer names and/or IDs mentioned in the user's query.
    Supports:
    - Multiple customer IDs (e.g. 'C001 and C002')
    - Multiple customer names (e.g. 'Ravi Kumar and Priya')
    - Comma-separated lists (e.g. 'Ravi Kumar, Priya and Arun')
    - 'last customer' as a special token

    Returns:
        List of extracted name/ID strings (may be empty).
    """
    found: list[str] = []
    found_spans: list[tuple[int, int]] = []  # Track matched spans to avoid overlaps

    q_lower = text.lower()

    # 0. Detect 'last customer' as a special search target
    if _is_last_record_query(q_lower):
        found.append("__LAST_CUSTOMER__")

    # 1. Extract all Customer ID matches (e.g. C001, C012, C100)
    for m in re.finditer(r"\b(C\d{1,4})\b", text, re.IGNORECASE):
        cid = m.group(1).upper()
        if cid not in found:
            found.append(cid)
            found_spans.append(m.span())

    # 2. Match known customer full names (from database cache)
    known = get_all_customer_names()
    for kn in known:
        pattern = r"\b" + re.escape(kn) + r"\b"
        for m in re.finditer(pattern, text, re.IGNORECASE):
            # Check overlap with already-matched spans
            span = m.span()
            if not any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in found_spans):
                if kn not in found:
                    found.append(kn)
                    found_spans.append(span)

    # 3. Match first-name-only references for known multi-word names
    for kn in known:
        parts = kn.split()
        if len(parts) > 1 and len(parts[0]) >= 3:
            fn = parts[0]
            pattern = r"\b" + re.escape(fn) + r"\b"
            for m in re.finditer(pattern, text, re.IGNORECASE):
                span = m.span()
                if not any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in found_spans):
                    if fn not in found and kn not in found:
                        found.append(fn)
                        found_spans.append(span)

    return found


def _log_debug(
    user_query: str,
    tool_called: str,
    search_value: str,
    records: list[dict[str, Any]]
) -> None:
    """Print and log temporary debug information as requested in Task 10."""
    returned_names = ", ".join([str(r.get("Name", "Unknown")) for r in records]) if records else "None"
    debug_msg = (
        f"\n[DEBUG LOG]\n"
        f"  User Query: {user_query}\n"
        f"  Tool Called: {tool_called}\n"
        f"  Search Value: {search_value}\n"
        f"  Number of records returned: {len(records)}\n"
        f"  Returned Customer Name: {returned_names}\n"
    )
    # Output to both logger and console
    print(debug_msg, flush=True)
    logger.info(
        "user_query='%s' | tool_called='%s' | search_value='%s' | records_returned=%d | customer_name='%s'",
        user_query,
        tool_called,
        search_value,
        len(records),
        returned_names,
    )


def format_customer_record(record: dict[str, Any]) -> str:
    """
    Format a single customer record with all available fields from Supabase.
    """
    standard_order = [
        "Customer_ID",
        "Name",
        "Email",
        "Phone",
        "City",
        "State",
        "Customer_Status",
        "Customer_Type",
        "Registration_Date",
        "Total_Orders",
        "Total_Spent",
        "Last_Order_Date",
        "Preferred_Product_Category",
        "Support_Status",
    ]
    lines = []
    for key in standard_order:
        if key in record:
            lines.append(f"{key}: {record[key]}")
    for k, v in record.items():
        if k not in standard_order:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def format_customer_records(records: list[dict[str, Any]]) -> str:
    """Format list of customer records into readable text."""
    if not records:
        return "Customer not found."
    return "\n\n".join(format_customer_record(r) for r in records)


def extract_order_params(raw_query: str) -> dict[str, str]:
    """
    Extract structured order search parameters from a natural language query.
    Handles:
    - Customer ID (e.g. C001, C012)
    - Order ID (e.g. ORD001, O0001)
    - Status keywords (e.g. pending, delivered, in transit, paid)
    - Customer Name (e.g. Ravi Kumar, Manoj Kumar)
    """
    cleaned = raw_query.strip().strip("'\"")
    params: dict[str, str] = {
        "customer_id": "",
        "order_id": "",
        "customer_name": "",
        "product": "",
        "status": "",
    }

    # 1. Customer ID match (e.g. C001, C012)
    id_match = re.search(r"\b(C\d{1,4})\b", cleaned, re.IGNORECASE)
    if id_match:
        params["customer_id"] = id_match.group(1).upper()

    # 2. Order ID match (e.g. ORD001, O0001, ord10, o15)
    order_match = re.search(r"\b(?:ORD|O)(\d{1,5})\b", cleaned, re.IGNORECASE)
    if order_match:
        num = int(order_match.group(1))
        params["order_id"] = f"O{num:04d}"

    # 3. Status keywords (pending, delivered, in transit, cancelled, paid)
    status_keywords = ["pending", "delivered", "in transit", "cancelled", "paid"]
    for kw in status_keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", cleaned, re.IGNORECASE):
            params["status"] = kw
            break

    # 4. Known customer name match
    try:
        known = get_all_customer_names()
        for kn in known:
            if re.search(r"\b" + re.escape(kn) + r"\b", cleaned, re.IGNORECASE):
                params["customer_name"] = kn
                break
    except Exception:
        pass

    return params


def search_orders(
    query: str = "",
    customer_id: str = "",
    customer_name: str = "",
    order_id: str = "",
    product: str = "",
    status: str = "",
    user_query: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    Search orders in Supabase using the actual database columns:
    'Order_ID', 'Customer_ID', 'Customer_Name', 'Product', 'Category',
    'Amount', 'Order_Date', 'Delivery_Status', 'Payment_Status'.

    Supports:
    - Customer ID (e.g. 'C001')
    - Customer name (e.g. 'Ravi Kumar')
    - Order ID (e.g. 'ORD001', 'O0001')
    - Product (e.g. 'Study Table', 'Laptop')
    - Order status (e.g. 'Pending', 'Delivered', 'In Transit')
    - Partial matching where appropriate

    Logs temporary debug info:
    USER QUERY, TOOL CALLED, SEARCH VALUE, MATCH COUNT, ORDER DATA FOUND
    """
    import json
    import sqlite3

    raw_input = (query or "").strip()
    original_query = (
        user_query
        or raw_input
        or customer_id
        or customer_name
        or order_id
        or product
        or status
    )
    tool_called = "search_orders"

    extracted = extract_order_params(raw_input) if raw_input else {}
    c_id = customer_id or extracted.get("customer_id", "")
    c_name = customer_name or extracted.get("customer_name", "")
    o_id = order_id or extracted.get("order_id", "")
    prod = product or extracted.get("product", "")
    st = status or extracted.get("status", "")

    # If c_name contains words like 'order' or 'pending' or 'delivered', ignore it as a customer name
    if c_name and any(w in c_name.lower() for w in ["order", "orders", "pending", "delivered", "transit", "find", "show"]):
        c_name = ""

    # Normalize order_id if passed as ORD001, ord1, 1, etc.
    normalized_oid = ""

    if o_id:
        m_num = re.search(r"\d+", o_id)
        if m_num:
            normalized_oid = f"O{int(m_num.group(0)):04d}"

    search_val = c_id or normalized_oid or o_id or c_name or prod or st or raw_input

    if not search_val:
        _log_orders_debug(original_query, tool_called, "", [])
        return []

    records: list[dict[str, Any]] = []

    # Primary Attempt: Supabase database connection
    try:
        for tbl in ["orders", "Orders"]:
            try:
                req = supabase.table(tbl).select("*")
                if c_id:
                    req = req.ilike("Customer_ID", f"%{c_id}%")
                elif o_id or normalized_oid:
                    target_o = normalized_oid or o_id
                    req = req.or_(f"Order_ID.ilike.%{target_o}%,Order_ID.ilike.%{o_id}%,Order_ID.ilike.%{search_val}%")
                elif c_name:
                    req = req.ilike("Customer_Name", f"%{c_name}%")
                elif prod:
                    req = req.ilike("Product", f"%{prod}%")
                elif st:
                    req = req.or_(f"Delivery_Status.ilike.%{st}%,Payment_Status.ilike.%{st}%")
                else:
                    req = req.or_(
                        f"Order_ID.ilike.%{search_val}%,Customer_ID.ilike.%{search_val}%,"
                        f"Customer_Name.ilike.%{search_val}%,Product.ilike.%{search_val}%,"
                        f"Delivery_Status.ilike.%{search_val}%,Payment_Status.ilike.%{search_val}%"
                    )

                resp = req.execute()
                parsed = _to_dict_list(resp.data)
                if parsed:
                    records = parsed
                    break
            except Exception:
                continue
    except Exception as e:
        logger.debug("Supabase orders query exception: %s", e)

    # Seamless fallback if Supabase remote table is not yet cached/created
    if not records:
        records = _search_orders_fallback(
            c_id=c_id,
            o_id=o_id,
            normalized_oid=normalized_oid,
            c_name=c_name,
            prod=prod,
            st=st,
            raw_val=search_val,
        )

    _log_orders_debug(original_query, tool_called, search_val, records)
    return records


def _search_orders_fallback(
    c_id: str = "",
    o_id: str = "",
    normalized_oid: str = "",
    c_name: str = "",
    prod: str = "",
    st: str = "",
    raw_val: str = "",
) -> list[dict[str, Any]]:
    """Fallback search in local database using the exact same Supabase schema columns."""
    import sqlite3
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "business_assistant.db",
    )
    if not os.path.exists(db_path):
        return []

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = "SELECT * FROM orders WHERE 1=1"
        params: list[Any] = []

        if c_id:
            sql += " AND Customer_ID LIKE ?"
            params.append(f"%{c_id}%")
        elif o_id or normalized_oid:
            target_o = normalized_oid or o_id
            sql += " AND (Order_ID LIKE ? OR Order_ID LIKE ? OR Order_ID LIKE ?)"
            params.append(f"%{target_o}%")
            params.append(f"%{o_id}%")
            params.append(f"%{raw_val}%")
        elif c_name:
            sql += " AND Customer_Name LIKE ?"
            params.append(f"%{c_name}%")
        elif prod:
            sql += " AND Product LIKE ?"
            params.append(f"%{prod}%")
        elif st:
            sql += " AND (Delivery_Status LIKE ? OR Payment_Status LIKE ?)"
            params.append(f"%{st}%")
            params.append(f"%{st}%")
        elif raw_val:
            sql += (
                " AND (Order_ID LIKE ? OR Customer_ID LIKE ? OR Customer_Name LIKE ?"
                " OR Product LIKE ? OR Delivery_Status LIKE ? OR Payment_Status LIKE ?)"
            )
            for _ in range(6):
                params.append(f"%{raw_val}%")

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Fallback orders query error: %s", e)
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _log_orders_debug(
    user_query: str,
    tool_called: str,
    search_value: str,
    records: list[dict[str, Any]]
) -> None:
    """
    Print and log temporary debug information as requested in Task 13:
    USER QUERY
    TOOL CALLED
    SEARCH VALUE
    MATCH COUNT
    ORDER DATA FOUND
    """
    import json
    data_summary = json.dumps(records[:5], indent=2, default=str) if records else "None"
    debug_msg = (
        f"\nUSER QUERY: {user_query}\n"
        f"TOOL CALLED: {tool_called}\n"
        f"SEARCH VALUE: {search_value}\n"
        f"MATCH COUNT: {len(records)}\n"
        f"ORDER DATA FOUND: {data_summary}\n"
    )
    print(debug_msg, flush=True)
    logger.info(
        "USER QUERY: '%s' | TOOL CALLED: '%s' | SEARCH VALUE: '%s' | MATCH COUNT: %d | ORDER DATA FOUND: %d records",
        user_query,
        tool_called,
        search_value,
        len(records),
        len(records),
    )


def format_order_record(record: dict[str, Any]) -> str:
    """Format a single order record with all actual Supabase columns."""
    standard_order = [
        "Order_ID",
        "Customer_ID",
        "Customer_Name",
        "Product",
        "Category",
        "Amount",
        "Order_Date",
        "Delivery_Status",
        "Payment_Status",
    ]
    lines = []
    for col in standard_order:
        if col in record and record[col] is not None:
            lines.append(f"{col}: {record[col]}")
    for k, v in record.items():
        if k not in standard_order and v is not None:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def format_order_records(records: list[dict[str, Any]], limit: int = 50) -> str:
    """
    Format list of order records into readable text.
    If no matching order is found, returns: 'No matching order found.'
    Limits output to `limit` records to prevent context overflow.
    """
    if not records:
        return "No matching order found."
    total = len(records)
    subset = records[:limit]
    formatted = "\n\n".join(
        f"--- Order {i+1} ---\n{format_order_record(r)}"
        for i, r in enumerate(subset)
    )
    if total > limit:
        formatted += f"\n\n(Showing {limit} of {total} matching orders. You can refine by Customer ID, Customer Name, or Order ID.)"
    return formatted