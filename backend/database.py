"""
DCI AI Business Assistant - Database Layer

Provides SQLite relational storage and search for 100 business customer records,
complaints, and support tickets.
Ensures zero hallucinations by grounding all lookups in verified database rows.
"""

import sqlite3
import os
from pathlib import Path
from typing import Any, Optional

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "business_assistant.db"

# Seed dataset of 100 customer records
INITIAL_CUSTOMERS = [
    {"customer_id": "C001", "name": "Ravi Kumar", "email": "ravi.kumar@example.com", "phone": "+91-98765-43210", "status": "Active", "account_type": "Enterprise", "created_at": "2023-01-15"},
    {"customer_id": "C002", "name": "Alice Smith", "email": "alice.smith@example.com", "phone": "+1-555-0102", "status": "Active", "account_type": "Standard", "created_at": "2023-02-20"},
    {"customer_id": "C003", "name": "Bob Jones", "email": "bob.jones@example.com", "phone": "+1-555-0103", "status": "Active", "account_type": "Enterprise", "created_at": "2023-03-10"},
    {"customer_id": "C004", "name": "Charlie Brown", "email": "charlie.brown@example.com", "phone": "+1-555-0104", "status": "Inactive", "account_type": "Standard", "created_at": "2023-04-05"},
    {"customer_id": "C005", "name": "Priya Sharma", "email": "priya.sharma@example.com", "phone": "+91-98765-43211", "status": "Active", "account_type": "Enterprise", "created_at": "2023-04-18"},
    {"customer_id": "C006", "name": "Arun Patel", "email": "arun.patel@example.com", "phone": "+91-98765-43212", "status": "Inactive", "account_type": "Standard", "created_at": "2023-05-02"},
    {"customer_id": "C007", "name": "David Miller", "email": "david.miller@example.com", "phone": "+1-555-0107", "status": "Active", "account_type": "Premium", "created_at": "2023-05-15"},
    {"customer_id": "C008", "name": "Emily Davis", "email": "emily.davis@example.com", "phone": "+1-555-0108", "status": "Active", "account_type": "Standard", "created_at": "2023-05-28"},
    {"customer_id": "C009", "name": "Fatima Al-Sayed", "email": "fatima.alsayed@example.com", "phone": "+971-50-123456", "status": "Active", "account_type": "Enterprise", "created_at": "2023-06-11"},
    {"customer_id": "C010", "name": "George Clark", "email": "george.clark@example.com", "phone": "+44-20-7946-0100", "status": "Active", "account_type": "Standard", "created_at": "2023-06-25"},
    {"customer_id": "C011", "name": "Hannah Abbott", "email": "hannah.abbott@example.com", "phone": "+44-20-7946-0101", "status": "Active", "account_type": "Standard", "created_at": "2023-07-04"},
    {"customer_id": "C012", "name": "Ian Wright", "email": "ian.wright@example.com", "phone": "+44-20-7946-0102", "status": "Inactive", "account_type": "Standard", "created_at": "2023-07-19"},
    {"customer_id": "C013", "name": "Jasmine Kaur", "email": "jasmine.kaur@example.com", "phone": "+91-98765-43213", "status": "Active", "account_type": "Enterprise", "created_at": "2023-08-01"},
    {"customer_id": "C014", "name": "Kevin Zhao", "email": "kevin.zhao@example.com", "phone": "+1-555-0114", "status": "Inactive", "account_type": "Standard", "created_at": "2023-08-14"},
    {"customer_id": "C015", "name": "Laura Chen", "email": "laura.chen@example.com", "phone": "+1-555-0115", "status": "Active", "account_type": "Premium", "created_at": "2023-08-29"},
    {"customer_id": "C016", "name": "Mohammed Ali", "email": "mohammed.ali@example.com", "phone": "+971-50-234567", "status": "Active", "account_type": "Standard", "created_at": "2023-09-10"},
    {"customer_id": "C017", "name": "Nina Dobrev", "email": "nina.dobrev@example.com", "phone": "+1-555-0117", "status": "Active", "account_type": "Enterprise", "created_at": "2023-09-22"},
    {"customer_id": "C018", "name": "Oscar Vance", "email": "oscar.vance@example.com", "phone": "+1-555-0118", "status": "Inactive", "account_type": "Standard", "created_at": "2023-10-05"},
    {"customer_id": "C019", "name": "Peter Pan", "email": "peter.pan@example.com", "phone": "+44-20-7946-0103", "status": "Active", "account_type": "Standard", "created_at": "2023-10-18"},
    {"customer_id": "C020", "name": "Rachel Green", "email": "rachel.green@example.com", "phone": "+1-555-0120", "status": "Inactive", "account_type": "Standard", "created_at": "2023-10-31"},
    {"customer_id": "C021", "name": "Suresh Sharma", "email": "suresh.sharma@example.com", "phone": "+91-98765-43214", "status": "Active", "account_type": "Enterprise", "created_at": "2023-11-12"},
    {"customer_id": "C022", "name": "Tara Singh", "email": "tara.singh@example.com", "phone": "+91-98765-43215", "status": "Active", "account_type": "Standard", "created_at": "2023-11-25"},
    {"customer_id": "C023", "name": "Uma Thurman", "email": "uma.thurman@example.com", "phone": "+1-555-0123", "status": "Active", "account_type": "Premium", "created_at": "2023-12-08"},
    {"customer_id": "C024", "name": "Victor Hugo", "email": "victor.hugo@example.com", "phone": "+33-1-4268-0124", "status": "Inactive", "account_type": "Standard", "created_at": "2023-12-20"},
    {"customer_id": "C025", "name": "Wendy Darling", "email": "wendy.darling@example.com", "phone": "+44-20-7946-0104", "status": "Active", "account_type": "Enterprise", "created_at": "2024-01-05"},
    {"customer_id": "C026", "name": "Xavier Woods", "email": "xavier.woods@example.com", "phone": "+1-555-0126", "status": "Active", "account_type": "Standard", "created_at": "2024-01-18"},
    {"customer_id": "C027", "name": "Yasmin Khan", "email": "yasmin.khan@example.com", "phone": "+91-98765-43216", "status": "Active", "account_type": "Premium", "created_at": "2024-02-01"},
    {"customer_id": "C028", "name": "Zachary Taylor", "email": "zachary.taylor@example.com", "phone": "+1-555-0128", "status": "Active", "account_type": "Standard", "created_at": "2024-02-14"},
    {"customer_id": "C029", "name": "Aarav Gupta", "email": "aarav.gupta@example.com", "phone": "+91-98765-43217", "status": "Active", "account_type": "Enterprise", "created_at": "2024-02-27"},
    {"customer_id": "C030", "name": "Bella Swan", "email": "bella.swan@example.com", "phone": "+1-555-0130", "status": "Inactive", "account_type": "Standard", "created_at": "2024-03-10"},
    {"customer_id": "C031", "name": "Carlos Gomez", "email": "carlos.gomez@example.com", "phone": "+34-91-123-4567", "status": "Active", "account_type": "Standard", "created_at": "2024-03-22"},
    {"customer_id": "C032", "name": "Deepika Padukone", "email": "deepika.p@example.com", "phone": "+91-98765-43218", "status": "Active", "account_type": "Enterprise", "created_at": "2024-04-04"},
    {"customer_id": "C033", "name": "Edward Cullen", "email": "edward.cullen@example.com", "phone": "+1-555-0133", "status": "Active", "account_type": "Premium", "created_at": "2024-04-17"},
    {"customer_id": "C034", "name": "Fiona Gallagher", "email": "fiona.g@example.com", "phone": "+1-555-0134", "status": "Inactive", "account_type": "Standard", "created_at": "2024-04-30"},
    {"customer_id": "C035", "name": "Gaurav Verma", "email": "gaurav.verma@example.com", "phone": "+91-98765-43219", "status": "Active", "account_type": "Enterprise", "created_at": "2024-05-12"},
    {"customer_id": "C036", "name": "Harper Lee", "email": "harper.lee@example.com", "phone": "+1-555-0136", "status": "Active", "account_type": "Standard", "created_at": "2024-05-25"},
    {"customer_id": "C037", "name": "Ishaan Roy", "email": "ishaan.roy@example.com", "phone": "+91-98765-43220", "status": "Active", "account_type": "Standard", "created_at": "2024-06-07"},
    {"customer_id": "C038", "name": "Jessica Pearson", "email": "jessica.p@example.com", "phone": "+1-555-0138", "status": "Active", "account_type": "Enterprise", "created_at": "2024-06-20"},
    {"customer_id": "C039", "name": "Karan Mehra", "email": "karan.mehra@example.com", "phone": "+91-98765-43221", "status": "Inactive", "account_type": "Standard", "created_at": "2024-07-02"},
    {"customer_id": "C040", "name": "Lily Evans", "email": "lily.evans@example.com", "phone": "+44-20-7946-0105", "status": "Active", "account_type": "Premium", "created_at": "2024-07-15"},
    {"customer_id": "C041", "name": "Manish Tiwari", "email": "manish.tiwari@example.com", "phone": "+91-98765-43222", "status": "Active", "account_type": "Standard", "created_at": "2024-07-28"},
    {"customer_id": "C042", "name": "Nora Fatehi", "email": "nora.fatehi@example.com", "phone": "+91-98765-43223", "status": "Active", "account_type": "Enterprise", "created_at": "2024-08-10"},
    {"customer_id": "C043", "name": "Oliver Queen", "email": "oliver.queen@example.com", "phone": "+1-555-0143", "status": "Active", "account_type": "Enterprise", "created_at": "2024-08-22"},
    {"customer_id": "C044", "name": "Pooja Hegde", "email": "pooja.hegde@example.com", "phone": "+91-98765-43224", "status": "Inactive", "account_type": "Standard", "created_at": "2024-09-04"},
    {"customer_id": "C045", "name": "Quentin Tarantino", "email": "quentin.t@example.com", "phone": "+1-555-0145", "status": "Active", "account_type": "Premium", "created_at": "2024-09-17"},
    {"customer_id": "C046", "name": "Rohan Joshi", "email": "rohan.joshi@example.com", "phone": "+91-98765-43225", "status": "Active", "account_type": "Standard", "created_at": "2024-09-29"},
    {"customer_id": "C047", "name": "Samantha Ruth", "email": "samantha.ruth@example.com", "phone": "+91-98765-43226", "status": "Active", "account_type": "Enterprise", "created_at": "2024-10-12"},
    {"customer_id": "C048", "name": "Tom Holland", "email": "tom.holland@example.com", "phone": "+44-20-7946-0106", "status": "Active", "account_type": "Standard", "created_at": "2024-10-25"},
    {"customer_id": "C049", "name": "Utkarsh Sinha", "email": "utkarsh.sinha@example.com", "phone": "+91-98765-43227", "status": "Inactive", "account_type": "Standard", "created_at": "2024-11-06"},
    {"customer_id": "C050", "name": "Violet Baudelaire", "email": "violet.b@example.com", "phone": "+1-555-0150", "status": "Active", "account_type": "Enterprise", "created_at": "2024-11-19"},
    {"customer_id": "C051", "name": "William Shakespeare", "email": "william.s@example.com", "phone": "+44-20-7946-0107", "status": "Active", "account_type": "Premium", "created_at": "2024-12-01"},
    {"customer_id": "C052", "name": "Xena Warrior", "email": "xena.w@example.com", "phone": "+1-555-0152", "status": "Active", "account_type": "Standard", "created_at": "2024-12-14"},
    {"customer_id": "C053", "name": "Yuvraj Singh", "email": "yuvraj.singh@example.com", "phone": "+91-98765-43228", "status": "Active", "account_type": "Enterprise", "created_at": "2024-12-27"},
    {"customer_id": "C054", "name": "Zoe Saldana", "email": "zoe.saldana@example.com", "phone": "+1-555-0154", "status": "Inactive", "account_type": "Standard", "created_at": "2025-01-08"},
    {"customer_id": "C055", "name": "Ajay Devgn", "email": "ajay.devgn@example.com", "phone": "+91-98765-43229", "status": "Active", "account_type": "Enterprise", "created_at": "2025-01-20"},
    {"customer_id": "C056", "name": "Barry Allen", "email": "barry.allen@example.com", "phone": "+1-555-0156", "status": "Active", "account_type": "Standard", "created_at": "2025-02-02"},
    {"customer_id": "C057", "name": "Clara Oswald", "email": "clara.oswald@example.com", "phone": "+44-20-7946-0108", "status": "Active", "account_type": "Premium", "created_at": "2025-02-15"},
    {"customer_id": "C058", "name": "Divya Khosla", "email": "divya.khosla@example.com", "phone": "+91-98765-43230", "status": "Inactive", "account_type": "Standard", "created_at": "2025-02-27"},
    {"customer_id": "C059", "name": "Ethan Hunt", "email": "ethan.hunt@example.com", "phone": "+1-555-0159", "status": "Active", "account_type": "Enterprise", "created_at": "2025-03-11"},
    {"customer_id": "C060", "name": "Farhan Akhtar", "email": "farhan.akhtar@example.com", "phone": "+91-98765-43231", "status": "Active", "account_type": "Standard", "created_at": "2025-03-24"},
    {"customer_id": "C061", "name": "Grace Kelly", "email": "grace.kelly@example.com", "phone": "+1-555-0161", "status": "Active", "account_type": "Premium", "created_at": "2025-04-05"},
    {"customer_id": "C062", "name": "Harsh Vardhan", "email": "harsh.v@example.com", "phone": "+91-98765-43232", "status": "Inactive", "account_type": "Standard", "created_at": "2025-04-18"},
    {"customer_id": "C063", "name": "Iris West", "email": "iris.west@example.com", "phone": "+1-555-0163", "status": "Active", "account_type": "Standard", "created_at": "2025-05-01"},
    {"customer_id": "C064", "name": "Jitendra Kumar", "email": "jitendra.k@example.com", "phone": "+91-98765-43233", "status": "Active", "account_type": "Enterprise", "created_at": "2025-05-14"},
    {"customer_id": "C065", "name": "Katrina Kaif", "email": "katrina.kaif@example.com", "phone": "+91-98765-43234", "status": "Active", "account_type": "Enterprise", "created_at": "2025-05-27"},
    {"customer_id": "C066", "name": "Lucas Scott", "email": "lucas.scott@example.com", "phone": "+1-555-0166", "status": "Inactive", "account_type": "Standard", "created_at": "2025-06-08"},
    {"customer_id": "C067", "name": "Meera Rajput", "email": "meera.rajput@example.com", "phone": "+91-98765-43235", "status": "Active", "account_type": "Standard", "created_at": "2025-06-21"},
    {"customer_id": "C068", "name": "Nathan Drake", "email": "nathan.drake@example.com", "phone": "+1-555-0168", "status": "Active", "account_type": "Premium", "created_at": "2025-07-03"},
    {"customer_id": "C069", "name": "Omkar Nath", "email": "omkar.nath@example.com", "phone": "+91-98765-43236", "status": "Active", "account_type": "Standard", "created_at": "2025-07-16"},
    {"customer_id": "C070", "name": "Pam Beesly", "email": "pam.beesly@example.com", "phone": "+1-555-0170", "status": "Inactive", "account_type": "Standard", "created_at": "2025-07-29"},
    {"customer_id": "C071", "name": "Qasim Sheikh", "email": "qasim.sheikh@example.com", "phone": "+971-50-345678", "status": "Active", "account_type": "Enterprise", "created_at": "2025-08-10"},
    {"customer_id": "C072", "name": "Rhea Chakraborty", "email": "rhea.c@example.com", "phone": "+91-98765-43237", "status": "Active", "account_type": "Standard", "created_at": "2025-08-22"},
    {"customer_id": "C073", "name": "Steve Rogers", "email": "steve.rogers@example.com", "phone": "+1-555-0173", "status": "Active", "account_type": "Enterprise", "created_at": "2025-09-04"},
    {"customer_id": "C074", "name": "Tanmay Bhat", "email": "tanmay.bhat@example.com", "phone": "+91-98765-43238", "status": "Active", "account_type": "Premium", "created_at": "2025-09-17"},
    {"customer_id": "C075", "name": "Urvashi Rautela", "email": "urvashi.r@example.com", "phone": "+91-98765-43239", "status": "Inactive", "account_type": "Standard", "created_at": "2025-09-29"},
    {"customer_id": "C076", "name": "Varun Dhawan", "email": "varun.dhawan@example.com", "phone": "+91-98765-43240", "status": "Active", "account_type": "Enterprise", "created_at": "2025-10-12"},
    {"customer_id": "C077", "name": "Wanda Maximoff", "email": "wanda.m@example.com", "phone": "+1-555-0177", "status": "Active", "account_type": "Enterprise", "created_at": "2025-10-24"},
    {"customer_id": "C078", "name": "Xander Cage", "email": "xander.cage@example.com", "phone": "+1-555-0178", "status": "Inactive", "account_type": "Standard", "created_at": "2025-11-05"},
    {"customer_id": "C079", "name": "Yami Gautam", "email": "yami.gautam@example.com", "phone": "+91-98765-43241", "status": "Active", "account_type": "Standard", "created_at": "2025-11-18"},
    {"customer_id": "C080", "name": "Zack Snyder", "email": "zack.snyder@example.com", "phone": "+1-555-0180", "status": "Active", "account_type": "Premium", "created_at": "2025-11-30"},
    {"customer_id": "C081", "name": "Ananya Panday", "email": "ananya.p@example.com", "phone": "+91-98765-43242", "status": "Active", "account_type": "Enterprise", "created_at": "2025-12-12"},
    {"customer_id": "C082", "name": "Bruce Wayne", "email": "bruce.wayne@example.com", "phone": "+1-555-0182", "status": "Active", "account_type": "Enterprise", "created_at": "2025-12-24"},
    {"customer_id": "C083", "name": "Chandler Bing", "email": "chandler.bing@example.com", "phone": "+1-555-0183", "status": "Inactive", "account_type": "Standard", "created_at": "2026-01-05"},
    {"customer_id": "C084", "name": "Disha Patani", "email": "disha.patani@example.com", "phone": "+91-98765-43243", "status": "Active", "account_type": "Standard", "created_at": "2026-01-17"},
    {"customer_id": "C085", "name": "Elon Vance", "email": "elon.vance@example.com", "phone": "+1-555-0185", "status": "Active", "account_type": "Premium", "created_at": "2026-01-29"},
    {"customer_id": "C086", "name": "Freida Pinto", "email": "freida.pinto@example.com", "phone": "+91-98765-43244", "status": "Active", "account_type": "Enterprise", "created_at": "2026-02-10"},
    {"customer_id": "C087", "name": "Gokul Nath", "email": "gokul.nath@example.com", "phone": "+91-98765-43245", "status": "Inactive", "account_type": "Standard", "created_at": "2026-02-21"},
    {"customer_id": "C088", "name": "Hermione Granger", "email": "hermione.g@example.com", "phone": "+44-20-7946-0109", "status": "Active", "account_type": "Premium", "created_at": "2026-03-04"},
    {"customer_id": "C089", "name": "Irfan Pathan", "email": "irfan.pathan@example.com", "phone": "+91-98765-43246", "status": "Active", "account_type": "Standard", "created_at": "2026-03-16"},
    {"customer_id": "C090", "name": "Joey Tribbiani", "email": "joey.t@example.com", "phone": "+1-555-0190", "status": "Inactive", "account_type": "Standard", "created_at": "2026-03-27"},
    {"customer_id": "C091", "name": "Kriti Sanon", "email": "kriti.sanon@example.com", "phone": "+91-98765-43247", "status": "Active", "account_type": "Enterprise", "created_at": "2026-04-08"},
    {"customer_id": "C092", "name": "Leonardo DiCaprio", "email": "leo.d@example.com", "phone": "+1-555-0192", "status": "Active", "account_type": "Premium", "created_at": "2026-04-19"},
    {"customer_id": "C093", "name": "Madhuri Dixit", "email": "madhuri.d@example.com", "phone": "+91-98765-43248", "status": "Active", "account_type": "Enterprise", "created_at": "2026-04-30"},
    {"customer_id": "C094", "name": "Neville Longbottom", "email": "neville.l@example.com", "phone": "+44-20-7946-0110", "status": "Inactive", "account_type": "Standard", "created_at": "2026-05-11"},
    {"customer_id": "C095", "name": "Oprah Winfrey", "email": "oprah.w@example.com", "phone": "+1-555-0195", "status": "Active", "account_type": "Enterprise", "created_at": "2026-05-22"},
    {"customer_id": "C096", "name": "Pankaj Tripathi", "email": "pankaj.t@example.com", "phone": "+91-98765-43249", "status": "Active", "account_type": "Premium", "created_at": "2026-06-02"},
    {"customer_id": "C097", "name": "Queen Latifah", "email": "queen.l@example.com", "phone": "+1-555-0197", "status": "Active", "account_type": "Standard", "created_at": "2026-06-13"},
    {"customer_id": "C098", "name": "Ranveer Singh", "email": "ranveer.singh@example.com", "phone": "+91-98765-43250", "status": "Active", "account_type": "Enterprise", "created_at": "2026-06-24"},
    {"customer_id": "C099", "name": "Sherlock Holmes", "email": "sherlock.h@example.com", "phone": "+44-20-7946-0111", "status": "Active", "account_type": "Enterprise", "created_at": "2026-07-05"},
    {"customer_id": "C100", "name": "Zubair Ahmed", "email": "zubair.ahmed@example.com", "phone": "+91-98765-43251", "status": "Inactive", "account_type": "Standard", "created_at": "2026-07-16"},
]

