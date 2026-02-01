# User Flows Documentation

This document outlines all user flows in the GC Closet Manager application, covering both frontend (React Native) and backend (FastAPI) interactions.

## 1. Authentication Flows

### 1.1 User Registration Flow
**Frontend Path:** `LandingScreen → RegistrationScreen → MainApp`

1. User opens app → Lands on `LandingScreen`
2. User taps "Sign Up" → Navigates to `RegistrationScreen`
3. User enters:
   - Name
   - Email
   - Password
4. Frontend calls: `POST /api/v1/auth/register`
5. Backend validates input, creates user in Supabase
6. Backend returns: `AuthResponse` with user data and access token
7. Frontend stores token in AsyncStorage
8. Frontend navigates to `MainApp` (Home tab)

**Backend Endpoints:**
- `POST /api/v1/auth/register` - Creates new user account

### 1.2 User Login Flow
**Frontend Path:** `LandingScreen → LoginScreen → MainApp`

1. User opens app → Lands on `LandingScreen`
2. User taps "Login" → Navigates to `LoginScreen`
3. User enters email and password
4. Frontend calls: `POST /api/v1/auth/login`
5. Backend validates credentials against Supabase
6. Backend generates JWT access token and refresh token
7. Backend returns: `AuthResponse` with tokens and user data
8. Frontend stores tokens in AsyncStorage
9. Frontend navigates to `MainApp` (Home tab)

**Backend Endpoints:**
- `POST /api/v1/auth/login` - Authenticates user

### 1.3 User Logout Flow
**Frontend Path:** `ProfileScreen → LandingScreen`

1. User navigates to `ProfileScreen`
2. User taps "Logout"
3. Frontend calls: `POST /api/v1/auth/logout`
4. Backend invalidates session (optional)
5. Frontend clears AsyncStorage (tokens, user data)
6. Frontend navigates to `LandingScreen`

**Backend Endpoints:**
- `POST /api/v1/auth/logout` - Logs out user

### 1.4 Password Reset Flow
**Frontend Path:** `LoginScreen → Password Reset`

1. User on `LoginScreen` taps "Forgot Password"
2. User enters email
3. Frontend calls: `POST /api/v1/auth/reset-password`
4. Backend sends password reset email via Supabase
5. User receives email with reset link
6. User resets password via email link

**Backend Endpoints:**
- `POST /api/v1/auth/reset-password` - Sends reset email

### 1.5 Token Refresh Flow
**Frontend Path:** Automatic (background)

1. Frontend detects access token is expired
2. Frontend calls: `POST /api/v1/auth/refresh` with refresh token
3. Backend validates refresh token
4. Backend generates new access token
5. Frontend updates stored access token

**Backend Endpoints:**
- `POST /api/v1/auth/refresh` - Refreshes access token

## 2. Clothing Item Management Flows

### 2.1 Add Clothing Item Flow
**Frontend Path:** `HomeScreen → AddClothesScreen → (AI Processing) → HomeScreen`

1. User on `HomeScreen` taps "Add Item" button
2. User selects category (Tops, Bottoms, Shoes, etc.)
3. User selects image source (Camera or Gallery)
4. User captures/selects image
5. Frontend navigates to `AddClothesScreen` with image URI
6. Frontend calls: `POST /api/v1/upload/smart-upload-async` with base64 image
7. Backend processes in parallel:
   - Background removal (rembg)
   - Clothing classification (TensorFlow)
   - Season detection
   - Title generation
8. Backend returns processed image and metadata
9. Frontend displays processed image and AI suggestions:
   - Category (auto-detected)
   - Season (auto-detected)
   - Title suggestions
10. User reviews/edits:
    - Item name (from AI suggestions or manual)
    - Category (can override AI)
    - Seasons (can select multiple)
11. User taps "Save"
12. Frontend calls: `POST /api/v1/clothes` with item data
13. Backend uploads image to Supabase Storage
14. Backend creates clothing item record in database
15. Backend returns: `ClothingItemResponse`
16. Frontend refreshes clothing items list
17. Frontend navigates back to `HomeScreen`

**Backend Endpoints:**
- `POST /api/v1/upload/smart-upload-async` - AI processing
- `POST /api/v1/clothes` - Create clothing item
- `POST /api/v1/upload/unified` - Image upload to storage

### 2.2 View Clothing Items Flow
**Frontend Path:** `HomeScreen` or `ClosetScreen`

1. User navigates to `HomeScreen` or `ClosetScreen`
2. Frontend calls: `GET /api/v1/clothes`
3. Backend retrieves all clothing items for current user
4. Backend returns: `ClothingItemsResponse` with array of items
5. Frontend groups items by category
6. Frontend displays items in category sections

