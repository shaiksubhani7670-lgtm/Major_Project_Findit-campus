You are a Senior Full Stack Developer, UI/UX Designer, AI Engineer, Software Architect, and Database Designer.

I am building my B.Tech Final Year Project.

The project must be developed professionally with clean architecture, modular code, and industry-standard practices.

Never skip any feature mentioned below.

Never simplify the project.

If the response becomes too long, continue automatically from where you stopped without removing any features.

=====================================================

PROJECT NAME

=====================================================

FindIt Campus

Tagline

AI-Powered Lost & Found Management System for College Campuses

=====================================================

PROJECT OVERVIEW

=====================================================

FindIt Campus is a web application developed for students to report lost and found items inside the college campus.

The system uses Artificial Intelligence to compare Lost Item reports with Found Item reports and notify users when a high-confidence match is found.

This project is designed for ONLY ONE COLLEGE.

College Name

Geethanjali Institute of Science and Technology

This is NOT a multi-college platform.

Only students of this college can register.

=====================================================

PROJECT OBJECTIVES

=====================================================

Students should be able to

• Register

• Login

• Report Lost Items

• Report Found Items

• View their reports

• Receive AI match notifications

• Verify ownership

• Successfully recover lost belongings

The system should automatically compare reports using AI.

=====================================================

PROJECT SCOPE

=====================================================

Single College Only

Student Accounts Only

No Admin Panel

No Faculty Portal

No Public Users

No Multi-College Support

No Marketplace

No Chat System

No Social Features

Only Lost and Found Management.

=====================================================

TECH STACK

=====================================================

Frontend

Next.js

React

TypeScript

Tailwind CSS

Framer Motion

Backend

Python Flask

Database

PostgreSQL

Authentication

JWT Authentication

Password Hashing using bcrypt

Image Storage

Store locally during development.

The storage structure should be easy to migrate to Cloudinary later.

=====================================================

AI MODULES

=====================================================

YOLOv8

Detect uploaded object category.

OpenCV

Extract image features.

EasyOCR

Extract visible text from uploaded images.

Sentence Transformers

Compare descriptions semantically.

FAISS

Fast similarity search.

=====================================================

IMPORTANT DEVELOPMENT RULES

=====================================================

Generate production-quality code.

Follow clean architecture.

Use reusable components.

Use proper folder structure.

Write maintainable code.

Write comments only where necessary.

Separate frontend and backend.

Create REST APIs.

Use validation everywhere.

Handle errors properly.

Display meaningful error messages.

Create loading states.

Create empty states.

Create success messages.

Create responsive pages.

=====================================================

UI / UX REQUIREMENTS

=====================================================

IMPORTANT

The website should NOT look like a typical AI-generated website.

Avoid:

Heavy Glassmorphism

Huge gradients

3D cards

Complex animations

Over-designed landing pages

Fancy floating elements

Particle backgrounds

Large hero sections

Overly rounded components

Instead create

A simple

Modern

Professional

Practical

Clean user interface.

The design should look like a real software application developed by engineering students.

=====================================================

UI DESIGN STYLE

=====================================================

Simple Modern Dashboard

Minimal Design

Professional Layout

Consistent Spacing

Clean Typography

Flat Design

Responsive

Fast Loading

Easy Navigation

Subtle Hover Effects

Small Animations

Rounded Corners

Professional Forms

Simple Cards

Simple Icons

No unnecessary visual effects.

=====================================================

COLOR PALETTE

=====================================================

Primary

Blue

#2563EB

Secondary

White

#FFFFFF

Background

#F8FAFC

Cards

White

Text

#1F2937

Success

#22C55E

Warning

#F59E0B

Danger

#EF4444

Borders

#E5E7EB

=====================================================

ANIMATIONS

=====================================================

Only use

Button Hover

Card Hover

Smooth Fade

Page Transition

Loading Spinner

Skeleton Loader

Do NOT use

Glass Effects

Parallax

3D Rotation

Floating Objects

Hero Animations

Complex Motion

=====================================================

RESPONSIVE DESIGN

=====================================================

Desktop

Laptop

Tablet

Mobile

All pages must work perfectly.

=====================================================

PROJECT WORKFLOW

=====================================================

Landing Page

↓

Student Registration

↓

Login

↓

Dashboard

↓

Report Lost Item

or

Report Found Item

↓

AI Matching

↓

Notification

↓

Ownership Verification

↓

Item Returned

↓

Report Closed

=====================================================

LANDING PAGE

=====================================================

Simple Navigation Bar

College Logo

Project Name

Short Project Description

Three Main Buttons

Login

Register

Report Found Item

Simple Statistics Section

Total Lost Reports

Total Found Reports

Recovered Items

Footer

Project Name

Team Members

College Name

Copyright

No huge banners.

No unnecessary animations.

=====================================================

DASHBOARD

=====================================================

Simple Sidebar

Home

Report Lost Item

Report Found Item

My Reports

Notifications

Profile

Main Dashboard

Recent Reports

Recent Notifications

Quick Actions

Simple statistics cards.

=====================================================

CODE QUALITY

