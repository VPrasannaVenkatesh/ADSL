"""
Database Migration & Profile Enrichment Script.
Applies:
1. accounts: adds account_classification ('GENUINE', 'SUSPICIOUS', 'MULE', 'COMPROMISED', 'UNKNOWN')
   and aligns account_type ('PERSONAL', 'BUSINESS')
2. Creates personal_profiles and business_profiles tables
3. Seeds rich, contextual accounts: students, salaried employees, freelancers, retired citizens,
   professionals, small business owners, retail shops, restaurants, wholesale, IT, e-commerce, and manufacturing.
"""

import random
from datetime import datetime, date, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from simulator.db_connection import get_all_bank_connections, BANK_NAMES


PERSONAL_OCCUPATIONS = [
    ("Student", 25000, 1500, 2, "LOW"),
    ("Software Engineer", 180000, 15000, 5, "UPPER_MIDDLE"),
    ("Salaried Employee", 80000, 8000, 3, "MIDDLE"),
    ("Freelancer", 120000, 12000, 4, "MIDDLE"),
    ("Retired Teacher", 45000, 4000, 1, "MIDDLE"),
    ("Doctor / Medical Professional", 250000, 25000, 6, "HIGH"),
    ("Chartered Accountant", 200000, 20000, 5, "UPPER_MIDDLE"),
    ("Govt Officer", 95000, 9000, 3, "MIDDLE"),
]

BUSINESS_CATEGORIES = [
    ("Retail Supermarket", 3500000, 45000, 40, "RETAIL"),
    ("Multi-Cuisine Restaurant", 2200000, 28000, 30, "FOOD_HOSPITALITY"),
    ("IT Solutions & Cloud Services", 8500000, 350000, 15, "TECH_SERVICES"),
    ("Wholesale Garments & Textiles", 6000000, 250000, 20, "WHOLESALE"),
    ("E-Commerce Merchant Store", 4500000, 18000, 60, "ECOMMERCE"),
    ("Light Industrial Manufacturing", 9500000, 450000, 12, "MANUFACTURING"),
    ("Logistics & Freight Services", 5200000, 180000, 25, "LOGISTICS"),
]

INDIAN_NAMES = [
    "Aarav Sharma", "Priya Patel", "Vikram Malhotra", "Ananya Rao", "Rahul Verma",
    "Sneha Nair", "Rohan Iyer", "Deepa Nambiar", "Karthik Pillai", "Pooja Hegde",
    "Arjun Sen", "Meera Joshi", "Aditya Deshmukh", "Neha Kulkarni", "Vivek Reddy",
    "Divya Menon", "Sanjay Ghosh", "Kavita Singhal", "Gautam Mehta", "Sunita Jain",
    "Rajesh Gupta", "Nidhi Agarwal", "Manish Tiwari", "Swati Bhatt", "Amitabh Roy"
]

CITIES = ["Chennai", "Bangalore", "Mumbai", "Delhi", "Hyderabad", "Kolkata", "Pune"]


