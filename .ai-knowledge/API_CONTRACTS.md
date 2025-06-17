# External API Contracts

## Fireflies API
- **Purpose**: Transcript ingestion
- **Frequency**: Every 15 minutes
- **Endpoint**: https://api.fireflies.ai/graphql
- **Rate Limit**: 100 requests/minute

## Gemini API  
- **Purpose**: AI task extraction
- **Frequency**: Every 5 minutes
- **Endpoint**: https://generativelanguage.googleapis.com/v1beta
- **Rate Limit**: 60 requests/minute

## Monday.com API
- **Purpose**: Task delivery
- **Frequency**: Hourly (for tasks >18h old)
- **Endpoint**: https://api.monday.com/v2
- **Rate Limit**: 100 requests/minute
