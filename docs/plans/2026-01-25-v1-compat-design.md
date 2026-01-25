# /v1 Compatibility Layer Design

## Goal
Accept OpenAI-style `/v1/*` requests and route them to existing codex-lb proxy endpoints without changing current behavior.

## Non-Goals
- No new business logic or auth changes.
- No changes to existing `/backend-api/codex/*` routes.
- No response shape changes.

## Approach
Add a lightweight HTTP middleware that rewrites any path starting with `/v1/` to `/backend-api/codex/` and then continues normal request handling.

Rewrite rule:
- If `path` starts with `/v1/`, replace the `/v1` prefix with `/backend-api/codex`.
- Example: `/v1/responses` -> `/backend-api/codex/responses`.

The middleware updates `scope["path"]` and `scope["raw_path"]` so downstream routing resolves correctly.

## Error Handling
- If the rewritten path does not exist, normal 404 behavior remains unchanged.
- All existing exception handlers and middleware remain in place.

## Testing
- Add an integration test that POSTs to `/v1/responses` and asserts the same behavior as `/backend-api/codex/responses` in the no-accounts case.

## Risks
- Minimal; the rewrite only activates for `/v1/` and does not affect existing routes.
