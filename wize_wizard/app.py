from __future__ import annotations
from pathlib import Path
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, TabbedContent, TabPane, Input, Button, Select, DataTable, Static, TextArea, Label
from textual import on

from .db import connect
from .models import LAFLEY, LEVELS, pert_three_point, derive_from_best, derive_estimates, communications_report
from .exporter import export_project


class WizeWizard(App):
    TITLE = "🧙 Wize Wizard"
    SUB_TITLE = "Strategy • PERT • Execution"
    CSS = """
    Screen { layout: vertical; }
    .row { height: auto; }
    .grow { width: 1fr; }
    Input, Select { margin: 0 1 1 0; }
    Button { margin-right: 1; }
    #status { height: 3; padding: 1; }
    .report { min-height: 8; padding: 1; border: round $accent; }
    DataTable { height: 1fr; }
    TextArea { height: 10; }
    """
    BINDINGS = [("ctrl+s", "save_context", "Save"), ("ctrl+e", "export", "Export"), ("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.project_id: int | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(classes="row"):
            yield Select([], prompt="Project", id="project_select", classes="grow")
            yield Input(placeholder="New project name", id="new_project", classes="grow")
            yield Button("New Project", id="create_project", variant="primary")
        yield Static("Create or choose a project. All integrated records share its project_id.", id="status")
        with TabbedContent():
            with TabPane("Strategy + Whys"):
                with ScrollableContainer():
                    yield Static("""HOW TO USE THIS PAGE
<<<<<<< HEAD
Choose one Lafley strategy question and write a complete Wize statement. You never select Need, Want, Wish, or Dream yourself; Wize Wizard advances Initial Need → Want → Wish → Dream in the background. Every saved statement becomes a linked task automatically. The optional Because field is also indexed in Clay Tablets.

Required grammar: [As a ___,] I need to ___ so that I can ___ [because ___].""")
                    yield Select([(x, x) for x in LAFLEY], prompt="Lafley question", id="category")
                    yield Static("Next automatic stage: Initial Need", id="why_stage")
=======
Choose one Lafley strategy question and write a complete Wize statement. You never select Need, Wish, Dream, or Fantasy yourself; Wize Wizard advances Need → Wish → Dream → Fantasy in the background. Every saved statement becomes a linked task automatically. The optional Because field is also indexed in Clay Tablets.

Required grammar: [As a ___,] I need to ___ so that I can ___ [because ___].""")
                    yield Select([(x, x) for x in LAFLEY], prompt="Lafley question", id="category")
                    yield Static("Next automatic stage: Need", id="why_stage")
>>>>>>> 034f4b1 (Harden Wize Wizard production baseline)
                    yield Input(placeholder="As a... (optional)", id="as_a")
                    yield Input(placeholder="I need to...", id="need")
                    yield Input(placeholder="so that I can...", id="so_that")
                    yield Input(placeholder="because... (optional → Clay Tablets)", id="because")
                    yield Select([("1 Critical",1),("2 High",2),("3 Medium",3),("4 Low",4),("5 Someday",5)], value=3, id="strategy_priority")
                    yield Button("Save Statement + Create Task + Next Why", id="save_strategy", variant="success")
                    yield DataTable(id="strategy_table")
            with TabPane("PERT / Stress"):
                with ScrollableContainer():
                    yield Input(placeholder="Task title", id="pert_task")
                    yield Select([(u,u) for u in ["minute","hour","day","week","month"]], value="hour", id="unit")
                    with Horizontal():
                        with ScrollableContainer(classes="grow"):
                            yield Label("Best case")
                            yield Input(placeholder="Optimistic / best case", id="o", type="number")
                        with ScrollableContainer(classes="grow"):
                            yield Label("Most likely (auto midpoint)")
                            yield Input(placeholder="Auto = midpoint of Best and Pessimistic", id="m", type="number", disabled=True)
                        with ScrollableContainer(classes="grow"):
                            yield Label("Worst case")
                            yield Input(placeholder="Pessimistic / worst case", id="p", type="number")
                    yield Select([("1 Minimal",1),("2 Low",2),("3 Moderate",3),("4 High",4),("5 Critical",5)], value=3, id="severity")
                    yield Static("""HOW TO USE THIS PAGE
1) Enter Best Case. 2) Enter Pessimistic/Worst Case when you know it; otherwise leave it blank. 3) Wize Wizard calculates Most Likely as the midpoint between Best and Pessimistic. If Pessimistic is blank, it derives Pessimistic = Best × 2 first, then calculates the midpoint. 4) Choose severity and press START PERT REPORT.