def migrate_and_enrich_bank(bank_name: str, conn: psycopg2.extensions.connection):
    print(f"\n[Migration] Migrating schema and accounts in {bank_name}_db...")
    cur = conn.cursor()

    # 1. Update accounts table schema
    cur.execute("""
        ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_classification VARCHAR NOT NULL DEFAULT 'GENUINE';
    """)

    # 2. Update existing accounts: map SAVINGS -> PERSONAL, CURRENT -> BUSINESS
    cur.execute("""
        UPDATE accounts SET account_type = 'PERSONAL' WHERE account_type IN ('SAVINGS', 'Personal');
        UPDATE accounts SET account_type = 'BUSINESS' WHERE account_type IN ('CURRENT', 'Business');
    """)

    # 3. Create personal_profiles table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS personal_profiles (
            account_id VARCHAR PRIMARY KEY REFERENCES accounts(account_id) ON DELETE CASCADE,
            occupation VARCHAR NOT NULL,
            expected_monthly_volume BIGINT NOT NULL DEFAULT 50000,
            typical_transaction_amount BIGINT NOT NULL DEFAULT 5000,
            expected_daily_tx_count INTEGER NOT NULL DEFAULT 3,
            typical_hours_start INTEGER NOT NULL DEFAULT 8,
            typical_hours_end INTEGER NOT NULL DEFAULT 22,
            income_bracket VARCHAR DEFAULT 'MIDDLE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. Create business_profiles table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS business_profiles (
            account_id VARCHAR PRIMARY KEY REFERENCES accounts(account_id) ON DELETE CASCADE,
            business_name VARCHAR NOT NULL,
            business_category VARCHAR NOT NULL,
            registration_date DATE NOT NULL,
            expected_monthly_turnover BIGINT NOT NULL DEFAULT 1500000,
            avg_transaction_amount BIGINT NOT NULL DEFAULT 150000,
            expected_tx_count INTEGER NOT NULL DEFAULT 25,
            operating_hours_start INTEGER NOT NULL DEFAULT 9,
            operating_hours_end INTEGER NOT NULL DEFAULT 20,
            avg_monthly_credit BIGINT DEFAULT 1500000,
            avg_monthly_debit BIGINT DEFAULT 1400000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # 5. Populate profiles for existing accounts that lack them
    cur.execute("""
        SELECT account_id, account_type, customer_name FROM accounts
        WHERE account_id NOT IN (SELECT account_id FROM personal_profiles)
          AND account_id NOT IN (SELECT account_id FROM business_profiles)
    """)
    existing_rows = cur.fetchall()

    personal_count = 0
    business_count = 0

    for acc_id, acc_type, cust_name in existing_rows:
        if acc_type == 'BUSINESS':
            b_cat, turnover, avg_amt, tx_cnt, sector = random.choice(BUSINESS_CATEGORIES)
            b_name = f"{cust_name.split()[0]} {sector.capitalize()} Pvt Ltd"
            cur.execute("""
                INSERT INTO business_profiles (
                    account_id, business_name, business_category, registration_date,
                    expected_monthly_turnover, avg_transaction_amount, expected_tx_count,
                    operating_hours_start, operating_hours_end, avg_monthly_credit, avg_monthly_debit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 9, 20, %s, %s)
                ON CONFLICT (account_id) DO NOTHING
            """, (
                acc_id, b_name, b_cat, date(2020, 1, 15),
                turnover, avg_amt, tx_cnt, turnover, int(turnover * 0.92)
            ))
            business_count += 1
        else:
            occ, vol, typ_amt, daily_cnt, bracket = random.choice(PERSONAL_OCCUPATIONS)
            cur.execute("""
                INSERT INTO personal_profiles (
                    account_id, occupation, expected_monthly_volume, typical_transaction_amount,
                    expected_daily_tx_count, typical_hours_start, typical_hours_end, income_bracket
                ) VALUES (%s, %s, %s, %s, %s, 8, 22, %s)
                ON CONFLICT (account_id) DO NOTHING
            """, (acc_id, occ, vol, typ_amt, daily_cnt, bracket))
            personal_count += 1

    conn.commit()
    print(f"  [OK] Initial profiles created for existing: {personal_count} personal, {business_count} business.")

    # 6. Check total accounts. If under 600, insert diverse new accounts
    cur.execute("SELECT count(*) FROM accounts")
    total_accs = cur.fetchone()[0]
    to_add = max(0, 600 - total_accs)

    if to_add > 0:
        print(f"  Adding {to_add} diverse new accounts to {bank_name}_db...")
        prefix = f"{bank_name}-"
        for i in range(to_add):
            idx = total_accs + i + 1
            acc_id = f"{prefix}{idx:05d}"
            acc_num = f"{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
            cust_name = f"{random.choice(INDIAN_NAMES)} {i+1}"
            phone = f"98{random.randint(10000000, 99999999)}"
            city = random.choice(CITIES)

            # Realistic account distribution: 70% Personal, 30% Business
            is_biz = random.random() < 0.30
            acc_type = "BUSINESS" if is_biz else "PERSONAL"

            # Classification: 85% GENUINE, 8% SUSPICIOUS, 4% MULE, 3% COMPROMISED
            r_cls = random.random()
            if r_cls < 0.85:
                classification = "GENUINE"
            elif r_cls < 0.93:
                classification = "SUSPICIOUS"
            elif r_cls < 0.97:
                classification = "MULE"
            else:
                classification = "COMPROMISED"

            balance = random.randint(500000, 5000000) if is_biz else random.randint(15000, 250000)
            created_date = date.today() - timedelta(days=random.randint(60, 1200))

            cur.execute("""
                INSERT INTO accounts (
                    account_id, account_number, customer_name, phone_number,
                    account_type, account_classification, current_balance,
                    account_created_date, home_location, account_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
                ON CONFLICT (account_id) DO NOTHING
            """, (acc_id, acc_num, cust_name, phone, acc_type, classification, balance, created_date, city))

            if is_biz:
                b_cat, turnover, avg_amt, tx_cnt, sector = random.choice(BUSINESS_CATEGORIES)
                b_name = f"{cust_name.split()[0]} {sector.capitalize()} Pvt Ltd"
                cur.execute("""
                    INSERT INTO business_profiles (
                        account_id, business_name, business_category, registration_date,
                        expected_monthly_turnover, avg_transaction_amount, expected_tx_count,
                        operating_hours_start, operating_hours_end, avg_monthly_credit, avg_monthly_debit
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 9, 20, %s, %s)
                    ON CONFLICT (account_id) DO NOTHING
                """, (acc_id, b_name, b_cat, created_date, turnover, avg_amt, tx_cnt, turnover, int(turnover * 0.92)))
            else:
                occ, vol, typ_amt, daily_cnt, bracket = random.choice(PERSONAL_OCCUPATIONS)
                cur.execute("""
                    INSERT INTO personal_profiles (
                        account_id, occupation, expected_monthly_volume, typical_transaction_amount,
                        expected_daily_tx_count, typical_hours_start, typical_hours_end, income_bracket
                    ) VALUES (%s, %s, %s, %s, %s, 8, 22, %s)
                    ON CONFLICT (account_id) DO NOTHING
                """, (acc_id, occ, vol, typ_amt, daily_cnt, bracket))

        conn.commit()
        print(f"  [OK] Successfully enriched {bank_name}_db with new diverse accounts.")

    cur.close()


def main():
    print("=" * 70)
    print("  Migrating & Enriching Accounts & Profiles across Bank Databases")
    print("=" * 70)
    conns = get_all_bank_connections()
    for bank_name, conn in conns.items():
        try:
            migrate_and_enrich_bank(bank_name, conn)
        except Exception as e:
            print(f"Error migrating {bank_name}: {e}")
        finally:
            conn.close()
    print("\nAll bank databases successfully migrated and enriched!")


if __name__ == "__main__":
    main()
