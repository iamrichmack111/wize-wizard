from __future__ import annotations
import os, secrets, sqlite3, math, random, statistics
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from .db import connect
from .models import derive_estimates, communications_report, LAFLEY, LEVELS
from .learning import LESSONS, LESSON_MAP, FINAL_PLAN_TIPS
from .exporter import export_project


def _db():
    return connect()


def _csrf():
    token = session.get("csrf")
    if not token:
        token = session["csrf"] = secrets.token_urlsafe(24)
    return token


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("WIZE_SECRET_KEY", secrets.token_hex(32)),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("WIZE_SECURE_COOKIE", "0") == "1",
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    bootstrap_admin()

    @app.context_processor
    def inject_globals():
        guides = {
            "home": ("Start here", "Create or select a project, then answer the five strategic Need questions.", "five_whys", "Start the Five Strategic Questions"),
            "wizard": ("Answer, then ask WHY", "For one strategic question, write the Need. Wize immediately asks WHY; answer it as another complete I need to… so that I can… statement for Wish, then Dream, then Fantasy.", "pert_original", "Assess the original Need with PERT"),
            "five_whys": ("Build each strategic Why chain", "Choose one strategic question. Save its Need goal, then answer WHY immediately as Wish, Dream and Fantasy using the same I need to… so that I can… grammar.", "wizard", "Continue the selected Why chain"),
            "pert_original": ("Test the goals", "Choose a Need goal and estimate Best / Most Likely / Worst. Do this before treating the goal as execution-ready.", "tasks", "Review execution tasks"),
            "tasks": ("Execute", "Work the tasks generated from strategy statements. Update status as work moves from Backlog to Doing to Done.", "communications", "Plan team communication"),
            "communications": ("Design the team", "Enter total people. Wize gives each working group a Manager and Product Lead where the group is large enough, preserves stable contributor pairs, promotes any remainder into coordination management, and recalculates the communication reduction.", "reports", "Review the project report"),
            "clay_tablets": ("Challenge assumptions", "Record reasons, assumptions and evidence that should survive beyond a single task.", "journal", "Continue to the journal"),
            "journal": ("Record what happened", "Capture observations, changes and lessons from execution so the next strategy pass can improve.", "reports", "Review reports"),
            "reports": ("Check readiness", "Confirm each Need goal has a PERT assessment, inspect the Wish/Dream/Fantasy trace and review communication structure.", "five_whys", "Start another strategy pass"),
            "handbook": ("Read, then apply", "Read the handbook inside Wize. Do not memorize acronyms first: start with the plain-English meaning, worked example, when to use it, and when not to overread it. Then convert the conclusion into an I need to… so that I can… statement.", "learn", "Open guided lessons"),
            "learn": ("Learn before choosing", "If you do not know what to do yet, start here. Each lesson tells you the question the concept answers, spells out every acronym, shows an animated example, explains the steps, and links directly to the live tool.", "wizard", "Apply learning to a real project"),
            "lesson": ("Understand → watch → try → apply", "First learn what the concept means in plain English. Then watch the animated example, work the example, and use the linked live tool. Finish by converting the conclusion into a Wize Need or project decision.", "wizard", "Apply it in Wize"),
            "market": ("Understand the market before acting", "Enter the competitor shares you actually know. Wize spells out the concentration measures, shows what each number means, and tells you what evidence to check next. Do not treat a concentration number as a decision by itself.", "reports", "Carry the finding into the project plan"),
            "finance": ("Test whether growth creates value", "Enter operating profit after tax, invested capital, and the financing cost. Wize explains each term in plain English before comparing the return with the cost of capital.", "reports", "Carry the finding into the project plan"),
            "risk": ("Turn one estimate into a range", "Use this after the original PERT test when uncertainty matters. The simulation shows a range of plausible outcomes; it does not replace the Need Goal or the original PERT record.", "reports", "Carry the risk range into the project plan"),
        }
        guide = guides.get(request.endpoint)
        guide_data = None
        if guide:
            title, body, endpoint, label = guide
            try: next_url = url_for(endpoint, project_id=session.get("project_id"))
            except Exception: next_url = url_for("home")
            guide_data = {"title": title, "body": body, "next_url": next_url, "next_label": label}
        return {"csrf_token": _csrf, "current_user": current_user(), "lesson_count": len(LESSONS), "workflow_help": guide_data}

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        resp.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; media-src 'self'; frame-src 'self'; object-src 'self';")
        return resp

    def require_csrf():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
                abort(400, "Invalid CSRF token")

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login", next=request.path))
            return fn(*args, **kwargs)
        return wrapper

    def admin_required(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            u = current_user()
            if not u or u["role"] != "admin":
                abort(403)
            return fn(*args, **kwargs)
        return wrapper

    @app.get("/healthz")
    def healthz():
        con = _db(); con.execute("SELECT 1").fetchone(); con.close()
        return {"ok": True, "service": "wize-wizard"}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            require_csrf()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            con = _db(); user = con.execute("SELECT * FROM users WHERE username=? AND active=1", (username,)).fetchone(); con.close()
            if not user or not check_password_hash(user["password_hash"], password):
                flash("Invalid username or password.", "danger")
            else:
                session.clear(); session["user_id"] = user["id"]; _csrf()
                if user["must_change_password"]:
                    flash("Temporary password accepted. Change it now.", "warning")
                    return redirect(url_for("change_password"))
                return redirect(request.args.get("next") or url_for("home"))
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        require_csrf(); session.clear(); return redirect(url_for("login"))

    @app.route("/change-password", methods=["GET", "POST"])
    @login_required
    def change_password():
        u = current_user()
        if request.method == "POST":
            require_csrf()
            old = request.form.get("old_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            if not check_password_hash(u["password_hash"], old):
                flash("Current password is incorrect.", "danger")
            elif len(new) < 10:
                flash("New password must be at least 10 characters.", "danger")
            elif new != confirm:
                flash("New passwords do not match.", "danger")
            else:
                con=_db(); con.execute("UPDATE users SET password_hash=?, must_change_password=0 WHERE id=?", (generate_password_hash(new), u["id"])); con.commit(); con.close()
                flash("Password changed.", "success"); return redirect(url_for("home"))
        return render_template("change_password.html")

    @app.get("/")
    @login_required
    def home():
        con=_db()
        stats={
            "projects": con.execute("SELECT COUNT(*) n FROM projects").fetchone()["n"],
            "tasks": con.execute("SELECT COUNT(*) n FROM tasks").fetchone()["n"],
            "lessons_done": con.execute("SELECT COUNT(*) n FROM lesson_progress WHERE user_id=? AND completed=1", (session["user_id"],)).fetchone()["n"],
            "users": con.execute("SELECT COUNT(*) n FROM users WHERE active=1").fetchone()["n"],
        }
        recent=con.execute("SELECT * FROM projects ORDER BY id DESC LIMIT 5").fetchall(); con.close()
        return render_template("home.html", stats=stats, recent=recent)

    @app.get("/handbook")
    @login_required
    def handbook():
        return render_template("handbook.html")

    @app.get("/handbook/pdf")
    @login_required
    def handbook_pdf():
        resp = send_from_directory(app.static_folder, "strategists_handbook.pdf", mimetype="application/pdf", as_attachment=False)
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'self';"
        return resp

    @app.get("/learn")
    @login_required
    def learn():
        con=_db(); rows=con.execute("SELECT lesson_slug, completed, best_score FROM lesson_progress WHERE user_id=?", (session["user_id"],)).fetchall(); con.close()
        progress={r["lesson_slug"]: dict(r) for r in rows}
        return render_template("learn.html", lessons=LESSONS, progress=progress)

    @app.route("/learn/<slug>", methods=["GET", "POST"])
    @login_required
    def lesson(slug):
        item=LESSON_MAP.get(slug)
        if not item: abort(404)
        result=None
        if request.method == "POST":
            require_csrf(); choice=int(request.form.get("choice", -1)); score=100 if choice == item["quiz"]["answer"] else 0
            con=_db(); con.execute("""INSERT INTO lesson_progress(user_id,lesson_slug,completed,best_score) VALUES(?,?,1,?)
                 ON CONFLICT(user_id,lesson_slug) DO UPDATE SET completed=1,best_score=MAX(best_score,excluded.best_score),updated_at=CURRENT_TIMESTAMP""", (session["user_id"], slug, score)); con.commit(); con.close(); result=score
        video_name=f"{slug}.mp4"
        video_path=Path(app.static_folder)/"videos"/video_name
        return render_template("lesson.html", lesson=item, result=result, video_name=video_name, video_exists=video_path.exists())

    @app.route("/strategy", methods=["GET", "POST"])
    @login_required
    def strategy():
        con=_db()
        if request.method == "POST":
            require_csrf()
            project=request.form.get("project", "").strip(); decision=request.form.get("decision", "").strip(); must=request.form.get("must_be_true", "").strip(); evidence=request.form.get("evidence", "").strip(); action=request.form.get("action", "").strip()
            if not all([project, decision, must, action]): flash("Project, decision, assumption and action are required.", "danger")
            else:
                cur=con.execute("INSERT INTO projects(name,description) VALUES(?,?)", (project, decision)); pid=cur.lastrowid
                con.execute("INSERT INTO strategy(project_id,category,level,need,so_that,because,priority) VALUES(?,?,?,?,?,?,?)", (pid,"Strategy Decision","Need",action,decision,must,2))
                con.execute("INSERT INTO clay_tablets(project_id,text) VALUES(?,?)", (pid, f"Assumption: {must}. Evidence: {evidence}"))
                con.execute("INSERT INTO tasks(project_id,title,need,so_that,because,source_level,priority) VALUES(?,?,?,?,?,?,?)", (pid,action,action,decision,must,"Need",2)); con.commit(); flash("Strategy converted into an executable project.", "success")
        projects=con.execute("SELECT * FROM projects ORDER BY id DESC LIMIT 20").fetchall(); con.close()
        return render_template("strategy.html", projects=projects)

    @app.route("/market", methods=["GET", "POST"])
    @login_required
    def market():
        result=None
        if request.method == "POST":
            require_csrf()
            shares=[]
            for x in request.form.get("shares", "").split(","):
                try: shares.append(float(x.strip()))
                except ValueError: pass
            if not shares or any(x < 0 for x in shares) or sum(shares) > 100.0001:
                flash("Enter comma-separated non-negative shares totaling no more than 100.", "danger")
            else:
                s=sorted(shares, reverse=True); cr4=sum(s[:4]); hhi=sum(x*x for x in s); leader=s[0]
                result={
                    "shares":s,"cr4":cr4,"hhi":hhi,"leader":leader,"remaining":100-sum(s),
                    "cr4_explanation": f"The four largest entered firms together control {cr4:.1f}% of the market share you entered.",
                    "hhi_explanation": f"The Herfindahl-Hirschman Index is {hhi:.0f} for the entered firms. Because shares are squared, larger firms influence this number more heavily.",
                    "next_checks": [
                        "Confirm that the market has been defined correctly before interpreting concentration.",
                        "Add missing competitor shares if the unentered remainder is material.",
                        "Compare concentration with growth, margins, buyer power, supplier power, substitutes and competitor response.",
                        "If this supports a decision, convert the conclusion into an I need to… so that I can… statement and PERT-test the resulting Need Goal.",
                    ],
                }
        return render_template("market.html", result=result)

    @app.route("/finance", methods=["GET", "POST"])
    @login_required
    def finance():
        result=None
        if request.method == "POST":
            require_csrf()
            try:
                nopat=float(request.form["nopat"]); capital=float(request.form["capital"]); wacc=float(request.form["wacc"])/100
                if capital <= 0: raise ValueError
                roic=nopat/capital; ep=nopat-(capital*wacc)
                result={"roic":roic*100,"wacc":wacc*100,"spread":(roic-wacc)*100,"economic_profit":ep,"creates":roic>wacc}
            except (ValueError, KeyError): flash("Enter valid positive capital and numeric values.", "danger")
        return render_template("finance.html", result=result)

    @app.route("/risk", methods=["GET", "POST"])
    @login_required
    def risk():
        result=None
        if request.method == "POST":
            require_csrf()
            try:
                estimate=float(request.form["estimate"])
                if estimate <= 0:
                    raise ValueError("Enter an estimate greater than zero.")
                uncertainty=request.form.get("uncertainty","medium")
                impact=request.form.get("impact","medium")
                spreads={"low":0.15,"medium":0.35,"high":0.65}
                spread=spreads.get(uncertainty,0.35)
                best=max(estimate*(1-spread), estimate*0.05)
                worst=estimate*(1+spread)
                samples=sorted(random.triangular(best,worst,estimate) for _ in range(5000))
                p50,p80,p95=samples[2499],samples[3999],samples[4749]
                maximum=max(p95, estimate, 0.01)
                if impact == "high":
                    recommendation=f"Because the impact is high, plan near the Very cautious value ({p95:.2f}) unless you can remove the biggest uncertainty first."
                elif impact == "medium":
                    recommendation=f"Use the Safer value ({p80:.2f}) as the working plan, then revisit it as evidence improves."
                else:
                    recommendation=f"The Typical value ({p50:.2f}) may be enough for routine work, with the Safer value ({p80:.2f}) as your fallback."
                result={
                    "estimate":estimate,"uncertainty":uncertainty,"impact":impact,
                    "p50":p50,"p80":p80,"p95":p95,
                    "p50_pct":round(100*p50/maximum,1),"p80_pct":round(100*p80/maximum,1),"p95_pct":100,
                    "recommendation":recommendation,
                }
            except Exception as e:
                flash(str(e) or "Enter a valid estimate.", "danger")
        return render_template("risk.html", result=result)



    def _projects_and_selected():
        con=_db(); projects=con.execute("SELECT * FROM projects ORDER BY id DESC").fetchall(); con.close()
        raw=request.values.get("project_id") or session.get("project_id")
        try: pid=int(raw) if raw else (int(projects[0]["id"]) if projects else None)
        except (TypeError,ValueError): pid=int(projects[0]["id"]) if projects else None
        if pid: session["project_id"]=pid
        return projects,pid

    def _statement(as_a, need, so_that, because):
        prefix=f"As a {as_a}, " if as_a else ""; suffix=f" because {because}" if because else ""
        return f"{prefix}I need to {need} so that I can {so_that}{suffix}"

    @app.post("/projects/add")
    @login_required
    def add_project():
        require_csrf(); name=request.form.get("name","").strip(); description=request.form.get("description","").strip()
        if not name: flash("Project name is required.","danger")
        else:
            con=_db(); cur=con.execute("INSERT INTO projects(name,description) VALUES(?,?)",(name,description)); con.commit(); con.close(); session["project_id"]=cur.lastrowid; flash("Project created.","success")
        return redirect(request.referrer or url_for("wizard"))

    @app.route("/wizard", methods=["GET","POST"])
    @login_required
    def wizard():
        projects,pid=_projects_and_selected(); con=_db()
        selected_category=request.values.get("category") or LAFLEY[0]
        if selected_category not in LAFLEY:
            selected_category=LAFLEY[0]
        if request.method=="POST" and request.form.get("action")=="save_strategy":
            require_csrf()
            if not pid:
                flash("Create a project first.","danger")
            else:
                category=request.form.get("category","").strip(); as_a=request.form.get("as_a","").strip(); need=request.form.get("need","").strip(); so_that=request.form.get("so_that","").strip(); because=request.form.get("because","").strip(); priority=int(request.form.get("priority",3))
                if category not in LAFLEY or not need or not so_that:
                    flash("Choose a strategy question and complete I need to / so that I can.","danger")
                else:
                    n=con.execute("SELECT COUNT(*) c FROM strategy WHERE project_id=? AND category=?",(pid,category)).fetchone()["c"]
                    if n >= len(LEVELS):
                        flash("This question already has a complete Need → Wish → Dream → Fantasy Why chain.","danger")
                    else:
                        level=LEVELS[n]
                        title=_statement(as_a,need,so_that,because)
                        cur=con.execute("INSERT INTO strategy(project_id,category,level,as_a,need,so_that,because,priority) VALUES(?,?,?,?,?,?,?,?)",(pid,category,level,as_a,need,so_that,because,priority)); sid=cur.lastrowid
                        con.execute("INSERT INTO tasks(project_id,strategy_id,title,as_a,need,so_that,because,source_level,priority) VALUES(?,?,?,?,?,?,?,?,?)",(pid,sid,title,as_a,need,so_that,because,level,priority))
                        if because: con.execute("INSERT INTO clay_tablets(project_id,strategy_id,text) VALUES(?,?,?)",(pid,sid,because))
                        con.commit()
                        if level == "Need":
                            flash("Need saved. WHY 1 now appears for this same strategic question. Answer it in the same I need to… so that I can… format.", "success")
                        elif level == "Wish":
                            flash("Wish / Why 1 saved. WHY 2 now asks why that Wish matters. Keep the same sentence format.", "success")
                        elif level == "Dream":
                            flash("Dream / Why 2 saved. WHY 3 now asks why that Dream matters. Keep the same sentence format.", "success")
                        else:
                            flash("Fantasy / Why 3 saved. This strategic question is complete. PERT will assess the original Need goal.", "success")
                        return redirect(url_for("wizard", project_id=pid, category=category, why_prompt=1))
        chain=con.execute("SELECT * FROM strategy WHERE project_id=? AND category=? ORDER BY id",(pid,selected_category)).fetchall() if pid else []
        n=len(chain)
        complete=n >= len(LEVELS)
        next_level=None if complete else LEVELS[n]
        previous=chain[-1] if chain else None
        rows=con.execute("SELECT * FROM strategy WHERE project_id=? ORDER BY category,id",(pid,)).fetchall() if pid else []
        counts={}
        if pid:
            for c in LAFLEY:
                counts[c]=con.execute("SELECT COUNT(*) c FROM strategy WHERE project_id=? AND category=?",(pid,c)).fetchone()["c"]
        why_prompt=request.args.get("why_prompt")=="1" and n>0 and not complete
        con.close()
        return render_template("wizard.html",projects=projects,project_id=pid,categories=LAFLEY,next_level=next_level,selected_category=selected_category,rows=rows,counts=counts,why_prompt=why_prompt,chain=chain,previous=previous,complete=complete)

    @app.route("/five-whys")
    @login_required
    def five_whys():
        projects,pid=_projects_and_selected(); con=_db(); chains={}
        if pid:
            for question in LAFLEY:
                chains[question]=con.execute("SELECT * FROM strategy WHERE project_id=? AND category=? ORDER BY id",(pid,question)).fetchall()
        con.close()
        return render_template("five_whys.html",projects=projects,project_id=pid,questions=LAFLEY,chains=chains,levels=LEVELS)

    @app.route("/pert", methods=["GET","POST"])
    @login_required
    def pert_original():
        projects,pid=_projects_and_selected(); con=_db(); result=None
        goal_tasks=con.execute("""SELECT t.id,t.title,s.category FROM tasks t JOIN strategy s ON s.id=t.strategy_id
            WHERE t.project_id=? AND s.level='Need' ORDER BY s.id""",(pid,)).fetchall() if pid else []
        if request.method=="POST":
            require_csrf()
            try:
                best=float(request.form["best"]); worst_raw=request.form.get("worst","").strip(); worst=float(worst_raw) if worst_raw else None
                severity=int(request.form.get("severity",3)); unit=request.form.get("unit","hour")
                o,m,pess,r,derived=derive_estimates(best,worst,severity)
                selected_task=int(request.form.get("task_id") or 0)
                task=con.execute("SELECT * FROM tasks WHERE id=? AND project_id=?",(selected_task,pid)).fetchone() if selected_task and pid else None
                if task:
                    tid=task["id"]; title=task["title"]
                else:
                    title=request.form.get("title","").strip() or "Untitled PERT goal"
                    cur=con.execute("INSERT INTO tasks(project_id,title,need,so_that,source_level,priority) VALUES(?,?,?,?,?,?)",(pid,title,title,"complete the estimated outcome","PERT",severity)); tid=cur.lastrowid
                con.execute("INSERT INTO pert(project_id,task_id,unit,optimistic,likely,pessimistic,severity,estimate_mode,expected,sigma,low_stress,high_stress,derived,confidence_sentence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (pid,tid,unit,o,m,pess,severity,r.mode,r.expected,r.sigma,r.low_stress,r.high_stress,1 if derived else 0,r.confidence_sentence))
                con.commit(); result={"title":title,"o":o,"m":m,"p":pess,"r":r,"unit":unit,"derived":derived}
                flash("PERT assessment saved against the selected Need goal." if task else "PERT assessment saved.","success")
            except Exception as e: flash(str(e) or "Enter valid PERT values.","danger")
        history=con.execute("SELECT p.*,t.title FROM pert p LEFT JOIN tasks t ON t.id=p.task_id WHERE p.project_id=? ORDER BY p.id DESC",(pid,)).fetchall() if pid else []
        con.close(); return render_template("pert_original.html",projects=projects,project_id=pid,result=result,history=history,goal_tasks=goal_tasks)

    @app.route("/tasks", methods=["GET","POST"])
    @login_required
    def tasks():
        projects,pid=_projects_and_selected(); con=_db()
        if request.method=="POST":
            require_csrf(); action=request.form.get("action")
            if not pid: flash("Create a project first.","danger")
            elif action=="add":
                as_a=request.form.get("as_a","").strip(); need=request.form.get("need","").strip(); so=request.form.get("so_that","").strip(); because=request.form.get("because","").strip(); priority=int(request.form.get("priority",3))
                if not need or not so: flash("Tasks require both I need to and so that I can.","danger")
                else:
                    title=_statement(as_a,need,so,because); con.execute("INSERT INTO tasks(project_id,title,as_a,need,so_that,because,source_level,priority) VALUES(?,?,?,?,?,?,?,?)",(pid,title,as_a,need,so,because,"Manual",priority)); con.commit(); flash("Structured task added.","success")
            elif action=="status":
                tid=int(request.form.get("task_id",0)); status=request.form.get("status","Backlog")
                if status in {"Backlog","Doing","Done"}: con.execute("UPDATE tasks SET status=? WHERE id=? AND project_id=?",(status,tid,pid)); con.commit()
        rows=con.execute("SELECT * FROM tasks WHERE project_id=? ORDER BY priority,id",(pid,)).fetchall() if pid else []; con.close()
        total=len(rows); done=sum(1 for r in rows if r["status"]=="Done"); weighted=sum(max(1,6-int(r["priority"])) for r in rows); weighted_done=sum(max(1,6-int(r["priority"])) for r in rows if r["status"]=="Done")
        return render_template("tasks.html",projects=projects,project_id=pid,rows=rows,total=total,done=done,weighted=weighted,weighted_done=weighted_done)

    @app.route("/communications", methods=["GET","POST"])
    @login_required
    def communications():
        projects,pid=_projects_and_selected(); result=None; con=_db()
        if request.method=="POST":
            require_csrf()
            try:
                n=int(request.form["people"]);
                if n<1: raise ValueError("People must be at least 1.")
                result=communications_report(n)
                if pid:
                    con.execute("INSERT INTO communications(project_id,people,channels,suggested_group_size,groups,structured_channels,reduction,reduction_pct,report,remainder,managers,oversight_channels,manager_channels,local_supervisors,workers,local_management_channels,supervisor_coordination,management_ratio,avg_span,product_leaders,stable_pair_channels) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(pid,n,result["channels"],result["group_size"],result["groups"],result["structured"],result["reduction"],result["reduction_pct"],result["sentence"],result["remainder"],result["managers"],result["oversight"],result["manager_channels"],result["local_supervisors"],result["workers"],result["local_management_channels"],result["supervisor_coordination"],result["management_ratio"],result["avg_span"],result["product_leaders"],result["stable_pair_channels"])); con.commit()
            except Exception as e: flash(str(e) or "Enter a whole number of people.","danger")
        history_rows=con.execute("SELECT * FROM communications WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall() if pid else []
        # Recalculate old log entries with the current Wize management model so a prior
        # v0.7.1 row cannot keep showing zero managers/product leads after the algorithm changes.
        history=[]
        for row in history_rows:
            fresh=communications_report(row["people"])
            fresh["id"]=row["id"]; fresh["created_at"]=row["created_at"]
            history.append(fresh)
            con.execute("UPDATE communications SET channels=?,suggested_group_size=?,groups=?,structured_channels=?,reduction=?,reduction_pct=?,report=?,remainder=?,managers=?,oversight_channels=?,manager_channels=?,local_supervisors=?,workers=?,local_management_channels=?,supervisor_coordination=?,management_ratio=?,avg_span=?,product_leaders=?,stable_pair_channels=? WHERE id=?",(fresh["channels"],fresh["group_size"],fresh["groups"],fresh["structured"],fresh["reduction"],fresh["reduction_pct"],fresh["sentence"],fresh["remainder"],fresh["managers"],fresh["oversight"],fresh["manager_channels"],fresh["local_supervisors"],fresh["workers"],fresh["local_management_channels"],fresh["supervisor_coordination"],fresh["management_ratio"],fresh["avg_span"],fresh["product_leaders"],fresh["stable_pair_channels"],row["id"]))
        if history_rows: con.commit()
        con.close()
        return render_template("communications.html",projects=projects,project_id=pid,result=result,history=history)

    @app.route("/clay-tablets")
    @login_required
    def clay_tablets():
        projects,pid=_projects_and_selected(); con=_db(); rows=con.execute("SELECT * FROM clay_tablets WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall() if pid else []; con.close(); return render_template("clay.html",projects=projects,project_id=pid,rows=rows)

    @app.route("/journal", methods=["GET","POST"])
    @login_required
    def journal():
        projects,pid=_projects_and_selected(); con=_db()
        if request.method=="POST":
            require_csrf(); body=request.form.get("body","").strip()
            if pid and body: con.execute("INSERT INTO journal(project_id,body) VALUES(?,?)",(pid,body)); con.commit(); flash("Journal entry saved.","success")
            else: flash("Choose a project and enter a journal note.","danger")
        rows=con.execute("SELECT * FROM journal WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall() if pid else []; con.close(); return render_template("journal.html",projects=projects,project_id=pid,rows=rows)

    @app.route("/reports")
    @login_required
    def reports():
        projects,pid=_projects_and_selected(); con=_db()
        project=con.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone() if pid else None
        pert=con.execute("SELECT p.*,t.title FROM pert p LEFT JOIN tasks t ON p.task_id=t.id WHERE p.project_id=? ORDER BY p.id",(pid,)).fetchall() if pid else []
        strategy_rows=con.execute("SELECT * FROM strategy WHERE project_id=? ORDER BY id",(pid,)).fetchall() if pid else []
        goals=con.execute("""SELECT s.*, t.id AS task_id, t.title AS task_title,
            p.expected, p.sigma, p.low_stress, p.high_stress, p.unit, p.confidence_sentence
            FROM strategy s LEFT JOIN tasks t ON t.strategy_id=s.id
            LEFT JOIN pert p ON p.id=(SELECT p2.id FROM pert p2 WHERE p2.task_id=t.id ORDER BY p2.id DESC LIMIT 1)
            WHERE s.project_id=? AND s.level='Need' ORDER BY s.id""",(pid,)).fetchall() if pid else []
        tasks=con.execute("SELECT * FROM tasks WHERE project_id=? ORDER BY priority,id",(pid,)).fetchall() if pid else []
        comm_rows=con.execute("SELECT * FROM communications WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall() if pid else []
        comms=[]
        for row in comm_rows:
            fresh=communications_report(row["people"])
            fresh["id"]=row["id"]; fresh["created_at"]=row["created_at"]
            comms.append(fresh)
        clay=con.execute("SELECT * FROM clay_tablets WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall() if pid else []
        journal=con.execute("SELECT * FROM journal WHERE project_id=? ORDER BY id DESC LIMIT 10",(pid,)).fetchall() if pid else []
        con.close()
        assessed=sum(1 for g in goals if g["expected"] is not None)
        completed_chains=0
        for q in LAFLEY:
            if sum(1 for r in strategy_rows if r["category"]==q) >= len(LEVELS): completed_chains += 1
        readiness_items=[
            ("Five strategic questions", completed_chains==len(LAFLEY), f"{completed_chains}/{len(LAFLEY)} complete"),
            ("Need Goals defined", len(goals)>=len(LAFLEY), f"{len(goals)} goals"),
            ("Goals PERT-assessed", len(goals)>0 and assessed==len(goals), f"{assessed}/{len(goals)} assessed" if goals else "0 assessed"),
            ("Execution tasks created", len(tasks)>0, f"{len(tasks)} tasks"),
            ("Communication structure designed", len(comms)>0, "logged" if comms else "not yet"),
            ("Assumptions captured", len(clay)>0, f"{len(clay)} Clay Tablets"),
        ]
        ready_count=sum(1 for _,ok,_ in readiness_items if ok)
        readiness_pct=round(100*ready_count/len(readiness_items)) if readiness_items else 0
        return render_template(
            "reports.html", projects=projects, project_id=pid, project=project, pert=pert, strategy_rows=strategy_rows,
            goals=goals, tasks=tasks, comms=comms, clay=clay, journal=journal, final_tips=FINAL_PLAN_TIPS,
            readiness_items=readiness_items, readiness_pct=readiness_pct
        )

    @app.get("/admin/users")
    @admin_required
    def admin_users():
        con=_db(); users=con.execute("SELECT id,username,role,active,must_change_password,created_at FROM users ORDER BY username").fetchall(); con.close()
        return render_template("admin_users.html", users=users)

    @app.post("/admin/users/add")
    @admin_required
    def add_user():
        require_csrf(); username=request.form.get("username","").strip(); password=request.form.get("password",""); role=request.form.get("role","user")
        if not username or len(password)<10 or role not in {"admin","user"}: flash("Username and 10+ character password required.", "danger")
        else:
            try:
                con=_db(); con.execute("INSERT INTO users(username,password_hash,role,must_change_password) VALUES(?,?,?,1)",(username,generate_password_hash(password),role)); con.commit(); con.close(); flash("User added with a temporary password.","success")
            except sqlite3.IntegrityError: flash("Username already exists.","danger")
        return redirect(url_for("admin_users"))

    @app.post("/admin/users/<int:uid>/reset")
    @admin_required
    def reset_user(uid):
        require_csrf(); password=request.form.get("password","")
        if len(password)<10: flash("Temporary password must be at least 10 characters.","danger")
        else:
            con=_db(); con.execute("UPDATE users SET password_hash=?,must_change_password=1 WHERE id=?",(generate_password_hash(password),uid)); con.commit(); con.close(); flash("Password reset; user must change it at next login.","success")
        return redirect(url_for("admin_users"))

    @app.post("/admin/users/<int:uid>/delete")
    @admin_required
    def delete_user(uid):
        require_csrf()
        if uid == session["user_id"]: flash("You cannot remove your own active account.","danger")
        else:
            con=_db(); con.execute("UPDATE users SET active=0 WHERE id=?",(uid,)); con.commit(); con.close(); flash("User removed.","success")
        return redirect(url_for("admin_users"))

    return app


def current_user():
    uid=session.get("user_id")
    if not uid: return None
    con=_db(); u=con.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone(); con.close(); return u


def bootstrap_admin():
    con=_db()
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user', active INTEGER NOT NULL DEFAULT 1, must_change_password INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    con.execute("""CREATE TABLE IF NOT EXISTS lesson_progress (
        user_id INTEGER NOT NULL, lesson_slug TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0,
        best_score INTEGER NOT NULL DEFAULT 0, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, lesson_slug), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""")
    exists=con.execute("SELECT 1 FROM users WHERE username='admin'").fetchone()
    if not exists:
        import os

        admin_username = os.environ.get("WIZE_ADMIN_USERNAME", "").strip()
        admin_password = os.environ.get("WIZE_ADMIN_PASSWORD", "")

        if not admin_username or not admin_password:
            raise RuntimeError(
                "No users exist and WIZE_ADMIN_USERNAME/WIZE_ADMIN_PASSWORD are not configured"
            )

        if len(admin_password) < 12:
            raise RuntimeError(
                "WIZE_ADMIN_PASSWORD must be at least 12 characters"
            )

        con.execute(
            "INSERT INTO users(username,password_hash,role,must_change_password) VALUES(?,?,?,0)",
            (
                admin_username,
                generate_password_hash(admin_password),
                "admin",
            ),
        )
    con.commit(); con.close()


def main():
    app=create_app()
    host=os.environ.get("WIZE_HOST","127.0.0.1")
    port=int(os.environ.get("WIZE_PORT","8080"))
    if os.environ.get("WIZE_DEV","0")=="1": app.run(host=host,port=port,debug=False)
    else:
        from waitress import serve
        serve(app,host=host,port=port,threads=int(os.environ.get("WIZE_THREADS","6")))

if __name__ == "__main__": main()