INITIAL_COMPLAINTS = [
    {"complaint_id": "CMP101", "customer_id": "C001", "customer_name": "Ravi Kumar", "issue": "Damaged product", "status": "Open", "date": "2026-08-10"},
    {"complaint_id": "CMP102", "customer_id": "C002", "customer_name": "Alice Smith", "issue": "Delayed delivery for invoice #INV-2024", "status": "Under Review", "date": "2026-08-12"},
    {"complaint_id": "CMP103", "customer_id": "C003", "customer_name": "Bob Jones", "issue": "Incorrect charge on subscription renewal", "status": "Resolved", "date": "2026-08-14"},
    {"complaint_id": "CMP104", "customer_id": "C004", "customer_name": "Charlie Brown", "issue": "Account cancellation request", "status": "Closed", "date": "2026-08-15"},
    {"complaint_id": "CMP105", "customer_id": "C007", "customer_name": "David Miller", "issue": "Damaged packaging on arrival", "status": "Open", "date": "2026-08-18"},
    {"complaint_id": "CMP106", "customer_id": "C008", "customer_name": "Emily Davis", "issue": "Billing discrepancy for quarterly service", "status": "Under Review", "date": "2026-08-20"},
    {"complaint_id": "CMP107", "customer_id": "C009", "customer_name": "Fatima Al-Sayed", "issue": "Software license activation key failed", "status": "Open", "date": "2026-08-22"},
    {"complaint_id": "CMP108", "customer_id": "C010", "customer_name": "George Clark", "issue": "Defective component in hardware shipment", "status": "Resolved", "date": "2026-08-25"},
    {"complaint_id": "CMP109", "customer_id": "C013", "customer_name": "Jasmine Kaur", "issue": "Delayed refund processing", "status": "Open", "date": "2026-08-28"},
    {"complaint_id": "CMP110", "customer_id": "C014", "customer_name": "Kevin Zhao", "issue": "Account inactivity warning notice", "status": "Closed", "date": "2026-08-30"},
    {"complaint_id": "CMP111", "customer_id": "C015", "customer_name": "Laura Chen", "issue": "Duplicate transaction charge", "status": "Under Review", "date": "2026-09-02"},
    {"complaint_id": "CMP112", "customer_id": "C016", "customer_name": "Mohammed Ali", "issue": "Product manual missing from order", "status": "Resolved", "date": "2026-09-05"},
    {"complaint_id": "CMP113", "customer_id": "C017", "customer_name": "Nina Dobrev", "issue": "Warranty claim for broken screen", "status": "Open", "date": "2026-09-08"},
    {"complaint_id": "CMP114", "customer_id": "C021", "customer_name": "Suresh Sharma", "issue": "Delivery delayed beyond estimated date", "status": "Open", "date": "2026-09-11"},
    {"complaint_id": "CMP115", "customer_id": "C022", "customer_name": "Tara Singh", "issue": "Subscription auto-renewed without notice", "status": "Resolved", "date": "2026-09-14"},
    {"complaint_id": "CMP116", "customer_id": "C024", "customer_name": "Victor Hugo", "issue": "Service suspension inquiry", "status": "Closed", "date": "2026-09-16"},
    {"complaint_id": "CMP117", "customer_id": "C027", "customer_name": "Yasmin Khan", "issue": "Wrong item variant delivered", "status": "Open", "date": "2026-09-18"},
    {"complaint_id": "CMP118", "customer_id": "C028", "customer_name": "Zachary Taylor", "issue": "Damaged goods during transit", "status": "Under Review", "date": "2026-09-20"},
]