=====================================================

Use reusable React components.

Create separate API services.

Separate business logic.

Use environment variables.

Never hardcode secrets.

Use proper naming conventions.

Create scalable folder structure.

=====================================================

IMPORTANT

Do not generate everything at once.

Generate this project module-by-module.

Wait for confirmation before moving to the next module.

Do not skip any requirement mentioned in this prompt.

Continue developing the FindIt Campus project.

Follow all requirements from Part 1 exactly.

Do not modify any previously defined feature.

Generate this module completely before moving to another module.

=====================================================

PROJECT FOLDER STRUCTURE

=====================================================

Use the following project structure.

findit-campus/

│

├── frontend/

│ ├── app/

│ ├── components/

│ ├── services/

│ ├── hooks/

│ ├── lib/

│ ├── types/

│ ├── public/

│ ├── styles/

│ ├── middleware/

│ └── package.json

│

├── backend/

│ ├── app.py

│ ├── config.py

│ ├── requirements.txt

│ ├── database/

│ ├── models/

│ ├── routes/

│ ├── controllers/

│ ├── services/

│ ├── middleware/

│ ├── ai/

│ ├── uploads/

│ │ ├── lost/

│ │ └── found/

│ ├── utils/

│ └── migrations/

│

└── README.md

=====================================================

DATABASE

=====================================================

Use PostgreSQL.

Create proper foreign keys.

Use UUID or auto increment IDs.

Create timestamps.

created_at

updated_at

=====================================================

TABLES

=====================================================

Students

Accounts

Lost_Items

Found_Items

Question_Answers

Notifications

Matches

Claims

=====================================================

STUDENTS TABLE

=====================================================

This table contains only preloaded college students.

Fields

student_id

roll_number

student_name

department

college_email

year

section

created_at

The system should automatically generate around 1000 dummy students.

Example

Roll Number

23A91A0501

Name

Rahul

Department

AI&ML

Email

23a91a0501@gist.edu

=====================================================

ACCOUNTS TABLE

=====================================================

Fields

account_id

student_id

password_hash

created_at

last_login

status

=====================================================

REGISTRATION

=====================================================

Students CANNOT freely register.

Registration should work like this.

Student enters

Roll Number

Student Name

College Email

Password

Confirm Password

Backend verifies

Roll Number exists

Student Name matches

College Email matches

If all three match

Create account.

Otherwise

Display

Student record not found.

If account already exists

Display

Account already exists. Please login.

=====================================================

PASSWORD RULES

=====================================================

Minimum 8 characters.

One uppercase letter.

One lowercase letter.

One number.

One special character.

Hash password using bcrypt.

Never store plain text passwords.

=====================================================

LOGIN

=====================================================

Login using

Roll Number

Password

If credentials are correct

Generate JWT Token.

Store securely.

Redirect to Dashboard.

=====================================================

JWT

=====================================================

Protect all APIs except

Login

Register

Health Check

Reject unauthorized requests.

Automatically redirect expired sessions to Login.

=====================================================

LOGOUT

=====================================================

Clear JWT.

Redirect to Login.

=====================================================

PROFILE PAGE

=====================================================

Display

Student Name

Roll Number

Department

Email

Year

Section

Profile Avatar

Allow

Change Password

Logout

Do NOT allow

Editing

Roll Number

Department

Email

=====================================================

CHANGE PASSWORD

=====================================================

Require

Current Password

New Password

Confirm Password

Validate password rules.

=====================================================

FORM VALIDATION

=====================================================

Validate every input.

Display inline errors.

Examples

Roll Number Required

Invalid Email

Password Too Short

Passwords Do Not Match

=====================================================

ERROR HANDLING

=====================================================

Show professional error messages.

Examples

Invalid Credentials

Account Not Found

Session Expired

Server Error

=====================================================

SUCCESS MESSAGES

=====================================================

Registration Successful

Login Successful

Password Updated Successfully

=====================================================

SECURITY

=====================================================

Use bcrypt.

Use JWT.

Prevent SQL Injection.

Validate every request.

Sanitize inputs.

Never expose passwords.

Never expose JWT secret.

Use environment variables.

=====================================================

DUMMY DATA

=====================================================

Automatically create

1000 Students

Departments

AI&ML

CSE

ECE

EEE

Civil

Mechanical

MBA

Generate realistic names.

Generate realistic roll numbers.

Generate realistic college emails.

=====================================================

BACKEND APIs

=====================================================

POST

/api/auth/register

POST

/api/auth/login

POST

/api/auth/logout

POST

/api/auth/change-password

GET

/api/profile

=====================================================

FRONTEND PAGES

=====================================================

Register Page

Login Page

Forgot Password (Optional Placeholder)

Profile Page

=====================================================

UI REQUIREMENTS

=====================================================

Simple Modern Design.

Clean Forms.

Medium Width Cards.

Blue Primary Buttons.

White Background.

Minimal Icons.

Soft Shadows.

Rounded Corners.

No Glassmorphism.

No Heavy Animations.

Professional College Software Appearance.

=====================================================

IMPORTANT

Generate

