from app import create_app, db
from app.models.user import User, Student, Staff, Admin, UserRole
from app.models.lost_item import LostItem, ItemStatus, ItemCategory
from app.models.found_item import FoundItem, FoundItemStatus
from app.models.match import Match, MatchStatus, MatchConfidence
from app.models.claim import Claim, ClaimStatus
from app.models.notification import Notification
from datetime import datetime, date, time, timezone

app = create_app()
with app.app_context():
    print("Clearing tables...")
    # Delete in correct order to respect foreign keys
    db.session.query(Notification).delete()
    db.session.query(Claim).delete()
    db.session.query(Match).delete()
    db.session.query(LostItem).delete()
    db.session.query(FoundItem).delete()
    db.session.query(User).delete()
    db.session.commit()
    print("Tables cleared.")

    # Create Admin
    admin = Admin(
        email='admin@finditcampus.com',
        full_name='System Administrator',
        phone='+919876543210',
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        admin_level='super'
    )
    admin.set_password('Admin@123')
    db.session.add(admin)

    # Create Staff
    guards = [
        Staff(email='guard1@finditcampus.com', full_name='Rajesh Kumar', phone='+919876543211', role=UserRole.STAFF, is_active=True, is_verified=True, staff_id='SEC001', security_office='Main Gate Security', shift='morning'),
        Staff(email='guard2@finditcampus.com', full_name='Suresh Patel', phone='+919876543212', role=UserRole.STAFF, is_active=True, is_verified=True, staff_id='SEC002', security_office='Library Security', shift='evening'),
        Staff(email='guard3@finditcampus.com', full_name='Anil Sharma', phone='+919876543213', role=UserRole.STAFF, is_active=True, is_verified=True, staff_id='SEC003', security_office='Hostel Security', shift='night')
    ]
    for guard in guards:
        guard.set_password('Staff@123')
        db.session.add(guard)

    # Create Students
    students = [
        Student(email='rahul@college.edu', full_name='Rahul Verma', phone='+919876543220', role=UserRole.STUDENT, is_active=True, is_verified=True, roll_number='CSE2021001', department='Computer Science', year_of_study=3, section='A'),
        Student(email='priya@college.edu', full_name='Priya Singh', phone='+919876543221', role=UserRole.STUDENT, is_active=True, is_verified=True, roll_number='IT2021015', department='Information Technology', year_of_study=3, section='B'),
        Student(email='amit@college.edu', full_name='Amit Gupta', phone='+919876543222', role=UserRole.STUDENT, is_active=True, is_verified=True, roll_number='ECE2022010', department='Electronics', year_of_study=2, section='A'),
        Student(email='sneha@college.edu', full_name='Sneha Reddy', phone='+919876543223', role=UserRole.STUDENT, is_active=True, is_verified=True, roll_number='ME2020005', department='Mechanical', year_of_study=4, section='C'),
        Student(email='vikram@college.edu', full_name='Vikram Joshi', phone='+919876543224', role=UserRole.STUDENT, is_active=True, is_verified=True, roll_number='CSE2022030', department='Computer Science', year_of_study=2, section='B')
    ]
    for student in students:
        student.set_password('Student@123')
        db.session.add(student)

    # Load and Seed Students from Excel
    try:
        import os, zipfile, xml.etree.ElementTree as ET
        
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

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        excel_path_2 = os.path.join(base_dir, 'login_password_roll_numbers (2).xlsx')
        excel_path_1 = os.path.join(base_dir, 'login_password_roll_numbers.xlsx')
        
        records = read_excel_records(excel_path_2) or read_excel_records(excel_path_1)
        
        if records:
            added_count = 0
            for rec in records:
                login_val = str(rec.get('login', '')).strip()
                pass_val = str(rec.get('password', '')).strip()
                name_val = str(rec.get('names', rec.get('name', ''))).strip() or f"Student {login_val}"
                if not login_val:
                    continue
                # Skip duplicate if already in default students
                if login_val in ['CSE2021001', 'IT2021015', 'ECE2022010', 'ME2020005', 'CSE2022030']:
                    continue
                excel_student = Student(
                    email=f"{login_val.lower()}@college.edu",
                    full_name=name_val,
                    phone=None,
                    role=UserRole.STUDENT,
                    roll_number=login_val,
                    department='Computer Science',
                    year_of_study=3,
                    section='A',
                    is_active=True,
                    is_verified=True
                )
                excel_student.set_password(pass_val if pass_val else login_val)
                db.session.add(excel_student)
                added_count += 1
            print(f"Loaded {added_count} students from Excel.")
        else:
            print("Warning: No Excel student records found.")
    except Exception as ex:
        print("Failed to seed Excel students:", ex)

    db.session.commit()
    print("Users created.")

    # Refresh to get IDs
    db.session.refresh(students[0]) # Rahul
    db.session.refresh(students[1]) # Priya
    db.session.refresh(students[2]) # Amit
    db.session.refresh(students[3]) # Sneha
    db.session.refresh(students[4]) # Vikram
    db.session.refresh(guards[0]) # guard1
    db.session.refresh(guards[1]) # guard2

    # Create Lost Items
    lost_items = [
        LostItem(
            student_id=students[0].id, # Rahul
            item_name='HP Laptop',
            category=ItemCategory.LAPTOP,
            brand='HP',
            primary_color='Silver',
            secondary_color='Black',
            material='Aluminum',
            description='HP Pavilion 15 laptop with a blue sticker on the cover. Has my name written on a label underneath.',
            lost_date=date(2026, 7, 1),
            lost_time=time(14, 30, 0),
            building='CSE Block',
            floor='2nd Floor',
            room_number='204',
            exact_location='Left on bench near lab entrance',
            reward='500 Rupees',
            status=ItemStatus.ACTIVE
        ),
        LostItem(
            student_id=students[1].id, # Priya
            item_name='Blue Wildcraft Bag',
            category=ItemCategory.BAG,
            brand='Wildcraft',
            primary_color='Blue',
            secondary_color='Grey',
            material='Polyester',
            description='Dark blue Wildcraft backpack with a red keychain attached. Contains some notebooks and a calculator.',
            lost_date=date(2026, 7, 2),
            lost_time=time(11, 0, 0),
            building='Library',
            floor='1st Floor',
            exact_location='Reading section table 5',
            status=ItemStatus.ACTIVE
        ),
        LostItem(
            student_id=students[2].id, # Amit
            item_name='iPhone 15',
            category=ItemCategory.MOBILE,
            brand='Apple',
            primary_color='Black',
            material='Glass',
            description='iPhone 15 with a transparent case. Has a crack on the top right corner of screen protector.',
            lost_date=date(2026, 7, 3),
            lost_time=time(9, 45, 0),
            building='Cafeteria',
            floor='Ground Floor',
            exact_location='Near the billing counter',
            reward='1000 Rupees',
            status=ItemStatus.ACTIVE
        ),
        LostItem(
            student_id=students[3].id, # Sneha
            item_name='Brown Leather Wallet',
            category=ItemCategory.WALLET,
            brand='Woodland',
            primary_color='Brown',
            material='Leather',
            description='Brown Woodland leather wallet containing college ID and some cash. Has my initials SR embossed.',
            lost_date=date(2026, 7, 4),
            lost_time=time(16, 0, 0),
            building='Admin Block',
            floor='1st Floor',
            room_number='105',
            exact_location='Dropped near the staircase',
            status=ItemStatus.ACTIVE
        ),
        LostItem(
            student_id=students[4].id, # Vikram
            item_name='Boat Earbuds',
            category=ItemCategory.EARBUDS,
            brand='Boat',
            primary_color='Black',
            secondary_color='Red',
            material='Plastic',
            description='Boat Airdopes 141 wireless earbuds in black case with red accents. Left charging case behind.',
            lost_date=date(2026, 7, 5),
            lost_time=time(13, 15, 0),
            building='IT Block',
            floor='3rd Floor',
            room_number='301',
            exact_location='Lecture hall back row',
            status=ItemStatus.ACTIVE
        )
    ]
    for item in lost_items:
        db.session.add(item)

    # Create Found Items
    found_items = [
        FoundItem(
            staff_id=guards[0].id, # guard1
            item_name='Silver HP Laptop',
            category=ItemCategory.LAPTOP,
            brand='HP',
            detected_color='Silver',
            manual_color='Silver',
            material='Aluminum',
            description='HP Pavilion laptop found unattended. Silver body with blue sticker. Has a name label on bottom.',
            found_date=date(2026, 7, 1),
            found_time=time(17, 0, 0),
            building='CSE Block',
            floor='2nd Floor',
            room_number='204',
            exact_location='Found on bench outside lab 204',
            security_office='Main Gate Security',
            storage_location='Locker A1',
            status=FoundItemStatus.STORED
        ),
        FoundItem(
            staff_id=guards[1].id, # guard2
            item_name='Dark Blue Backpack',
            category=ItemCategory.BAG,
            brand='Wildcraft',
            detected_color='Blue',
            manual_color='Dark Blue',
            material='Polyester',
            description='Dark blue Wildcraft backpack found in library. Has red keychain. Contains notebooks inside.',
            found_date=date(2026, 7, 2),
            found_time=time(18, 30, 0),
            building='Library',
            floor='1st Floor',
            exact_location='Left at reading section',
            security_office='Library Security',
            storage_location='Shelf B3',
            status=FoundItemStatus.STORED
        ),
        FoundItem(
            staff_id=guards[0].id, # guard1
            item_name='Black iPhone',
            category=ItemCategory.MOBILE,
            brand='Apple',
            detected_color='Black',
            manual_color='Black',
            material='Glass',
            description='iPhone with transparent case found near cafeteria counter. Screen protector has small crack on corner.',
            found_date=date(2026, 7, 3),
            found_time=time(12, 0, 0),
            building='Cafeteria',
            floor='Ground Floor',
            exact_location='Behind billing counter',
            security_office='Main Gate Security',
            storage_location='Locker A3',
            status=FoundItemStatus.STORED
        ),
        FoundItem(
            staff_id=guards[1].id, # guard2
            item_name='Leather Wallet',
            category=ItemCategory.WALLET,
            brand='Woodland',
            detected_color='Brown',
            manual_color='Brown',
            material='Leather',
            description='Brown wallet found on staircase. Woodland brand. Contains college ID card with initials.',
            found_date=date(2026, 7, 4),
            found_time=time(17, 30, 0),
            building='Admin Block',
            floor='1st Floor',
            exact_location='Staircase between floors',
            security_office='Hostel Security',
            storage_location='Drawer C2',
            status=FoundItemStatus.STORED
        ),
        FoundItem(
            staff_id=guards[0].id, # guard1
            item_name='Water Bottle',
            category=ItemCategory.BOTTLE,
            brand='Milton',
            detected_color='Blue',
            manual_color='Blue',
            material='Steel',
            description='Blue Milton steel water bottle found in parking area. Has some scratches.',
            found_date=date(2026, 7, 5),
            found_time=time(10, 0, 0),
            building='Parking',
            floor='Ground Floor',
            exact_location='Two-wheeler parking stand',
            security_office='Main Gate Security',
            storage_location='Shelf A5',
            status=FoundItemStatus.STORED
        )
    ]
    for item in found_items:
        db.session.add(item)

    db.session.commit()
    print("Items created.")

    # Refresh items to get IDs
    for item in lost_items:
        db.session.refresh(item)
    for item in found_items:
        db.session.refresh(item)

    # Create Matches
    matches = [
        Match(
            lost_item_id=lost_items[0].id, # HP Laptop
            found_item_id=found_items[0].id, # Silver HP Laptop
            confidence_score=96.5,
            confidence_level=MatchConfidence.VERY_HIGH,
            image_similarity=0.95,
            text_similarity=0.92,
            color_similarity=1.0,
            brand_similarity=1.0,
            location_similarity=1.0,
            date_similarity=0.9,
            status=MatchStatus.AUTO_NOTIFIED,
            match_details={"weights": {"image": 0.40, "text": 0.25, "color": 0.10, "brand": 0.10, "location": 0.10, "date": 0.05}}
        ),
        Match(
            lost_item_id=lost_items[1].id, # Blue Wildcraft Bag
            found_item_id=found_items[1].id, # Dark Blue Backpack
            confidence_score=93.2,
            confidence_level=MatchConfidence.HIGH,
            image_similarity=0.88,
            text_similarity=0.90,
            color_similarity=0.90,
            brand_similarity=1.0,
            location_similarity=1.0,
            date_similarity=0.9,
            status=MatchStatus.PENDING,
            match_details={"weights": {"image": 0.40, "text": 0.25, "color": 0.10, "brand": 0.10, "location": 0.10, "date": 0.05}}
        ),
        Match(
            lost_item_id=lost_items[2].id, # iPhone 15
            found_item_id=found_items[2].id, # Black iPhone
            confidence_score=91.8,
            confidence_level=MatchConfidence.HIGH,
            image_similarity=0.90,
            text_similarity=0.88,
            color_similarity=1.0,
            brand_similarity=1.0,
            location_similarity=1.0,
            date_similarity=0.7,
            status=MatchStatus.PENDING,
            match_details={"weights": {"image": 0.40, "text": 0.25, "color": 0.10, "brand": 0.10, "location": 0.10, "date": 0.05}}
        ),
        Match(
            lost_item_id=lost_items[3].id, # Brown Leather Wallet
            found_item_id=found_items[3].id, # Leather Wallet
            confidence_score=88.5,
            confidence_level=MatchConfidence.HIGH,
            image_similarity=0.82,
            text_similarity=0.85,
            color_similarity=1.0,
            brand_similarity=1.0,
            location_similarity=1.0,
            date_similarity=0.9,
            status=MatchStatus.PENDING,
            match_details={"weights": {"image": 0.40, "text": 0.25, "color": 0.10, "brand": 0.10, "location": 0.10, "date": 0.05}}
        )
    ]
    for match in matches:
        db.session.add(match)

    db.session.commit()
    print("Matches created.")

    # Refresh matches
    for match in matches:
        db.session.refresh(match)

    # Create Notifications
    notifications = [
        Notification(
            user_id=students[0].id, # Rahul
            title='🎉 Excellent Match Found!',
            message='We found a 96.5% match for your lost HP Laptop! This is a very high confidence match. Please review and claim your item.',
            type='match_found',
            priority='urgent',
            related_item_id=lost_items[0].id,
            related_match_id=matches[0].id,
            action_url=f'/dashboard/student/matches',
            is_read=False
        ),
        Notification(
            user_id=students[1].id, # Priya
            title='🔍 Potential Match Found',
            message='We found a potential match (93.2%) for your lost Blue Wildcraft Bag. Please review the match details.',
            type='match_found',
            priority='high',
            related_item_id=lost_items[1].id,
            related_match_id=matches[1].id,
            action_url=f'/dashboard/student/matches',
            is_read=False
        ),
        Notification(
            user_id=students[2].id, # Amit
            title='🔍 Potential Match Found',
            message='We found a potential match (91.8%) for your lost iPhone 15. Please review the match details.',
            type='match_found',
            priority='high',
            related_item_id=lost_items[2].id,
            related_match_id=matches[2].id,
            action_url=f'/dashboard/student/matches',
            is_read=False
        ),
        Notification(
            user_id=students[0].id, # Rahul
            title='👋 Welcome to FindIt Campus!',
            message='Hi Rahul! Welcome to FindIt Campus. You can report lost items and we will use AI to help find them.',
            type='welcome',
            priority='low',
            action_url='/dashboard',
            is_read=True
        )
    ]
    for notif in notifications:
        db.session.add(notif)

    # Let's seed one pending claim for Guard/Admin review
    claim = Claim(
        student_id=students[0].id, # Rahul
        match_id=matches[0].id, # Match HP Laptop
        lost_item_id=lost_items[0].id,
        found_item_id=found_items[0].id,
        claim_description='This is my HP Pavilion 15 laptop. It has a blue sticker of GitHub on the center cover and my name tag Rahul on the bottom side.',
        proof_images=['https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg'],
        status=ClaimStatus.PENDING
    )
    db.session.add(claim)

    db.session.commit()
    print("Database seeding completed successfully!")