The report uses standard PERT weighting: (Best + 4×Most Likely + Pessimistic) / 6. Sigma is (Worst − Best) / 6. Wize planning envelopes then expand OUTWARD from the Best/Worst boundaries: 68% = Best−1σ to Worst+1σ, 95% = Best−2σ to Worst+2σ, and 99.7% = Best−3σ to Worst+3σ. Lower bounds are never allowed below zero.""")
                    yield Button("START PERT REPORT", id="calc_pert", variant="primary")
                    yield Static("Press START PERT REPORT to calculate. The result will explain every value shown here.", id="pert_result", classes="report")
                    yield DataTable(id="pert_table")
            with TabPane("Best Case Only"):
                with ScrollableContainer():
                    yield Static("""HOW TO USE THIS PAGE
Use this page when Best Case is the only duration you can estimate. Enter one positive Best Case value, choose severity, and run the report. Wize Wizard derives Pessimistic = Best × 2 and Most Likely = (Best + Pessimistic) / 2. It then performs the same PERT, sigma, 68%/95%/99.7% range, stress, and confidence analysis. Because two inputs are derived, the result is explicitly labeled a planning heuristic rather than measured uncertainty.""")
                    yield Input(placeholder="Task title", id="quick_task")
                    yield Select([(u,u) for u in ["minute","hour","day","week","month"]], value="hour", id="quick_unit")
                    yield Label("Best case only")
                    yield Input(placeholder="Best-case duration", id="quick_best", type="number")
                    yield Select([("1 Minimal",1),("2 Low",2),("3 Moderate",3),("4 High",4),("5 Critical",5)], value=3, id="quick_severity")
                    yield Button("Derive Worst Case + Run Report", id="quick_pert", variant="warning")
                    yield Static("", id="quick_result", classes="report")
            with TabPane("Tasks / Burndown"):
                with ScrollableContainer():
                    yield Static("""HOW TO USE THIS PAGE
Strategy/Why statements appear here automatically as linked tasks. Add extra tasks only with the same Wize grammar: [As a ___,] I need to ___ so that I can ___ [because ___]. Choose priority before saving. The burndown summarizes remaining work by priority and status so execution stays traceable to the strategy language.""")
                    yield Input(placeholder="As a... (optional)", id="task_as_a")
                    yield Input(placeholder="I need to...", id="task_need")
                    yield Input(placeholder="so that I can...", id="task_so_that")
                    yield Input(placeholder="because... (optional)", id="task_because")
                    with Horizontal():
                        yield Select([("1 Critical",1),("2 High",2),("3 Medium",3),("4 Low",4),("5 Someday",5)], value=3, id="task_priority")
                        yield Button("Add Structured Task", id="add_task", variant="primary")
                    yield DataTable(id="task_table")
                    yield Static("", id="burndown", classes="report")
            with TabPane("Communications"):
                with ScrollableContainer():
                    yield Static("""HOW TO USE THIS PAGE
Enter the number of people who may need pairwise communication, then press START COMMUNICATIONS REPORT. Wize Wizard calculates n(n−1)/2 possible channels, proposes smaller working groups, estimates internal plus lead-to-lead channels, and reports the absolute and percentage reduction. Treat the grouping result as a coordination-design suggestion, not a rule that necessary cross-team communication should be blocked.""")
                    yield Input(placeholder="Number of people", id="people", type="integer")
                    yield Static("Formula: communication channels = n(n−1)/2. The report also tests a smaller-group structure and compares raw all-to-all channels with grouped internal + lead-to-lead channels.")
                    yield Button("START COMMUNICATIONS REPORT", id="analyze_comms", variant="success")
                    yield Static("Press START COMMUNICATIONS REPORT to calculate channel complexity and grouping recommendations.", id="comms_result", classes="report")
                    yield DataTable(id="comms_table")
            with TabPane("Reports / Charts"):
                with ScrollableContainer():
                    yield Static("""HOW TO USE THIS PAGE
