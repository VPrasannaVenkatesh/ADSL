import os
import sys
import random
import datetime

# Add parent directory to path to import database modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection
import psycopg2

BANKS = ["SBI", "AXIS", "IOB"]

NAMES = [
    "Arjun Kumar", "Prasanna Venkatesh", "Karthik Reddy", "Sandeep Nair", 
    "Ananya Iyer", "Divya Krishnan", "Aarav Sharma", "Rohan Singh", 
    "Aditya Verma", "Priya Gupta", "Neha Kapoor", "Ananya Banerjee",
    "Vikram Patel", "Sneha Desai", "Rahul Chatterjee", "Pooja Joshi",
    "Rajesh Khanna", "Amitabh Bachchan", "Shahrukh Khan", "Salman Khan",
    "Akshay Kumar", "Ajay Devgn", "Hrithik Roshan", "Ranbir Kapoor",
    "Ranveer Singh", "Varun Dhawan", "Tiger Shroff", "Ayushmann Khurrana",
    "Rajkummar Rao", "Vicky Kaushal", "Kartik Aaryan", "Sushant Singh Rajput",
    "R. Madhavan", "Suriya", "Vijay", "Ajith Kumar", "Dhanush", "Karthi"
]

LOCATIONS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Bengaluru", "Mysuru", "Mangaluru", "Hubballi",
    "Kochi", "Thiruvananthapuram", "Kozhikode",
    "Hyderabad", "Visakhapatnam", "Vijayawada", "Tirupati",
    "Delhi", "Mumbai", "Pune", "Kolkata", "Ahmedabad", "Jaipur", 
    "Lucknow", "Chandigarh", "Patna", "Bhopal", "Indore", "Guwahati", "Bhubaneswar"
]

def generate_phone():
    prefix = random.choice(['6', '7', '8', '9'])
    return prefix + "".join([str(random.randint(0, 9)) for _ in range(9)])

def generate_name():
    first = random.choice([n.split()[0] for n in NAMES])
    last = random.choice([n.split()[-1] for n in NAMES if len(n.split()) > 1])
    return f"{first} {last}"

def update_db(bank):
    print(f"\n--- Updating {bank} Database ---")
    conn = get_connection(bank)
    cursor = conn.cursor()
    
    # 1. Add column if not exists
    cursor.execute("""
        ALTER TABLE accounts 
        ADD COLUMN IF NOT EXISTS phone_number VARCHAR(15);
    """)
    conn.commit()
    
    # 2. Get all accounts and their earliest transaction dates
    cursor.execute("""
        SELECT a.account_id, MIN(t.transaction_timestamp) 
        FROM accounts a
        LEFT JOIN transactions t ON a.account_id = t.sender_account_id OR a.account_id = t.receiver_account_id
        GROUP BY a.account_id
    """)
    accounts = cursor.fetchall()
    
    # 3. Update each account
    used_phones = set()
    update_count = 0
    
    for account_id, min_tx_time in accounts:
        # Generate unique phone
        phone = generate_phone()
        while phone in used_phones:
            phone = generate_phone()
        used_phones.add(phone)
        
        name = generate_name()
        loc = random.choice(LOCATIONS)
        
        # Calculate new created date
        if min_tx_time:
            # Earliest tx exists, ensure created date is before it (between 30 and 1000 days before)
            created_date = (min_tx_time - datetime.timedelta(days=random.randint(30, 1000))).date()
        else:
            # No transactions, random date in last 3 years
            created_date = datetime.date.today() - datetime.timedelta(days=random.randint(30, 1000))
            
        cursor.execute("""
            UPDATE accounts 
            SET customer_name = %s, phone_number = %s, home_location = %s, account_created_date = %s
            WHERE account_id = %s
        """, (name, phone, loc, created_date, account_id))
        update_count += 1
        
    # Apply unique constraint to phone_number now that all are populated
    try:
        cursor.execute("""
            ALTER TABLE accounts ADD CONSTRAINT unique_phone_number UNIQUE (phone_number);
        """)
        conn.commit()
    except psycopg2.errors.DuplicateTable:
        conn.rollback()
    except psycopg2.errors.DuplicateObject:
        conn.rollback()
    except Exception as e:
        conn.rollback()
        try:
            cursor.execute("ALTER TABLE accounts ADD UNIQUE (phone_number);")
            conn.commit()
        except:
            conn.rollback()
    
    # Also enforce NOT NULL now
    try:
        cursor.execute("ALTER TABLE accounts ALTER COLUMN phone_number SET NOT NULL;")
        conn.commit()
    except Exception:
        conn.rollback()
    
    print(f"Updated {update_count} accounts in {bank}_DB")
    
    # Run Verification queries
    print(f"Verification Stats for {bank}_DB:")
    cursor.execute("SELECT COUNT(*) FROM accounts")
    print(f"  Total accounts: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE customer_name IS NOT NULL AND customer_name != '' AND customer_name NOT LIKE 'Customer_%'")
    print(f"  Accounts with realistic names: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE phone_number IS NOT NULL")
    print(f"  Accounts with phones: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(DISTINCT phone_number) FROM accounts")
    print(f"  Unique phone numbers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(DISTINCT home_location) FROM accounts")
    print(f"  Unique locations: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT MIN(account_created_date), MAX(account_created_date) FROM accounts")
    res = cursor.fetchone()
    print(f"  Oldest account: {res[0]}")
    print(f"  Newest account: {res[1]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    for bank in BANKS:
        update_db(bank)
