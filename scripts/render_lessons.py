from __future__ import annotations
import shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'wize_wizard'/'static'/'videos'; out.mkdir(parents=True,exist_ok=True)
media=ROOT/'media'; media.mkdir(exist_ok=True)
if not shutil.which('manim'):
    print("Manim not found. Install optional animation dependencies first: pip install -e '.[animation]'")
    print("The in-app browser animations remain available without Manim.")
    sys.exit(0)

SCENES={
    'wize-why-ladder':'WhyLadder', 'wize-pert':'PERTStress', 'wize-communications':'CommunicationChannels',
    'strategy-foundations':'StrategyLoop', 'bcg-henderson':'BCGExperience', 'mece-hypothesis':'MECEIssueTree',
    'five-forces':'FiveForces', 'market-structure':'MarketConcentration', 'value-creation':'ROICvsWACC',
    'risk-monte-carlo':'MonteCarloRisk', 'constraints-flow':'ConstraintsFlow', 'integrated-case':'IntegratedDecision',
}
for slug,scene in SCENES.items():
    print(f"Rendering {slug} ({scene})...")
    subprocess.run(['manim','-qm','--media_dir',str(media),'-o',f'{slug}.mp4',str(ROOT/'animations'/'strategy_lessons.py'),scene],check=True)
    candidates=list(media.rglob(f'{slug}.mp4'))
    if not candidates: raise SystemExit(f"Rendered file for {slug} not found under {media}")
    shutil.copy2(candidates[-1], out/f'{slug}.mp4')
print(f"Rendered {len(SCENES)} lesson videos into {out}")
