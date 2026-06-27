---
name: cc-connect-do-not-deploy
description: Never replace cc-connect binary or restart its service — user explicitly forbids this
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7fb1730e-7dd7-4ae0-a5f4-fc224ac086f9
---

Never replace, compile, deploy, or restart the cc-connect binary or systemd service. Do not touch `/home/rucli/.npm-global/bin/cc-connect` or run `systemctl --user` commands related to cc-connect.

**Why:** User gave a direct permanent ban after a prior attempt to replace the binary.

**How to apply:** When cc-connect changes are needed (config edits, binary fixes), make the source change only and inform the user — do not attempt to build, deploy, restart, or otherwise touch the running service.
