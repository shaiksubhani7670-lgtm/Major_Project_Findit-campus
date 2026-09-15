-- ============================================
-- FindIt Campus — Seed Data
-- Sample data for development and demo purposes
-- ============================================

-- Admin user (password: Admin@123)
INSERT INTO users (email, password_hash, full_name, phone, role, is_active, is_verified, admin_level)
VALUES (
    'admin@finditcampus.com',
    'scrypt:32768:8:1$salt$hash_placeholder',  -- Use Flask's generate_password_hash in practice
    'System Administrator',
    '+919876543210',
    'admin', TRUE, TRUE, 'super'
);

-- Staff users (password: Staff@123)
INSERT INTO users (email, password_hash, full_name, phone, role, is_active, is_verified, staff_id, security_office, shift)
VALUES
    ('guard1@finditcampus.com', 'scrypt:32768:8:1$salt$hash_placeholder', 'Rajesh Kumar', '+919876543211', 'staff', TRUE, TRUE, 'SEC001', 'Main Gate Security', 'morning'),
    ('guard2@finditcampus.com', 'scrypt:32768:8:1$salt$hash_placeholder', 'Suresh Patel', '+919876543212', 'staff', TRUE, TRUE, 'SEC002', 'Library Security', 'evening'),
    ('guard3@finditcampus.com', 'scrypt:32768:8:1$salt$hash_placeholder', 'Anil Sharma', '+919876543213', 'staff', TRUE, TRUE, 'SEC003', 'Hostel Security', 'night');

-- Student users (password: Student@123)
INSERT INTO users (email, password_hash, full_name, phone, role, is_active, is_verified, roll_number, department, year_of_study, section)
VALUES
    ('rahul@college.edu', 'scrypt:32768:8:1$salt$hash_placeholder', 'Rahul Verma', '+919876543220', 'student', TRUE, TRUE, 'CSE2021001', 'Computer Science', 3, 'A'),
    ('priya@college.edu', 'scrypt:32768:8:1$salt$hash_placeholder', 'Priya Singh', '+919876543221', 'student', TRUE, TRUE, 'IT2021015', 'Information Technology', 3, 'B'),
    ('amit@college.edu', 'scrypt:32768:8:1$salt$hash_placeholder', 'Amit Gupta', '+919876543222', 'student', TRUE, TRUE, 'ECE2022010', 'Electronics', 2, 'A'),
    ('sneha@college.edu', 'scrypt:32768:8:1$salt$hash_placeholder', 'Sneha Reddy', '+919876543223', 'student', TRUE, TRUE, 'ME2020005', 'Mechanical', 4, 'C'),
    ('vikram@college.edu', 'scrypt:32768:8:1$salt$hash_placeholder', 'Vikram Joshi', '+919876543224', 'student', TRUE, TRUE, 'CSE2022030', 'Computer Science', 2, 'B');

-- Sample Lost Items
INSERT INTO lost_items (student_id, item_name, category, brand, primary_color, secondary_color, material, description, lost_date, lost_time, building, floor, room_number, exact_location, reward, status)
VALUES
    (5, 'HP Laptop', 'laptop', 'HP', 'Silver', 'Black', 'Aluminum', 'HP Pavilion 15 laptop with a blue sticker on the cover. Has my name written on a label underneath.', '2026-07-01', '14:30:00', 'CSE Block', '2nd Floor', '204', 'Left on bench near lab entrance', '500 Rupees', 'active'),
    (6, 'Blue Wildcraft Bag', 'bag', 'Wildcraft', 'Blue', 'Grey', 'Polyester', 'Dark blue Wildcraft backpack with a red keychain attached. Contains some notebooks and a calculator.', '2026-07-02', '11:00:00', 'Library', '1st Floor', NULL, 'Reading section table 5', NULL, 'active'),
    (7, 'iPhone 15', 'mobile', 'Apple', 'Black', NULL, 'Glass', 'iPhone 15 with a transparent case. Has a crack on the top right corner of screen protector.', '2026-07-03', '09:45:00', 'Cafeteria', 'Ground Floor', NULL, 'Near the billing counter', '1000 Rupees', 'active'),
    (8, 'Brown Leather Wallet', 'wallet', 'Woodland', 'Brown', NULL, 'Leather', 'Brown Woodland leather wallet containing college ID and some cash. Has my initials SR embossed.', '2026-07-04', '16:00:00', 'Admin Block', '1st Floor', '105', 'Dropped near the staircase', NULL, 'active'),
    (9, 'Boat Earbuds', 'earbuds', 'Boat', 'Black', 'Red', 'Plastic', 'Boat Airdopes 141 wireless earbuds in black case with red accents. Left charging case behind.', '2026-07-05', '13:15:00', 'IT Block', '3rd Floor', '301', 'Lecture hall back row', NULL, 'active');

