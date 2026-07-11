# StudyMatch

Study matching platform for Amrita students. Find your study circle.

## Project Structure

```
study_match/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/   # REST API routes
│   │   ├── core/     # Config, DB, security
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   ├── alembic/      # DB migrations
│   └── Dockerfile
├── mobile/           # Flutter mobile app
│   └── lib/
│       ├── app/      # Theme, router
│       ├── core/     # API client, constants
│       ├── models/   # Data models
│       ├── providers/# Riverpod state
│       ├── screens/  # All screens
│       └── widgets/  # Reusable widgets
└── docker-compose.yml
```

## Quick Start

### 1. Backend Setup

**Option A: Docker (recommended)**
```bash
docker-compose up -d
```

**Option B: Manual**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Start PostgreSQL and Redis locally first, then:
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 2. Flutter Setup

Install Flutter SDK:
1. Download from https://docs.flutter.dev/get-started/install/windows/mobile
2. Extract and add to PATH
3. Run `flutter doctor` to verify

```bash
cd mobile
flutter pub get
flutter run      # With phone connected via USB (USB debugging enabled)
```

### 3. Google OAuth Setup

1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable Google Sign-In API
4. Create OAuth 2.0 credentials (Android)
5. Add your SHA-1 fingerprint:
   ```bash
   keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
   ```
6. Set the client ID in `backend/.env`

### 4. Connect Flutter to Backend

When testing on a physical device, update the API base URL in:
`mobile/lib/core/constants.dart`

Change `10.0.2.2` (emulator) to your computer's local IP:
```dart
static const String baseUrl = 'http://192.168.x.x:8000/api/v1';
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Mobile**: Flutter, Riverpod, GoRouter, Dio
- **Auth**: Google OAuth (Amrita emails only)
