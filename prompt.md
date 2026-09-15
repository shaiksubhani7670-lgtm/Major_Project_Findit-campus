# ROLE

You are an expert team of Senior Software Engineers, UI/UX Designers, AI/ML Engineers, DevOps Engineers, and Database Architects.

Your task is to build a COMPLETE production-quality AI-powered Lost & Found Management System called "FindIt Campus".

Do NOT generate placeholders, dummy pages, or incomplete code. Generate fully working code with proper architecture, clean coding practices, reusable components, comments where necessary, and responsive design.

The final project should be suitable as a Final Year Engineering AI/ML Major Project.

====================================================================================

PROJECT NAME

FindIt Campus
AI-Powered Smart Lost & Found Management System for Colleges

====================================================================================

PROJECT OBJECTIVE

Students lose valuable items every day inside the college campus.

Instead of manually searching, they can report the lost item through the website.

Security staff privately upload found items.

Found items must NEVER be visible publicly.

An AI model automatically compares lost and found items using images, text descriptions, colors, brands, categories, location, and date.

When a high-confidence match is found, the system automatically notifies both parties.

The system should significantly reduce the time required to recover lost items.

====================================================================================

MAIN USERS

1. Student
2. Security Staff
3. Administrator

====================================================================================

TECH STACK

Frontend

• Next.js 15
• React 19
• TypeScript
• Tailwind CSS
• Framer Motion
• GSAP
• Shadcn UI
• React Hook Form
• React Query
• Axios
• React Icons
• Lottie
• Lucide Icons

Backend

• Python
• Flask
• Flask REST API
• SQLAlchemy
• JWT Authentication
• Flask Mail
• Celery
• Redis

Database

• PostgreSQL

Machine Learning

• YOLOv8
• OpenCV
• TensorFlow
• PyTorch
• Sentence Transformers
• EasyOCR
• Scikit-Learn
• FAISS
• NumPy
• Pandas

Storage

• Cloudinary

Deployment

• Vercel
• Render

====================================================================================

UI STYLE

The UI should look premium like

Apple
Stripe
Linear
Framer
Notion
Vercel

Use

Glassmorphism

Neumorphism

Gradient Borders

Floating Cards

Animated Background

Modern Typography

Blur Effects

Premium Shadows

Rounded Components

Micro Interactions

Smooth Hover Effects

Premium Dashboard

====================================================================================

COLOR PALETTE

Primary

#2563EB

Secondary

#7C3AED

Accent

#06B6D4

Background

#030712

Cards

rgba(255,255,255,0.08)

Text

White

====================================================================================

ANIMATIONS

Use Framer Motion on every page.

Include

Fade

Slide

Scale

Zoom

Rotate

Hover Lift

Card Flip

Parallax

Scroll Reveal

Animated Counters

Typing Effect

Animated Blob Background

Floating Objects

Button Ripple

Cursor Glow

Smooth Page Transition

Loading Skeleton

Animated Progress Bar

Animated Charts

Magnetic Buttons

Animated Sidebar

Glass Navbar

Animated Footer

====================================================================================

LANDING PAGE

Beautiful Hero Section

Animated Title

3D Floating Lost Items

Laptop

Phone

Wallet

Keys

Bag

Bottle

Watch

ID Card

Animated Search Box

Call To Action

Statistics

How It Works

Features

Benefits

AI Matching Demo

Testimonials

FAQ

Contact

Footer

====================================================================================

STUDENT FEATURES

Student Dashboard

Profile

Report Lost Item

Track Reports

Notification Center

Claim History

Settings

Dark Mode

====================================================================================

STAFF FEATURES

Staff Login

Upload Found Item

Verify Item

Approve Claims

Reject Fake Claims

View AI Matches

Notification Center

====================================================================================

ADMIN FEATURES

Admin Dashboard

Manage Students

Manage Staff

Manage Reports

Analytics

System Logs

ML Accuracy

Heatmap

Settings

====================================================================================

LOST ITEM FORM

Student Name

Roll Number

Department

Phone Number

College Email

Item Name

Category

Brand

Primary Color

Secondary Color

Material

Description

Lost Date

Lost Time

Building

Floor

Room Number

Exact Location

Reward

Upload Multiple Images

====================================================================================

FOUND ITEM FORM