Complete PostgreSQL schema.

Complete Flask APIs.

Complete JWT Authentication.

Complete Validation.

Complete Frontend Forms.

Complete Folder Structure.

Do not leave TODOs.

Do not generate dummy UI.

Everything must be functional.

Continue developing the FindIt Campus project.

Follow all requirements from Part 1 and Part 2 exactly.

Do not modify any previous feature.

Generate this module completely.

=====================================================

LOST & FOUND MODULE

=====================================================

The application contains two main reporting modules.

1. Report Lost Item

2. Report Found Item

Both modules should use exactly the same workflow.

The only difference is

Lost Item = Item owned by the student but lost.

Found Item = Item found by the student.

=====================================================

REPORTING WORKFLOW

=====================================================

Dashboard

↓

User clicks

Report Lost Item

or

Report Found Item

↓

Step 1

Select Item Category

↓

Step 2

Fill Common Details

↓

Step 3

Fill Category Specific Details

↓

Step 4

Answer Category Questions

↓

Step 5

Upload Image (Optional)

↓

Preview Report

↓

Submit Report

↓

Save into Database

↓

Trigger AI Matching Automatically

=====================================================

STEP 1

ITEM CATEGORY

=====================================================

Display categories as modern responsive cards with icon and name.

Available Categories

📱 Phone

💻 Laptop

🎧 Earbuds

⌚ Watch

👛 Wallet

💍 Ring

📿 Chain

🪬 Bracelet

👟 Shoes

🪪 ID Card

📚 Book

🔑 Keys

🥤 Water Bottle

🍱 Lunch Box

🎒 Backpack

🧮 Calculator

🔌 Charger

🔋 Power Bank

👓 Spectacles

☂️ Umbrella

🪖 Helmet

💾 Pen Drive

🧥 Jacket / Hoodie

📦 Others

After selecting a category,

Automatically navigate to the reporting form.

=====================================================

STEP 2

COMMON DETAILS

=====================================================

These fields are mandatory for EVERY item.

Item Name *

Color *

Location *

Date *

Time *

Description *

Upload Image (Optional)

Description should support multiple lines.

Location can be selected using

Dropdown

or

Searchable list of common college locations.

Example

Library

Canteen

Ground

Parking Area

Bus Stop

Block A

Block B

Lab

Classroom

Auditorium

Hostel

Others

=====================================================

STEP 3

CATEGORY SPECIFIC DETAILS

=====================================================

Show only the fields related to the selected category.

PHONE

Brand

Model

LAPTOP

Brand

Model

Screen Size (Optional)

EARBUDS

Brand

Model

WATCH

Brand

Strap Color

WALLET

Brand

Material

RING

Material

Ring Size (Optional)

CHAIN

Material

BRACELET

Material

SHOES

Brand

Shoe Size

ID CARD

Student/Staff

Department

BOOK

Book Title

Author

KEYS

Number of Keys

WATER BOTTLE

Brand

Capacity

LUNCH BOX

Brand

Number of Compartments

BACKPACK

Brand

Number of Compartments

CALCULATOR

Brand

Model

CHARGER

Brand

Type

POWER BANK

Brand

Capacity

SPECTACLES

Brand

Frame Type

UMBRELLA

Brand

Type

HELMET

Brand

Helmet Type

PEN DRIVE

Brand

Storage Capacity

JACKET / HOODIE

Brand

Size

OTHERS

Custom Details Field

=====================================================

STEP 4

CATEGORY QUESTIONS

=====================================================

Show four questions after the category-specific details.

PHONE

Back Cover? (Yes/No)

Stickers? (Yes/No)

Screen Scratched? (Yes/No)

Any Unique Feature? (Text)

LAPTOP

Stickers? (Yes/No)

Charger Available? (Yes/No)

Visible Scratches? (Yes/No)

Any Unique Feature? (Text)

EARBUDS

Charging Case Available? (Yes/No)

Scratches? (Yes/No)

Silicone Tips? (Yes/No)

Any Unique Feature? (Text)

WATCH

Smart Watch? (Yes/No)

Scratches? (Yes/No)

Leather Strap? (Yes/No)

Any Unique Feature? (Text)

WALLET

Contains ID Card? (Yes/No)

Has Zipper? (Yes/No)

Cash Inside? (Yes/No)

Any Unique Feature? (Text)

RING

Gemstone? (Yes/No)

Engraving? (Yes/No)

Adjustable? (Yes/No)

Any Unique Feature? (Text)

CHAIN

Has Pendant? (Yes/No)

Thick Chain? (Yes/No)

Broken Clasp? (Yes/No)

Any Unique Feature? (Text)

BRACELET

Has Charms? (Yes/No)

Adjustable? (Yes/No)

Engraving? (Yes/No)

Any Unique Feature? (Text)

SHOES

Has Laces? (Yes/No)

Dirty Marks? (Yes/No)

Brand Logo Visible? (Yes/No)

Any Unique Feature? (Text)

ID CARD

Card Holder? (Yes/No)

Lanyard Attached? (Yes/No)

Transparent Holder? (Yes/No)