**Backend Endpoints:**
- `GET /api/v1/clothes` - Get all clothing items

### 2.3 Get Clothing Item by Category Flow
**Frontend Path:** `HomeScreen` or `SearchScreen`

1. User filters by category (e.g., "Tops")
2. Frontend calls: `GET /api/v1/clothes/category/{category}`
3. Backend filters items by category
4. Backend returns: `ClothingItemsResponse` with filtered items
5. Frontend displays filtered results

**Backend Endpoints:**
- `GET /api/v1/clothes/category/{category}` - Get items by category

### 2.4 Get Clothing Items by Season Flow
**Frontend Path:** `SearchScreen`

1. User selects season filter (Spring, Summer, Fall, Winter)
2. Frontend calls: `GET /api/v1/clothes/season/{season}`
3. Backend filters items by season
4. Backend returns: `ClothingItemsResponse` with filtered items
5. Frontend displays filtered results

**Backend Endpoints:**
- `GET /api/v1/clothes/season/{season}` - Get items by season

### 2.5 Update Clothing Item Flow
**Frontend Path:** `ClosetScreen → Item Details → Edit → Save`

1. User navigates to `ClosetScreen`
2. User taps on a clothing item
3. User taps "Edit"
4. User modifies:
   - Name
   - Category
   - Seasons
   - Description
5. Frontend calls: `PUT /api/v1/clothes/{item_id}`
6. Backend updates clothing item in database
7. Backend returns: `ClothingItemResponse` with updated item
8. Frontend refreshes item display

**Backend Endpoints:**
- `PUT /api/v1/clothes/{item_id}` - Update clothing item

### 2.6 Delete Clothing Item Flow
**Frontend Path:** `ClosetScreen → Item Details → Delete`

1. User navigates to `ClosetScreen`
2. User taps on a clothing item
3. User taps "Delete"
4. Frontend confirms deletion
5. Frontend calls: `DELETE /api/v1/clothes/{item_id}`
6. Backend deletes image from Supabase Storage
7. Backend deletes clothing item from database
8. Backend returns: `DeleteResponse`
9. Frontend removes item from list

**Backend Endpoints:**
- `DELETE /api/v1/clothes/{item_id}` - Delete clothing item

## 3. Avatar & Virtual Try-On Flows

### 3.1 Upload Avatar Flow
**Frontend Path:** `AvatarScreen → Camera/Gallery → Processing → AvatarScreen`

1. User navigates to `AvatarScreen`
2. User taps "Upload Avatar" or "Take Photo"
3. User selects/captures image
4. Frontend calls: `POST /api/v1/avatar/upload` with image file
5. Backend processes avatar:
   - Uploads to Supabase Storage
   - Runs MediaPipe pose detection
   - Calculates quality score
   - Creates avatar record
6. Backend returns: `AvatarResponse` with avatar data
7. Frontend displays avatar with quality score
8. Frontend stores avatar ID for try-on

**Backend Endpoints:**
- `POST /api/v1/avatar/upload` - Upload and process avatar

### 3.2 Get User Avatar Flow
**Frontend Path:** `AvatarScreen` (on load)

1. User navigates to `AvatarScreen`
2. Frontend calls: `GET /api/v1/avatar`
3. Backend retrieves user's current avatar
4. Backend returns: `AvatarResponse` with avatar data
5. Frontend displays avatar if exists, else shows upload prompt

**Backend Endpoints:**
- `GET /api/v1/avatar` - Get user's avatar

### 3.3 Virtual Try-On Flow
**Frontend Path:** `DressingRoomScreen → Select Items → Try-On → Result`

1. User navigates to `DressingRoomScreen`
2. User selects clothing items:
   - Top (required)
   - Bottom (optional)
   - Shoes (optional)
   - Accessories (optional)
   - Outerwear (optional)
3. User taps "Try On" button
4. Frontend calls: `POST /api/v1/avatar/try-on` with:
   - `avatar_id`
   - `clothing_item_id` (top)
5. Backend processes try-on:
   - Retrieves avatar image
   - Retrieves clothing item image
   - Runs VITON (Virtual Try-On) model
   - Generates try-on result image
6. Backend saves try-on result to database
7. Backend returns: Try-on result with image URL
8. Frontend displays try-on result
9. User can save outfit or try different items

**Backend Endpoints:**
- `POST /api/v1/avatar/try-on` - Perform virtual try-on

### 3.4 Get Try-On History Flow
**Frontend Path:** `AvatarScreen → History`