Security Staff Name

Security Office

Item Name

Category

Brand

Detected Color

Manual Color

Material

Description

Found Date

Found Time

Building

Floor

Room Number

Exact Location

Upload Multiple Images

Current Status

====================================================================================

ITEM CATEGORIES

Laptop

Mobile

Wallet

Watch

Keys

ID Card

Bag

Bottle

Books

Earbuds

Headphones

Calculator

Power Bank

Helmet

Shoes

Jewelry

USB Drive

Clothes

Umbrella

Other

====================================================================================

DATABASE

Create proper PostgreSQL database with relationships.

Tables

Students

Staff

Admins

LostItems

FoundItems

Notifications

Claims

Matches

Logs

Sessions

====================================================================================

IMAGE PROCESSING

When image uploads

Resize

Compress

Remove Background

Enhance

Extract Features

Store Embeddings

====================================================================================

AI MODEL

Build an intelligent AI matching system.

Step 1

YOLOv8

Detect object

Examples

Laptop

Bottle

Wallet

Phone

Watch

Bag

Keys

Helmet

Book

ID Card

Step 2

OpenCV

Extract

Shape

Texture

Edges

Pattern

Color

Size

Step 3

Color Detection

HSV

Dominant Color

Secondary Color

Color Percentage

Step 4

OCR

EasyOCR

Read

Name

Roll Number

Sticker

Book Name

Laptop Label

ID Card Text

Step 5

Sentence Transformer

Convert descriptions into embeddings

Examples

Lost

Blue Wildcraft Bag

Found

Dark Blue Wildcraft Backpack

Understand semantic similarity.

Step 6

FAISS

Store embeddings

Perform nearest neighbor search

Step 7

Similarity Score

Image Similarity

40%

Text Similarity

25%

Color

10%

Brand

10%

Location

10%

Date

5%

Generate Final Confidence Score

====================================================================================

MATCH CONFIDENCE

95-100

Very High Match

Automatically Notify

80-94

High Match

Recommend to Staff

65-79

Possible Match

Needs Manual Review

Below 65

No Match

====================================================================================

SEARCH ENGINE

Natural Language Search

Examples

"I lost my black HP laptop"

"My blue Wildcraft bag"

"Wallet near CSE Block"

Use AI search.

====================================================================================

NOTIFICATIONS

Website Notification

Email

SMS Ready Architecture

WhatsApp Ready Architecture

====================================================================================

CLAIM PROCESS

Student requests item.

Staff verifies.

Admin approves if required.

Status

Pending

Approved

Rejected

Collected

====================================================================================

ANALYTICS

Lost Items per Month

Recovered Items

Recovery Rate

Average Recovery Time

Popular Locations

Most Lost Categories

Department Statistics

Charts

Heatmaps

====================================================================================

SECURITY

JWT Authentication

Role Based Access

Password Hashing

CSRF

Rate Limiting

Input Validation

Image Validation

SQL Injection Protection

Secure File Upload

====================================================================================

RESPONSIVE DESIGN

Desktop

Laptop

Tablet

Mobile

====================================================================================

ACCESSIBILITY

ARIA Labels

Keyboard Navigation

Screen Reader Support

High Contrast Mode

====================================================================================

PROJECT STRUCTURE

frontend/

backend/

database/

ml/

training/

datasets/

models/

uploads/

api/

utils/

scripts/

docs/

====================================================================================

BONUS AI FEATURES

Duplicate Lost Report Detection

Auto Category Detection

Auto Brand Detection

Background Removal

Image Enhancement

AI Chatbot

Voice Search

QR Scanner

Barcode Scanner

Smart Suggestions

AI Recommendations

====================================================================================

DELIVERABLES

Generate the ENTIRE project.

Include

Complete Frontend

Complete Backend

Complete PostgreSQL Database

Complete Flask REST API

Complete AI Model

Training Scripts

Inference Scripts

Model Integration

Authentication

Notification System

Dashboards

Documentation

README

API Documentation

Deployment Guide

Testing

Folder Structure

Database Schema

ER Diagram

Flowchart

UI Assets

Animations

Sample Dataset

Seed Data

Requirements.txt

package.json

Docker Support

Everything should be production-ready, cleanly organized, fully functional, and without placeholders or incomplete sections.