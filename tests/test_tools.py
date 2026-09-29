"""
Test script for agents/tools.py
"""

import os
import sys

# Add project root directory to sys.path so the test can import project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.tools import search_customer


def main():
    print("Testing search_customer tool...\n")

    # Test 1: Search for an existing customer
    print("--- Test 1: Existing Customer ('Ravi Kumar') ---")
    result1 = search_customer.invoke("Ravi Kumar")
    print(result1)

    print("\n" + "=" * 40 + "\n")

    # Test 2: Search for an unknown customer
    print("--- Test 2: Unknown Customer ('Unknown Customer') ---")
    result2 = search_customer.invoke("Unknown Customer")
    print(result2)


if __name__ == "__main__":
    main()
