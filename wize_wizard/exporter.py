from __future__ import annotations
import csv, json
from pathlib import Path
from .db import connect

TABLES = ["projects","strategy","clay_tablets","tasks","pert","communications","journal"]

def export_project(project_id: int, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    con = connect(); payload = {}
    for table in TABLES:
        rows = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchall() if table == "projects" else con.execute(f"SELECT * FROM {table} WHERE project_id=?", (project_id,)).fetchall()
        data = [dict(r) for r in rows]; payload[table] = data
        if data:
            with (out_dir / f"{table}.csv").open("w", newline="", encoding="utf-8") as f:
                w=csv.DictWriter(f, fieldnames=data[0].keys()); w.writeheader(); w.writerows(data)
    (out_dir/"project.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    p=payload['projects'][0] if payload['projects'] else {'name':f'Project {project_id}','description':''}
    lines=["# Wize Wizard Project Export", "", f"## {p['name']}", p.get('description',''), "", "## Strategy / Automatic Why Ladder"]
    for r in payload['strategy']:
        prefix=f"As a {r['as_a']}, " if r['as_a'] else ""; because=f" because {r['because']}" if r['because'] else ""
        lines.append(f"- **{r['category']} / {r['level']}**: {prefix}I need to {r['need']} so that I can {r['so_that']}{because}.")
    lines += ["", "## Tasks"] + [f"- [{r['status']}] P{r['priority']} ({r.get('source_level','')}) {r['title']}" for r in payload['tasks']]
    lines += ["", "## PERT / Stress"]
    for r in payload['pert']:
        source="derived from best case" if r.get('derived') else "full input"
        lines.append(f"- {source}: best {r['optimistic']} / likely {r['likely']} / worst {r['pessimistic']} {r['unit']}; expected {r['expected']:.2f}; σ {r['sigma']:.2f}; high-stress {r['high_stress']:.2f}; low-stress {r['low_stress']:.2f}; {r['estimate_mode']}. {r.get('confidence_sentence','')}")
    lines += ["", "## Communications"] + [f"- {r.get('report','')}" for r in payload['communications']]
    lines += ["", "## Clay Tablets"] + [f"- {r['text']}" for r in payload['clay_tablets']]
    lines += ["", "## Journal"] + [f"- {r['created_at']}: {r['body']}" for r in payload['journal']]
    (out_dir/"project.md").write_text("\n".join(lines),encoding="utf-8")
    return out_dir