Holder/Lanyard Color? (Text)

BOOK

Name Written? (Yes/No)

Handwritten Notes? (Yes/No)

Bookmark? (Yes/No)

Any Unique Feature? (Text)

KEYS

Keychain Attached? (Yes/No)

Tag Attached? (Yes/No)

Bike/Car Key? (Yes/No)

Any Unique Feature? (Text)

WATER BOTTLE

Has Stickers? (Yes/No)

Name Written? (Yes/No)

Carrying Handle? (Yes/No)

Any Unique Feature? (Text)

LUNCH BOX

Multiple Compartments? (Yes/No)

Spoon Included? (Yes/No)

Insulated? (Yes/No)

Any Unique Feature? (Text)

BACKPACK

Laptop Compartment? (Yes/No)

Bottle Pocket? (Yes/No)

Keychain Attached? (Yes/No)

Any Unique Feature? (Text)

CALCULATOR

Scientific Calculator? (Yes/No)

Protective Cover? (Yes/No)

Name Written? (Yes/No)

Any Unique Feature? (Text)

CHARGER

Cable Included? (Yes/No)

Fast Charger? (Yes/No)

Damaged? (Yes/No)

Any Unique Feature? (Text)

POWER BANK

Digital Display? (Yes/No)

Built-in Cable? (Yes/No)

Scratches? (Yes/No)

Any Unique Feature? (Text)

SPECTACLES

Case Included? (Yes/No)

Power Glasses? (Yes/No)

Lens Scratched? (Yes/No)

Any Unique Feature? (Text)

UMBRELLA

Foldable? (Yes/No)

Automatic? (Yes/No)

Pattern? (Yes/No)

Any Unique Feature? (Text)

HELMET

Full Face? (Yes/No)

Stickers? (Yes/No)

Tinted Visor? (Yes/No)

Any Unique Feature? (Text)

PEN DRIVE

Metal Body? (Yes/No)

Keychain Attached? (Yes/No)

Password Protected? (Yes/No)

Any Unique Feature? (Text)

JACKET / HOODIE

Has Hood? (Yes/No)

Has Zipper? (Yes/No)

Logo Present? (Yes/No)

Any Unique Feature? (Text)

OTHERS

Generate suitable questions dynamically based on the item name.

=====================================================

STEP 5

REPORT PREVIEW

=====================================================

Before submission,

Display a preview card containing

Category

Item Name

Color

Location

Date

Time

Description

Additional Details

Question Answers

Image Preview (if uploaded)

Buttons

Edit

Submit

=====================================================

DATABASE STORAGE

=====================================================

Store Lost Reports in

Lost_Items

Store Found Reports in

Found_Items

Store question answers in

Question_Answers

Store uploaded images inside

backend/uploads/lost/

backend/uploads/found/

=====================================================

STATUS

=====================================================

Every report has one status.

Searching

Matched

Claim Pending

Completed

Cancelled

=====================================================

MY REPORTS PAGE

=====================================================

Student can view

Lost Reports

Found Reports

Search reports

Filter by status

Sort by date

View report details

Edit report (only before a match is found)

Delete report (only before a match is found)

=====================================================

VALIDATION

=====================================================

Validate every required field.

Prevent empty submissions.

Validate uploaded image type.

Allow only

jpg

jpeg

png

Maximum image size

5 MB

=====================================================

BACKEND APIs

=====================================================

POST /api/lost/report

POST /api/found/report

GET /api/lost/all

GET /api/found/all

GET /api/report/:id

PUT /api/report/update/:id

DELETE /api/report/delete/:id

=====================================================

UI REQUIREMENTS

=====================================================

Use a clean multi-step form with a progress indicator.

Show one section at a time.

Use responsive cards for category selection.

Display validation messages below each field.

Keep the layout simple, modern, and easy to use.

Do not use heavy animations, glassmorphism, or flashy effects.

=====================================================

IMPORTANT

After a report is successfully submitted, automatically trigger the AI Matching Engine in the background. Do not make the user manually start the matching process.

Continue developing the FindIt Campus project.

Follow every requirement from Part 1, Part 2 and Part 3.

Do not modify previous modules.

This module implements the complete AI Matching Engine.

=====================================================

AI MATCHING ENGINE

=====================================================

The AI Matching Engine automatically starts whenever

A Lost Report is submitted

OR

A Found Report is submitted.

The user should never manually start AI matching.

Matching runs automatically in the background.

=====================================================

MATCHING FLOW

=====================================================

New Report Submitted

↓

Identify Report Category

↓

Find reports of SAME CATEGORY only

↓

Filter reports created within the last 60 days

↓

Extract AI Features

↓

Calculate Similarity

↓

Generate Match Score

↓

Store Result

↓

If score ≥ 85%

Send Notification

Otherwise

Store internally without notifying.

=====================================================

DO NOT COMPARE

=====================================================

Phone ↔ Laptop

Phone ↔ Watch

Laptop ↔ Wallet

Book ↔ Shoes

etc.

Compare only identical categories.

=====================================================

AI PIPELINE

=====================================================

