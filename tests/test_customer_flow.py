import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.supabase_client import search_customer, format_customer_records

queries = [
    "find Manoj Kumar",
    "find Manoj",
    "find customer C012",
    "what is Manoj Kumar's email?"
]

for q in queries:
    print(f"\n>>> TESTING QUERY: '{q}'")
    results = search_customer(name=q, user_query=q)
    print(f"Results Count: {len(results)}")
    if results:
        print("First Result Formatted:")
        print(format_customer_records([results[0]]))
    else:
        print("No results found.")
    print("-" * 60)
