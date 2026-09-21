import os
import sys
import random
import datetime
import uuid
import json
import psycopg2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from simulator.db_connection import get_bank_connection, BANK_NAMES
from risk_engine.aggregator import score_to_level

NAMES = [
    "Aarav Sharma", "Aditya Verma", "Akshay Kumar", "Amitabh Bachchan", "Ananya Banerjee",
    "Ananya Iyer", "Arjun Kumar", "Ayushmann Khurrana", "Divya Krishnan", "Karthik Reddy",
    "Kartik Aaryan", "Meera Nambiar", "Neha Kapoor", "Pooja Joshi", "Prasanna Venkatesh",
    "Priya Gupta", "R. Madhavan", "Rahul Chatterjee", "Rajesh Khanna", "Rajkummar Rao",
    "Ranbir Kapoor", "Ranveer Singh", "Rohan Singh", "Salman Khan", "Sandeep Nair",
    "Shahrukh Khan", "Sneha Desai", "Suriya", "Tiger Shroff", "Varun Dhawan",
    "Vicky Kaushal", "Vijay", "Vikram Patel", "Ajith Kumar", "Dhanush", "Karthi"
]

LOCATIONS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Bengaluru", "Mysuru", "Mangaluru", "Hubballi",
    "Kochi", "Thiruvananthapuram", "Kozhikode",
    "Hyderabad", "Visakhapatnam", "Vijayawada", "Tirupati",
    "Delhi", "Mumbai", "Pune", "Kolkata", "Ahmedabad", "Jaipur",
    "Lucknow", "Chandigarh", "Patna", "Bhopal", "Indore", "Guwahati", "Bhubaneswar"
]

BUSINESS_CATEGORIES = [
    "RETAIL", "ECOMMERCE", "HEALTHCARE", "EDUCATION", "IT_SERVICES",
    "LOGISTICS", "FOOD_BEVERAGE", "CONSTRUCTION", "HOSPITALITY", "FINANCIAL_SERVICES"
]

def generate_phone(bank_idx, acc_num):
    prefix = ['9', '8', '7'][bank_idx % 3]
    return f"{prefix}{bank_idx + 1}{acc_num:08d}"

def expand_accounts_for_bank(bank, bank_idx):
    conn = get_bank_connection(bank)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM accounts")
    current_count = cur.fetchone()[0]
    print(f"[{bank}] Currently has {current_count} accounts.")

    target_count = 1000
    if current_count < target_count:
        accounts_to_add = target_count - current_count
        print(f"[{bank}] Adding {accounts_to_add} accounts ({current_count + 1} to {target_count})...")

        for i in range(current_count + 1, target_count + 1):
            acc_id = f"{bank}-{i:05d}"
            acc_number = f"{random.randint(1000, 9999)}{i:06d}"
            name = random.choice(NAMES)
            phone = generate_phone(bank_idx, i)
            is_business = (random.random() < 0.25)
            acc_type = "CURRENT" if is_business else random.choice(["SAVINGS", "SALARY", "SAVINGS"])
            balance = random.randint(50000, 5000000) if is_business else random.randint(5000, 850000)
            created_days = random.randint(180, 1800)
            created_date = datetime.date.today() - datetime.timedelta(days=created_days)
            location = random.choice(LOCATIONS)
            classification = "BUSINESS" if is_business else "PERSONAL"
            biz_cat = random.choice(BUSINESS_CATEGORIES) if is_business else "NONE"
            tx_range = "50000-500000" if is_business else "500-50000"
            freq = "HIGH" if is_business else "NORMAL"

            cur.execute("""
                INSERT INTO accounts (
                    account_id, account_number, customer_name, phone_number,
                    account_type, current_balance, account_created_date,
                    home_location, account_status, account_classification,
                    business_category, expected_tx_range, tx_frequency_pattern
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, 'ACTIVE', %s,
                    %s, %s, %s
                ) ON CONFLICT (account_id) DO NOTHING
            """, (
                acc_id, acc_number, name, phone,
                acc_type, balance, created_date,
                location, classification,
                biz_cat, tx_range, freq
            ))

        conn.commit()
        cur.execute("SELECT COUNT(*) FROM accounts")
        print(f"[{bank}] Successfully expanded to {cur.fetchone()[0]} accounts.")
    else:
        print(f"[{bank}] Already has {current_count} accounts (>= {target_count}).")

    cur.close()
    conn.close()

def recalibrate_and_backfill_risk(bank):
    conn = get_bank_connection(bank)
    cur = conn.cursor()
    print(f"\n[{bank}] Recalibrating existing risk assessment scores and levels...")

    # Fetch existing assessments
    cur.execute("""
        SELECT assessment_id, amount_risk, velocity_risk, behaviour_deviation_risk,
               device_risk, location_risk, counterparty_risk, timing_risk, network_pattern_risk
        FROM risk_assessments
    """)
    rows = cur.fetchall()
    print(f"[{bank}] Found {len(rows)} assessments to recalibrate.")

    updates = []
    for r in rows:
        ass_id = r[0]
        scores = [float(s or 0.0) for s in r[1:]]
        # weights: 0.18, 0.18, 0.14, 0.08, 0.08, 0.12, 0.05, 0.17
        weights = [0.18, 0.18, 0.14, 0.08, 0.08, 0.12, 0.05, 0.17]
        base_score = sum(s * w for s, w in zip(scores, weights))

        severe_count = sum(1 for s in scores if s >= 45.0)
        critical_count = sum(1 for s in scores if s >= 65.0)
        peak_score = max(scores) if scores else 0.0

        if critical_count >= 2:
            boosted = max(base_score * 1.5, base_score * 0.45 + peak_score * 0.55)
            final = boosted + 10.0 * (critical_count - 1)
        elif severe_count >= 2:
            final = max(base_score * 1.25, base_score * 0.6 + peak_score * 0.4)
        elif peak_score >= 80.0:
            final = max(base_score, peak_score * 0.75)
        else:
            final = base_score

        final = round(min(100.0, max(0.0, final)), 2)
        lvl = score_to_level(final)
        updates.append((final, lvl, ass_id))

    # Batch update
    from psycopg2.extras import execute_batch
    execute_batch(cur, """
        UPDATE risk_assessments
        SET final_risk_score = %s, risk_level = %s
        WHERE assessment_id = %s
    """, updates, page_size=1000)
    conn.commit()

    cur.execute("""
        SELECT risk_level, COUNT(*), MIN(final_risk_score), MAX(final_risk_score)
        FROM risk_assessments
        GROUP BY risk_level
    """)
    print(f"[{bank}] Recalibrated risk breakdown:")
    for row in cur.fetchall():
        print(f"   {row[0]}: {row[1]} (Score Range: {row[2]} - {row[3]})")

    cur.close()
    conn.close()

if __name__ == "__main__":
    print("=== BANK DATABASE EXPANSION & RISK RECALIBRATION ===")
    for idx, bank in enumerate(BANK_NAMES):
        expand_accounts_for_bank(bank, idx)
        recalibrate_and_backfill_risk(bank)
    print("\n=== ALL BANKS UPDATED SUCCESSFULLY ===")
