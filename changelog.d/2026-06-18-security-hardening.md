Security hardening:

- Apply MCP HTTP auth to audit, map proxy, and direct UI resource routes when auth is enabled.
- Prevent failed auth requests from persisting new HTTP session IDs.
- Reject unsafe ONS geography cache database filenames.
- Disable automatic OS API redirects and mask OS upstream secrets in error payloads.
- Render geography selector tool results with DOM text nodes instead of HTML sinks.