def get_db_connection() -> sqlite3.Connection:
    """Get connection to the persistent SQLite database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Create tables and seed initial 100 customer records and complaints if not present."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    status TEXT NOT NULL,
                    account_type TEXT,
                    created_at TEXT
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    complaint_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    customer_name TEXT NOT NULL,
                    issue TEXT NOT NULL,
                    status TEXT NOT NULL,
                    date TEXT
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    issue TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT
                );
            """)

            # Create search indices for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_complaints_customer_name ON complaints(customer_name);")

            # Check if customers are already seeded
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM customers")
            count = cur.fetchone()[0]

            if count < 100:
                # Seed or refresh the 100 customer records
                for c in INITIAL_CUSTOMERS:
                    conn.execute("""
                        INSERT OR REPLACE INTO customers (customer_id, name, email, phone, status, account_type, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (c["customer_id"], c["name"], c["email"], c["phone"], c["status"], c["account_type"], c["created_at"]))

            # Seed complaints if empty
            cur.execute("SELECT COUNT(*) FROM complaints")
            comp_count = cur.fetchone()[0]
            if comp_count < len(INITIAL_COMPLAINTS):
                for comp in INITIAL_COMPLAINTS:
                    conn.execute("""
                        INSERT OR REPLACE INTO complaints (complaint_id, customer_id, customer_name, issue, status, date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (comp["complaint_id"], comp["customer_id"], comp["customer_name"], comp["issue"], comp["status"], comp["date"]))

    finally:
        conn.close()


def get_customer_by_name(customer_name: str) -> dict[str, Any] | str:
    """
    Search customer data by customer name (exact or partial).
    Returns dictionary with customer details if found, or 'Customer not found.'
    """
    term = customer_name.strip()
    if not term:
        return "Customer not found."

    # Check Supabase first
    try:
        from backend.supabase_client import search_customer as supa_search
        supa_res = supa_search(name=term, user_query=customer_name)
        if supa_res:
            rec = supa_res[0]
            return {
                "customer_id": rec.get("Customer_ID"),
                "name": rec.get("Name"),
                "email": rec.get("Email"),
                "phone": str(rec.get("Phone", "")),
                "status": rec.get("Customer_Status"),
                "account_type": rec.get("Customer_Type"),
                **rec,
            }
    except Exception:
        pass

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        term_lower = term.lower()
        # First try exact match (case-insensitive)
        cur.execute("SELECT * FROM customers WHERE LOWER(name) = ?", (term_lower,))
        row = cur.fetchone()

        if not row:
            # Then try partial match
            cur.execute("SELECT * FROM customers WHERE LOWER(name) LIKE ?", (f"%{term}%",))
            row = cur.fetchone()

        if row:
            return {
                "customer_id": row["customer_id"],
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"],
                "status": row["status"],
                "account_type": row["account_type"],
            }
        return "Customer not found."
    finally:
        conn.close()


def get_complaint_by_customer_name(customer_name: str) -> dict[str, Any] | str:
    """
    Search complaint data by customer name.
    Returns complaint details if found, or 'Complaint not found.'
    """
    term = customer_name.strip().lower()
    if not term:
        return "Complaint not found."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM complaints WHERE LOWER(customer_name) = ?", (term,))
        row = cur.fetchone()

        if not row:
            cur.execute("SELECT * FROM complaints WHERE LOWER(customer_name) LIKE ?", (f"%{term}%",))
            row = cur.fetchone()

        if row:
            return {
                "complaint_id": row["complaint_id"],
                "customer_id": row["customer_id"],
                "customer_name": row["customer_name"],
                "issue": row["issue"],
                "status": row["status"],
                "date": row["date"],
            }
        return "Complaint not found."
    finally:
        conn.close()


def get_customers_by_status(status_val: str) -> list[dict[str, Any]]:
    """
    Filter customers by status (e.g. 'Inactive', 'Active', 'Suspended').
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE LOWER(status) = ? ORDER BY customer_id ASC", (status_val.strip().lower(),))
        rows = cur.fetchall()
        return [
            {
                "customer_id": r["customer_id"],
                "name": r["name"],
                "email": r["email"],
                "status": r["status"],
                "account_type": r["account_type"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_all_customer_names() -> list[str]:
    """Retrieve all customer names from the database for fast recognition."""
    all_names: set[str] = set()

    try:
        from backend.supabase_client import get_all_customer_names as supa_names
        for n in supa_names():
            if n:
                all_names.add(n)
    except Exception:
        pass

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM customers")
        for r in cur.fetchall():
            if r["name"]:
                all_names.add(r["name"])
        return sorted(list(all_names), key=len, reverse=True)
    finally:
        conn.close()


def get_total_customer_count() -> int:
    """Return total number of customer records stored."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM customers")
        return cur.fetchone()[0]
    finally:
        conn.close()


def create_support_ticket(customer_name: str, issue: str) -> dict[str, str]:
    """Insert a support ticket into the database and return ticket details."""
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM tickets")
            ticket_number = cur.fetchone()[0] + 1
            ticket_id = f"T{ticket_number:03d}"

            conn.execute("""
                INSERT INTO tickets (ticket_id, customer_name, issue, status, created_at)
                VALUES (?, ?, ?, 'Open', datetime('now'))
            """, (ticket_id, customer_name, issue))

            return {
                "ticket_id": ticket_id,
                "status": "Open",
            }
    finally:
        conn.close()


# Initialize on import
init_database()
