# Security scope

This public template contains no credentials and starts no external automation. The reference is a single-user loopback teaching app. Its session bootstrap assumes the local machine and browser are trusted; it is not remote authentication or protection from other local processes. Do not expose it through a proxy or tunnel.

Review boundaries include untrusted input rendering, named operations, source/digest-bound review, idempotency, origin/session checks, and preventing runtime-file serving. Production additions require their own threat model, identity and authorization, resource limits, backup/recovery, and integration-specific tests.

Please report suspected vulnerabilities through GitHub private vulnerability reporting when enabled. Do not post private data or exploit credentials in public issues.
