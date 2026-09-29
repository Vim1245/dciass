import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.supabase_client import supabase

response = (
    supabase
    .table("customers")
    .select("*")
    .limit(5)
    .execute()
)

print("Customer data:")
print(response.data)