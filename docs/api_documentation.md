# API Documentation

## Endpoints

### POST /api/query
Process a student query

**Request:**
```json
{
  "query": "What is photosynthesis?",
  "grade": 7,
  "subject": "science",
  "student_id": "12345"
}