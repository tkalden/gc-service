# GC Closet Manager - Architecture Diagrams

This document provides comprehensive architecture diagrams for the GC Closet Manager application.

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Backend Architecture](#backend-architecture)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Deployment Architecture](#deployment-architecture)
7. [Technology Stack](#technology-stack)

---

## System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Mobile[React Native App<br/>iOS & Android]
    end
    
    subgraph "API Gateway"
        FastAPI[FastAPI Backend<br/>REST API]
    end
    
    subgraph "Services Layer"
        Auth[Authentication Service]
        Clothing[Clothing Service]
        Outfit[Outfit Service]
        Avatar[Avatar Service]
        AI[AI Processing Service]
        Storage[Storage Service]
    end
    
    subgraph "Data Layer"
        SupabaseDB[(Supabase PostgreSQL<br/>Database)]
        SupabaseStorage[(Supabase Storage<br/>S3 Compatible)]
    end
    
    subgraph "AI Models"
        TFModel[TensorFlow Model<br/>Clothing Classification]
        RembgModel[U²-Net Model<br/>Background Removal]
        MediaPipe[MediaPipe<br/>Pose Detection]
    end
    
    Mobile -->|HTTPS/REST| FastAPI
    FastAPI --> Auth
    FastAPI --> Clothing
    FastAPI --> Outfit
    FastAPI --> Avatar
    FastAPI --> AI
    FastAPI --> Storage
    
    Auth --> SupabaseDB
    Clothing --> SupabaseDB
    Outfit --> SupabaseDB
    Avatar --> SupabaseDB
    
    Storage --> SupabaseStorage
    AI --> TFModel
    AI --> RembgModel
    AI --> MediaPipe
```

---

## High-Level Architecture

```mermaid
graph LR
    subgraph "Frontend - React Native"
        UI[UI Components]
        Screens[Screen Components]
        Services[Service Layer]
        Cache[Cache Layer]
    end
    
    subgraph "Backend - FastAPI"
        API[API Routes]
        Middleware[Middleware]
        ServicesBackend[Business Logic]
        Models[Data Models]
    end
    
    subgraph "External Services"
        Supabase[(Supabase)]
        AI[AI Models]
    end
    
    UI --> Screens
    Screens --> Services
    Services --> Cache
    Services -->|HTTP/HTTPS| API
    
    API --> Middleware
    Middleware --> ServicesBackend
    ServicesBackend --> Models
    ServicesBackend --> Supabase
    ServicesBackend --> AI
```

---

## Frontend Architecture

```mermaid
graph TD
    subgraph "Presentation Layer"
        App[App.tsx<br/>Root Component]
        Nav[Navigation Stack]
        Tabs[Bottom Tab Navigator]
    end
    
    subgraph "Screen Components"
        Home[HomeScreen]
        Closet[ClosetScreen]
        Explore[ExploreScreen]
        Outfits[OutfitsScreen]
        Profile[ProfileScreen]
        AddClothes[AddClothesScreen]
        Avatar[AvatarScreen]
        DressingRoom[DressingRoomScreen]
        Search[SearchScreen]
    end
    
    subgraph "UI Components"
        Cards[ClothingItemCard]
        Headers[CommonHeader]
        Modals[Modals]
        Forms[Form Components]
    end
    
    subgraph "Service Layer"
        AuthService[optimizedAuthService]
        DataService[optimizedDataService]
        ImageService[imageCacheService]
        UploadService[smartUploadService]
        OutfitService[outfitService]
        ReplicateService[replicateService]
    end
    
    subgraph "State Management"
        GlobalData[useGlobalData Hook]
        Auth[useAuth Hook]
        Outfits[useOutfits Hook]
    end
    
    subgraph "Cache Layer"
        MemoryCache[In-Memory Cache]
        AsyncStorage[AsyncStorage]
        ImageCache[FileSystem Cache]
    end
    
    App --> Nav
    Nav --> Tabs
    Tabs --> Home
    Tabs --> Closet
    Tabs --> Explore
    Tabs --> Outfits
    Tabs --> Profile
    Nav --> AddClothes
    Nav --> Avatar
    Nav --> DressingRoom
    Nav --> Search
    
    Home --> Cards
    Home --> Headers
    Closet --> Cards
    AddClothes --> Forms
    AddClothes --> Modals
    
    Home --> GlobalData
    Closet --> GlobalData
    Outfits --> Outfits
    Profile --> Auth
    
    GlobalData --> DataService
    Auth --> AuthService
    Outfits --> OutfitService
    AddClothes --> UploadService
    Avatar --> ReplicateService
    
    DataService --> MemoryCache
    DataService --> AsyncStorage
    ImageService --> ImageCache
    ImageService --> MemoryCache
```

---

## Backend Architecture

```mermaid
graph TD
    subgraph "API Layer"
        Main[main.py<br/>FastAPI App]
        Router[API Router<br/>/api/v1]
    end
    
    subgraph "Route Handlers"
        AuthRouter[/auth/*]
        ClothesRouter[/clothes/*]
        OutfitsRouter[/outfits/*]
        AvatarRouter[/avatar/*]
        UploadRouter[/upload/*]
        ImagesRouter[/images/*]
        AdminRouter[/admin/*]
    end
    
    subgraph "Middleware"
        CORS[CORS Middleware]
        Security[Security Middleware]
        AuthMiddleware[Auth Middleware]
        Logging[Logging Middleware]
    end
    
    subgraph "Service Layer"
        AuthService[AuthService]
        DatabaseService[DatabaseService]
        StorageService[StorageService]
        OutfitService[OutfitService]
        AvatarService[AvatarService]
        BackgroundRemoval[BackgroundRemovalService]
        Classifier[ClothingClassifier]
        EnhancedClassifier[EnhancedClothingClassifier]
        TitleGenerator[TitleGenerator]
        ReplicateService[ReplicateService]
    end
    
    subgraph "Core Components"
        Models[Pydantic Models]
        Exceptions[Exception Handlers]
        Logger[Logging System]
        Config[Settings/Config]
    end
    
    subgraph "External Dependencies"
        Supabase[(Supabase Client)]
        AI[AI Models]
    end
    
    Main --> Router
    Router --> AuthRouter
    Router --> ClothesRouter
    Router --> OutfitsRouter
    Router --> AvatarRouter
    Router --> UploadRouter
    Router --> ImagesRouter
    Router --> AdminRouter
    
    Main --> CORS
    Main --> Security
    Main --> AuthMiddleware
    Main --> Logging
    
    AuthRouter --> AuthService
    ClothesRouter --> DatabaseService
    ClothesRouter --> StorageService
    OutfitsRouter --> OutfitService
    OutfitsRouter --> DatabaseService
    AvatarRouter --> AvatarService
    UploadRouter --> BackgroundRemoval
    UploadRouter --> Classifier
    UploadRouter --> EnhancedClassifier
    UploadRouter --> TitleGenerator
    UploadRouter --> StorageService
    
    AuthService --> Supabase
    DatabaseService --> Supabase
    StorageService --> Supabase
    AvatarService --> AI
    BackgroundRemoval --> AI
    Classifier --> AI
    EnhancedClassifier --> AI
    
    AuthService --> Models
    DatabaseService --> Models
    OutfitService --> Models
    
    Main --> Exceptions
    Main --> Logger
    Main --> Config
```

---

## Data Flow Diagrams

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant AuthService
    participant Backend
    participant Supabase
    
    User->>Frontend: Enter credentials
    Frontend->>AuthService: login(email, password)
    AuthService->>Backend: POST /api/v1/auth/login
    Backend->>Supabase: Validate credentials
    Supabase-->>Backend: User data + session
    Backend->>Backend: Generate JWT token
    Backend-->>AuthService: Token + user data
    AuthService->>AuthService: Store in AsyncStorage
    AuthService->>AuthService: Cache in memory
    AuthService-->>Frontend: Success response
    Frontend-->>User: Navigate to Home
```

### Clothing Item Upload Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant UploadService
    participant Backend
    participant AI
    participant Storage
    participant Database
    
    User->>Frontend: Select image
    Frontend->>UploadService: processImage(image)
    UploadService->>Backend: POST /upload/smart-upload-async
    
    par Background Removal
        Backend->>AI: Remove background
        AI-->>Backend: Processed image
    and Classification
        Backend->>AI: Classify clothing
        AI-->>Backend: Category + season
    and Title Generation
        Backend->>AI: Generate title
        AI-->>Backend: Title options
    end
    
    Backend-->>UploadService: AI results
    UploadService-->>Frontend: Display suggestions
    User->>Frontend: Confirm/Edit details
    Frontend->>Backend: POST /clothes (with data)
    Backend->>Storage: Upload image
    Storage-->>Backend: Image URL
    Backend->>Database: Save clothing item
    Database-->>Backend: Item created
    Backend-->>Frontend: Success response
    Frontend-->>User: Item added
```

### Virtual Try-On Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant DressingRoom
    participant Backend
    participant AvatarService
    participant Replicate
    participant Database
    
    User->>DressingRoom: Select clothing items
    User->>DressingRoom: Tap "Try On"
    DressingRoom->>Backend: POST /avatar/try-on
    Backend->>Database: Get avatar image
    Database-->>Backend: Avatar data
    Backend->>Database: Get clothing item
    Database-->>Backend: Clothing data
    Backend->>AvatarService: Process try-on
    AvatarService->>Replicate: Generate try-on
    Replicate-->>AvatarService: Result image
    AvatarService->>Database: Save try-on result
    Database-->>AvatarService: Saved
    AvatarService-->>Backend: Try-on result
    Backend-->>DressingRoom: Result URL
    DressingRoom-->>User: Display result
```

### Data Caching Flow

```mermaid
sequenceDiagram
    participant Screen
    participant DataService
    participant MemoryCache
    participant AsyncStorage
    participant Backend
    participant Supabase
    
    Screen->>DataService: loadClothingItems()
    DataService->>MemoryCache: Check cache
    alt Cache Hit (Valid)
        MemoryCache-->>DataService: Return cached data
        DataService-->>Screen: Return data
        DataService->>Backend: Background refresh
    else Cache Miss or Stale
        DataService->>AsyncStorage: Check persistent cache
        alt Persistent Cache Hit
            AsyncStorage-->>DataService: Return cached data
            DataService->>MemoryCache: Update memory cache
            DataService-->>Screen: Return data
        else Cache Miss
            DataService->>Backend: GET /clothes
            Backend->>Supabase: Query database
            Supabase-->>Backend: Clothing items
            Backend-->>DataService: Response
            DataService->>MemoryCache: Update cache
            DataService->>AsyncStorage: Update persistent cache
            DataService-->>Screen: Return data
        end
    end
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Client Devices"
        iOS[iOS Devices]
        Android[Android Devices]
    end
    
    subgraph "CDN & Distribution"
        AppStore[Apple App Store]
        PlayStore[Google Play Store]
        Expo[Expo CDN]
    end
    
    subgraph "Backend Infrastructure"
        Vercel[Vercel Serverless<br/>FastAPI Functions]
        Edge[Vercel Edge Network]
    end
    
    subgraph "Database & Storage"
        SupabaseDB[(Supabase PostgreSQL<br/>Primary Database)]
        SupabaseStorage[(Supabase Storage<br/>S3 Compatible)]
        Replica[(Read Replicas)]
    end
    
    subgraph "AI Services"
        AICompute[AI Compute<br/>CPU/GPU]
        Models[Model Storage]
    end
    
    subgraph "Monitoring & Logging"
        Logs[Application Logs]
        Metrics[Metrics & Analytics]
    end
    
    iOS --> AppStore
    Android --> PlayStore
    AppStore --> Expo
    PlayStore --> Expo
    
    iOS -->|HTTPS| Edge
    Android -->|HTTPS| Edge
    Edge --> Vercel
    
    Vercel --> SupabaseDB
    Vercel --> SupabaseStorage
    SupabaseDB --> Replica
    
    Vercel --> AICompute
    AICompute --> Models
    
    Vercel --> Logs
    Vercel --> Metrics
```

---

## Technology Stack

```mermaid
graph LR
    subgraph "Frontend Stack"
        RN[React Native]
        TS[TypeScript]
        Expo[Expo]
        Nav[React Navigation]
        Async[AsyncStorage]
    end
    
    subgraph "Backend Stack"
        FastAPI[FastAPI]
        Python[Python 3.9+]
        Pydantic[Pydantic]
        Uvicorn[Uvicorn]
    end
    
    subgraph "Database & Storage"
        Postgres[PostgreSQL]
        Supabase[Supabase]
        S3[S3 Storage]
    end
    
    subgraph "AI & ML"
        TensorFlow[TensorFlow]
        Rembg[rembg/U²-Net]
        MediaPipe[MediaPipe]
        Replicate[Replicate API]
    end
    
    subgraph "Infrastructure"
        Vercel[Vercel]
        Serverless[Serverless Functions]
        CDN[CDN]
    end
    
    subgraph "Development Tools"
        Jest[Jest]
        Pytest[pytest]
        Git[Git]
        Docker[Docker]
    end
    
    RN --> TS
    RN --> Expo
    RN --> Nav
    RN --> Async
    
    FastAPI --> Python
    FastAPI --> Pydantic
    FastAPI --> Uvicorn
    
    Supabase --> Postgres
    Supabase --> S3
    
    TensorFlow --> Python
    Rembg --> Python
    MediaPipe --> Python
    
    FastAPI --> Vercel
    Vercel --> Serverless
    Vercel --> CDN
```

---

## Component Interaction Diagram

```mermaid
graph TB
    subgraph "User Interface"
        A[User Action]
    end
    
    subgraph "Frontend Services"
        B[Service Layer]
        C[Cache Layer]
    end
    
    subgraph "API Communication"
        D[HTTP Client]
        E[Request Interceptor]
        F[Response Handler]
    end
    
    subgraph "Backend API"
        G[Route Handler]
        H[Middleware]
        I[Service Layer]
    end
    
    subgraph "Data Processing"
        J[Database Service]
        K[Storage Service]
        L[AI Service]
    end
    
    subgraph "External Systems"
        M[(Supabase DB)]
        N[(Supabase Storage)]
        O[AI Models]
    end
    
    A --> B
    B --> C
    B --> D
    D --> E
    E --> G
    G --> H
    H --> I
    I --> J
    I --> K
    I --> L
    J --> M
    K --> N
    L --> O
    I --> F
    F --> E
    E --> D
    D --> B
    B --> A
```

---

## Security Architecture

```mermaid
graph TD
    subgraph "Client Security"
        JWT1[JWT Token Storage<br/>AsyncStorage]
        Encrypt1[Data Encryption]
        Validate1[Input Validation]
    end
    
    subgraph "Network Security"
        HTTPS[HTTPS/TLS]
        CORS[CORS Policy]
        Headers[Security Headers]
    end
    
    subgraph "API Security"
        Auth[Authentication]
        Authz[Authorization]
        RateLimit[Rate Limiting]
        Validate2[Input Validation]
    end
    
    subgraph "Database Security"
        RLS[Row Level Security]
        Encrypt2[Data Encryption]
        Backup[Backup & Recovery]
    end
    
    JWT1 --> HTTPS
    Encrypt1 --> HTTPS
    Validate1 --> HTTPS
    
    HTTPS --> CORS
    CORS --> Headers
    Headers --> Auth
    
    Auth --> Authz
    Authz --> RateLimit
    RateLimit --> Validate2
    
    Validate2 --> RLS
    RLS --> Encrypt2
    Encrypt2 --> Backup
```

---

## AI Processing Pipeline

```mermaid
graph LR
    A[Image Input] --> B{Processing Type}
    
    B -->|Background Removal| C[U²-Net Model]
    B -->|Classification| D[TensorFlow Model]
    B -->|Season Detection| E[Color Analysis]
    B -->|Pose Detection| F[MediaPipe]
    
    C --> G[Processed Image]
    D --> H[Category + Label]
    E --> I[Season Scores]
    F --> J[Pose Landmarks]
    
    G --> K[Title Generator]
    H --> K
    I --> K
    
    K --> L[Final Result]
    J --> M[Avatar Quality]
    
    L --> N[Storage]
    M --> N
```

---

## File Structure Overview

```
gc-closet-manager/
├── gc-ui/ (React Native Frontend)
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── screens/        # Screen components
│   │   ├── services/       # API & business logic
│   │   ├── hooks/          # Custom React hooks
│   │   ├── navigation/     # Navigation setup
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   └── assets/             # Images, fonts, etc.
│
└── gc-service/ (FastAPI Backend)
    ├── app/
    │   ├── api/v1/         # API route handlers
    │   ├── core/           # Core functionality
    │   ├── middleware/     # Middleware components
    │   ├── models/         # Pydantic models
    │   ├── services/       # Business logic services
    │   └── utils/          # Utility functions
    ├── config/             # Configuration
    ├── ai_models/          # AI model files
    └── tests/              # Test files
```

---

## Performance Optimization Architecture

```mermaid
graph TD
    subgraph "Frontend Optimization"
        A1[Image Caching]
        A2[Data Caching]
        A3[Lazy Loading]
        A4[Code Splitting]
    end
    
    subgraph "Backend Optimization"
        B1[Connection Pooling]
        B2[Query Optimization]
        B3[Async Processing]
        B4[Batch Operations]
    end
    
    subgraph "Network Optimization"
        C1[CDN]
        C2[Image Compression]
        C3[Request Batching]
        C4[Pagination]
    end
    
    A1 --> C1
    A2 --> C3
    A3 --> C2
    A4 --> C1
    
    B1 --> B2
    B2 --> B3
    B3 --> B4
    
    C1 --> D[User Experience]
    C2 --> D
    C3 --> D
    C4 --> D
```

---

## Notes

- All diagrams use Mermaid syntax and can be rendered in most markdown viewers
- For best viewing, use tools like:
  - GitHub (renders Mermaid natively)
  - VS Code with Mermaid extension
  - Online Mermaid editors
  - Documentation platforms (GitBook, Notion, etc.)

- Architecture is designed for:
  - Scalability (serverless, auto-scaling)
  - Performance (caching, optimization)
  - Security (JWT, RLS, encryption)
  - Maintainability (modular, testable)

---

*Last Updated: Based on current codebase structure*

