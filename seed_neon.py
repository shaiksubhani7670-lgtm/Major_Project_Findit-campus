"""
seed_neon.py - Seeds a Neon PostgreSQL database with all students and accounts from the local SQLite DB.
Usage: python seed_neon.py <NEON_DATABASE_URL>
Example: python seed_neon.py "postgresql://user:pass@host.neon.tech/dbname?sslmode=require"
"""

import sys
import os
import sqlite3
import psycopg2
import bcrypt
import zipfile
import xml.etree.ElementTree as ET

SQLITE_PATH = r'c:/Users/saive/Music/final year project/findit-campus/backend/findit_campus.db'
EXCEL_PATH = r'c:/Users/saive/Music/final year project/login_password_roll_numbers (2).xlsx'


def read_excel_records(filepath):
    """Read student login records from the Excel file."""
    if not os.path.exists(filepath):
        print(f"Excel file not found: {filepath}")
        return {}
    records = {}
    with zipfile.ZipFile(filepath, 'r') as z:
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for elem in tree.iter():
                if elem.tag.endswith('t') and elem.text:
                    shared_strings.append(elem.text)
        sheet_tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows = []
        for row in sheet_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
            row_vals = []
            for cell in row.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                t = cell.attrib.get('t')
                v = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                val = v.text if v is not None else ''
                if t == 's' and val.isdigit() and int(val) < len(shared_strings):
                    val = shared_strings[int(val)]
                row_vals.append(val)
            rows.append(row_vals)
    if len(rows) < 2:
        return {}
    headers = [str(h).strip().lower() for h in rows[0]]
    for r in rows[1:]:
        rec = {headers[i]: r[i] if i < len(r) else '' for i in range(len(headers))}
        login = str(rec.get('login', '')).strip()
        password = str(rec.get('password', '')).strip()
        if login:
            records[login.upper()] = password if password else login
    print(f"  Read {len(records)} students from Excel.")
    return records


