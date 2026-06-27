---
name: ssh-shadow-server
description: "Aliyun Shadow server SSH access — <SHADOW_HOST>, PEM key at <PEM_DIR>/<PEM_FILENAME>"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# Aliyun Shadow Server SSH

- **Host**: <SHADOW_HOST>
- **User**: root
- **Key**: `<PEM_KEY_PATH>
- **App directory**: `/root/scanner/`
- **Python venv**: `/root/speed1-venv/`
- **MongoDB**: Docker container `mongo:7`, port 27017
- **Crontab**:
  - 15:30 Mon-Fri: `run_daily.sh` (daily scanner)
  - 16:00 Mon-Fri: `generate_and_send_report.py` (report + email)
  - 17:00 Mon: `alignment_checker.py`
- **Systemd mongod**: disabled (conflicts with Docker MongoDB)