The AI engine should compare multiple features.

Each feature contributes to the final score.

=====================================================

1. IMAGE SIMILARITY

=====================================================

Weight

40%

Use

YOLOv8

OpenCV

Workflow

Detect object

↓

Crop object

↓

Extract visual features

↓

Compare images

↓

Generate Image Similarity Score

=====================================================

2. BRAND + MODEL

=====================================================

Weight

20%

Compare

Brand

Model

Case insensitive.

Minor spelling mistakes should still match.

=====================================================

3. DESCRIPTION

=====================================================

Weight

15%

Use

Sentence Transformers

Generate embeddings.

Compare using cosine similarity.

Examples

"Black OnePlus phone"

and

"OnePlus mobile in black color"

should produce a high similarity score.

=====================================================

4. COLOR

=====================================================

Weight

10%

Normalize colors.

Examples

Dark Blue

Blue

Navy Blue

should be treated as similar.

=====================================================

5. LOCATION + DATE + TIME

=====================================================

Weight

10%

Compare

Location

Date

Time

Example

Lost

Library

2:00 PM

Found

Library

2:15 PM

High score.

Lost

Parking

Found

Library

Low score.

=====================================================

6. QUESTION ANSWERS

=====================================================

Weight

5%

Compare

Yes/No answers

Text answer

Each Yes/No contributes equally.

The text answer should use semantic similarity.

Question similarity is only a supporting factor.

=====================================================

TOTAL

=====================================================

Image

40%

Brand + Model

20%

Description

15%

Color

10%

Location + Date + Time

10%

Questions

5%

TOTAL

100%

=====================================================

SIMILARITY LEVELS

=====================================================

95–100%

Excellent Match

Notify immediately.

90–94%

Very High Match

Notify immediately.

85–89%

High Match

Notify.

75–84%

Potential Match

Store only.

Below 75%

Ignore.

=====================================================

MATCH DATABASE

=====================================================

Store every comparison.

Fields

match_id

lost_report_id

found_report_id

image_score

brand_model_score

description_score

color_score

location_score

question_score

overall_score

created_at

=====================================================

NOTIFICATIONS

=====================================================

Notify ONLY when

Overall Score ≥ 85%.

Notification Example

Great News!

A highly similar item has been found.

Category

Phone

Match Confidence

92%

Location

Library

Button

Verify Ownership

=====================================================

NOTIFICATION TABLE

=====================================================

notification_id

student_id

report_id

title

message

status

created_at

=====================================================

OWNERSHIP VERIFICATION

=====================================================

The application must NEVER publicly reveal

Found item details

Finder details

Phone number

Email

Address

Ownership must be verified first.

=====================================================

VERIFY OWNERSHIP

=====================================================

Student clicks

Verify Ownership

↓

System displays verification form

↓

Student answers questions

↓

Backend compares answers

↓

If answers are acceptable

Approve Claim

↓

Reveal finder information

↓

Mark report completed.

=====================================================

VERIFICATION QUESTIONS

=====================================================

Generate questions using

Original report

Category questions

Description

Additional details

Example

Phone

What brand is your phone?

What model is it?

What color is it?

Did it have a back cover?

Any stickers?

Unique feature?

The finder should NOT see these answers.

=====================================================

CLAIMS TABLE

=====================================================

claim_id

match_id

student_id

verification_score

status

approved_by_system

created_at

=====================================================

CLAIM STATUS

=====================================================

Pending

Approved

Rejected

Completed

=====================================================

APPROVAL RULES

=====================================================

If verification score ≥ 80%

Approve automatically.

Otherwise

Reject.

=====================================================

COMPLETED REPORT

=====================================================

After approval

Mark Lost Report

Completed

Mark Found Report

Completed

Create completion timestamp.

=====================================================

PROFILE STATISTICS

=====================================================

Show

Total Lost Reports

Total Found Reports

Items Returned

Pending Reports

=====================================================

BACKGROUND PROCESSING

=====================================================

AI Matching should run asynchronously.

The user should receive immediate confirmation that the report was submitted.

The AI processing should continue in the background without blocking the interface.

=====================================================

BACKEND SERVICES

=====================================================

Create separate services.

Image Service

OCR Service

Embedding Service

Matching Service

Notification Service

Claim Service

=====================================================

API ENDPOINTS

=====================================================

POST

/api/match/run

GET

/api/matches

GET

/api/match/{id}

POST

/api/claim/verify

POST

/api/claim/approve

POST

/api/claim/reject

GET

/api/notifications

PUT

/api/notifications/read

=====================================================

UI

=====================================================

Notifications page should display

Title

Category

Similarity

Date

Button

View Match

Match Details page should display

Lost Report

Found Report

Similarity Breakdown

Image Score

Brand Score

Description Score

Color Score

Location Score

Question Score

Overall Score

Button

Verify Ownership

=====================================================

IMPORTANT

Write modular AI code.

Keep every AI model in a separate service.

Do not hardcode paths.

Keep the AI pipeline reusable.

The matching engine should be easy to improve in the future without changing the frontend.

Continue developing the FindIt Campus project.

