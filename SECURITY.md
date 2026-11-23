# Security & Privacy

## Reporting a vulnerability
Please email **susmithakotharu27@gmail.com** with details. Do not open a public issue. You'll get a response within 5 business days.

## How Aira protects users
| Area | Control |
|---|---|
| Crisis safety | Crisis language is detected before the LLM; fixed, reviewed responses with 988 / 14416 |
| Data minimization | Only emotions are stored by default; message text is not (`AIRA_STORE_EXCERPTS=false`) |
| Erasure | `DELETE /v1/users/{id}` removes all stored data for a user |
| Logging | Metadata only; message content is never logged |
| Access | `X-API-Key` authentication and per-user rate limiting |
| Input | Max message length, validated user IDs, prompt-injection-resistant system prompt |
| Runtime | Non-root container user, no secrets in the image, local LLM (no third-party AI API) |

## Operator checklist
- Set a strong `AIRA_API_KEY` and serve over HTTPS.
- Restrict `AIRA_CORS_ORIGINS` to your own front-end domains.
- Back up and encrypt the `/data` volume at rest.
