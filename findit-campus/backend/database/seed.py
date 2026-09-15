import os
import random
import pandas as pd
from datetime import datetime, timezone
from app import create_app, db
from app.models.student import Student
from app.models.account import Account

def seed_data():
    app = create_app()
    with app.app_context():
        print("Recreating database tables with updated schema...")
        db.drop_all()
        db.create_all()
        print("Database schema created successfully.")

        print("Generating 1000 dummy students...")
        
        # Deterministic random generator
        rng = random.Random(42)
        
        first_names = [
            "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Neha", "Sanjay", "Anjali", "Ravi", "Divya",
            "Kiran", "Meera", "Arjun", "Pooja", "Rajesh", "Swathi", "Harish", "Kavya", "Manoj", "Deepika",
            "Vijay", "Aisha", "Suresh", "Ritu", "Anil", "Sandhya", "Prasad", "Jyothi", "Ganesh", "Lakshmi",
            "Karthik", "Bindu", "Naresh", "Sravani", "Pradeep", "Madhavi", "Ramesh", "Sunitha", "Srinivas", "Roopa"
        ]
        
        last_names = [
            "Reddy", "Verma", "Singh", "Gupta", "Rao", "Kumar", "Nair", "Patel", "Sharma", "Naidu",
            "Joshi", "Bose", "Varma", "Yadav", "Choudhury", "Mishra", "Das", "Pillai", "Menon", "Acharya",
            "Somayaji", "Kulkarni", "Deshmukh", "Chavan", "Shinde", "Patil", "Jadhav", "Bhat", "Shenoy", "Hegde"
        ]

        departments = ["AI&ML", "CSE", "ECE", "EEE", "Civil", "Mechanical", "MBA"]
        dept_codes = {
            "AI&ML": "33",
            "CSE": "05",
            "ECE": "04",
            "EEE": "02",
            "Civil": "01",
            "Mechanical": "03",
            "MBA": "E0"
        }

        students_added = 0
        
        # We need around 1000 students
        sections = ["A", "B", "C"]
        years = [1, 2, 3, 4]
        
        for year in years:
            admission_year = 26 - year # 25 for year 1, 24 for year 2, etc.
            
            for dept in departments:
                code = dept_codes[dept]
                
                for i in range(1, 37):
                    roll_seq = f"{i:02d}"
                    roll_number = f"{admission_year}A91A{code}{roll_seq}"
                    
                    name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
                    section = sections[(i - 1) % len(sections)]
                    email = f"{roll_number.lower()}@gist.edu.in"
                    
                    student = Student(
                        roll_number=roll_number,
                        student_name=name,
                        department=dept,
                        year=year,
                        section=section,
                        college_email=email
                    )
                    
                    db.session.add(student)
                    students_added += 1

        db.session.commit()
        print(f"Successfully preloaded {students_added} dummy students.")

        # Read logins, passwords & names from Excel file
        import zipfile, xml.etree.ElementTree as ET
        
        def read_excel_records(filepath):
            if not os.path.exists(filepath):
                return []
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
                if not rows:
                    return []
                headers = [str(h).strip().lower() for h in rows[0]]
                records = []
                for r in rows[1:]:
                    rec = {}
                    for idx, h in enumerate(headers):
                        rec[h] = r[idx] if idx < len(r) else ''
                    if any(rec.values()):
                        records.append(rec)
                return records

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        excel_path_2 = os.path.join(base_dir, 'login_password_roll_numbers (2).xlsx')
        excel_path_1 = os.path.join(base_dir, 'login_password_roll_numbers.xlsx')
        
        records = read_excel_records(excel_path_2) or read_excel_records(excel_path_1)
        
        if records:
            print(f"Reading login details from Excel records ({len(records)} entries)...")
            accounts_seeded = 0
            for rec in records:
                login = str(rec.get('login', '')).strip()
                password = str(rec.get('password', '')).strip() or login
                name_val = str(rec.get('names', rec.get('name', ''))).strip()
                if not login:
                    continue
                
                # Check if student already exists in db
                student = Student.query.filter_by(roll_number=login).first()
                if not student:
                    name = name_val or f"{rng.choice(first_names)} {rng.choice(last_names)}"
                    dept = "AI&ML"
                    year = 3 # Default to 3rd year
                    section = rng.choice(sections)
                    email = f"{login.lower()}@gist.edu.in"
                    
                    student = Student(
                        roll_number=login,
                        student_name=name,
                        department=dept,
                        year=year,
                        section=section,
                        college_email=email
                    )
                    db.session.add(student)
                    db.session.flush() # Get student_id
                elif name_val:
                    student.student_name = name_val
                
                # Check if account already exists
                account = Account.query.filter_by(student_id=student.student_id).first()
                if not account:
                    account = Account(
                        student_id=student.student_id,
                        status='active'
                    )
                    account.set_password(password)
                    db.session.add(account)
                    accounts_seeded += 1
            
            db.session.commit()
            print(f"Successfully seeded {accounts_seeded} student login accounts from Excel.")
        else:
            print(f"Warning: Excel file not found or empty.")

if __name__ == '__main__':
    seed_data()
