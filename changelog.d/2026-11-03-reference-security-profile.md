# Reference security assessment

- Assess the undeployed reference profile explicitly in CI after owner scope
  confirmation. Keep the default production validator, historical attestations,
  expiry policy and separate production-gap report.
- Bind fresh reference evidence to reviewed configuration, code, tests and its
  evidence document with SHA-256 checks. Reject unknown profiles, stale/future
  evidence, changed bytes, unsafe paths and production evidence used as reference.
- Preserve tool-manifest integrity, high-risk approval and minimum-bar checks;
  distinguish reference verification from operational or production readiness.
