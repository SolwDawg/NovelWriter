# ADR-0019: Alpha authentication

## Context

Alpha needs a personal workspace and authorization boundary without exposing
provider details to the browser. The invariant is
`AuthenticatedPrincipal → WorkspaceMembership → Permission`.

## Decision

Use application-owned sessions: Argon2id password hashes, opaque random session
tokens in an HttpOnly/Secure/SameSite cookie, and server-side session records
with expiry and revocation. Authorization resolves workspace membership before
project/story access.

## Consequences

The API remains self-hostable and identity-provider agnostic. Redis may cache
short-lived session lookups later, but PostgreSQL is the durable source for
membership and revocation state.

## Revisit trigger

Revisit if Alpha onboarding requires a third-party identity provider, enterprise
SSO, or a measured need for delegated OAuth login.

