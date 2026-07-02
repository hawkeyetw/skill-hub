# skill-hub demo (proof of concept, local-only, no external accounts needed)

Everything here runs on this machine. No GitHub account needed — the real product
shouldn't live on public GitHub anyway (see `.trellis/spec/architecture/03-deployment-and-auth.md`,
this is meant to be intranet-only). `registry/` stands in for the internal git repo;
in production it *is* a git repo (each `--approve` would be a commit).

This proves the core pipeline from `.trellis/spec/security/05-solo-operator-playbook.md`
actually works, end to end, against real content — not just on paper.

## What's seeded in `registry/pending/`

| Skill | Track | What it is |
|---|---|---|
| `algorithmic-art` | E (external) | A **real** skill fetched from Anthropic's public `anthropics/skills` repo — a legitimate external-source example |
| `commit-message-helper` | I (internal) | A simple skill written for this demo — a legitimate internal-source example |
| `pdf-utils-pro` | E (external) | **Synthetic test fixture** — hidden prompt-injection instruction in an HTML comment + a bundled script with a real-but-throwaway private key (generated solely for this fixture, never used anywhere) + `curl \| bash` pattern. Network target is inert (non-resolving `.test` domain). Meant to be caught by the *static* scanner. |
| `weather-cli-helper` | E (external) | **Synthetic test fixture** — deliberately written to dodge every static regex (no literal secret format, no shell-pipe pattern, no injection phrases) while its bundled script quietly reads `~/.aws/credentials` and POSTs it out disguised as "usage analytics." Meant to be caught by the *dynamic sandbox* step, not static scan. |

`NOTES.md` inside `pdf-utils-pro/` and the module docstring in `weather-cli-helper/scripts/format.py`
both self-label as synthetic fixtures — not real exploits.

## Run it

```bash
cd /root/skill-hub

# 1. Run the full pipeline against each pending skill.
#    Static scan -> track-based read-through/sandbox decision -> reject or (with
#    --approve) publish. Omit --approve to see the checks without publishing.
python3 scripts/review_pipeline.py algorithmic-art --approve       # -> approved (real external skill, clean)
python3 scripts/review_pipeline.py commit-message-helper --approve # -> approved (internal, clean)
python3 scripts/review_pipeline.py pdf-utils-pro --approve         # -> rejected at static scan
python3 scripts/review_pipeline.py weather-cli-helper --approve    # -> passes static scan, rejected by sandbox

# 2. Generate the index from whatever's in registry/approved/
python3 scripts/generate_index.py

# 3. Generate the two static pages:
#    - catalog.html: "how does an end user browse and get the install command"
#      (architecture/04-audience-distribution-channels.md). Browse/download only -
#      publishing always goes through review_pipeline.py, never a web upload form,
#      so the review gate can't be bypassed.
#    - audit.html: the review pipeline itself (every static-scan/sandbox run,
#      pass/fail, findings) rendered from registry/audit-log.jsonl - no git-log
#      spelunking needed to see what happened.
python3 scripts/generate_catalog_html.py
python3 scripts/generate_audit_html.py
python3 -m http.server 18899 --bind 127.0.0.1 --directory registry &
# then open http://127.0.0.1:18899/catalog.html and http://127.0.0.1:18899/audit.html

# 4. "Install" an approved skill the way an OpenCode user actually would
bash scripts/install.sh algorithmic-art demo-client/.agents/skills
bash scripts/install.sh commit-message-helper demo-client/.agents/skills

# Try installing something that never got approved - refused:
bash scripts/install.sh pdf-utils-pro demo-client/.agents/skills   # -> error, not in approved/

# 5. Reset back to the starting state to re-run
bash scripts/reset_demo.sh
```

## Secret scanning uses the real market-standard tool, not hand-rolled regex

`static_scan.py` shells out to **TruffleHog** (trufflesecurity/trufflehog) if it's on
PATH, falling back to a regex backstop only if it isn't installed. This matters:
TruffleHog structurally validates secret material (parses PEM blocks, checksums key
formats) instead of naive substring matching, so it doesn't false-positive on
placeholder strings - `pdf-utils-pro`'s fixture had to use a real (throwaway,
never-used-anywhere) `openssl`-generated keypair for this reason; a fake string like
`"AKIAFAKE..."` doesn't trigger it, on purpose.

ClamAV (what Hugging Face Hub actually uses for malware scanning) was evaluated too -
it's real and legitimate, but this sandboxed dev environment's CDN access for virus
definitions is rate-limited/blocked (`freshclam` returns 429/403), so it's not wired
in here. Production deployment should still add it; note it as a known gap, not a
design choice.

## What this does and doesn't prove

**Proves**: the Track E/I branching logic works on real content; the static scanner
(TruffleHog + custom prompt-injection/dangerous-shell heuristics) catches an obvious
injection+secret+dangerous-shell fixture; the sandbox catches a fixture specifically
built to dodge static patterns (real credential exfiltration attempt, observed live
inside an isolated, network-restricted Docker container); approval state gates what
`install.sh` will hand to a client; there's a real (if minimal) end-user-facing view
of "what can I install and how" via the generated catalog page; the whole thing runs
with zero external dependencies beyond Docker + a couple of downloaded binaries.

**Doesn't prove** (deliberately out of scope for a "does the concept work" demo,
these are Phase 2/3 per `.trellis/spec/architecture/03-deployment-and-auth.md`):
production-grade network-egress allowlisting (the sandbox uses `--network none` +
loopback, not the manifest-driven domain allowlist from
`.trellis/spec/security/03-manifest-and-runtime-enforcement.md`), SSO/LDAP
integration (the catalog page has no auth - fine for a demo, not for production),
IT/non-technical-audience catalog views, signing/provenance, gVisor/Firecracker-tier
isolation for `risk_tier: high` skills, ClamAV malware scanning (see above), or real
git-based version history (this demo mutates `registry/` in place; production commits
it).