1. User navigates to `AvatarScreen`
2. User taps "Try-On History"
3. Frontend calls: `GET /api/v1/avatar/try-on/history?limit=20`
4. Backend retrieves user's try-on results
5. Backend returns: Array of try-on results
6. Frontend displays history grid

**Backend Endpoints:**
- `GET /api/v1/avatar/try-on/history` - Get try-on history

## 4. Outfit Management Flows

### 4.1 Create Outfit from Items Flow
**Frontend Path:** `DressingRoomScreen → Select Items → Create Outfit → OutfitsScreen`

1. User navigates to `DressingRoomScreen`
2. User selects clothing items for outfit
3. User taps "Create Outfit"
4. Frontend calls: `POST /api/v1/outfits/generate` with:
   - `name`
   - `clothing_item_ids` (array)
   - `season` (optional)
   - `occasion` (optional)
   - `description` (optional)
5. Backend validates clothing items belong to user
6. Backend creates outfit record in database
7. Backend returns: `OutfitResponse` with outfit data
8. Frontend navigates to `OutfitsScreen`
9. Frontend displays new outfit

**Backend Endpoints:**
- `POST /api/v1/outfits/generate` - Create outfit from items

### 4.2 Create Outfit with Images Flow
**Frontend Path:** `OutfitsScreen → Create → Upload Images → Save`

1. User navigates to `OutfitsScreen`
2. User taps "Create Outfit"
3. User selects multiple images
4. User enters outfit details:
   - Name
   - Description
   - Season
   - Occasion
   - Weather condition
   - Rating
   - Tags
5. Frontend calls: `POST /api/v1/outfits/upload` with:
   - Form data (name, description, etc.)
   - Multiple image files
6. Backend uploads images to Supabase Storage
7. Backend creates outfit record with image paths
8. Backend returns: `OutfitResponse` with outfit data
9. Frontend displays new outfit

**Backend Endpoints:**
- `POST /api/v1/outfits/upload` - Create outfit with images

### 4.3 View Outfits Flow
**Frontend Path:** `OutfitsScreen`

1. User navigates to `OutfitsScreen`
2. Frontend calls: `GET /api/v1/outfits?limit=20&offset=0`
3. Backend retrieves user's outfits with pagination
4. Backend returns: `OutfitsResponse` with outfits array
5. Frontend displays outfits in grid/list view

**Backend Endpoints:**
- `GET /api/v1/outfits` - Get user's outfits

### 4.4 Filter Outfits Flow
**Frontend Path:** `OutfitsScreen → Filter`

1. User navigates to `OutfitsScreen`
2. User applies filters:
   - Season
   - Occasion
   - Weather condition
   - Favorite status
   - Date range
   - Minimum rating
   - Tags
3. Frontend calls: `POST /api/v1/outfits/filter` with filter criteria
4. Backend applies filters to query
5. Backend returns: `OutfitsResponse` with filtered outfits
6. Frontend displays filtered results

**Backend Endpoints:**
- `POST /api/v1/outfits/filter` - Filter outfits

### 4.5 Get Outfit Details Flow
**Frontend Path:** `OutfitsScreen → Outfit Card → Details`

1. User navigates to `OutfitsScreen`
2. User taps on an outfit card
3. Frontend calls: `GET /api/v1/outfits/{outfit_id}/details`
4. Backend retrieves outfit with associated clothing items
5. Backend returns: Outfit details with clothing items array
6. Frontend displays outfit details with clothing items

**Backend Endpoints:**
- `GET /api/v1/outfits/{outfit_id}/details` - Get outfit with items

### 4.6 Update Outfit Flow
**Frontend Path:** `OutfitsScreen → Outfit Details → Edit → Save`

1. User navigates to outfit details
2. User taps "Edit"
3. User modifies outfit properties
4. Frontend calls: `PUT /api/v1/outfits/{outfit_id}` with update data
5. Backend updates outfit in database
6. Backend returns: `OutfitResponse` with updated outfit
7. Frontend refreshes outfit display

**Backend Endpoints:**
- `PUT /api/v1/outfits/{outfit_id}` - Update outfit

### 4.7 Delete Outfit Flow
**Frontend Path:** `OutfitsScreen → Outfit Details → Delete`

1. User navigates to outfit details
2. User taps "Delete"
3. Frontend confirms deletion
4. Frontend calls: `DELETE /api/v1/outfits/{outfit_id}`
5. Backend deletes outfit images from storage
6. Backend deletes outfit record from database
7. Backend returns: `DeleteResponse`
8. Frontend removes outfit from list

