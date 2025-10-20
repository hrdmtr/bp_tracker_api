# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **backend API service** for a blood pressure tracking mobile application. The API acts as a **proxy/relay service** that:
- Receives blood pressure meter images and forwards them to OpenAI API for recognition
- Retrieves weather data from OpenWeatherMap API based on city name
- Returns combined results to the Flutter mobile app
- **Does NOT store any user data** - privacy-first design

**Important**: This backend does not persist any health data. All blood pressure measurements, personal information, and health records are stored exclusively on the user's device (SQLite). This API is stateless and serves only as a relay to third-party APIs.

## Current Status

**Pre-implementation phase** - The repository currently contains only documentation:
- `API_spec.md`: Complete API specification (Japanese)
- `docs/RD.md`: Requirements definition document (Japanese)

No source code has been implemented yet.

## Architecture

### Data Flow
```
[Mobile App] → [This Backend API] → [OpenAI API (image recognition)]
                    ↓                        ↓
              [OpenWeatherMap API]    [Recognition results]
                    ↓                        ↓
              [Weather data]                 |
                    ↓________________________|
                               ↓
                    [Combined JSON response]
                               ↓
                        [Mobile App]
                               ↓
                    [Local SQLite storage]
```

### Key API Endpoints (Planned)

1. **POST /api/v1/record-measurement** (Unified API - Recommended)
   - Accepts: multipart/form-data with blood pressure meter image, city name, timestamp
   - Returns: Blood pressure values + weather data in single response
   - Graceful degradation: Returns BP data even if weather API fails

2. **POST /api/v1/recognize-blood-pressure** (Individual)
   - Image recognition only

3. **GET /api/v1/weather** (Individual)
   - Weather data retrieval only

### Authentication Strategy (Phased Approach)

**Phase 1 (MVP - Current)**: Soft UUID Authentication
- Client generates UUID (no pre-registration required)
- All API requests include `X-User-UUID` header
- Rate limiting: 100 requests/day per UUID, 1000 requests/hour per IP
- Automatic temporary blocking for suspicious patterns

**Phase 2 (Future)**: Blacklist system for repeat offenders

**Phase 3 (Future)**: Mandatory UUID registration with device transfer support

## Implementation Requirements

### External API Integration

**OpenAI API**:
- Model: `gpt-4o` or `gpt-4o-mini` with Vision
- Extract: systolic/diastolic pressure, pulse rate, device model
- Timeout: 30 seconds
- No retry logic (prompt user to retake photo)

**OpenWeatherMap API**:
- Endpoint: Current Weather Data API
- Parameters: city (Japanese → English conversion), units=metric, lang=ja
- Timeout: 10 seconds
- Graceful failure handling

### Security & Privacy Requirements

**Critical Privacy Rules**:
- NEVER store blood pressure measurements on the server
- NEVER log personal health data (BP values, device models, city names)
- Images must be deleted from memory immediately after recognition
- Only log: timestamp, endpoint, HTTP status code, UUID
- Log retention: 30 days maximum

**HTTPS Required**:
- TLS 1.2 or higher for all endpoints
- API keys stored in secrets manager (AWS Secrets Manager / Google Cloud Secret Manager / Azure Key Vault)

**Rate Limiting**:
- Implement per-UUID and per-IP rate limits
- Detect anomalous patterns (e.g., >10 different UUIDs from same IP)
- Auto-block suspicious activity for 1-24 hours

### Error Handling

**Error Response Format**:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly message in Japanese",
    "details": "Optional technical details"
  }
}
```

**Critical Error Codes**:
- `MISSING_UUID`: No X-User-UUID header
- `RECOGNITION_FAILED`: Cannot extract BP values from image
- `WEATHER_API_UNAVAILABLE`: Weather service temporarily unavailable
- `RATE_LIMIT_EXCEEDED`: Request quota exceeded

## Development Guidelines

### When Implementing This API

1. **Choose Technology Stack First**:
   - Document recommends consideration of: Python (Flask/FastAPI), Go, Node.js, or Ruby
   - Consider: deployment target (Cloud Run, Lambda, EC2, etc.)
   - Decision should be based on developer familiarity and scaling needs

2. **Environment Variables**:
   ```bash
   OPENAI_API_KEY=sk-xxxxx
   OPENWEATHERMAP_API_KEY=xxxxx
   ```

3. **Data Retention**:
   - NO database for user data
   - Phase 3 will require database for:
     - `registered_users` table (UUID registration)
     - `transfer_codes` table (device transfer)
     - `blacklisted_uuids` table (abuse prevention)

4. **Testing Strategy**:
   - Test with multiple blood pressure meter brands/models
   - Mock OpenAI/OpenWeatherMap APIs for unit tests
   - Test rate limiting and blocking mechanisms
   - Verify no data persistence (memory only)

5. **Japanese Language Support**:
   - All error messages must be in Japanese
   - Weather descriptions must be translated to Japanese
   - City name conversion table (Japanese → English)

6. **Logging Best Practices**:
   - Use structured logging (JSON format)
   - Never log request/response bodies containing health data
   - Include request ID for tracing
   - Separate access logs from application logs

## Documentation Language

All documentation in this repository is written in **Japanese**. When adding code:
- Code comments should be in English (standard practice)
- API documentation should remain in Japanese
- Error messages returned by API must be in Japanese

## Related Repositories

The Flutter mobile application is a separate repository (not yet created as of this writing).

## Future Enhancements (Phase 2+)

- Batch image recognition
- Historical weather data (for measurements within 5 days)
- Webhook notifications
- Anonymous aggregate statistics API
- Device transfer functionality with time-limited codes