Follow all previous parts exactly.

Do NOT change any previous feature.

Generate the complete frontend.

=====================================================

FRONTEND TECHNOLOGY

=====================================================

Framework

Next.js (Latest App Router)

Language

TypeScript

Styling

Tailwind CSS

Animation

Framer Motion

State Management

React Context API

HTTP Client

Axios

Icons

Lucide React

Form Validation

React Hook Form + Zod

=====================================================

FRONTEND FOLDER STRUCTURE

=====================================================

frontend/

app/

(auth)

login/

register/

dashboard/

home/

report-lost/

report-found/

my-reports/

notifications/

profile/

components/

layout/

forms/

cards/

buttons/

sidebar/

navbar/

dialogs/

modals/

tables/

services/

hooks/

types/

utils/

styles/

public/

=====================================================

DESIGN PRINCIPLES

=====================================================

The website MUST NOT look AI-generated.

Create a clean and realistic software interface.

Avoid

❌ Huge gradients

❌ Glassmorphism

❌ Fancy 3D effects

❌ Floating animations

❌ Large hero banners

❌ Over-designed landing page

Instead create

✅ Clean

✅ Professional

✅ Practical

✅ Minimal

✅ Easy to navigate

=====================================================

GLOBAL LAYOUT

=====================================================

Top Navigation

College Logo

Project Name

Notification Icon

Profile Menu

Logout

Dashboard Layout

Left Sidebar

Main Content Area

Responsive Layout

=====================================================

SIDEBAR

=====================================================

Home

Report Lost Item

Report Found Item

My Reports

Notifications

Profile

Logout

Sidebar should collapse automatically on mobile.

=====================================================

HOME DASHBOARD

=====================================================

Display

Welcome Student

Statistics Cards

Total Lost Reports

Total Found Reports

Items Recovered

Pending Reports

Recent Notifications

Recent Reports

Quick Action Buttons

Report Lost Item

Report Found Item

=====================================================

REPORT FORM

=====================================================

Use a step-by-step wizard.

Step 1

Choose Category

↓

Step 2

Common Details

↓

Step 3

Category Details

↓

Step 4

Questions

↓

Step 5

Preview

↓

Submit

Display a progress bar.

=====================================================

CATEGORY SELECTION

=====================================================

Show all categories as responsive cards.

Each card contains

Simple Icon

Category Name

Hover Effect

Selected State

=====================================================

COMMON DETAILS FORM

=====================================================

Fields

Item Name

Color

Location

Date

Time

Description

Upload Image

Use

Dropdowns

Date Picker

Time Picker

Textarea

Image Preview

=====================================================

CATEGORY DETAILS

=====================================================

Render dynamically.

Example

Phone

Brand

Model

Laptop

Brand

Model

Screen Size

Book

Title

Author

etc.

=====================================================

QUESTIONS

=====================================================

Display Yes/No questions using radio buttons.

Display text question using textarea.

=====================================================

PREVIEW PAGE

=====================================================

Show

Category

Image

Common Details

Additional Details

Question Answers

Buttons

Edit

Submit

=====================================================

MY REPORTS PAGE

=====================================================

Tabs

Lost Reports

Found Reports

Filters

Searching

Matched

Completed

Cancelled

Search Bar

Sort

Newest

Oldest

Highest Match

Report Card

Image

Status

Category

Location

Date

Buttons

View

Edit

Delete

=====================================================

NOTIFICATIONS PAGE

=====================================================

Display

Notification Card

Title

Message

Date

Similarity

View Match Button

Unread notifications should have a small blue indicator.

=====================================================

MATCH DETAILS PAGE

=====================================================

Display

Lost Report

Found Report

Similarity Breakdown

Image Similarity

Brand & Model

Description

Color

Location

Questions

Overall Score

Buttons

Verify Ownership

=====================================================

PROFILE PAGE

=====================================================

Profile Picture

Student Name

Roll Number

Department

Year

Section

College Email

Buttons

Change Password

Logout

=====================================================

FORMS

=====================================================

Every form should have

Required indicators

Inline validation

Error messages

Success messages

Loading state

=====================================================

BUTTONS

=====================================================

Primary

Blue

Secondary

White

Danger

Red

Disabled

Gray

=====================================================

TABLES

=====================================================

Use responsive tables only where required.

Otherwise use cards.

=====================================================

RESPONSIVENESS

=====================================================

Desktop

Laptop

Tablet

Mobile

No horizontal scrolling.

=====================================================

LOADING STATES

=====================================================

Skeleton Cards

Loading Spinner

Progress Indicator

=====================================================

EMPTY STATES

=====================================================

No Reports Found

No Notifications

No Matches

No Search Results

=====================================================

ERROR PAGES

=====================================================

404

500

Unauthorized

=====================================================

TOAST NOTIFICATIONS

=====================================================

Show

Success

Error

Warning

Info

=====================================================

THEME

=====================================================

Light Mode only.

Do not implement Dark Mode.

=====================================================

COLOR SYSTEM

=====================================================

Primary

#2563EB

Background

#F8FAFC

Card

