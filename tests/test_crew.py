import os
import sys

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")

from agents.business_crew import run_business_crew


request = """
Ravi Kumar has a damaged product.
Analyze the customer request and identify
what business action should be taken.
"""


result = run_business_crew(request)

print("\n")
print("=" * 60)
print("FINAL BUSINESS REPORT")
print("=" * 60)
print(result)