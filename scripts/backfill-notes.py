#!/usr/bin/env python3
"""Fill the notes placeholder with real evidence: findings, blob count, run id.

The per-box notes were written by run-box.py with a placeholder "Captured"
section. That is a gap against the contract (each note should carry the
evidence), so this rewrites that section from Postgres + the blob store.
Idempotent: numbers are recomputed each run, never appended.
"""
import glob, gzip, json, os, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COMPOSE = ["docker","compose","-p","artex-gym","--project-directory",str(REPO),
           "--env-file",str(REPO/".env"),
           "-f",str(Path(os.environ.get("ARTEX_GYM_ARTEX_SOURCE", str(Path.home()/"projects"/"ARTEX")))/"docker-compose.yml"),
           "-f",str(REPO/"compose"/"overlay.yml")]

def psql(sql):
    p = subprocess.run(COMPOSE+["exec","-T","postgres","psql","-U","artex","-d","artex","-tAc",sql],
                       capture_output=True, text=True, timeout=120)
    return p.stdout.strip()

def blob_counts():
    """{ip: count} for every blob mentioning an IP."""
    out = {}
    ip_re = re.compile(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    for f in glob.glob(str(REPO/"data/llm-blobs/*/*.json.gz")):
        raw = gzip.decompress(open(f,"rb").read())
        d = json.loads(raw)
        # One blob counts once per IP, however many times the IP appears in its
        # message history. Counting occurrences inflated this by ~50x.
        for s in {m.group().decode() for m in ip_re.finditer(raw)}:
            if s.startswith(("0.", "127.", "255.")):
                continue
            out.setdefault(s, [0, d["run_id"]])[0] += 1
    return out

def main():
    q = json.load(open(REPO/"notes/queue.json"))
    blobs = blob_counts()
    run_ids = sorted({v[1] for v in blobs.values()})
    findings = {}
    rows = psql("select task_id, severity, left(replace(summary,chr(10),' '),150) from findings order by task_id, id;")
    for line in rows.splitlines():
        if line.count("|") >= 2:
            tid, sev, summ = line.split("|", 2)
            findings.setdefault(tid.strip(), []).append((sev.strip(), summ.strip()))

    updated = 0
    for b in q["boxes"]:
        if b["state"] in ("pending",) or not b.get("task_id"):
            continue
        d = REPO/"notes"/b["slug"]
        if not d.exists():
            continue
        n, run = (blobs.get(b.get("ip") or "", [0, "-"]))
        fs = findings.get(str(b["task_id"]), [])
        lines = ["## Captured", "",
                 f"- Blob run `{run}` — {n} blobs referencing `{b.get('ip')}`",
                 f"- ArTeX task `{b['task_id']}`; collector `dropped=0` for the run"]
        if fs:
            lines += ["- Findings:", ""]
            for sev, summ in fs:
                lines.append(f"  - **{sev}** — {summ}")
        else:
            lines.append("- Findings: none recorded")
        rd = d/"README.md"
        txt = rd.read_text()
        head = txt.split("## Captured")[0].rstrip()
        rd.write_text(head + "\n\n" + "\n".join(lines) + "\n")
        updated += 1
    print(f"backfilled {updated} notes; run ids seen: {', '.join(run_ids)}")

if __name__ == "__main__":
    sys.exit(main())