#FFFFFF

Text

#1F2937

Border

#E5E7EB

Success

#22C55E

Warning

#F59E0B

Danger

#EF4444

=====================================================

ANIMATIONS

=====================================================

Only

Fade

Slide

Button Hover

Card Hover

Loading Spinner

Nothing else.

=====================================================

ACCESSIBILITY

=====================================================

Proper labels

Keyboard navigation

ARIA labels

Responsive fonts

=====================================================

IMPORTANT

Every page must use reusable React components.

Do not duplicate code.

Keep components modular.

The UI should look like a genuine college software application, not an AI-generated landing page or startup website.

Generate production-ready frontend code.

Continue developing the FindIt Campus project.

Follow every requirement from Parts 1–5 exactly.

Do not remove or modify any previous functionality.

Generate the complete backend architecture using Flask.

=====================================================

BACKEND TECHNOLOGY

=====================================================

Framework

Python Flask

Database

PostgreSQL

ORM

SQLAlchemy

Authentication

JWT

Password Encryption

bcrypt

Validation

Marshmallow or Pydantic

Environment Variables

python-dotenv

File Upload

Werkzeug

AI

YOLOv8

OpenCV

EasyOCR

Sentence Transformers

FAISS

=====================================================

BACKEND FOLDER STRUCTURE

=====================================================

backend/

app.py

config.py

requirements.txt

.env

database/

connection.py

seed.py

models/

student.py

account.py

lost_item.py

found_item.py

question_answer.py

notification.py

match.py

claim.py

routes/

auth_routes.py

lost_routes.py

found_routes.py

match_routes.py

notification_routes.py

claim_routes.py

profile_routes.py

controllers/

auth_controller.py

lost_controller.py

found_controller.py

match_controller.py

notification_controller.py

claim_controller.py

profile_controller.py

services/

auth_service.py

lost_service.py

found_service.py

match_service.py

notification_service.py

claim_service.py

image_service.py

ocr_service.py

embedding_service.py

color_service.py

middleware/

jwt_auth.py

error_handler.py

validators.py

ai/

yolo_detector.py

opencv_matcher.py

ocr_reader.py

sentence_matcher.py

faiss_engine.py

uploads/

lost/

found/

utils/

helpers.py

constants.py

logger.py

=====================================================

API DESIGN

=====================================================

Follow REST API principles.

Return JSON only.

Use standard HTTP status codes.

200

201

400

401

403

404

500

=====================================================

AUTHENTICATION APIs

=====================================================

POST

/api/auth/register

POST

/api/auth/login

POST

/api/auth/logout

POST

/api/auth/change-password

=====================================================

PROFILE APIs

=====================================================

GET

/api/profile

PUT

/api/profile/password

=====================================================

LOST ITEM APIs

=====================================================

POST

/api/lost/report

GET

/api/lost

GET

/api/lost/{id}

PUT

/api/lost/{id}

DELETE

/api/lost/{id}

=====================================================

FOUND ITEM APIs

=====================================================

POST

/api/found/report

GET

/api/found

GET

/api/found/{id}

PUT

/api/found/{id}

DELETE

/api/found/{id}

=====================================================

MATCH APIs

=====================================================

POST

/api/match/run

GET

/api/match/{id}

GET

/api/matches

=====================================================

CLAIM APIs

=====================================================

POST

/api/claim/create

POST

/api/claim/verify

POST

/api/claim/approve

POST

/api/claim/reject

GET

/api/claims

=====================================================

NOTIFICATION APIs

=====================================================

GET

/api/notifications

PUT

/api/notifications/read

DELETE

/api/notifications/{id}

=====================================================

VALIDATION

=====================================================

Validate every request.

Required fields.

Correct data types.

Maximum image size.

Allowed image formats.

JWT authentication.

=====================================================

FILE UPLOAD

=====================================================

Allowed

jpg

jpeg

png

Maximum

5 MB

Automatically rename files using UUID.

Store uploads separately.

uploads/lost/

uploads/found/

=====================================================

DATABASE OPERATIONS

=====================================================

Create

Read

Update

Delete

Soft delete reports.

Never permanently remove completed reports.

=====================================================

BACKGROUND TASKS

=====================================================

After submitting a Lost Report

Run AI Matching automatically.

After submitting a Found Report

Run AI Matching automatically.

Background tasks should not block user requests.

=====================================================

AI SERVICES

=====================================================

Each AI model should have its own service.

YOLO

Detect object.

OpenCV

Compare visual features.

EasyOCR

Extract visible text.

Sentence Transformer

Compare descriptions.

FAISS

Fast nearest-neighbour search.

=====================================================

LOGGING

=====================================================

Log

Login

Registration

Report Submission

AI Matching

Errors

Claims

=====================================================

ERROR HANDLING

=====================================================

Return clean JSON responses.

Example

{
"success": false,
"message": "Invalid Credentials"
}

=====================================================

SUCCESS RESPONSE

=====================================================

{
"success": true,
"message": "Lost Report Submitted Successfully",
"data": {}
}

=====================================================

SECURITY

=====================================================

Hash passwords.