**Backend Endpoints:**
- `DELETE /api/v1/outfits/{outfit_id}` - Delete outfit

## 5. Image Processing Flows

### 5.1 Background Removal Flow
**Frontend Path:** `AddClothesScreen → Remove Background`

1. User on `AddClothesScreen` with selected image
2. User taps "Remove Background"
3. Frontend calls: `POST /api/v1/upload/remove-background/base64` with base64 image
4. Backend processes image with rembg (U2Net model)
5. Backend returns: Processed image in base64
6. Frontend displays processed image
7. User can proceed with item creation

**Backend Endpoints:**
- `POST /api/v1/upload/remove-background/base64` - Remove background

### 5.2 Clothing Classification Flow
**Frontend Path:** `AddClothesScreen → AI Classification` (automatic)

1. User uploads image in `AddClothesScreen`
2. Frontend calls: `POST /api/v1/upload/classify-clothing` with base64 image
3. Backend runs TensorFlow model for classification
4. Backend returns:
   - Category (Tops, Bottoms, etc.)
   - ML label (t-shirt, jeans, etc.)
   - Confidence score
   - All category scores
5. Frontend auto-fills category suggestion

**Backend Endpoints:**
- `POST /api/v1/upload/classify-clothing` - Classify clothing

## 6. Search & Discovery Flows

### 6.1 Search Clothing Items Flow
**Frontend Path:** `SearchScreen` or `HomeScreen` (search bar)

1. User navigates to `SearchScreen` or uses search bar on `HomeScreen`
2. User enters search query
3. Frontend filters items client-side by:
   - Name (contains query)
   - Category (contains query)
4. Frontend displays filtered results in real-time
5. User can tap item to view details

### 6.2 Filter by Season Flow
**Frontend Path:** `SearchScreen → Season Filter`

1. User navigates to `SearchScreen`
2. User selects season (Spring, Summer, Fall, Winter)
3. Frontend filters items by selected season
4. Frontend displays items grouped by category for selected season
5. User can browse items by category within season

## 7. Profile Management Flows

### 7.1 View Profile Flow
**Frontend Path:** `ProfileScreen`

1. User navigates to `ProfileScreen` (from bottom tab)
2. Frontend calls: `GET /api/v1/auth/me` to get current user
3. Backend returns: User information
4. Frontend displays:
   - Profile picture
   - Name
   - Email
   - Statistics (item count, outfit count)

**Backend Endpoints:**
- `GET /api/v1/auth/me` - Get current user info

### 7.2 Update Profile Picture Flow
**Frontend Path:** `HomeScreen → Profile Picture → Camera/Gallery → Upload`

1. User on `HomeScreen` taps profile picture
2. User selects "Camera" or "Gallery"
3. User captures/selects image
4. Frontend calls: `POST /api/v1/upload/unified` with:
   - `bucket_name`: profile_pictures
   - Image file
5. Backend uploads to Supabase Storage
6. Backend updates user profile picture URL
7. Frontend refreshes profile picture display

**Backend Endpoints:**
- `POST /api/v1/upload/unified` - Upload profile picture

## 8. Data Loading & Caching Flows

### 8.1 Initial Data Load Flow
**Frontend Path:** `MainApp` (on app start)

1. User opens app (already authenticated)
2. Frontend checks AsyncStorage for cached data
3. Frontend calls: `GET /api/v1/clothes` (if cache expired)
4. Backend returns: All clothing items
5. Frontend caches data in memory and AsyncStorage
6. Frontend displays cached data immediately
7. Frontend refreshes in background if cache stale

### 8.2 Image Preloading Flow
**Frontend Path:** Background (automatic)

1. Frontend loads clothing items list
2. Frontend identifies critical images (visible items)
3. Frontend preloads images in background
4. Frontend caches images for faster display
5. Images display from cache when user scrolls

## Error Handling Flows

### Authentication Errors
- Invalid credentials → Show error message, stay on login screen
- Token expired → Auto-refresh token, retry request
- Refresh token expired → Redirect to login screen

### Network Errors
- Request timeout → Show retry option
- No internet → Show offline message, use cached data
- Server error → Show error message, log error

### Validation Errors
- Invalid input → Show field-specific error messages
- Missing required fields → Highlight missing fields
- File size too large → Show size limit message

## Notes

- All API requests include JWT token in Authorization header
- All image uploads use Supabase Storage
- All database operations use Supabase PostgreSQL
- AI processing (background removal, classification) is optional and gracefully degrades if unavailable
- Frontend implements optimistic updates where appropriate
- Frontend caches data to reduce API calls

