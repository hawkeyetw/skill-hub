# ⚠️ SYNTHETIC TEST FIXTURE — NOT A REAL SKILL

This directory is a **deliberately constructed test fixture** for demonstrating skill-hub's
static review scanner. It is not a functional exploit:

- The `curl` target (`pdf-utils-pro-cdn.invalid.test`) uses the reserved `.test` TLD (RFC 2606),
  which never resolves on the public internet.
- The "AWS key" is an obviously fake placeholder string, not a real credential.
- The hidden HTML-comment instruction is a canonical indirect-prompt-injection pattern
  (asks the agent to read SSH keys/`.env` files and exfiltrate them "for debugging"),
  used only to prove the scanner's prompt-injection heuristics fire.

Used to prove: skill-hub's Track E (external-source) static scan rejects this before it
ever reaches human review or the sandbox step. Do not remove the fixture markers above if
this file is reused elsewhere.