JWT Authentication.

Prevent SQL Injection.

Validate all inputs.

Protect every private endpoint.

Never expose sensitive information.

=====================================================

IMPORTANT

Use a modular architecture.

Controllers should only handle requests.

Business logic must remain inside Services.

Models should contain only database definitions.

Routes should remain clean.

Generate production-quality backend code.

Continue developing the FindIt Campus project.

Follow Parts 1 to 6 exactly.

Do not modify any previous functionality.

This is the final integration phase.

Everything should now become a complete production-ready application.

=====================================================

DATABASE

=====================================================

Use PostgreSQL.

Generate complete SQL schema.

Generate SQLAlchemy models.

Generate relationships.

Generate indexes.

Generate foreign keys.

=====================================================

TABLES

=====================================================

Students

Accounts

Lost_Items

Found_Items

Question_Answers

Matches

Notifications

Claims

=====================================================

STUDENTS

=====================================================

Fields

student_id

roll_number

student_name

department

year

section

college_email

created_at

=====================================================

ACCOUNTS

=====================================================

account_id

student_id

password_hash

last_login

status

created_at

=====================================================

LOST_ITEMS

=====================================================

report_id

student_id

category

item_name

color

location

date

time

description

image_path

additional_details (JSON)

status

created_at

updated_at

=====================================================

FOUND_ITEMS

=====================================================

Same structure as Lost_Items.

=====================================================

QUESTION_ANSWERS

=====================================================

answer_id

report_type

report_id

question

answer

created_at

=====================================================

MATCHES

=====================================================

match_id

lost_report_id

found_report_id

image_score

brand_score

description_score

color_score

location_score

question_score

overall_score

created_at

=====================================================

NOTIFICATIONS

=====================================================

notification_id

student_id

title

message

is_read

created_at

=====================================================

CLAIMS

=====================================================

claim_id

match_id

student_id

verification_score

status

created_at

=====================================================

DATABASE RELATIONSHIPS

=====================================================

One Student

↓

Many Reports

One Report

↓

Many Question Answers

One Match

↓

One Claim

One Student

↓

Many Notifications

=====================================================

PERFORMANCE

=====================================================

Optimize database queries.

Use indexes on

Category

Location

Date

Student ID

Status

Overall Score

=====================================================

SEARCH

=====================================================

Allow searching by

Item Name

Category

Location

Status

=====================================================

FILTERS

=====================================================

Filter reports by

Searching

Matched

Completed

Cancelled

Newest

Oldest

=====================================================

SORTING

=====================================================

Sort reports

Newest First

Oldest First

Highest Similarity

=====================================================

PAGINATION

=====================================================

Use pagination.

Default

10 reports per page.

=====================================================

IMAGE OPTIMIZATION

=====================================================

Compress uploaded images.

Generate thumbnails.

Store original image.

=====================================================

PROJECT CONFIGURATION

=====================================================

Create

.env.example

README.md

requirements.txt

package.json

.gitignore

=====================================================

README

=====================================================

Include

Project Description

Features

Technology Stack

Folder Structure

Installation

Database Setup

Backend Setup

Frontend Setup

Environment Variables

Running Locally

Future Scope

=====================================================

INSTALLATION

=====================================================

Backend

python -m venv venv

pip install -r requirements.txt

python seed.py

python app.py

Frontend

npm install

npm run dev

=====================================================

TESTING

=====================================================

Test

Registration

Login

JWT

Lost Report

Found Report

Image Upload

AI Matching

Notifications

Claim Verification

Profile

Logout

=====================================================

ERROR TESTING

=====================================================

Wrong Password

Invalid Image

Missing Fields

Expired JWT

Duplicate Registration

Invalid Report

=====================================================

DEPLOYMENT

=====================================================

Frontend

Vercel

Backend

Render

Railway

or VPS

Database

PostgreSQL

=====================================================

FUTURE SCOPE

=====================================================

Cloudinary Storage

Email Notifications

Push Notifications

QR Code Item Verification

Faculty Portal

Admin Dashboard

Mobile App

Multiple Colleges

Live Camera Detection

=====================================================

PROJECT QUALITY

=====================================================

Generate production-quality code.

No placeholder components.

No incomplete APIs.

No TODO comments.

No fake implementations.

Everything should work together.

=====================================================

CODING STANDARDS

=====================================================

Follow PEP8.

Use TypeScript best practices.

Use reusable components.

Keep code modular.

Follow SOLID principles.

Use meaningful variable names.

Write clean comments only where necessary.

=====================================================

FINAL REQUIREMENTS

=====================================================

The project should feel like a real software application built by engineering students.

It should NOT look like an AI-generated website.

Prioritize usability, maintainability, and clean architecture over flashy UI.

The final output should include:

• Complete frontend
• Complete backend
• Complete PostgreSQL database
• Complete AI integration
• Fully working REST APIs
• Authentication
• Responsive UI
• Notifications
• Ownership verification
• AI Matching Engine
• Modular architecture
• Documentation
• Deployment-ready project

Generate every module completely and ensure that all parts integrate correctly into one working application.