-- Sample Found Items (uploaded by staff)
INSERT INTO found_items (staff_id, item_name, category, brand, detected_color, manual_color, material, description, found_date, found_time, building, floor, room_number, exact_location, security_office, storage_location, status)
VALUES
    (2, 'Silver HP Laptop', 'laptop', 'HP', 'Silver', 'Silver', 'Aluminum', 'HP Pavilion laptop found unattended. Silver body with blue sticker. Has a name label on bottom.', '2026-07-01', '17:00:00', 'CSE Block', '2nd Floor', '204', 'Found on bench outside lab 204', 'Main Gate Security', 'Locker A1', 'stored'),
    (3, 'Dark Blue Backpack', 'bag', 'Wildcraft', 'Blue', 'Dark Blue', 'Polyester', 'Dark blue Wildcraft backpack found in library. Has red keychain. Contains notebooks inside.', '2026-07-02', '18:30:00', 'Library', '1st Floor', NULL, 'Left at reading section', 'Library Security', 'Shelf B3', 'stored'),
    (2, 'Black iPhone', 'mobile', 'Apple', 'Black', 'Black', 'Glass', 'iPhone with transparent case found near cafeteria counter. Screen protector has small crack on corner.', '2026-07-03', '12:00:00', 'Cafeteria', 'Ground Floor', NULL, 'Behind billing counter', 'Main Gate Security', 'Locker A3', 'stored'),
    (4, 'Leather Wallet', 'wallet', 'Woodland', 'Brown', 'Brown', 'Leather', 'Brown wallet found on staircase. Woodland brand. Contains college ID card with initials.', '2026-07-04', '17:30:00', 'Admin Block', '1st Floor', NULL, 'Staircase between floors', 'Hostel Security', 'Drawer C2', 'stored'),
    (2, 'Water Bottle', 'bottle', 'Milton', 'Blue', 'Blue', 'Steel', 'Blue Milton steel water bottle found in parking area. Has some scratches.', '2026-07-05', '10:00:00', 'Parking', 'Ground Floor', NULL, 'Two-wheeler parking stand', 'Main Gate Security', 'Shelf A5', 'stored');

-- Sample Matches (AI-generated)
INSERT INTO matches (lost_item_id, found_item_id, confidence_score, confidence_level, image_similarity, text_similarity, color_similarity, brand_similarity, location_similarity, date_similarity, status, match_details)
VALUES
    (1, 1, 96.5, 'very_high', 0.95, 0.92, 1.0, 1.0, 1.0, 0.9, 'auto_notified', '{"weights": {"image": 0.40, "text": 0.25, "color": 0.10, "brand": 0.10, "location": 0.10, "date": 0.05}}'),
    (2, 2, 93.2, 'high', 0.88, 0.90, 0.90, 1.0, 1.0, 0.9, 'pending', '{"weights": {"image": 0.40, "text": 0.25, "color": 0.10, "brand": 0.10, "location": 0.10, "date": 0.05}}'),
    (3, 3, 91.8, 'high', 0.90, 0.88, 1.0, 1.0, 1.0, 0.7, 'pending', '{"weights": {"image": 0.40, "text": 0.25, "color": 0.10, "brand": 0.10, "location": 0.10, "date": 0.05}}'),
    (4, 4, 88.5, 'high', 0.82, 0.85, 1.0, 1.0, 1.0, 0.9, 'pending', '{"weights": {"image": 0.40, "text": 0.25, "color": 0.10, "brand": 0.10, "location": 0.10, "date": 0.05}}');

-- Sample Notifications
INSERT INTO notifications (user_id, title, message, type, priority, related_item_id, related_match_id, action_url, is_read)
VALUES
    (5, '🎉 Excellent Match Found!', 'We found a 96.5% match for your lost HP Laptop! This is a very high confidence match. Please review and claim your item.', 'match_found', 'urgent', 1, 1, '/dashboard/student/matches/1', FALSE),
    (6, '🔍 Potential Match Found', 'We found a potential match (93.2%) for your lost Blue Wildcraft Bag. Please review the match details.', 'match_found', 'high', 2, 2, '/dashboard/student/matches/2', FALSE),
    (7, '🔍 Potential Match Found', 'We found a potential match (91.8%) for your lost iPhone 15. Please review the match details.', 'match_found', 'high', 3, 3, '/dashboard/student/matches/3', FALSE),
    (5, '👋 Welcome to FindIt Campus!', 'Hi Rahul! Welcome to FindIt Campus. You can report lost items and we will use AI to help find them.', 'welcome', 'low', NULL, NULL, '/dashboard', TRUE);