def seed_neon(neon_url):
    print("\n=== FindIt Campus — Neon PostgreSQL Seeder ===\n")

    # 1. Load Excel passwords
    print("[1] Reading Excel credentials...")
    excel_creds = read_excel_records(EXCEL_PATH)

    # 2. Read from local SQLite
    print("[2] Reading from local SQLite database...")
    sqlite = sqlite3.connect(SQLITE_PATH)
    sqlite.row_factory = sqlite3.Row
    cur = sqlite.cursor()

    cur.execute("SELECT * FROM students")
    all_students = cur.fetchall()
    print(f"  Found {len(all_students)} students in SQLite.")

    cur.execute("SELECT * FROM accounts")
    all_accounts = cur.fetchall()
    print(f"  Found {len(all_accounts)} accounts in SQLite.")

    # Build a set of student_ids that have accounts (Excel-registered)
    account_student_ids = {a['student_id'] for a in all_accounts}
    sqlite.close()

    # 3. Connect to Neon
    print(f"\n[3] Connecting to Neon PostgreSQL...")
    conn = psycopg2.connect(neon_url)
    conn.autocommit = False
    pg = conn.cursor()
    print("  Connected successfully!")

    # 4. Create tables if they don't exist
    print("\n[4] Creating tables...")
    pg.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id SERIAL PRIMARY KEY,
            roll_number VARCHAR(50) UNIQUE NOT NULL,
            student_name VARCHAR(150) NOT NULL,
            department VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
            year INTEGER NOT NULL DEFAULT 3,
            section VARCHAR(10) NOT NULL DEFAULT 'A',
            college_email VARCHAR(255) UNIQUE NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            email_verification_token VARCHAR(255),
            email_verification_sent_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    pg.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id SERIAL PRIMARY KEY,
            student_id INTEGER UNIQUE NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            password_hash VARCHAR(255) NOT NULL,
            last_login TIMESTAMP,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    pg.execute("""
        CREATE TABLE IF NOT EXISTS lost_items (
            item_id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            item_name VARCHAR(200) NOT NULL,
            category VARCHAR(100),
            description TEXT,
            location VARCHAR(200),
            lost_date DATE,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    pg.execute("""
        CREATE TABLE IF NOT EXISTS found_items (
            item_id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            item_name VARCHAR(200) NOT NULL,
            category VARCHAR(100),
            description TEXT,
            location VARCHAR(200),
            found_date DATE,
            status VARCHAR(50) NOT NULL DEFAULT 'stored',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    pg.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            message TEXT,
            type VARCHAR(100),
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    pg.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id SERIAL PRIMARY KEY,
            lost_item_id INTEGER,
            found_item_id INTEGER,
            confidence_score FLOAT,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    pg.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            match_id INTEGER,
            claim_description TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    pg.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id SERIAL PRIMARY KEY,
            sender_id INTEGER,
            receiver_id INTEGER,
            content TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    pg.execute("""
        CREATE TABLE IF NOT EXISTS question_answers (
            qa_id SERIAL PRIMARY KEY,
            question TEXT,
            answer TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    conn.commit()
    print("  Tables ready.")

    # 5. Clear existing data
    print("\n[5] Clearing existing data from Neon...")
    pg.execute("DELETE FROM claims")
    pg.execute("DELETE FROM matches")
    pg.execute("DELETE FROM notifications")
    pg.execute("DELETE FROM found_items")
    pg.execute("DELETE FROM lost_items")
    pg.execute("DELETE FROM accounts")
    pg.execute("DELETE FROM students")
    conn.commit()
    print("  Cleared.")

    # 6. Insert all students
    print(f"\n[6] Inserting {len(all_students)} students into Neon...")
    student_id_map = {}  # old sqlite id -> new neon id
    for s in all_students:
        roll = s['roll_number'].strip()
        email = s['college_email'].strip().lower()
        name = s['student_name'].strip()
        dept = s['department'] or 'Computer Science'
        year = s['year'] or 3
        section = s['section'] or 'A'
        pg.execute("""
            INSERT INTO students (roll_number, student_name, department, year, section, college_email, points, is_email_verified, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (roll_number) DO UPDATE SET student_name=EXCLUDED.student_name
            RETURNING student_id
        """, (roll, name, dept, year, section, email, s['points'] or 0, bool(s['is_email_verified'])))
        new_id = pg.fetchone()[0]
        student_id_map[s['student_id']] = new_id

    conn.commit()
    print(f"  Inserted {len(student_id_map)} students.")

    # 7. Insert accounts for Excel students
    print(f"\n[7] Creating accounts for Excel students...")
    account_count = 0
    for s in all_students:
        old_id = s['student_id']
        roll = s['roll_number'].strip().upper()
        # Only create account if student was in accounts table OR in excel
        if old_id not in account_student_ids and roll not in excel_creds:
            continue
        new_id = student_id_map.get(old_id)
        if not new_id:
            continue
        # Get password from Excel
        password = excel_creds.get(roll, roll)  # fallback: use roll number as password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        pg.execute("""
            INSERT INTO accounts (student_id, password_hash, status, created_at)
            VALUES (%s, %s, 'active', NOW())
            ON CONFLICT (student_id) DO NOTHING
        """, (new_id, hashed))
        account_count += 1

    conn.commit()
    print(f"  Created {account_count} accounts.")

    pg.close()
    conn.close()
    print("\n✅ Neon database seeded successfully!")
    print(f"\nStudents: {len(student_id_map)}")
    print(f"Accounts: {account_count} (these students can log in)")
    print("\nTo log in, use:")
    print("  Roll Number: <any roll number from Excel>")
    print("  Password: <same as the roll number> (e.g., 232U1A3367)")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python seed_neon.py <NEON_DATABASE_URL>")
        print('Example: python seed_neon.py "postgresql://user:pass@host.neon.tech/dbname?sslmode=require"')
        sys.exit(1)
    seed_neon(sys.argv[1])