This page summarizes every saved PERT record for the active project. A PERT run now always has a project: if none is selected, Wize Wizard automatically creates a Quick Analysis project and saves the estimate there. The Gantt-style bars compare expected duration with the 3σ low-stress maximum (Worst + 3σ). Press Refresh Project Charts at any time to rebuild this view from the database.""")
                    yield Button("Refresh Project Charts", id="refresh_reports", variant="primary")
                    yield Static("", id="chart_report", classes="report")
            with TabPane("Clay Tablets"):
                yield Static("""HOW TO USE THIS PAGE
Clay Tablets is the reasoning ledger. Every optional Because statement entered in the Strategy/Whys workflow is copied here automatically while retaining its project and source-strategy link. Use it to review recurring principles, constraints, motives, and assumptions.""")
                yield DataTable(id="clay_table")
            with TabPane("Journal"):
                yield Static("""HOW TO USE THIS PAGE
Record observations, actual outcomes, estimation errors, decisions, and lessons for the active project. Journal entries are timestamped and exported with the project so future reviews can compare what was predicted with what actually happened.""")
                yield TextArea(id="journal_body")
                yield Button("Save Journal Entry", id="save_journal")
                yield DataTable(id="journal_table")
            with TabPane("Course"):
<<<<<<< HEAD
                yield Static("# Wize Wizard Course\n\n1. Winning aspiration\n2. Where to play\n3. Tools\n4. Skills\n5. Management systems\n6. Automatic structured Whys: Initial → Want → Wish → Dream\n7. PERT and stress ranges\n8. Sparse-input estimation\n9. Communications complexity\n10. Priority, execution, review, journal, and export", markup=True)
=======
                yield Static("# Wize Wizard Course\n\n1. Winning aspiration\n2. Where to play\n3. Tools\n4. Skills\n5. Management systems\n6. Automatic structured Whys: Need → Wish → Dream → Fantasy\n7. PERT and stress ranges\n8. Sparse-input estimation\n9. Communications complexity\n10. Priority, execution, review, journal, and export", markup=True)
>>>>>>> 034f4b1 (Harden Wize Wizard production baseline)
        yield Footer()

    def on_mount(self):
        self.setup_tables(); self.refresh_projects()

    def setup_tables(self):
        self.query_one("#strategy_table", DataTable).add_columns("ID","Question","Stage","Statement","Priority")
        self.query_one("#pert_table", DataTable).add_columns("Task","Best","Likely","Worst","Expected","σ","High stress","Low stress","Mode","Unit")
        self.query_one("#task_table", DataTable).add_columns("ID","Priority","Status","Source","Task")
        self.query_one("#comms_table", DataTable).add_columns("People","Raw","Groups","Group size","Structured","Reduction","Reduction %")
        self.query_one("#clay_table", DataTable).add_columns("ID","Because / Principle","Created")
        self.query_one("#journal_table", DataTable).add_columns("ID","Created","Entry")

    def refresh_projects(self):
        rows = connect().execute("SELECT id,name FROM projects ORDER BY id DESC").fetchall()
        sel = self.query_one("#project_select", Select)
        sel.set_options([(r['name'], r['id']) for r in rows])
        if rows and self.project_id is None:
            self.project_id = rows[0]['id']; sel.value = self.project_id; self.refresh_all()

    @on(Select.Changed, "#project_select")
    def choose_project(self, event):
        if event.value is not Select.BLANK:
            self.project_id = int(event.value); self.refresh_all()

    @on(Select.Changed, "#category")
    def category_changed(self, event):
        if event.value is not Select.BLANK: self.update_why_stage(str(event.value))

    def next_level(self, category: str) -> str:
        if not self.project_id: return LEVELS[0]
        n = connect().execute("SELECT COUNT(*) c FROM strategy WHERE project_id=? AND category=?", (self.project_id, category)).fetchone()['c']
        return LEVELS[min(n % len(LEVELS), len(LEVELS)-1)]

    def update_why_stage(self, category: str):
        self.query_one("#why_stage", Static).update(f"Next automatic stage: {self.next_level(category)}")

    @on(Input.Changed, "#o")
    @on(Input.Changed, "#p")
    def pert_inputs_changed(self, event: Input.Changed):
        """Preview Most Likely from the current Best/Pessimistic values."""
        best_raw = self.query_one("#o", Input).value.strip()
        pess_raw = self.query_one("#p", Input).value.strip()
        m_input = self.query_one("#m", Input)
        if not best_raw:
            m_input.value = ""
            return
        try:
            best = float(best_raw)
            if best <= 0:
                m_input.value = ""
                return
            pess = float(pess_raw) if pess_raw else best * 2.0
            if pess < best:
                m_input.value = ""
                return
            m_input.value = f"{(best + pess) / 2.0:g}"
        except ValueError:
            m_input.value = ""

    @on(Button.Pressed, "#create_project")
    def create_project(self):
        name = self.query_one("#new_project", Input).value.strip()
        if not name: return self.note("Enter a project name.")
        con=connect(); cur=con.execute("INSERT INTO projects(name) VALUES(?)",(name,)); con.commit(); self.project_id=cur.lastrowid
        self.query_one("#new_project", Input).value=""; self.refresh_projects(); self.note(f"Project created: {name}")

    @on(Button.Pressed, "#save_strategy")
    def save_strategy(self):
        if not self.require_project(): return
        category = self.query_one("#category", Select).value
        need = self.query_one("#need", Input).value.strip(); so_that = self.query_one("#so_that", Input).value.strip()
        if category is Select.BLANK or not need or not so_that:
            return self.note("Choose a Lafley question and complete I need to / so that I can.")
        category = str(category); level = self.next_level(category)
        as_a=self.query_one("#as_a",Input).value.strip(); because=self.query_one("#because",Input).value.strip(); priority=int(self.query_one("#strategy_priority",Select).value)
        title=self.statement(as_a,need,so_that,because)
        con=connect(); cur=con.execute("INSERT INTO strategy(project_id,category,level,as_a,need,so_that,because,priority) VALUES(?,?,?,?,?,?,?,?)",(self.project_id,category,level,as_a,need,so_that,because,priority)); sid=cur.lastrowid
        con.execute("INSERT INTO tasks(project_id,strategy_id,title,as_a,need,so_that,because,source_level,priority) VALUES(?,?,?,?,?,?,?,?,?)",(self.project_id,sid,title,as_a,need,so_that,because,level,priority))
        if because: con.execute("INSERT INTO clay_tablets(project_id,strategy_id,text) VALUES(?,?,?)",(self.project_id,sid,because))
        con.commit()
        for i in ["#as_a","#need","#so_that","#because"]: self.query_one(i,Input).value=""
        self.refresh_all(); self.update_why_stage(category); self.note(f"Saved {level}; linked task created automatically.")

    @on(Button.Pressed, "#add_task")
    def add_task(self):
        if not self.require_project(): return
        as_a=self.query_one("#task_as_a",Input).value.strip(); need=self.query_one("#task_need",Input).value.strip(); so=self.query_one("#task_so_that",Input).value.strip(); because=self.query_one("#task_because",Input).value.strip()
        if not need or not so: return self.note("Manual tasks must include both I need to and so that I can.")
        pr=int(self.query_one("#task_priority",Select).value); title=self.statement(as_a,need,so,because)
        con=connect(); con.execute("INSERT INTO tasks(project_id,title,as_a,need,so_that,because,source_level,priority) VALUES(?,?,?,?,?,?,?,?)",(self.project_id,title,as_a,need,so,because,"Manual",pr)); con.commit()
        for i in ["#task_as_a","#task_need","#task_so_that","#task_because"]: self.query_one(i,Input).value=""
        self.refresh_tasks(); self.note("Structured task added.")

    def ensure_analysis_project(self) -> int:
        """Ensure calculator output is always persisted so Reports/Charts can see it."""
        if self.project_id:
            return self.project_id
        name = f"Quick Analysis {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        con = connect()
        cur = con.execute("INSERT INTO projects(name,description) VALUES(?,?)",
                          (name, "Automatically created by Wize Wizard for calculator output."))
        con.commit()
        self.project_id = int(cur.lastrowid)
        self.refresh_projects()
        try:
            self.query_one("#project_select", Select).value = self.project_id
        except Exception:
            pass
        return self.project_id

    @on(Button.Pressed, "#calc_pert")
    def calc_pert(self):
        try:
            title=self.query_one("#pert_task",Input).value.strip() or "Untitled task"
            best=float(self.query_one("#o",Input).value)
            pess_raw=self.query_one("#p",Input).value.strip()
            pessimistic=float(pess_raw) if pess_raw else None
            severity=int(self.query_one("#severity",Select).value); unit=str(self.query_one("#unit",Select).value)
            if best <= 0: return self.note("Best Case must be positive.")
            if pessimistic is not None and pessimistic < best:
                return self.note("Pessimistic/Worst Case must be greater than or equal to Best Case.")
            o,m,p,r,derived=derive_estimates(best,pessimistic,severity)
            self.query_one("#m",Input).value=f"{m:g}"
        except ValueError:
            return self.note("Enter a numeric Best Case. Pessimistic is optional, but if entered it must be numeric.")
        self.ensure_analysis_project()
        self.save_pert(title,unit,o,m,p,severity,r,derived); saved=True
        self.query_one("#pert_result",Static).update(self.pert_report(o,m,p,unit,severity,r,derived))
        if saved: self.refresh_all()
        self.note("PERT report calculated" + (" and saved to the active project." if saved else ". Select a project to save future reports."))

    @on(Button.Pressed, "#quick_pert")
    def quick_pert(self):
        try:
            title=self.query_one("#quick_task",Input).value.strip() or "Untitled sparse-input task"
            best=float(self.query_one("#quick_best",Input).value); severity=int(self.query_one("#quick_severity",Select).value); unit=str(self.query_one("#quick_unit",Select).value)
            if best <= 0: raise ValueError
        except ValueError: return self.note("Enter a positive best-case estimate.")
        o,m,p,r=derive_from_best(best,severity)
        self.ensure_analysis_project()
        self.save_pert(title,unit,o,m,p,severity,r,True); saved=True
        self.query_one("#quick_result",Static).update(self.pert_report(o,m,p,unit,severity,r,True))
        if saved: self.refresh_all()
        self.note("Sparse-input PERT report calculated" + (" and saved." if saved else ". Select a project to save future reports."))

    def save_pert(self,title,unit,o,m,p,severity,r,derived):
        con=connect(); cur=con.execute("INSERT INTO tasks(project_id,title,need,so_that,source_level,priority,status) VALUES(?,?,?,?,?,?,?)",(self.project_id,title,title,"complete the estimated outcome","PERT",severity,"Backlog")); tid=cur.lastrowid
        con.execute("INSERT INTO pert(project_id,task_id,unit,optimistic,likely,pessimistic,severity,estimate_mode,expected,sigma,low_stress,high_stress,derived,confidence_sentence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(self.project_id,tid,unit,o,m,p,severity,r.mode,r.expected,r.sigma,r.low_stress,r.high_stress,1 if derived else 0,r.confidence_sentence)); con.commit()

    def pert_report(self,o,m,p,unit,severity,r,derived):
        source="DERIVED PESSIMISTIC HEURISTIC" if derived else "USER-SUPPLIED PESSIMISTIC PERT"
        spread=p-o
        likely_rule=(
            f"Pessimistic was not supplied, so Wize Wizard derived Worst = Best × 2 = {p:.2f}; Most Likely is the midpoint: ({o:.2f} + {p:.2f}) / 2 = {m:.2f}."
            if derived else
            f"Pessimistic was supplied by the user; Most Likely is the midpoint: ({o:.2f} + {p:.2f}) / 2 = {m:.2f}."
        )
        r68=r.range_68; r95=r.range_95; r997=r.range_997
        pess_note = "derived from Best because the field was blank" if derived else "entered by the user"
        return (
            f"{source}\n\n"
            f"INPUT RANGE\n"
            f"• Best Case: {o:.2f} {unit}(s) — fastest credible duration.\n"
            f"• Most Likely: {m:.2f} {unit}(s) — {likely_rule}\n"
            f"• Pessimistic/Worst Case: {p:.2f} {unit}(s) — {pess_note}.\n"
            f"• Best-to-Worst Range: {spread:.2f} {unit}(s).\n\n"
            f"PERT RESULT\n"
            f"• Weighted Expected Time (μ): {r.expected:.2f} {unit}(s) = (Best + 4×Most Likely + Worst) / 6.\n"
            f"• Sigma (σ): {r.sigma:.2f} {unit}(s) = (Worst − Best) / 6.\n"
            f"• Severity: {severity}/5. Recommended estimate depth: {r.mode}.\n\n"
            f"WIZE STATISTICAL PLANNING ENVELOPES\n"
            f"• ~68% / 1σ envelope: Best − 1σ to Worst + 1σ = {r68[0]:.2f} to {r68[1]:.2f} {unit}(s).\n"
            f"• ~95% / 2σ envelope: Best − 2σ to Worst + 2σ = {r95[0]:.2f} to {r95[1]:.2f} {unit}(s).\n"
            f"• ~99.7% / 3σ envelope: Best − 3σ to Worst + 3σ = {r997[0]:.2f} to {r997[1]:.2f} {unit}(s).\n"
            f"• Any lower boundary that would fall below zero is clamped to 0.00.\n"
            f"The familiar 68/95/99.7 labels describe sigma depth; Wize Wizard uses those sigma amounts as outward planning cushions around the full Best-to-Worst estimate range rather than as mean-centered probability intervals.\n\n"
            f"WIZE STRESS INTERPRETATION\n"
            f"• 2σ High-Stress / aggressive boundary: max(0, Best − 2σ) = {r.high_stress:.2f} {unit}(s).\n"
            f"• 3σ Low-Stress / maximum boundary: Worst + 3σ = {r.low_stress:.2f} {unit}(s).\n\n"
            f"CONFIDENCE INTERPRETATION\n{r.confidence_sentence} "
            f"The outward cushion is {r.sigma:.2f} at 68%, {2*r.sigma:.2f} at 95%, and {3*r.sigma:.2f} at 99.7%; each amount is subtracted from Best and added to Worst, with the lower side floored at zero.\n\n"
            f"BOX/RANGE INTERPRETATION\n"
            f"Best {o:.2f} ├──── Most Likely {m:.2f} ────┤ Worst {p:.2f}\n"
            f"Best is the optimistic edge, Most Likely is the midpoint used as the four-times-weighted PERT anchor, and Worst is the pessimistic edge. "
            f"A wider Best-to-Worst span creates a larger σ and therefore wider outward planning envelopes around the original Best/Worst range."
        )

    @on(Button.Pressed, "#analyze_comms")
    def analyze_comms(self):
        try: n=int(self.query_one("#people",Input).value)
        except ValueError: return self.note("Enter a whole number of people, then press START COMMUNICATIONS REPORT.")
        if n < 1: return self.note("People must be at least 1.")
        r=communications_report(n)
        saved=False
        if self.project_id:
            con=connect(); con.execute("INSERT INTO communications(project_id,people,channels,suggested_group_size,groups,structured_channels,reduction,reduction_pct,report) VALUES(?,?,?,?,?,?,?,?,?)",(self.project_id,n,r['channels'],r['group_size'],r['groups'],r['structured'],r['reduction'],r['reduction_pct'],r['sentence'])); con.commit(); saved=True
        interpretation=(
            "Low communication complexity." if r['channels'] <= 10 else
            "Moderate communication complexity; defined ownership and meeting boundaries are useful." if r['channels'] <= 45 else
            "High communication complexity; all-to-all coordination is likely to create substantial overhead."
        )
        self.query_one("#comms_result",Static).update(
            "COMMUNICATIONS REPORT\n\n"
            f"Formula: n(n−1)/2 = {n}×{n-1}/2 = {r['channels']} possible pairwise channels.\n\n"
            f"RAW NETWORK\n• People: {n}\n• Potential all-to-all channels: {r['channels']}\n• Interpretation: {interpretation}\n\n"
            f"GROUPING SUGGESTION\n• Suggested group size: about {r['group_size']} people\n• Number of groups: {r['groups']}\n• Internal group channels: {r['internal']}\n• Lead-to-lead channels: {r['lead_channels']}\n• Structured total: {r['structured']}\n\n"
            f"REDUCTION\n• Channels avoided: {r['reduction']}\n• Reduction: {r['reduction_pct']:.1f}%\n\n"
            f"DETAIL\n{r['sentence']}\n\n"
            "Management suggestion: preserve rich communication inside small groups, but use explicit owners, interfaces, or group leads for cross-group coordination. "
            "This does not eliminate necessary communication; it reduces the number of relationships that must stay continuously synchronized."
        )
        if saved: self.refresh_comms()
        self.note("Communications report calculated" + (" and saved to the active project." if saved else ". Select a project to save future reports."))

    @on(Button.Pressed, "#refresh_reports")
    def refresh_reports_button(self): self.refresh_reports()

    @on(Button.Pressed, "#save_journal")
    def save_journal(self):
        if not self.require_project(): return
        body=self.query_one("#journal_body",TextArea).text.strip()
        if not body: return
        con=connect(); con.execute("INSERT INTO journal(project_id,body) VALUES(?,?)",(self.project_id,body)); con.commit(); self.query_one("#journal_body",TextArea).text=""; self.refresh_journal()

    def action_export(self):
        if not self.require_project(): return
        row=connect().execute("SELECT name FROM projects WHERE id=?",(self.project_id,)).fetchone(); safe="".join(c if c.isalnum() or c in "-_" else "-" for c in row['name']).strip("-") or f"project-{self.project_id}"
        out=Path.cwd()/"wize-exports"/safe; export_project(self.project_id,out); self.note(f"Exported to {out}")

    def action_save_context(self): self.note("Use the active tab's Save/Add/Run button. Ctrl+E exports the entire project.")

    def refresh_all(self):
        if not self.project_id: return
        self.refresh_strategy(); self.refresh_tasks(); self.refresh_pert(); self.refresh_comms(); self.refresh_clay(); self.refresh_journal(); self.refresh_reports()

    def refresh_strategy(self):
        t=self.query_one("#strategy_table",DataTable); t.clear(); rows=connect().execute("SELECT * FROM strategy WHERE project_id=? ORDER BY category,id",(self.project_id,)).fetchall()
        for r in rows: t.add_row(r['id'],r['category'],r['level'],self.statement(r['as_a'],r['need'],r['so_that'],r['because']),r['priority'])

    def refresh_tasks(self):
        t=self.query_one("#task_table",DataTable); t.clear(); rows=connect().execute("SELECT * FROM tasks WHERE project_id=? ORDER BY priority,id",(self.project_id,)).fetchall()
        for r in rows:t.add_row(r['id'],r['priority'],r['status'],r['source_level'] or 'Task',r['title'])
        total=len(rows); done=sum(1 for r in rows if r['status']=='Done'); bars=20; filled=round((done/total)*bars) if total else 0
        weighted=sum(max(1,6-int(r['priority'])) for r in rows); weighted_done=sum(max(1,6-int(r['priority'])) for r in rows if r['status']=='Done')
        self.query_one("#burndown",Static).update(f"Task completion: [{'█'*filled}{'░'*(bars-filled)}] {done}/{total} done\nWeighted remaining effort points: {weighted-weighted_done}/{weighted}")

    def refresh_pert(self):
        t=self.query_one("#pert_table",DataTable); t.clear(); rows=connect().execute("SELECT p.*,t.title FROM pert p LEFT JOIN tasks t ON p.task_id=t.id WHERE p.project_id=? ORDER BY p.id DESC",(self.project_id,)).fetchall()
        for r in rows:t.add_row(r['title'] or '',f"{r['optimistic']:.2f}",f"{r['likely']:.2f}",f"{r['pessimistic']:.2f}",f"{r['expected']:.2f}",f"{r['sigma']:.2f}",f"{r['high_stress']:.2f}",f"{r['low_stress']:.2f}",r['estimate_mode'],r['unit'])

    def refresh_comms(self):
        t=self.query_one("#comms_table",DataTable); t.clear(); rows=connect().execute("SELECT * FROM communications WHERE project_id=? ORDER BY id DESC",(self.project_id,)).fetchall()
        for r in rows:t.add_row(r['people'],r['channels'],r['groups'],r['suggested_group_size'],r['structured_channels'],r['reduction'],f"{r['reduction_pct']:.1f}%")

    def refresh_reports(self):
        if not self.project_id:
            self.query_one("#chart_report",Static).update("No active project yet. Run PERT once and Wize Wizard will create a Quick Analysis project automatically, save the estimate, and populate this chart.")
            return
        rows=connect().execute("SELECT p.*,t.title FROM pert p LEFT JOIN tasks t ON p.task_id=t.id WHERE p.project_id=? ORDER BY p.id",(self.project_id,)).fetchall()
        if not rows:
            self.query_one("#chart_report",Static).update("This project has no saved PERT records yet. Run START PERT REPORT, then return here or press Refresh Project Charts."); return
        mx=max(float(r['low_stress']) for r in rows) or 1
        lines=[f"PROJECT GANTT / STRESS BANDS — {len(rows)} saved PERT record(s)", "Legend: ▓ expected duration  ░ cushion out to Worst + 3σ", ""]
        for r in rows:
            exp=max(1,round(float(r['expected'])/mx*30)); low=max(exp,round(float(r['low_stress'])/mx*30))
            name=(r['title'] or 'Task')[:22].ljust(22); lines.append(f"{name} | {'▓'*exp}{'░'*(low-exp)} {r['unit']}")
        lines += ["", "PERT BOX / RANGE SUMMARY"]
        for r in rows:
            lines.append(f"{(r['title'] or 'Task')[:22]}: best {r['optimistic']:.2f} ├── likely {r['likely']:.2f} ──┤ worst {r['pessimistic']:.2f} | σ {r['sigma']:.2f}")
        self.query_one("#chart_report",Static).update("\n".join(lines))

    def refresh_clay(self):
        t=self.query_one("#clay_table",DataTable); t.clear(); rows=connect().execute("SELECT * FROM clay_tablets WHERE project_id=? ORDER BY id DESC",(self.project_id,)).fetchall()
        for r in rows:t.add_row(r['id'],r['text'],r['created_at'])

    def refresh_journal(self):
        t=self.query_one("#journal_table",DataTable); t.clear(); rows=connect().execute("SELECT * FROM journal WHERE project_id=? ORDER BY id DESC",(self.project_id,)).fetchall()
        for r in rows:t.add_row(r['id'],r['created_at'],r['body'][:100].replace('\n',' '))

    @staticmethod
    def statement(as_a,need,so_that,because):
        prefix=f"As a {as_a}, " if as_a else ""; b=f" because {because}" if because else ""
        return f"{prefix}I need to {need} so that I can {so_that}{b}"

    def require_project(self):
        if not self.project_id: self.note("Create or choose a project first."); return False
        return True

    def note(self,msg): self.query_one("#status",Static).update(msg)


def main(): WizeWizard().run()
if __name__ == "__main__": main()
