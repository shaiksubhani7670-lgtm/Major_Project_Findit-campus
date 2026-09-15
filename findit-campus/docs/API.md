# FindIt Campus — API Reference

All requests must use `Content-Type: application/json`. Authenticated routes require `Authorization: Bearer <JWT_ACCESS_TOKEN>`.

---

## Authentication

### `POST /api/auth/register`
Create a new user.
- **Request Body:**
  ```json
  {
    "email": "student@college.edu",
    "password": "Password123",
    "full_name": "Rahul Verma",
    "phone": "+919876543210",
    "role": "student",
    "roll_number": "CSE2021001",
    "department": "Computer Science",
    "year_of_study": 3,
    "section": "A"
  }
  ```
- **Response (201):**
  ```json
  {
    "success": true,
    "message": "Registration successful",
    "data": {
      "user": { ... },
      "access_token": "...",
      "refresh_token": "..."
    }
  }
  ```

### `POST /api/auth/login`
Authenticate and return JWT tokens.
- **Request Body:**
  ```json
  {
    "email": "student@college.edu",
    "password": "Password123"
  }
  ```
- **Response (200):**
  ```json
  {
    "success": true,
    "data": {
      "user": { ... },
      "access_token": "...",
      "refresh_token": "..."
    }
  }
  ```

### `POST /api/auth/refresh`
Obtain a new access token. Requires Bearer Refresh Token.
- **Response (200):**
  ```json
  {
    "success": true,
    "data": {
      "access_token": "..."
    }
  }
  ```

---

## Lost Items (Student Routes)

### `POST /api/lost-items/`
Report a lost item.
- **Request Body:**
  ```json
  {
    "item_name": "HP Laptop",
    "category": "laptop",
    "brand": "HP",
    "primary_color": "Silver",
    "description": "HP Pavilion 15 with a blue sticker on top",
    "lost_date": "2026-07-01",
    "lost_time": "14:30:00",
    "building": "CSE Block",
    "floor": "2nd Floor",
    "room_number": "204",
    "exact_location": "On bench near lab entrance",
    "reward": "500 Rupees",
    "images": ["url1", "url2"]
  }
  ```

### `GET /api/lost-items/`
List reports. Students see their own reports. Staff/Admin see all reports.
- **Parameters:** `category`, `status`, `building`, `search`, `page`, `per_page`

---

## Found Items (Staff Routes)

### `POST /api/found-items/`
Log a found item. (Staff/Admin only)
- **Request Body:**
  ```json
  {
    "item_name": "HP Laptop",
    "category": "laptop",
    "brand": "HP",
    "found_date": "2026-07-01",
    "building": "CSE Block",
    "description": "HP Laptop found in room 204",
    "storage_location": "Locker A1"
  }
  ```

---

## AI Matches

### `GET /api/matches/`
Get matches.
- **Parameters:** `confidence`, `status`, `min_score`

### `PATCH /api/matches/<id>/confirm`
Confirm an AI match. (Staff/Admin only)
- **Request Body:** `{"notes": "Verified name under label matches owner"}`

---

## Claims

### `POST /api/claims/`
Submit a claim.
- **Request Body:** `{"match_id": 1, "description": "It has my name on the label.", "proof_images": []}`

### `PATCH /api/claims/<id>/verify`
Verify claim. (Staff/Admin only)
- **Request Body:** `{"action": "approve", "notes": "Student verified details"}`
