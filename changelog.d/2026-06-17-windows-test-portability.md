Changed

- Hardened Windows portability for repo shell wrappers, stdio framing, direct script entrypoints, and OWASP/tooling validation so the post-update regression suite runs cleanly on Windows as well as Unix-like environments.

Fixed

- Normalized repo-relative path outputs and shell-launch behavior across helper scripts and tests, including Git Bash/OpenSSL discovery, shebang-script dispatch, and symlink-privilege-aware test handling.