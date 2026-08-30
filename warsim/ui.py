from __future__ import annotations
import math
import random
import tkinter as tk
from tkinter import ttk, messagebox

from .config import APP_NAME, VERSION, COLORS
from .data import ERAS, BRANCHES, NAVAL_RANKS, HELM_TOPICS, CAPTAIN_DEPARTMENTS, WRITTEN_QUESTIONS
from .models import CareerProfile, BridgeState, DamageState
from .ship import (
    create_training_ship, ship_tick, evaluate_ship_scenario, ship_summary,
    toggle_hatch, toggle_breaker, toggle_ventilation, toggle_firemain_valve,
    route_pump, stop_pump, assign_team, adjacent_hatches, neighbor_for,
)
from .persistence import load_profile, save_profile, save_path
from .systems import (
    promotion_status, promote, apply_written_exam, update_bridge, bridge_next_order,
    bridge_result, damage_tick, damage_action, damage_result, generate_crew, apply_ship_systems_result,
    apply_historical_result, apply_enterprise_duty_result, apply_shipboard_walk_result,
)
from .enterprise import (
    create_enterprise_duty_state, advance_enterprise, jump_to_next_enterprise_task,
    perform_station_action, action_catalog, station_snapshot, open_tasks, closed_tasks,
    enterprise_summary, evaluate_enterprise, assign_crew, STATION_DEFS, ENTERPRISE_SOURCES,
)
from .walkship import (
    create_shipboard_walk_state, move_player, interact, advance_shipboard, current_zone, current_station,
    nearby_equipment, nearby_aircraft, nearby_hatch, qualification_status, shipboard_summary, evaluate_shipboard,
    raycast, visible_equipment, visible_crew, update_crew_movement, active_objective, objective_navigation, ship_alarm_state,
    DECK_MAPS, DECK_NAMES, EQUIPMENT, HATCHES, ZONES, QUALIFICATION_REQUIREMENTS, STATION_ANCHORS,
)
from .historical import (
    create_midway_state, advance_historical, jump_to_next_event, active_prompt, upcoming_prompt,
    answer_decision, evaluate_historical, historical_summary, current_weather, min_to_hhmm,
    FORCE_PLOT, WEATHER_ZONES, SOURCES, ORDER_OF_BATTLE, EVENTS, DECISIONS,
)


class WarSimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1440x900")
        self.minsize(1180, 720)
        self.configure(bg=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.profile = load_profile() or CareerProfile()
        self.bridge_state = None
        self.damage_state = None
        self.ship_state = None
        self.ship_selected = "ENGINE_2"
        self.historical_state = None
        self.enterprise_state = None
        self.enterprise_station = "CIC"
        self.shipboard_state = None
        self._ship_keys = set()
        self._hist_prompt_key = None
        self._after_ids = []
        self._screen_name = None
        self._build_styles()
        self._build_shell()
        self.show_dashboard()

    def _build_styles(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("TFrame", background=COLORS["bg"])
        s.configure("Panel.TFrame", background=COLORS["panel"])
        s.configure("Panel2.TFrame", background=COLORS["panel2"])
        s.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        s.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"])
        s.configure("Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"])
        s.configure("Title.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI Semibold", 22))
        s.configure("Hero.TLabel", background=COLORS["panel"], foreground=COLORS["accent"], font=("Segoe UI Semibold", 26))
        s.configure("Section.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Segoe UI Semibold", 14))
        s.configure("Good.TLabel", background=COLORS["panel"], foreground=COLORS["good"])
        s.configure("Warn.TLabel", background=COLORS["panel"], foreground=COLORS["warn"])
        s.configure("Danger.TLabel", background=COLORS["panel"], foreground=COLORS["danger"])
        s.configure("Accent.TButton", background=COLORS["accent2"], foreground="white", borderwidth=0, padding=10)
        s.map("Accent.TButton", background=[("active", COLORS["accent"])])
        s.configure("Nav.TButton", background=COLORS["panel"], foreground=COLORS["muted"], borderwidth=0, padding=(16, 12), anchor="w")
        s.map("Nav.TButton", background=[("active", COLORS["panel2"])], foreground=[("active", COLORS["text"])])
        s.configure("TButton", background=COLORS["panel2"], foreground=COLORS["text"], borderwidth=0, padding=8)
        s.map("TButton", background=[("active", COLORS["line"])])
        s.configure("TCombobox", fieldbackground=COLORS["panel2"], background=COLORS["panel2"], foreground=COLORS["text"])
        s.configure("Horizontal.TProgressbar", troughcolor=COLORS["line"], background=COLORS["accent2"], bordercolor=COLORS["line"])
        s.configure("Treeview", background=COLORS["panel2"], fieldbackground=COLORS["panel2"], foreground=COLORS["text"], rowheight=28)
        s.configure("Treeview.Heading", background=COLORS["line"], foreground=COLORS["text"])

    def _build_shell(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        nav = ttk.Frame(self, style="Panel.TFrame", width=230)
        nav.grid(row=0, column=0, sticky="ns")
        nav.grid_propagate(False)
        nav.columnconfigure(0, weight=1)

        logo = tk.Canvas(nav, width=190, height=90, bg=COLORS["panel"], highlightthickness=0)
        logo.grid(row=0, column=0, padx=20, pady=(24, 14))
        logo.create_polygon(20, 45, 50, 15, 140, 15, 170, 45, 140, 75, 50, 75, fill=COLORS["panel2"], outline=COLORS["accent"], width=2)
        logo.create_text(95, 41, text="WAR", fill=COLORS["text"], font=("Segoe UI Semibold", 20))
        logo.create_text(95, 64, text="SIMULATOR", fill=COLORS["accent"], font=("Segoe UI Semibold", 10))

        buttons = [
            ("COMMAND CENTER", self.show_dashboard),
            ("NEW CAREER", self.show_new_career),
            ("ACADEMY", self.show_academy),
            ("BRIDGE PRACTICAL", self.show_bridge),
            ("DAMAGE CONTROL", self.show_damage_control),
            ("SHIP SYSTEMS", self.show_ship_systems),
            ("USS ENTERPRISE DUTY", self.show_enterprise_duty),
            ("ENTERPRISE WALKTHROUGH", self.show_shipboard_walkthrough),
            ("HISTORICAL OPERATIONS", self.show_historical_ops),
            ("HISTORICAL TIMELINE", self.show_timeline),
            ("CREW", self.show_crew),
            ("SERVICE RECORD", self.show_service_record),
        ]
        for i, (text, cmd) in enumerate(buttons, start=1):
            ttk.Button(nav, text=text, command=cmd, style="Nav.TButton").grid(row=i, column=0, sticky="ew", padx=10, pady=2)
        ttk.Separator(nav).grid(row=len(buttons)+1, column=0, sticky="ew", padx=20, pady=15)
        ttk.Button(nav, text="SAVE CAREER", command=self.save_now, style="Accent.TButton").grid(row=len(buttons)+2, column=0, sticky="ew", padx=18, pady=4)
        ttk.Button(nav, text="QUIT", command=self.on_close, style="Nav.TButton").grid(row=len(buttons)+3, column=0, sticky="ew", padx=10, pady=2)
        ttk.Label(nav, text=f"v{VERSION} • shipboard walkthrough build", style="Muted.TLabel").grid(row=len(buttons)+4, column=0, padx=20, pady=20, sticky="sw")
        nav.rowconfigure(len(buttons)+4, weight=1)

        self.content = ttk.Frame(self)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)
        self.header = ttk.Frame(self.content)
        self.header.grid(row=0, column=0, sticky="ew", padx=28, pady=(22, 10))
        self.header.columnconfigure(0, weight=1)
        self.header_title = ttk.Label(self.header, text="", style="Title.TLabel")
        self.header_title.grid(row=0, column=0, sticky="w")
        self.header_status = ttk.Label(self.header, text="", foreground=COLORS["muted"])
        self.header_status.grid(row=0, column=1, sticky="e")
        self.body = ttk.Frame(self.content)
        self.body.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 28))
        self.body.columnconfigure(0, weight=1)
        self.body.rowconfigure(0, weight=1)

    def _clear_body(self, title: str):
        self._cancel_after()
        try:
            self.unbind("<KeyPress>")
            self.unbind("<KeyRelease>")
        except Exception:
            pass
        self._ship_keys = set()
        self._screen_name = title
        for w in self.body.winfo_children():
            w.destroy()
        self.header_title.config(text=title)
        self.header_status.config(text=f"{self.profile.name} • {self.profile.rank} • {self.profile.branch} • {self.profile.era}")

    def _cancel_after(self):
        for aid in self._after_ids:
            try:
                self.after_cancel(aid)
            except Exception:
                pass
        self._after_ids.clear()

    def later(self, ms, func):
        holder = {}
        def wrapped():
            aid = holder.get("id")
            if aid in self._after_ids:
                self._after_ids.remove(aid)
            func()
        aid = self.after(ms, wrapped)
        holder["id"] = aid
        self._after_ids.append(aid)
        return aid

    def panel(self, parent, row=0, col=0, rowspan=1, colspan=1, sticky="nsew", padx=8, pady=8):
        f = ttk.Frame(parent, style="Panel.TFrame", padding=18)
        f.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan, sticky=sticky, padx=padx, pady=pady)
        return f

    def metric(self, parent, label, value, row, col):
        box = ttk.Frame(parent, style="Panel2.TFrame", padding=14)
        box.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        ttk.Label(box, text=label.upper(), background=COLORS["panel2"], foreground=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        ttk.Label(box, text=value, background=COLORS["panel2"], foreground=COLORS["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w", pady=(3, 0))
        return box

    def save_now(self, silent=False):
        path = save_profile(self.profile)
        if not silent:
            messagebox.showinfo(APP_NAME, f"Career saved.\n\n{path}")
        self.header_status.config(text=f"Saved • {self.profile.rank} • {self.profile.xp} XP")

    def show_dashboard(self):
        self._clear_body("COMMAND CENTER")
        root = ttk.Frame(self.body)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(1, weight=1)

        hero = self.panel(root, 0, 0, colspan=2)
        hero.columnconfigure(0, weight=1)
        ttk.Label(hero, text=self.profile.rank, style="Hero.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(hero, text=f"{self.profile.name}  •  {self.profile.branch}  •  {self.profile.era}", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Label(hero, text="EVERY PROMOTION IS EARNED", background=COLORS["panel"], foreground=COLORS["accent"], font=("Segoe UI Semibold", 10)).grid(row=0, column=1, rowspan=2, sticky="e")

        stats = self.panel(root, 1, 0)
        stats.columnconfigure((0, 1, 2), weight=1)
        ttk.Label(stats, text="Career Status", style="Section.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        self.metric(stats, "Experience", f"{self.profile.xp} XP", 1, 0)
        self.metric(stats, "Duty Periods", str(self.profile.duty_periods), 1, 1)
        self.metric(stats, "Reputation", f"{self.profile.reputation:.0f}%", 1, 2)
        self.metric(stats, "Written Exam", f"{self.profile.written_exam:.0f}%", 2, 0)
        self.metric(stats, "Practical", f"{self.profile.practical_exam:.0f}%", 2, 1)
        self.metric(stats, "Mission Perf.", f"{self.profile.mission_performance:.0f}%", 2, 2)
        self.metric(stats, "Leadership", f"{self.profile.leadership_eval:.0f}%", 3, 0)
        self.metric(stats, "Discipline", f"{self.profile.discipline:.0f}%", 3, 1)
        self.metric(stats, "Professionalism", f"{self.profile.professionalism:.0f}%", 3, 2)
        self.metric(stats, "Ship Systems Best", f"{self.profile.ship_systems_best:.0f}%", 4, 0)
        self.metric(stats, "Ship Drills", str(self.profile.ship_systems_runs), 4, 1)
        ttk.Button(stats, text="Launch Full Ship Systems Simulator", command=self.show_ship_systems).grid(row=4, column=2, sticky="nsew", padx=5, pady=5)
        self.metric(stats, "Historical Best", f"{self.profile.historical_best:.0f}%", 5, 0)
        self.metric(stats, "Historical Watches", str(self.profile.historical_runs), 5, 1)
        ttk.Button(stats, text="Launch Battle of Midway Watch", command=self.show_historical_ops, style="Accent.TButton").grid(row=5, column=2, sticky="nsew", padx=5, pady=5)
        self.metric(stats, "Enterprise Duty Best", f"{self.profile.enterprise_duty_best:.0f}%", 6, 0)
        self.metric(stats, "Enterprise Watches", str(self.profile.enterprise_duty_runs), 6, 1)
        ttk.Button(stats, text="Serve aboard USS Enterprise", command=self.show_enterprise_duty, style="Accent.TButton").grid(row=6, column=2, sticky="nsew", padx=5, pady=5)
        self.metric(stats, "Walkthrough Best", f"{self.profile.shipboard_walk_best:.0f}%", 7, 0)
        self.metric(stats, "Walkthrough Runs", str(self.profile.shipboard_walk_runs), 7, 1)
        ttk.Button(stats, text="Enter Enterprise Walkthrough", command=self.show_shipboard_walkthrough, style="Accent.TButton").grid(row=7, column=2, sticky="nsew", padx=5, pady=5)
        ttk.Button(stats, text="Open Promotion Board", command=self._promotion_board, style="Accent.TButton").grid(row=8, column=0, columnspan=3, sticky="ew", padx=5, pady=(14, 4))

        req = self.panel(root, 1, 1)
        ttk.Label(req, text=f"Next Promotion: {self.profile.next_rank}", style="Section.TLabel").pack(anchor="w", pady=(0, 12))
        for name, d in promotion_status(self.profile).items():
            row = ttk.Frame(req, style="Panel.TFrame")
            row.pack(fill="x", pady=3)
            mark = "✓" if d["met"] else "○"
            style = "Good.TLabel" if d["met"] else "Muted.TLabel"
            ttk.Label(row, text=mark, style=style, width=2).pack(side="left")
            ttk.Label(row, text=name, style="Panel.TLabel").pack(side="left")
            ttk.Label(row, text=f"{d['value']:.0f} / {d['required']}", style="Muted.TLabel").pack(side="right")

        log = self.panel(root, 2, 0, colspan=2)
        ttk.Label(log, text="Service Log", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        entries = self.profile.service_log[:6] or ["Career record initialized. Complete Academy and practical drills to begin earning advancement."]
        for item in entries:
            ttk.Label(log, text=f"• {item}", style="Muted.TLabel", wraplength=1000).pack(anchor="w", pady=2)

    def _promotion_board(self):
        ok, msg = promote(self.profile)
        if ok:
            self.save_now(silent=True)
            messagebox.showinfo("Promotion Board", msg)
        else:
            messagebox.showwarning("Promotion Board", msg)
        self.show_dashboard()

    def show_new_career(self):
        self._clear_body("NEW CAREER")
        f = self.panel(self.body)
        f.columnconfigure(1, weight=1)
        ttk.Label(f, text="Create a service career", style="Hero.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(f, text="Players begin at the bottom. The current build uses the document's complete example naval rank ladder for advancement.", style="Muted.TLabel", wraplength=900).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 20))
        ttk.Label(f, text="Service Name", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=8)
        name_var = tk.StringVar(value=self.profile.name)
        e = tk.Entry(f, textvariable=name_var, bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", font=("Segoe UI", 12))
        e.grid(row=2, column=1, sticky="ew", padx=(20, 0), ipady=8)
        ttk.Label(f, text="Branch", style="Panel.TLabel").grid(row=3, column=0, sticky="w", pady=8)
        branch_var = tk.StringVar(value=self.profile.branch)
        ttk.Combobox(f, textvariable=branch_var, values=BRANCHES, state="readonly").grid(row=3, column=1, sticky="ew", padx=(20, 0))
        ttk.Label(f, text="Starting Historical Era", style="Panel.TLabel").grid(row=4, column=0, sticky="w", pady=8)
        era_var = tk.StringVar(value=self.profile.era)
        ttk.Combobox(f, textvariable=era_var, values=list(ERAS), state="readonly").grid(row=4, column=1, sticky="ew", padx=(20, 0))

        warning = ttk.Frame(f, style="Panel2.TFrame", padding=14)
        warning.grid(row=5, column=0, columnspan=2, sticky="ew", pady=20)
        ttk.Label(warning, text="Historical-data safeguard", background=COLORS["panel2"], foreground=COLORS["warn"], font=("Segoe UI Semibold", 10)).pack(anchor="w")
        ttk.Label(warning, text="Historical scenarios are unlocked only after source verification. v0.6 includes the source-backed Battle of Midway operations watch, USS Enterprise (CV-6) station-duty mode, and the integrated training-schematic shipboard walkthrough with live crew, hatch control, objective routing, and explicitly simulated equipment-fault drills; unverified battles remain catalog-only until their data packages are researched.", background=COLORS["panel2"], foreground=COLORS["muted"], wraplength=900).pack(anchor="w", pady=(4, 0))

        def create():
            if not name_var.get().strip():
                messagebox.showwarning("New Career", "Enter a service name.")
                return
            if not messagebox.askyesno("New Career", "Start a new career? This replaces the current local save."):
                return
            self.profile = CareerProfile(name=name_var.get().strip(), branch=branch_var.get(), era=era_var.get())
            self.ship_state = None
            self.profile.add_log(f"Entered service as {self.profile.rank} in the {self.profile.branch}.")
            self.save_now(silent=True)
            self.show_dashboard()
        ttk.Button(f, text="BEGIN AT THE BOTTOM", command=create, style="Accent.TButton").grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def show_academy(self):
        self._clear_body("ACADEMY // HELMSMAN QUALIFICATION")
        root = ttk.Frame(self.body)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        topics = self.panel(root, 0, 0)
        ttk.Label(topics, text="Required Competencies", style="Section.TLabel").pack(anchor="w")
        ttk.Label(topics, text="The design document requires a helmsman to understand all nine areas below.", style="Muted.TLabel", wraplength=500).pack(anchor="w", pady=(4, 12))
        for t in HELM_TOPICS:
            row = ttk.Frame(topics, style="Panel.TFrame")
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=t, style="Panel.TLabel").pack(side="left")
            val = self.profile.topic_mastery.get(t, 0)
            ttk.Label(row, text=f"{val}% mastery", style="Good.TLabel" if val >= 70 else "Muted.TLabel").pack(side="right")
        ttk.Separator(topics).pack(fill="x", pady=15)
        ttk.Label(topics, text="Captain-level breadth", style="Section.TLabel").pack(anchor="w")
        ttk.Label(topics, text="Later progression will require proficiency across every ship department: " + ", ".join(CAPTAIN_DEPARTMENTS) + ".", style="Muted.TLabel", wraplength=520).pack(anchor="w", pady=(6, 0))

        exam = self.panel(root, 0, 1)
        ttk.Label(exam, text="Written Examination", style="Section.TLabel").pack(anchor="w")
        ttk.Label(exam, text=f"Best score: {self.profile.written_exam:.0f}% • Passing score: 70%", style="Muted.TLabel").pack(anchor="w", pady=(4, 14))
        ttk.Label(exam, text="The exam tests procedure and judgment. Passing it alone does not grant promotion; the practical examination and career requirements still apply.", style="Muted.TLabel", wraplength=520).pack(anchor="w")
        ttk.Button(exam, text="START WRITTEN EXAM", command=self.start_exam, style="Accent.TButton").pack(fill="x", pady=18)
        status = "QUALIFIED" if self.profile.qualifications.get("Helmsman") else "NOT YET QUALIFIED"
        ttk.Label(exam, text=f"Helmsman status: {status}", style="Good.TLabel" if status == "QUALIFIED" else "Warn.TLabel").pack(anchor="w")
        ttk.Label(exam, text="Qualification requires both written and bridge practical scores of at least 70% in this build.", style="Muted.TLabel", wraplength=520).pack(anchor="w", pady=(4, 0))

    def start_exam(self):
        self._clear_body("ACADEMY // WRITTEN EXAM")
        f = self.panel(self.body)
        state = {"i": 0, "correct": 0, "hits": {t: 0 for t in HELM_TOPICS}}
        q_label = ttk.Label(f, text="", style="Section.TLabel", wraplength=900, justify="left")
        q_label.pack(anchor="w", pady=(0, 18))
        choice_var = tk.IntVar(value=-1)
        options_frame = ttk.Frame(f, style="Panel.TFrame")
        options_frame.pack(fill="x")
        radios = []
        for i in range(4):
            rb = tk.Radiobutton(options_frame, variable=choice_var, value=i, text="", anchor="w", justify="left",
                                bg=COLORS["panel"], fg=COLORS["text"], selectcolor=COLORS["panel2"], activebackground=COLORS["panel"], activeforeground=COLORS["text"],
                                font=("Segoe UI", 11), padx=10, pady=8)
            rb.pack(fill="x")
            radios.append(rb)
        progress = ttk.Label(f, text="", style="Muted.TLabel")
        progress.pack(anchor="w", pady=(14, 0))

        def load_q():
            q = WRITTEN_QUESTIONS[state["i"]]
            q_label.config(text=f"Question {state['i'] + 1}: {q['q']}")
            for idx, txt in enumerate(q["choices"]):
                radios[idx].config(text=txt)
            choice_var.set(-1)
            progress.config(text=f"Question {state['i'] + 1} of {len(WRITTEN_QUESTIONS)}")

        def submit():
            if choice_var.get() < 0:
                messagebox.showwarning("Written Exam", "Select an answer.")
                return
            q = WRITTEN_QUESTIONS[state["i"]]
            if choice_var.get() == q["answer"]:
                state["correct"] += 1
                state["hits"][q["topic"]] += 1
            state["i"] += 1
            if state["i"] >= len(WRITTEN_QUESTIONS):
                score = 100 * state["correct"] / len(WRITTEN_QUESTIONS)
                apply_written_exam(self.profile, score, state["hits"])
                self.save_now(silent=True)
                messagebox.showinfo("Written Exam", f"Final score: {score:.0f}%\n\n{'PASS' if score >= 70 else 'NOT YET PASSED'}")
                self.show_academy()
            else:
                load_q()
        ttk.Button(f, text="SUBMIT ANSWER", command=submit, style="Accent.TButton").pack(fill="x", pady=(18, 0))
        load_q()

    def show_bridge(self):
        self._clear_body("BRIDGE PRACTICAL // HELMSMAN")
        self.bridge_state = BridgeState()
        root = ttk.Frame(self.body)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=4)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(0, weight=1)
        sim = self.panel(root, 0, 0)
        sim.columnconfigure(0, weight=1)
        sim.rowconfigure(1, weight=1)
        ttk.Label(sim, text="Maintain each ordered heading within ±5° for five seconds. Use A/D for rudder, W/S for throttle.", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        canvas = tk.Canvas(sim, bg=COLORS["water"], highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew")
        side = self.panel(root, 0, 1)
        labels = {}
        for key, title in [("ordered", "Ordered Heading"), ("heading", "Actual Heading"), ("rudder", "Rudder"), ("speed", "Speed"), ("wind", "Wind"), ("sea", "Sea State"), ("score", "Practical Score"), ("hold", "On-Course Hold")]:
            ttk.Label(side, text=title.upper(), style="Muted.TLabel").pack(anchor="w", pady=(8, 0))
            labels[key] = ttk.Label(side, text="--", style="Section.TLabel")
            labels[key].pack(anchor="w")
        ttk.Separator(side).pack(fill="x", pady=14)
        ttk.Button(side, text="RUDDER LEFT (A)", command=lambda: self._bridge_rudder(-5)).pack(fill="x", pady=3)
        ttk.Button(side, text="RUDDER RIGHT (D)", command=lambda: self._bridge_rudder(5)).pack(fill="x", pady=3)
        ttk.Button(side, text="MIDSHIPS (SPACE)", command=lambda: self._bridge_midships()).pack(fill="x", pady=3)
        ttk.Button(side, text="INCREASE THROTTLE (W)", command=lambda: self._bridge_throttle(.1)).pack(fill="x", pady=3)
        ttk.Button(side, text="DECREASE THROTTLE (S)", command=lambda: self._bridge_throttle(-.1)).pack(fill="x", pady=3)
        finish_btn = ttk.Button(side, text="END PRACTICAL", command=lambda: self._finish_bridge(), style="Accent.TButton")
        finish_btn.pack(fill="x", pady=(14, 0))

        def key(event):
            if event.keysym.lower() == 'a': self._bridge_rudder(-5)
            elif event.keysym.lower() == 'd': self._bridge_rudder(5)
            elif event.keysym.lower() == 'w': self._bridge_throttle(.1)
            elif event.keysym.lower() == 's': self._bridge_throttle(-.1)
            elif event.keysym == 'space': self._bridge_midships()
        self.bind("<KeyPress>", key)
        self.focus_force()

        def draw():
            if self._screen_name != "BRIDGE PRACTICAL // HELMSMAN" or not self.bridge_state:
                return
            st = self.bridge_state
            update_bridge(st, 0.10)
            if st.held_seconds >= 5.0 and st.completed_orders < 3:
                bridge_next_order(st)
            canvas.delete("all")
            w = max(400, canvas.winfo_width()); h = max(300, canvas.winfo_height())
            # sea lines
            for y in range(30, h, 55):
                offset = int((st.elapsed * 22 + y) % 60)
                for x in range(-60, w+60, 120):
                    canvas.create_arc(x+offset, y, x+offset+60, y+20, start=0, extent=180, style="arc", outline="#184565", width=2)
            cx, cy = w/2, h/2
            # ordered heading marker
            ang_o = math.radians(st.ordered_heading - 90)
            ox, oy = cx + math.cos(ang_o)*min(w,h)*0.38, cy + math.sin(ang_o)*min(w,h)*0.38
            canvas.create_line(cx, cy, ox, oy, fill=COLORS["accent"], width=2, dash=(6,4))
            # ship triangle
            ang = math.radians(st.heading - 90)
            pts=[]
            for a, r in [(0,34),(140,22),(220,22)]:
                aa=ang+math.radians(a)
                pts.extend([cx+math.cos(aa)*r, cy+math.sin(aa)*r])
            canvas.create_polygon(*pts, fill="#c8d0da", outline="white", width=2)
            canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill=COLORS["accent"], outline="")
            # compass ring
            r=min(w,h)*0.42
            canvas.create_oval(cx-r,cy-r,cx+r,cy+r,outline="#2a668e")
            for deg in range(0,360,45):
                a=math.radians(deg-90); tx=cx+math.cos(a)*(r-14); ty=cy+math.sin(a)*(r-14)
                canvas.create_text(tx,ty,text=f"{deg:03}",fill="#6f99b7",font=("Segoe UI",8))
            labels["ordered"].config(text=f"{st.ordered_heading:03.0f}°")
            labels["heading"].config(text=f"{st.heading:05.1f}°")
            labels["rudder"].config(text=f"{st.rudder:+.0f}°")
            labels["speed"].config(text=f"{st.speed:.1f} kt")
            labels["wind"].config(text=f"{st.wind_heading:.0f}° / {st.wind_speed:.0f} kt")
            labels["sea"].config(text=str(st.sea_state))
            labels["score"].config(text=f"{st.score:.0f}%")
            labels["hold"].config(text=f"{st.held_seconds:.1f}s / 5.0s  •  {st.completed_orders}/3 orders")
            if st.completed_orders >= 3:
                finish_btn.config(text="COMPLETE PRACTICAL")
            self.later(100, draw)
        draw()

    def _bridge_rudder(self, delta):
        if self.bridge_state:
            self.bridge_state.rudder = max(-30, min(30, self.bridge_state.rudder + delta))
    def _bridge_midships(self):
        if self.bridge_state: self.bridge_state.rudder = 0
    def _bridge_throttle(self, delta):
        if self.bridge_state: self.bridge_state.throttle = max(0.0, min(1.0, self.bridge_state.throttle + delta))
    def _finish_bridge(self):
        if not self.bridge_state: return
        score = bridge_result(self.profile, self.bridge_state)
        self.save_now(silent=True)
        messagebox.showinfo("Bridge Practical", f"Practical score: {score:.0f}%\nOrders completed: {self.bridge_state.completed_orders}/3\n\n{'PASS' if score >= 70 else 'NOT YET PASSED'}")
        self.show_academy()

    def show_damage_control(self):
        self._clear_body("DAMAGE CONTROL QUALIFICATION DRILL")
        self.damage_state = DamageState()
        root = ttk.Frame(self.body)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(0, weight=1)
        ship = self.panel(root, 0, 0)
        ship.columnconfigure(0, weight=1); ship.rowconfigure(1, weight=1)
        ttk.Label(ship, text="Control fire, flooding, smoke, power loss, and crew risk. Every action has consequences.", style="Muted.TLabel").grid(row=0,column=0,sticky="w",pady=(0,8))
        canvas = tk.Canvas(ship, bg="#0e141d", highlightthickness=0)
        canvas.grid(row=1,column=0,sticky="nsew")
        side = self.panel(root,0,1)
        stats = {}
        for k,title in [("hull","Hull"),("power","Electrical"),("flooding","Flooding"),("fire","Fire"),("smoke","Smoke"),("crew_health","Crew Health"),("fatigue","Fatigue"),("morale","Morale")]:
            row=ttk.Frame(side,style="Panel.TFrame"); row.pack(fill="x",pady=3)
            ttk.Label(row,text=title,style="Panel.TLabel").pack(side="left")
            stats[k]=ttk.Label(row,text="",style="Muted.TLabel"); stats[k].pack(side="right")
        ttk.Separator(side).pack(fill="x",pady=10)
        actions=[("Dispatch Fire Team","fire_team"),("Engage Dewatering Pumps","pumps"),("Isolate Electrical Zone","isolate"),("Controlled Ventilation","ventilate"),("Dispatch Medical Team","medical"),("Repair Power","repair_power")]
        for text, act in actions:
            ttk.Button(side,text=text,command=lambda a=act:self._damage_action(a)).pack(fill="x",pady=2)
        ttk.Button(side,text="END DRILL / EVALUATE",command=self._finish_damage,style="Accent.TButton").pack(fill="x",pady=(12,0))
        log_box=tk.Text(side,height=10,bg=COLORS["panel2"],fg=COLORS["muted"],insertbackground=COLORS["text"],relief="flat",wrap="word",font=("Consolas",9))
        log_box.pack(fill="both",expand=True,pady=(12,0))
        log_box.config(state="disabled")

        def render():
            if self._screen_name != "DAMAGE CONTROL QUALIFICATION DRILL" or not self.damage_state: return
            st=self.damage_state
            canvas.delete("all")
            w=max(canvas.winfo_width(),500); h=max(canvas.winfo_height(),400)
            compartments=[("BRIDGE",.06,.18,.27,.42),("CIC",.29,.18,.49,.42),("ENGINE",.51,.18,.72,.42),("STEERING",.74,.18,.94,.42),("MEDICAL",.06,.48,.27,.72),("GALLEY",.29,.48,.49,.72),("MACHINERY",.51,.48,.72,.72),("MAGAZINE",.74,.48,.94,.72)]
            for name,x1,y1,x2,y2 in compartments:
                fill="#181f29"
                outline=COLORS["line"]
                if name in ("ENGINE","MACHINERY"):
                    if st.fire>30: fill="#41212a"
                    elif st.fire>10: fill="#34252a"
                if name=="MACHINERY" and st.flooding>20: outline="#3d80a8"
                canvas.create_rectangle(w*x1,h*y1,w*x2,h*y2,fill=fill,outline=outline,width=2)
                canvas.create_text(w*(x1+x2)/2,h*(y1+y2)/2,text=name,fill=COLORS["text"],font=("Segoe UI Semibold",10))
            canvas.create_text(w*.5,h*.08,text="SIMULATED SHIP COMPARTMENT DAMAGE STATE",fill=COLORS["accent"],font=("Segoe UI Semibold",12))
            canvas.create_text(w*.5,h*.84,text=f"FIRE {st.fire:.0f}%   •   FLOODING {st.flooding:.0f}%   •   SMOKE {st.smoke:.0f}%",fill=COLORS["danger"] if st.fire>40 or st.flooding>40 else COLORS["warn"],font=("Segoe UI Semibold",12))
            for k,lbl in stats.items():
                v=getattr(st,k); lbl.config(text=f"{v:.0f}%")
            log_box.config(state="normal"); log_box.delete("1.0","end"); log_box.insert("1.0","\n".join(st.log)); log_box.config(state="disabled")
            if st.resolved or st.failed:
                return
            self.later(250, render)
        def tick():
            if self._screen_name != "DAMAGE CONTROL QUALIFICATION DRILL" or not self.damage_state: return
            damage_tick(self.damage_state)
            if not self.damage_state.resolved and not self.damage_state.failed:
                self.later(1000,tick)
        render(); tick()

    def _damage_action(self, action):
        if self.damage_state:
            damage_action(self.damage_state, action)
    def _finish_damage(self):
        if not self.damage_state:return
        score=damage_result(self.profile,self.damage_state)
        self.save_now(silent=True)
        messagebox.showinfo("Damage Control Evaluation",f"Evaluation: {score:.0f}%\nCrew survival: {self.damage_state.crew_health:.0f}%\nHull: {self.damage_state.hull:.0f}%\n\n{'PASS' if score>=70 else 'NOT YET PASSED'}")
        self.show_dashboard()

    def show_ship_systems(self):
        self._clear_body("FULL SHIP SYSTEMS SIMULATOR")
        if self.ship_state is None or self.ship_state.resolved or self.ship_state.failed:
            self.ship_state = create_training_ship()
            self.ship_selected = "ENGINE_2"

        root = ttk.Frame(self.body)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=7)
        root.columnconfigure(1, weight=3)
        root.rowconfigure(1, weight=1)

        top = self.panel(root, 0, 0, colspan=2, padx=0, pady=(0, 8))
        top.columnconfigure(tuple(range(7)), weight=1)
        self._ship_metric_labels = {}
        metrics = [
            ("TIME", "elapsed"), ("PORT PROP", "propulsion_port"),
            ("STBD PROP", "propulsion_starboard"), ("STEERING", "steering"),
            ("COMMS", "communications"), ("FIREMAIN", "firemain_pressure"),
            ("MAG RISK", "magazine_risk"),
        ]
        for col, (title, key) in enumerate(metrics):
            box = ttk.Frame(top, style="Panel2.TFrame", padding=(10, 8))
            box.grid(row=0, column=col, sticky="nsew", padx=3)
            ttk.Label(box, text=title, background=COLORS["panel2"], foreground=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            lbl = ttk.Label(box, text="--", background=COLORS["panel2"], foreground=COLORS["text"], font=("Segoe UI Semibold", 13))
            lbl.pack(anchor="w", pady=(2, 0))
            self._ship_metric_labels[key] = lbl

        map_panel = self.panel(root, 1, 0, padx=(0, 8), pady=0)
        map_panel.columnconfigure(0, weight=1)
        map_panel.rowconfigure(1, weight=1)
        header = ttk.Frame(map_panel, style="Panel.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="TRAINING SHIP • INTERNAL DAMAGE-CONTROL PLOT", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Click a compartment to inspect and control it.", style="Muted.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Button(header, text="RESET CASUALTY", command=self._ship_reset).grid(row=0, column=1, rowspan=2, padx=(8, 0))
        ttk.Button(header, text="END / EVALUATE", command=self._ship_finish, style="Accent.TButton").grid(row=0, column=2, rowspan=2, padx=(8, 0))

        canvas = tk.Canvas(map_panel, bg="#090d13", highlightthickness=1, highlightbackground=COLORS["line"])
        canvas.grid(row=1, column=0, sticky="nsew")
        canvas.bind("<Button-1>", self._ship_canvas_click)
        self._ship_canvas = canvas

        side = self.panel(root, 1, 1, padx=(8, 0), pady=0)
        side.columnconfigure(0, weight=1)
        side.rowconfigure(8, weight=1)
        self._ship_selected_title = ttk.Label(side, text="", style="Hero.TLabel")
        self._ship_selected_title.grid(row=0, column=0, sticky="w")
        self._ship_selected_stats = ttk.Label(side, text="", style="Muted.TLabel", justify="left")
        self._ship_selected_stats.grid(row=1, column=0, sticky="ew", pady=(3, 10))

        switch = ttk.Frame(side, style="Panel.TFrame")
        switch.grid(row=2, column=0, sticky="ew")
        for i in range(3): switch.columnconfigure(i, weight=1)
        ttk.Button(switch, text="BREAKER", command=self._ship_toggle_breaker).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(switch, text="VENT", command=self._ship_toggle_vent).grid(row=0, column=1, sticky="ew", padx=3)
        ttk.Button(switch, text="FIREMAIN", command=self._ship_toggle_firemain).grid(row=0, column=2, sticky="ew", padx=(3, 0))

        ttk.Separator(side).grid(row=3, column=0, sticky="ew", pady=10)
        ttk.Label(side, text="Adjacent hatches / watertight boundaries", style="Panel.TLabel").grid(row=4, column=0, sticky="w")
        self._ship_hatch_frame = ttk.Frame(side, style="Panel.TFrame")
        self._ship_hatch_frame.grid(row=5, column=0, sticky="ew", pady=(4, 8))
        self._ship_hatch_frame.columnconfigure(0, weight=1)

        crew_box = ttk.LabelFrame(side, text=" Crew Assignment ", padding=8)
        crew_box.grid(row=6, column=0, sticky="ew", pady=4)
        crew_box.columnconfigure(0, weight=1); crew_box.columnconfigure(1, weight=1)
        self._ship_team_var = tk.StringVar(value="REPAIR_1")
        self._ship_task_var = tk.StringVar(value="FIREFIGHT")
        team_combo = ttk.Combobox(crew_box, textvariable=self._ship_team_var, state="readonly", values=list(self.ship_state.teams.keys()))
        team_combo.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        task_combo = ttk.Combobox(crew_box, textvariable=self._ship_task_var, state="readonly", values=["FIREFIGHT", "DEWATER", "REPAIR", "ELECTRICAL", "MEDICAL", "SEAL"])
        task_combo.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(crew_box, text="DISPATCH TO SELECTED COMPARTMENT", command=self._ship_assign_team, style="Accent.TButton").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(7, 0))

        pump_box = ttk.LabelFrame(side, text=" Dewatering ", padding=8)
        pump_box.grid(row=7, column=0, sticky="ew", pady=4)
        pump_box.columnconfigure(0, weight=1)
        self._ship_pump_var = tk.StringVar(value="FIXED_1")
        ttk.Combobox(pump_box, textvariable=self._ship_pump_var, state="readonly", values=list(self.ship_state.pumps.keys())).grid(row=0, column=0, sticky="ew")
        prow = ttk.Frame(pump_box)
        prow.grid(row=1, column=0, sticky="ew", pady=(6, 0)); prow.columnconfigure((0,1), weight=1)
        ttk.Button(prow, text="ROUTE PUMP", command=self._ship_route_pump).grid(row=0, column=0, sticky="ew", padx=(0,3))
        ttk.Button(prow, text="SECURE", command=self._ship_stop_pump).grid(row=0, column=1, sticky="ew", padx=(3,0))

        notebook = ttk.Notebook(side)
        notebook.grid(row=8, column=0, sticky="nsew", pady=(8, 0))
        teams_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        log_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        notebook.add(teams_tab, text="Teams")
        notebook.add(log_tab, text="Damage Log")
        self._ship_team_tree = ttk.Treeview(teams_tab, columns=("team","task","loc","eta","fatigue","health"), show="headings", height=6)
        for col, title, width in [("team","Team",100),("task","Task",78),("loc","Location",90),("eta","ETA",42),("fatigue","Fat",42),("health","HP",42)]:
            self._ship_team_tree.heading(col, text=title); self._ship_team_tree.column(col, width=width, anchor="w")
        self._ship_team_tree.pack(fill="both", expand=True)
        self._ship_log = tk.Text(log_tab, height=9, bg=COLORS["panel2"], fg=COLORS["muted"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 8))
        self._ship_log.pack(fill="both", expand=True)
        self._ship_log.config(state="disabled")

        self._ship_rebuild_hatches()

        def render_loop():
            if self._screen_name != "FULL SHIP SYSTEMS SIMULATOR" or self.ship_state is None:
                return
            self._ship_render()
            self.later(250, render_loop)

        def sim_loop():
            if self._screen_name != "FULL SHIP SYSTEMS SIMULATOR" or self.ship_state is None:
                return
            if not self.ship_state.resolved and not self.ship_state.failed:
                ship_tick(self.ship_state, 1.0)
                self.later(1000, sim_loop)
            else:
                self._ship_render()

        self._ship_render()
        render_loop()
        if not self.ship_state.resolved and not self.ship_state.failed:
            sim_loop()

    def _ship_reset(self):
        self.ship_state = create_training_ship()
        self.ship_selected = "ENGINE_2"
        self.show_ship_systems()

    def _ship_canvas_click(self, event):
        if not self.ship_state or not hasattr(self, "_ship_canvas"):
            return
        w = max(1, self._ship_canvas.winfo_width())
        h = max(1, self._ship_canvas.winfo_height())
        x, y = event.x / w, event.y / h
        for key, c in self.ship_state.compartments.items():
            if c.x <= x <= c.x + c.w and c.y <= y <= c.y + c.h:
                self.ship_selected = key
                self._ship_rebuild_hatches()
                self._ship_render()
                return

    def _ship_hazard_fill(self, c):
        if c.fire >= 55:
            return "#5c2028"
        if c.fire >= 20:
            return "#3a2429"
        if c.flooding >= 55:
            return "#123b56"
        if c.flooding >= 20:
            return "#152c3e"
        if not c.powered:
            return "#16181d"
        return "#171f2c"

    def _ship_render(self):
        st = self.ship_state
        if st is None or not hasattr(self, "_ship_canvas"):
            return
        cv = self._ship_canvas
        cv.delete("all")
        w = max(cv.winfo_width(), 680)
        h = max(cv.winfo_height(), 520)

        # Draw connections first so the compartment boxes sit above them.
        for hatch in st.hatches.values():
            a = st.compartments[hatch.a]; b = st.compartments[hatch.b]
            ax = (a.x + a.w/2) * w; ay = (a.y + a.h/2) * h
            bx = (b.x + b.w/2) * w; by = (b.y + b.h/2) * h
            color = COLORS["good"] if hatch.open else COLORS["danger"]
            cv.create_line(ax, ay, bx, by, fill=color, width=2 if hatch.watertight else 1, dash=() if hatch.open else (4,3))

        for key, c in st.compartments.items():
            x1,y1,x2,y2 = c.x*w,c.y*h,(c.x+c.w)*w,(c.y+c.h)*h
            selected = key == self.ship_selected
            outline = COLORS["accent"] if selected else (COLORS["danger"] if c.fire > 50 else COLORS["line"])
            cv.create_rectangle(x1,y1,x2,y2,fill=self._ship_hazard_fill(c),outline=outline,width=3 if selected else 1)
            cv.create_text((x1+x2)/2,y1+15,text=c.name.upper(),fill=COLORS["text"],font=("Segoe UI Semibold",8),width=max(50,x2-x1-8))
            status = f"F {c.fire:02.0f}  W {c.flooding:02.0f}  S {c.smoke:02.0f}"
            cv.create_text((x1+x2)/2,y2-15,text=status,fill=COLORS["muted"],font=("Consolas",8))
            if not c.powered:
                cv.create_text(x2-9,y1+9,text="⚡",fill=COLORS["warn"],font=("Segoe UI Symbol",9))

        cv.create_text(8,8,anchor="nw",text="GREEN LINE = OPEN ROUTE   RED DASH = SHUT BOUNDARY   F = FIRE   W = WATER   S = SMOKE",fill=COLORS["muted"],font=("Consolas",8))
        if st.resolved:
            cv.create_rectangle(w*.17,h*.42,w*.83,h*.58,fill="#0f2d22",outline=COLORS["good"],width=3)
            cv.create_text(w*.5,h*.5,text="CASUALTY CONTROLLED — END / EVALUATE",fill=COLORS["good"],font=("Segoe UI Semibold",18))
        elif st.failed:
            cv.create_rectangle(w*.17,h*.42,w*.83,h*.58,fill="#3a151c",outline=COLORS["danger"],width=3)
            cv.create_text(w*.5,h*.5,text="SHIP LOST / DRILL FAILED — END / EVALUATE",fill=COLORS["danger"],font=("Segoe UI Semibold",17))

        # Top status metrics.
        vals = {
            "elapsed": f"{st.elapsed:.0f}s",
            "propulsion_port": f"{st.propulsion_port:.0f}%",
            "propulsion_starboard": f"{st.propulsion_starboard:.0f}%",
            "steering": f"{st.steering:.0f}%",
            "communications": f"{st.communications:.0f}%",
            "firemain_pressure": f"{st.firemain_pressure:.0f}%",
            "magazine_risk": f"{st.magazine_risk:.0f}%",
        }
        for key, text in vals.items():
            if key in self._ship_metric_labels:
                self._ship_metric_labels[key].config(text=text)

        c = st.compartments[self.ship_selected]
        self._ship_selected_title.config(text=c.name)
        self._ship_selected_stats.config(text=(
            f"Deck {c.deck} • {c.kind.replace('_',' ').title()}\n"
            f"Integrity {c.integrity:.0f}%   Fire {c.fire:.0f}%   Flooding {c.flooding:.0f}%\n"
            f"Smoke {c.smoke:.0f}%   O₂ {c.oxygen:.1f}%   Temp {c.temperature:.0f}°C\n"
            f"Breach {c.breach:.2f}   Casualties {c.casualties:.1f}%\n"
            f"Bus {c.bus} • {'POWERED' if c.powered else 'NO POWER'} • Breaker {'CLOSED' if c.breaker_closed else 'OPEN'}\n"
            f"Vent {'ON' if c.ventilation else 'SECURED'} • Firemain {'OPEN' if c.firemain_valve else 'ISOLATED'}"
        ))

        # Team table.
        for item in self._ship_team_tree.get_children(): self._ship_team_tree.delete(item)
        for key, team in st.teams.items():
            loc = st.compartments[team.location].name if team.location in st.compartments else team.location
            self._ship_team_tree.insert("", "end", values=(key, team.task, loc, f"{team.eta:.0f}", f"{team.fatigue:.0f}", f"{team.health:.0f}"))

        self._ship_log.config(state="normal")
        self._ship_log.delete("1.0", "end")
        self._ship_log.insert("1.0", "\n".join(st.log[:40]))
        self._ship_log.config(state="disabled")

    def _ship_rebuild_hatches(self):
        if not self.ship_state or not hasattr(self, "_ship_hatch_frame"):
            return
        for w in self._ship_hatch_frame.winfo_children(): w.destroy()
        hatches = adjacent_hatches(self.ship_state, self.ship_selected)
        for row, hatch in enumerate(hatches[:8]):
            other = neighbor_for(hatch, self.ship_selected)
            other_name = self.ship_state.compartments[other].name
            txt = f"{hatch.key} • {other_name} • {'OPEN' if hatch.open else 'SHUT'}"
            ttk.Button(self._ship_hatch_frame, text=txt, command=lambda hk=hatch.key:self._ship_toggle_hatch(hk)).grid(row=row, column=0, sticky="ew", pady=1)
        if not hatches:
            ttk.Label(self._ship_hatch_frame, text="No direct internal route.", style="Muted.TLabel").grid(row=0, column=0, sticky="w")

    def _ship_toggle_hatch(self, hatch_key):
        if self.ship_state:
            toggle_hatch(self.ship_state, hatch_key)
            self._ship_rebuild_hatches(); self._ship_render()

    def _ship_toggle_breaker(self):
        if self.ship_state:
            toggle_breaker(self.ship_state, self.ship_selected); self._ship_render()

    def _ship_toggle_vent(self):
        if self.ship_state:
            toggle_ventilation(self.ship_state, self.ship_selected); self._ship_render()

    def _ship_toggle_firemain(self):
        if self.ship_state:
            toggle_firemain_valve(self.ship_state, self.ship_selected); self._ship_render()

    def _ship_assign_team(self):
        if self.ship_state:
            assign_team(self.ship_state, self._ship_team_var.get(), self._ship_task_var.get(), self.ship_selected)
            self._ship_render()

    def _ship_route_pump(self):
        if self.ship_state:
            route_pump(self.ship_state, self._ship_pump_var.get(), self.ship_selected); self._ship_render()

    def _ship_stop_pump(self):
        if self.ship_state:
            stop_pump(self.ship_state, self._ship_pump_var.get()); self._ship_render()

    def _ship_finish(self):
        if not self.ship_state:
            return
        score = evaluate_ship_scenario(self.ship_state)
        summary = ship_summary(self.ship_state)
        apply_ship_systems_result(self.profile, score, summary)
        self.save_now(silent=True)
        status = "PASS" if score >= 70 else "NOT YET PASSED"
        messagebox.showinfo(
            "Ship Systems Evaluation",
            f"Evaluation: {score:.0f}% — {status}\n\n"
            f"Time: {summary['elapsed']:.0f}s\n"
            f"Worst fire: {summary['max_fire']:.0f}% ({summary['max_fire_location']})\n"
            f"Worst flooding: {summary['max_flooding']:.0f}% ({summary['max_flood_location']})\n"
            f"Crew casualties: {summary['casualties']:.1f}%\n"
            f"Steering: {summary['steering']:.0f}%\n"
            f"Communications: {summary['communications']:.0f}%\n"
            f"Magazine risk: {summary['magazine_risk']:.0f}%"
        )
        self.ship_state = None
        self.show_dashboard()


    def show_enterprise_duty(self):
        self._clear_body("USS ENTERPRISE (CV-6) — MIDWAY STATION DUTY")
        if self.enterprise_state is None or self.enterprise_state.evaluated:
            self.enterprise_state = create_enterprise_duty_state()
        st = self.enterprise_state
        if self.enterprise_station not in STATION_DEFS:
            self.enterprise_station = "CIC"
        st.selected_station = self.enterprise_station

        root = ttk.Frame(self.body)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=2)
        root.columnconfigure(1, weight=5)
        root.columnconfigure(2, weight=4)
        root.rowconfigure(2, weight=1)

        banner = self.panel(root, 0, 0, colspan=3, padx=0, pady=(0, 7))
        banner.columnconfigure(0, weight=1)
        ttk.Label(banner, text="USS ENTERPRISE (CV-6) • 4 JUNE 1942 • TASK FORCE 16", style="Hero.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            banner,
            text=("FULL SHIP DUTY MODE — station actions are tied to the v0.3 Midway historical clock. "
                  "Canonical battle events stay locked; your performance changes readiness, task completion, and career evaluation rather than rewriting the sourced history."),
            background=COLORS["panel"], foreground=COLORS["warn"], font=("Segoe UI Semibold", 9),
            wraplength=1050, justify="left"
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(banner, text="RESET WATCH", command=self._enterprise_reset).grid(row=0, column=1, rowspan=2, padx=(12, 0))
        ttk.Button(banner, text="END / EVALUATE", command=self._enterprise_finish, style="Accent.TButton").grid(row=0, column=2, rowspan=2, padx=(7, 0))

        metrics = self.panel(root, 1, 0, colspan=3, padx=0, pady=7)
        metrics.columnconfigure(tuple(range(8)), weight=1)
        self._ent_metric_labels = {}
        for col, (label, key) in enumerate([
            ("SIM TIME", "clock"), ("TASK SCORE", "score"), ("OPEN", "open"),
            ("SHIP READY", "ready"), ("PLANT", "plant"), ("DECK SAFE", "deck"),
            ("AA / RADAR", "aa"), ("FUEL", "fuel"),
        ]):
            box = ttk.Frame(metrics, style="Panel2.TFrame", padding=(10, 8))
            box.grid(row=0, column=col, sticky="nsew", padx=3)
            ttk.Label(box, text=label, background=COLORS["panel2"], foreground=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            value = ttk.Label(box, text="--", background=COLORS["panel2"], foreground=COLORS["text"], font=("Segoe UI Semibold", 12))
            value.pack(anchor="w", pady=(2, 0))
            self._ent_metric_labels[key] = value

        # Left column: ship schematic and station selector.
        left = self.panel(root, 2, 0, padx=(0, 7), pady=0)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        ttk.Label(left, text="SHIP STATIONS", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self._ent_ship_canvas = tk.Canvas(left, bg="#080d13", highlightthickness=1, highlightbackground=COLORS["line"], height=220)
        self._ent_ship_canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 10))
        self._ent_station_buttons = {}
        station_frame = ttk.Frame(left, style="Panel.TFrame")
        station_frame.grid(row=2, column=0, sticky="ew")
        station_frame.columnconfigure(0, weight=1)
        for i, key in enumerate(STATION_DEFS):
            btn = ttk.Button(station_frame, text=STATION_DEFS[key]["name"], command=lambda k=key: self._enterprise_select_station(k), style="Nav.TButton")
            btn.grid(row=i, column=0, sticky="ew", pady=2)
            self._ent_station_buttons[key] = btn

        controls = ttk.Frame(left, style="Panel.TFrame")
        controls.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        self._ent_run_btn = ttk.Button(controls, text="RUN", command=self._enterprise_toggle_run, style="Accent.TButton")
        self._ent_run_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(controls, text="ADVANCE 5 MIN", command=lambda: self._enterprise_advance(5)).grid(row=0, column=1, sticky="ew", padx=(3, 0))
        ttk.Button(controls, text="NEXT EVENT / DEADLINE", command=self._enterprise_next).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(controls, text="Simulation speed", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._ent_speed_var = tk.StringVar(value=f"{st.speed}x")
        speed = ttk.Combobox(controls, textvariable=self._ent_speed_var, state="readonly", values=["1x", "4x", "12x", "30x"], width=7)
        speed.grid(row=2, column=1, sticky="e", pady=(8, 0))
        speed.bind("<<ComboboxSelected>>", self._enterprise_speed_changed)

        # Center column: selected station detail and actions.
        center = self.panel(root, 2, 1, padx=7, pady=0)
        center.columnconfigure(0, weight=1)
        center.rowconfigure(5, weight=1)
        self._ent_station_title = ttk.Label(center, text="", style="Hero.TLabel")
        self._ent_station_title.grid(row=0, column=0, sticky="w")
        self._ent_station_mission = ttk.Label(center, text="", style="Muted.TLabel", wraplength=610, justify="left")
        self._ent_station_mission.grid(row=1, column=0, sticky="ew", pady=(4, 9))

        sm = ttk.Frame(center, style="Panel.TFrame")
        sm.grid(row=2, column=0, sticky="ew")
        sm.columnconfigure((0, 1, 2, 3), weight=1)
        self._ent_station_metrics = {}
        for c, key in enumerate(("readiness", "efficiency", "alert", "crew")):
            box = ttk.Frame(sm, style="Panel2.TFrame", padding=(10, 8))
            box.grid(row=0, column=c, sticky="nsew", padx=3)
            ttk.Label(box, text=key.upper(), background=COLORS["panel2"], foreground=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            lbl = ttk.Label(box, text="--", background=COLORS["panel2"], foreground=COLORS["text"], font=("Segoe UI Semibold", 11))
            lbl.pack(anchor="w", pady=(2, 0))
            self._ent_station_metrics[key] = lbl

        self._ent_system_text = ttk.Label(center, text="", background=COLORS["panel"], foreground=COLORS["muted"], wraplength=610, justify="left", font=("Consolas", 9))
        self._ent_system_text.grid(row=3, column=0, sticky="ew", pady=(10, 7))

        ttk.Label(center, text="STATION ACTIONS", style="Section.TLabel").grid(row=4, column=0, sticky="w", pady=(2, 4))
        self._ent_action_frame = ttk.Frame(center, style="Panel.TFrame")
        self._ent_action_frame.grid(row=5, column=0, sticky="nsew")
        self._ent_action_frame.columnconfigure((0, 1), weight=1)
        self._ent_action_result = ttk.Label(center, text="Select a station action. Scored tasks display in the duty queue.", style="Muted.TLabel", wraplength=610, justify="left")
        self._ent_action_result.grid(row=6, column=0, sticky="ew", pady=(8, 0))

        # Right column: task queue, crew assignment, logs and sources.
        right = self.panel(root, 2, 2, padx=(7, 0), pady=0)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        ttk.Label(right, text="DUTY QUEUE / WATCH TEAM", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        notebook = ttk.Notebook(right)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        task_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        crew_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=8)
        log_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        source_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        notebook.add(task_tab, text="Duty Queue")
        notebook.add(crew_tab, text="Crew")
        notebook.add(log_tab, text="Watch Log")
        notebook.add(source_tab, text="Sources")

        task_tab.rowconfigure(0, weight=1); task_tab.columnconfigure(0, weight=1)
        self._ent_task_tree = ttk.Treeview(task_tab, columns=("station", "due", "status", "task"), show="headings", height=16)
        for col, title, width in [("station", "Sta", 54), ("due", "Due", 48), ("status", "Status", 68), ("task", "Task", 245)]:
            self._ent_task_tree.heading(col, text=title); self._ent_task_tree.column(col, width=width, anchor="w")
        self._ent_task_tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(task_tab, orient="vertical", command=self._ent_task_tree.yview)
        sb.grid(row=0, column=1, sticky="ns"); self._ent_task_tree.configure(yscrollcommand=sb.set)

        ttk.Label(crew_tab, text="SIMULATION WATCH ROSTER — names are training placeholders, not a claim about Enterprise's actual 4 June watchbill.", background=COLORS["panel"], foreground=COLORS["warn"], wraplength=430, justify="left").grid(row=0, column=0, sticky="ew", pady=(0,6))
        ttk.Label(crew_tab, text="Crew member", background=COLORS["panel"], foreground=COLORS["muted"]).grid(row=1, column=0, sticky="w")
        crew_values = [f"{k} — {v.name}" for k, v in st.crew.items()]
        self._ent_crew_var = tk.StringVar(value=crew_values[0])
        crew_combo = ttk.Combobox(crew_tab, textvariable=self._ent_crew_var, values=crew_values, state="readonly", width=34)
        crew_combo.grid(row=2, column=0, sticky="ew", pady=(2, 8))
        ttk.Label(crew_tab, text="Assign to", background=COLORS["panel"], foreground=COLORS["muted"]).grid(row=3, column=0, sticky="w")
        station_values = [f"{k} — {v['name']}" for k, v in STATION_DEFS.items()]
        self._ent_assign_station_var = tk.StringVar(value=station_values[0])
        station_combo = ttk.Combobox(crew_tab, textvariable=self._ent_assign_station_var, values=station_values, state="readonly", width=34)
        station_combo.grid(row=4, column=0, sticky="ew", pady=(2, 8))
        ttk.Button(crew_tab, text="REASSIGN CREW", command=self._enterprise_reassign_crew, style="Accent.TButton").grid(row=5, column=0, sticky="ew")
        self._ent_crew_text = tk.Text(crew_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Consolas", 8), height=16)
        self._ent_crew_text.grid(row=6, column=0, sticky="nsew", pady=(10, 0))
        crew_tab.rowconfigure(6, weight=1); crew_tab.columnconfigure(0, weight=1)

        self._ent_log_text = tk.Text(log_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Consolas", 8))
        self._ent_log_text.pack(fill="both", expand=True)

        source_text = tk.Text(source_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Segoe UI", 8))
        source_text.pack(fill="both", expand=True)
        source_text.insert("end", "SOURCE POLICY\n", ("heading",))
        source_text.insert("end", "Historical event timing continues to come from the v0.3 Midway package. Enterprise-specific station details below are source-backed where cited; gameplay abstractions are labeled as simulation behavior.\n\n")
        for src in ENTERPRISE_SOURCES.values():
            source_text.insert("end", f"{src['organization']}\n{src['title']}\n{src['notes']}\n{src['url']}\n\n")
        source_text.tag_configure("heading", foreground=COLORS["text"], font=("Segoe UI Semibold", 10))
        source_text.config(state="disabled")

        self._enterprise_build_action_buttons()
        self._enterprise_render()

        def sim_loop():
            if self._screen_name != "USS ENTERPRISE (CV-6) — MIDWAY STATION DUTY" or self.enterprise_state is None:
                return
            if self.enterprise_state.running and not self.enterprise_state.completed:
                before = len(open_tasks(self.enterprise_state))
                advance_enterprise(self.enterprise_state, self.enterprise_state.speed)
                after = len(open_tasks(self.enterprise_state))
                # New shipboard obligations pause the accelerated clock so the player can act.
                if after > before:
                    self.enterprise_state.running = False
            self._enterprise_render()
            self.later(750, sim_loop)
        sim_loop()

    def _enterprise_select_station(self, station):
        self.enterprise_station = station
        if self.enterprise_state:
            self.enterprise_state.selected_station = station
        self._enterprise_build_action_buttons()
        self._enterprise_render()

    def _enterprise_build_action_buttons(self):
        if not hasattr(self, "_ent_action_frame"):
            return
        for child in self._ent_action_frame.winfo_children():
            child.destroy()
        station = self.enterprise_station
        for i, (action, label) in enumerate(action_catalog(station)):
            ttk.Button(
                self._ent_action_frame, text=label,
                command=lambda a=action, s=station: self._enterprise_action(s, a),
                style="Accent.TButton" if i == 0 else "TButton",
            ).grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)

    def _enterprise_action(self, station, action):
        if not self.enterprise_state:
            return
        ok, msg = perform_station_action(self.enterprise_state, station, action)
        self._ent_action_result.config(text=msg, foreground=COLORS["good"] if ok else COLORS["danger"])
        self._enterprise_render()

    def _enterprise_reassign_crew(self):
        if not self.enterprise_state:
            return
        try:
            crew_key = self._ent_crew_var.get().split(" — ", 1)[0]
            station_key = self._ent_assign_station_var.get().split(" — ", 1)[0]
        except Exception:
            return
        ok, msg = assign_crew(self.enterprise_state, crew_key, station_key)
        self._ent_action_result.config(text=msg, foreground=COLORS["good"] if ok else COLORS["danger"])
        self._enterprise_render()

    def _enterprise_toggle_run(self):
        if not self.enterprise_state or self.enterprise_state.completed:
            return
        self.enterprise_state.running = not self.enterprise_state.running
        self._enterprise_render()

    def _enterprise_advance(self, minutes):
        if not self.enterprise_state or self.enterprise_state.completed:
            return
        advance_enterprise(self.enterprise_state, minutes)
        self._enterprise_render()

    def _enterprise_next(self):
        if not self.enterprise_state or self.enterprise_state.completed:
            return
        jump_to_next_enterprise_task(self.enterprise_state)
        self._enterprise_render()

    def _enterprise_speed_changed(self, _event=None):
        if self.enterprise_state:
            try:
                self.enterprise_state.speed = int(self._ent_speed_var.get().replace("x", ""))
            except ValueError:
                self.enterprise_state.speed = 1

    def _enterprise_reset(self):
        self.enterprise_state = create_enterprise_duty_state()
        self.enterprise_station = "CIC"
        self.show_enterprise_duty()

    def _enterprise_finish(self):
        if not self.enterprise_state:
            return
        score = evaluate_enterprise(self.enterprise_state)
        summary = enterprise_summary(self.enterprise_state)
        apply_enterprise_duty_result(self.profile, score, summary)
        self.save_now(silent=True)
        status = "PASS" if score >= 70 else "NOT YET PASSED"
        messagebox.showinfo(
            "USS Enterprise Duty Evaluation",
            f"Evaluation: {score:.0f}% — {status}\n\n"
            f"Tasks complete: {summary['tasks_complete']}\n"
            f"Tasks missed: {summary['tasks_missed']}\n"
            f"Station readiness: {summary['station_readiness']:.0f}%\n"
            f"Crew efficiency: {summary['crew_efficiency']:.0f}%\n"
            f"Plant readiness: {summary['plant_readiness']:.0f}%\n"
            f"Flight-deck safety: {summary['deck_safety']:.0f}%\n"
            f"Strike launched: {'YES' if summary['strike_launched'] else 'NO'}\n"
            f"Recovery configuration: {'READY' if summary['recovery_ready'] else 'NOT SET'}\n\n"
            "Historical lock remained active: the sourced Midway event sequence was not rewritten by station score."
        )
        self.enterprise_state = None
        self.show_dashboard()

    def _enterprise_system_lines(self, st, station):
        if station == "BRIDGE":
            return (
                f"Heading       {st.bridge_heading:6.1f}°T     Ordered {st.ordered_heading:6.1f}°T\n"
                f"Speed         {st.speed_knots:6.1f} kt     Ordered {st.ordered_speed:6.1f} kt\n"
                f"Engine order  {st.engine_order}\n"
                f"Wind over deck {st.wind_over_deck:5.1f} kt  • gameplay approximation"
            )
        if station == "CIC":
            c = st.historical.contacts.get("JP_CARRIERS")
            contact = "NO VERIFIED CARRIER CONTACT" if not c else f"{c.classification} • {c.confidence:.0f}% confidence • ±{c.uncertainty_nm:.0f} NM"
            return f"Carrier plot   {contact}\nRadar readiness {st.radar_air_readiness:.0f}%\nReports received {len(st.historical.delivered_events)}\nIntel discipline {st.historical.intel_discipline:.0f}%"
        if station == "RADIO":
            return f"Priority routes {len(st.messages_routed)}\nHistorical reports received {len(st.historical.messages)}\nLatest report {st.historical.messages[0]['headline'] if st.historical.messages else 'None yet'}\nMessage timestamps preserve occurrence/report delay."
        if station == "ENGINEERING":
            return f"Plant readiness {st.plant_readiness:.0f}%\nElectrical load {st.electrical_load:.0f}%\nFuel state {st.fuel_state:.1f}%\nPropulsion demand {st.ordered_speed:.1f} kt"
        if station == "DAMAGE_CONTROL":
            return f"Repair parties {st.repair_party_readiness:.0f}%\nWatertight integrity {st.watertight_integrity:.0f}%\nEnterprise receives no invented Midway battle hit in historical-lock mode.\nThis station manages readiness around the sourced battle sequence."
        if station == "FIRE_CONTROL":
            return f"AA readiness {st.aa_readiness:.0f}%\nRadar/air track readiness {st.radar_air_readiness:.0f}%\nTrack doctrine POSITIVE CLASSIFICATION REQUIRED\nNo fictional Enterprise engagement is inserted into the canonical Midway sequence."
        return f"Deck spot {st.deck_spot:.0f}%\nFueled {st.aircraft_fueled:.0f}% • Armed {st.aircraft_armed:.0f}%\nCAP reserve {st.cap_reserve:.0f}% • Deck safety {st.deck_safety:.0f}%\nStrike launched {'YES' if st.strike_launched else 'NO'} • Recovery {'READY' if st.recovery_ready else 'NOT SET'}"

    def _enterprise_draw_ship(self):
        if not hasattr(self, "_ent_ship_canvas") or not self.enterprise_state:
            return
        cv = self._ent_ship_canvas
        cv.delete("all")
        w = max(250, cv.winfo_width()); h = max(190, cv.winfo_height())
        # Stylized top-down carrier diagram; intentionally schematic, not a claim of exact compartment geometry.
        x0, x1 = 22, w - 22
        y0, y1 = 58, h - 42
        cv.create_polygon(x0+12, y0, x1-12, y0, x1, (y0+y1)/2, x1-12, y1, x0+12, y1, x0, (y0+y1)/2,
                          fill="#141d28", outline=COLORS["accent"], width=2)
        cv.create_line(x0+28, (y0+y1)/2, x1-28, (y0+y1)/2, fill="#3b4655", dash=(8, 5))
        island_x = x0 + (x1-x0)*0.63
        cv.create_rectangle(island_x, y0+12, island_x+34, y0+48, fill="#202b38", outline=COLORS["text"])
        cv.create_text((x0+x1)/2, y0-24, text="USS ENTERPRISE (CV-6) • SCHEMATIC STATION MAP", fill=COLORS["muted"], font=("Consolas", 8))
        positions = {
            "BRIDGE": (island_x+17, y0+25), "CIC": (island_x+17, y0+44), "RADIO": (island_x-20, y0+45),
            "ENGINEERING": ((x0+x1)*0.48, y1-22), "DAMAGE_CONTROL": ((x0+x1)*0.56, y1-22),
            "FIRE_CONTROL": (island_x+48, y0+28), "AIR_OPS": ((x0+x1)*0.40, (y0+y1)/2),
        }
        for key, (x, y) in positions.items():
            selected = key == self.enterprise_station
            alert = self.enterprise_state.stations[key].alert
            outline = COLORS["danger"] if alert == "URGENT" else (COLORS["warn"] if alert == "ACTION" else COLORS["good"])
            r = 10 if selected else 7
            cv.create_oval(x-r, y-r, x+r, y+r, fill=COLORS["accent2"] if selected else "#182432", outline=outline, width=2)
            cv.create_text(x, y+17, text=STATION_DEFS[key]["short"], fill=COLORS["text"] if selected else COLORS["muted"], font=("Segoe UI Semibold", 7))

    def _enterprise_render(self):
        st = self.enterprise_state
        if st is None or not hasattr(self, "_ent_metric_labels"):
            return
        summary = enterprise_summary(st)
        score_pct = 100.0 * st.score_points / max(1, st.score_possible)
        values = {
            "clock": st.clock,
            "score": f"{score_pct:.0f}%",
            "open": str(summary["tasks_open"]),
            "ready": f"{summary['station_readiness']:.0f}%",
            "plant": f"{st.plant_readiness:.0f}%",
            "deck": f"{st.deck_safety:.0f}%",
            "aa": f"{(st.aa_readiness + st.radar_air_readiness)/2:.0f}%",
            "fuel": f"{st.fuel_state:.0f}%",
        }
        for k, v in values.items():
            self._ent_metric_labels[k].config(text=v)
        self._ent_run_btn.config(text="PAUSE" if st.running else "RUN")

        station = self.enterprise_station
        snap = station_snapshot(st, station)
        self._ent_station_title.config(text=snap["station"])
        self._ent_station_mission.config(text=STATION_DEFS[station]["mission"])
        self._ent_station_metrics["readiness"].config(text=f"{snap['readiness']:.0f}%")
        self._ent_station_metrics["efficiency"].config(text=f"{snap['efficiency']:.0f}%")
        self._ent_station_metrics["alert"].config(text=snap["alert"])
        self._ent_station_metrics["crew"].config(text=str(len(snap["crew"])))
        self._ent_system_text.config(text=self._enterprise_system_lines(st, station))

        for key, btn in self._ent_station_buttons.items():
            sta = st.stations[key]
            task_count = len(open_tasks(st, key))
            marker = "!" if sta.alert == "URGENT" else ("•" if task_count else "✓")
            btn.config(text=f"{marker}  {STATION_DEFS[key]['name']}   [{sta.readiness:.0f}%]" + (f"  ({task_count})" if task_count else ""))

        for item in self._ent_task_tree.get_children():
            self._ent_task_tree.delete(item)
        for key in st.task_order:
            task = st.tasks[key]
            sta = STATION_DEFS[task.station]["short"]
            self._ent_task_tree.insert("", "end", values=(sta, min_to_hhmm(task.deadline_minute), task.status, task.title))

        self._ent_crew_text.config(state="normal")
        self._ent_crew_text.delete("1.0", "end")
        for key, crew in st.crew.items():
            assigned = next((STATION_DEFS[k]["short"] for k, sta in st.stations.items() if key in sta.crew_keys), "UNASSIGNED")
            prof = crew.proficiency.get(station, 0.0)
            self._ent_crew_text.insert("end", f"{crew.name}\n  {crew.rating}\n  Assigned {assigned} • {station} proficiency {prof:.0f}% • Fatigue {crew.fatigue:.0f}% • Stress {crew.stress:.0f}%\n\n")
        self._ent_crew_text.config(state="disabled")

        self._ent_log_text.config(state="normal")
        self._ent_log_text.delete("1.0", "end")
        for line in st.action_log[:80]:
            self._ent_log_text.insert("end", line + "\n")
        self._ent_log_text.config(state="disabled")
        self._enterprise_draw_ship()


    def show_historical_ops(self):
        self._clear_body("HISTORICAL OPERATIONS — BATTLE OF MIDWAY")
        if self.historical_state is None or self.historical_state.evaluated:
            self.historical_state = create_midway_state()
        st = self.historical_state

        root = ttk.Frame(self.body)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=7)
        root.columnconfigure(1, weight=4)
        root.rowconfigure(2, weight=1)

        banner = self.panel(root, 0, 0, colspan=2, padx=0, pady=(0, 7))
        banner.columnconfigure(0, weight=1)
        ttk.Label(banner, text="4 JUNE 1942 • U.S. CARRIER TASK FORCE OPERATIONS WATCH", style="Hero.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            banner,
            text="HISTORICAL LOCK — canonical events remain fixed. You are evaluated on role-limited intelligence, communications discipline, readiness, and professional decisions.",
            background=COLORS["panel"], foreground=COLORS["warn"], font=("Segoe UI Semibold", 9), wraplength=1050, justify="left"
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(banner, text="RESET SCENARIO", command=self._hist_reset).grid(row=0, column=1, rowspan=2, padx=(12, 0))
        ttk.Button(banner, text="END / EVALUATE", command=self._hist_finish, style="Accent.TButton").grid(row=0, column=2, rowspan=2, padx=(7, 0))

        metrics = self.panel(root, 1, 0, colspan=2, padx=0, pady=7)
        metrics.columnconfigure(tuple(range(8)), weight=1)
        self._hist_metric_labels = {}
        for col, (label, key) in enumerate([
            ("SIM TIME", "clock"), ("COMMAND", "command"), ("INTEL DISC", "intel"),
            ("AVIATION", "aviation"), ("CONTACT", "contact"), ("DECISIONS", "decisions"), ("WEATHER", "weather"),
        ]):
            box = ttk.Frame(metrics, style="Panel2.TFrame", padding=(10, 8))
            box.grid(row=0, column=col, sticky="nsew", padx=3)
            ttk.Label(box, text=label, background=COLORS["panel2"], foreground=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            value = ttk.Label(box, text="--", background=COLORS["panel2"], foreground=COLORS["text"], font=("Segoe UI Semibold", 12))
            value.pack(anchor="w", pady=(2, 0))
            self._hist_metric_labels[key] = value

        map_panel = self.panel(root, 2, 0, padx=(0, 7), pady=0)
        map_panel.columnconfigure(0, weight=1)
        map_panel.rowconfigure(2, weight=1)
        ttk.Label(map_panel, text="TACTICAL INFORMATION PLOT", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(map_panel, text="Enemy symbols appear only after a report reaches your watch. Contact circles show uncertainty; the plot is schematic rather than exact geodesy.", style="Muted.TLabel", wraplength=760).grid(row=1, column=0, sticky="w", pady=(2, 8))
        self._hist_canvas = tk.Canvas(map_panel, bg="#080d13", highlightthickness=1, highlightbackground=COLORS["line"], height=430)
        self._hist_canvas.grid(row=2, column=0, sticky="nsew")

        controls = ttk.Frame(map_panel, style="Panel.TFrame")
        controls.grid(row=3, column=0, sticky="ew", pady=(9, 0))
        controls.columnconfigure(5, weight=1)
        self._hist_run_btn = ttk.Button(controls, text="RUN", command=self._hist_toggle_run, style="Accent.TButton")
        self._hist_run_btn.grid(row=0, column=0, padx=(0, 5))
        ttk.Button(controls, text="ADVANCE 5 MIN", command=lambda: self._hist_advance(5)).grid(row=0, column=1, padx=5)
        ttk.Button(controls, text="NEXT REPORT / DECISION", command=self._hist_next).grid(row=0, column=2, padx=5)
        ttk.Label(controls, text="Speed", style="Panel.TLabel").grid(row=0, column=3, padx=(14, 4))
        self._hist_speed_var = tk.StringVar(value=f"{st.speed}x")
        speed = ttk.Combobox(controls, textvariable=self._hist_speed_var, state="readonly", values=["1x", "4x", "12x", "30x"], width=6)
        speed.grid(row=0, column=4)
        speed.bind("<<ComboboxSelected>>", self._hist_speed_changed)
        self._hist_status = ttk.Label(controls, text="PAUSED", background=COLORS["panel"], foreground=COLORS["warn"], font=("Segoe UI Semibold", 9))
        self._hist_status.grid(row=0, column=6, sticky="e")

        side = self.panel(root, 2, 1, padx=(7, 0), pady=0)
        side.columnconfigure(0, weight=1)
        side.rowconfigure(5, weight=1)
        ttk.Label(side, text="WATCH DECISION", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self._hist_decision_title = ttk.Label(side, text="", background=COLORS["panel"], foreground=COLORS["accent"], font=("Segoe UI Semibold", 13), wraplength=420, justify="left")
        self._hist_decision_title.grid(row=1, column=0, sticky="ew", pady=(5, 2))
        self._hist_decision_text = ttk.Label(side, text="", style="Muted.TLabel", wraplength=420, justify="left")
        self._hist_decision_text.grid(row=2, column=0, sticky="ew")
        self._hist_decision_frame = ttk.Frame(side, style="Panel.TFrame")
        self._hist_decision_frame.grid(row=3, column=0, sticky="ew", pady=(8, 6))
        self._hist_decision_frame.columnconfigure(0, weight=1)
        self._hist_decision_result = ttk.Label(side, text="", style="Muted.TLabel", wraplength=420, justify="left")
        self._hist_decision_result.grid(row=4, column=0, sticky="ew", pady=(0, 7))

        notebook = ttk.Notebook(side)
        notebook.grid(row=5, column=0, sticky="nsew")
        intel_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        doctrine_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        oob_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        source_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        notebook.add(intel_tab, text="Intel Log")
        notebook.add(doctrine_tab, text="Doctrine AI")
        notebook.add(oob_tab, text="Order of Battle")
        notebook.add(source_tab, text="Sources")

        intel_tab.rowconfigure(0, weight=1); intel_tab.columnconfigure(0, weight=1)
        self._hist_intel_tree = ttk.Treeview(intel_tab, columns=("time", "lag", "cat", "report"), show="headings", height=11)
        for col, title, width in [("time", "Time", 48), ("lag", "Lag", 38), ("cat", "Type", 86), ("report", "Report", 230)]:
            self._hist_intel_tree.heading(col, text=title); self._hist_intel_tree.column(col, width=width, anchor="w")
        self._hist_intel_tree.grid(row=0, column=0, sticky="nsew")
        isb = ttk.Scrollbar(intel_tab, orient="vertical", command=self._hist_intel_tree.yview)
        isb.grid(row=0, column=1, sticky="ns"); self._hist_intel_tree.configure(yscrollcommand=isb.set)

        self._hist_doctrine_text = tk.Text(doctrine_tab, bg=COLORS["panel2"], fg=COLORS["muted"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Consolas", 8))
        self._hist_doctrine_text.pack(fill="both", expand=True)
        self._hist_doctrine_text.config(state="disabled")

        oob_text = tk.Text(oob_tab, bg=COLORS["panel2"], fg=COLORS["muted"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Segoe UI", 8))
        oob_text.pack(fill="both", expand=True)
        for formation, info in ORDER_OF_BATTLE.items():
            oob_text.insert("end", f"{formation}\n", ("heading",))
            for unit in info["units"]:
                oob_text.insert("end", f"  • {unit}\n")
            src = SOURCES[info["source"]]
            oob_text.insert("end", f"  Source: {src.title}\n\n")
        oob_text.tag_configure("heading", foreground=COLORS["text"], font=("Segoe UI Semibold", 9))
        oob_text.config(state="disabled")

        source_text = tk.Text(source_tab, bg=COLORS["panel2"], fg=COLORS["muted"], insertbackground=COLORS["text"], relief="flat", wrap="word", font=("Segoe UI", 8))
        source_text.pack(fill="both", expand=True)
        for src in SOURCES.values():
            source_text.insert("end", f"{src.organization}\n{src.title}\n{src.notes}\n{src.url}\n\n")
        source_text.config(state="disabled")

        self._hist_render()

        def sim_loop():
            if self._screen_name != "HISTORICAL OPERATIONS — BATTLE OF MIDWAY" or self.historical_state is None:
                return
            if self.historical_state.running and not self.historical_state.completed:
                advance_historical(self.historical_state, self.historical_state.speed)
                if active_prompt(self.historical_state):
                    self.historical_state.running = False
            self._hist_render()
            self.later(750, sim_loop)
        sim_loop()

    def _hist_toggle_run(self):
        if not self.historical_state or self.historical_state.completed:
            return
        self.historical_state.running = not self.historical_state.running
        self._hist_render()

    def _hist_advance(self, minutes):
        if not self.historical_state or self.historical_state.completed:
            return
        advance_historical(self.historical_state, minutes)
        self.historical_state.running = False
        self._hist_render()

    def _hist_next(self):
        if not self.historical_state or self.historical_state.completed:
            return
        jump_to_next_event(self.historical_state)
        self.historical_state.running = False
        self._hist_render()

    def _hist_speed_changed(self, _event=None):
        if self.historical_state:
            try:
                self.historical_state.speed = int(self._hist_speed_var.get().replace("x", ""))
            except ValueError:
                self.historical_state.speed = 1

    def _hist_reset(self):
        self.historical_state = create_midway_state()
        self.show_historical_ops()

    def _hist_answer(self, prompt_key, option_index):
        if not self.historical_state:
            return
        ok, rationale = answer_decision(self.historical_state, prompt_key, option_index)
        self._hist_decision_result.config(text=rationale, foreground=COLORS["good"] if ok else COLORS["danger"])
        self._hist_prompt_key = None
        self._hist_render()

    def _hist_finish(self):
        if not self.historical_state:
            return
        score = evaluate_historical(self.historical_state)
        summary = historical_summary(self.historical_state)
        apply_historical_result(
            self.profile,
            self.historical_state.scenario_id,
            "Battle of Midway — Historical Operations Watch",
            score,
            summary,
        )
        self.save_now(silent=True)
        status = "PASS" if score >= 70 else "NOT YET PASSED"
        messagebox.showinfo(
            "Historical Operations Evaluation",
            f"Evaluation: {score:.0f}% — {status}\n\n"
            f"Decisions answered: {summary['decisions_answered']}/{len(DECISIONS)}\n"
            f"Optimal decisions: {summary['optimal_decisions']}/{len(DECISIONS)}\n"
            f"Intel discipline: {summary['intel_discipline']:.0f}%\n"
            f"Command readiness: {summary['command_readiness']:.0f}%\n"
            f"Reports received: {summary['events_received']}\n\n"
            "Historical lock preserved: your decisions were evaluated without rewriting the canonical battle outcome."
        )
        self.historical_state = None
        self.show_dashboard()

    def _hist_render(self):
        st = self.historical_state
        if st is None or not hasattr(self, "_hist_canvas"):
            return
        weather = current_weather(st)
        contact = st.contacts.get("JP_CARRIERS")
        answered = len([d for d in st.decisions.values() if d.get("option") != "NO RESPONSE LOGGED"])
        values = {
            "clock": st.clock,
            "command": f"{st.command_readiness:.0f}%",
            "intel": f"{st.intel_discipline:.0f}%",
            "aviation": f"{st.aviation_readiness:.0f}%",
            "contact": f"{contact.confidence:.0f}%" if contact else "NONE",
            "decisions": f"{answered}/{len(DECISIONS)}",
            "weather": "SHOWERS" if "showers" in weather.conditions.lower() else "CLOUDY",
        }
        for key, value in values.items():
            if key in self._hist_metric_labels:
                self._hist_metric_labels[key].config(text=value)
        self._hist_run_btn.config(text="PAUSE" if st.running else "RUN")
        self._hist_status.config(
            text="COMPLETE" if st.completed else ("RUNNING" if st.running else "PAUSED"),
            foreground=COLORS["good"] if st.completed else (COLORS["accent"] if st.running else COLORS["warn"]),
        )

        cv = self._hist_canvas
        cv.delete("all")
        w = max(640, cv.winfo_width()); h = max(390, cv.winfo_height())
        cx, cy = w * FORCE_PLOT["MIDWAY"][0], h * FORCE_PLOT["MIDWAY"][1]
        # Plot grid and range rings.
        for frac in (0.18, 0.34, 0.50):
            r = min(w, h) * frac
            cv.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#1c2a39", dash=(3, 5))
        for x in range(0, int(w), 80): cv.create_line(x, 0, x, h, fill="#111b27")
        for y in range(0, int(h), 70): cv.create_line(0, y, w, y, fill="#111b27")
        cv.create_text(12, 12, anchor="nw", text=f"04 JUN 1942  {st.clock}  •  WEATHER: {weather.conditions}", fill=COLORS["muted"], font=("Consolas", 8))
        cv.create_oval(cx-7, cy-7, cx+7, cy+7, fill=COLORS["text"], outline=COLORS["accent"])
        cv.create_text(cx+12, cy-14, anchor="w", text="MIDWAY", fill=COLORS["text"], font=("Segoe UI Semibold", 9))

        for key, label in (("TF16", "TF 16 • ENTERPRISE / HORNET"), ("TF17", "TF 17 • YORKTOWN")):
            px, py = w * FORCE_PLOT[key][0], h * FORCE_PLOT[key][1]
            cv.create_polygon(px, py-8, px+8, py, px, py+8, px-8, py, fill="#20384d", outline=COLORS["good"])
            cv.create_text(px+12, py, anchor="w", text=label, fill=COLORS["good"], font=("Segoe UI", 8))

        # Weather cell in the enemy-force area; this exists even when the force itself is not plotted.
        wx, wy = w * FORCE_PLOT["JAPANESE_SEARCH_AREA"][0], h * FORCE_PLOT["JAPANESE_SEARCH_AREA"][1]
        cv.create_oval(wx-105, wy-72, wx+105, wy+72, outline="#334253", dash=(6, 5))
        cv.create_text(wx, wy-82, text="BROKEN CLOUD / SHOWERS\nSCOUTING UNCERTAINTY", fill="#718096", font=("Consolas", 7), justify="center")

        if contact:
            import math
            rad = math.radians(contact.bearing_deg)
            dist = min(0.42, contact.range_nm / 430.0)
            px = cx + math.sin(rad) * w * dist
            py = cy - math.cos(rad) * h * dist
            ur = max(18, min(w, h) * (contact.uncertainty_nm / 520.0))
            cv.create_oval(px-ur, py-ur, px+ur, py+ur, outline=COLORS["danger"], dash=(5, 4), width=2)
            cv.create_rectangle(px-7, py-7, px+7, py+7, outline=COLORS["danger"], width=2)
            cv.create_text(px+13, py, anchor="w", text=f"{contact.classification}\nCONF {contact.confidence:.0f}% • ±{contact.uncertainty_nm:.0f} NM", fill=COLORS["danger"], font=("Consolas", 8), justify="left")
        else:
            cv.create_text(wx, wy, text="NO VERIFIED ENEMY-CARRIER\nCONTACT ON YOUR PLOT", fill=COLORS["warn"], font=("Consolas", 9), justify="center")

        # Decision area is rebuilt only when the active prompt changes.
        prompt = active_prompt(st)
        prompt_key = prompt.key if prompt else None
        if prompt_key != self._hist_prompt_key:
            self._hist_prompt_key = prompt_key
            for child in self._hist_decision_frame.winfo_children(): child.destroy()
            if prompt:
                self._hist_decision_title.config(text=f"{prompt.title}  •  window closes {min_to_hhmm(prompt.expires_minute)}")
                self._hist_decision_text.config(text=prompt.briefing)
                for idx, option in enumerate(prompt.options):
                    ttk.Button(
                        self._hist_decision_frame,
                        text=option.label,
                        command=lambda pk=prompt.key, i=idx: self._hist_answer(pk, i),
                        style="Accent.TButton" if idx == 0 else "TButton",
                    ).grid(row=idx, column=0, sticky="ew", pady=3)
            else:
                nxt = upcoming_prompt(st)
                if st.completed:
                    self._hist_decision_title.config(text="Watch complete")
                    self._hist_decision_text.config(text="Evaluate the scenario to record your historical-operations qualification score.")
                elif nxt:
                    self._hist_decision_title.config(text=f"No active decision • next window {min_to_hhmm(nxt.minute)}")
                    self._hist_decision_text.config(text="Run the clock, advance five minutes, or jump to the next report/decision. Incoming reports can change the plot before the next decision.")
                else:
                    self._hist_decision_title.config(text="No further decision prompts")
                    self._hist_decision_text.config(text="Continue the watch through the end of the historical timeline.")

        for item in self._hist_intel_tree.get_children(): self._hist_intel_tree.delete(item)
        for msg in st.messages[:40]:
            lag = f"+{msg['lag']}m" if msg["lag"] else "0"
            self._hist_intel_tree.insert("", "end", values=(msg["report_time"], lag, msg["category"], msg["headline"]))

        self._hist_doctrine_text.config(state="normal")
        self._hist_doctrine_text.delete("1.0", "end")
        for group in st.doctrine_groups.values():
            age = "n/a" if group.last_intel_minute is None else f"{max(0, st.current_minute-group.last_intel_minute)} min"
            self._hist_doctrine_text.insert("end", f"{group.name}\n")
            self._hist_doctrine_text.insert("end", f"Doctrine: {group.doctrine}\n")
            self._hist_doctrine_text.insert("end", f"Current action: {group.current_action}\n")
            self._hist_doctrine_text.insert("end", f"Known-enemy confidence: {group.known_enemy_confidence:.0f}%  |  Intel age: {age}\n")
            self._hist_doctrine_text.insert("end", f"Fuel {group.fuel:.0f}%  |  Readiness {group.readiness:.0f}%  |  Morale {group.morale:.0f}%\n\n")
        self._hist_doctrine_text.config(state="disabled")

    def show_shipboard_walkthrough(self):
        self._clear_body("USS ENTERPRISE (CV-6) — SHIPBOARD WALKTHROUGH")
        if self.shipboard_state is None or self.shipboard_state.evaluated:
            # Reuse a live Enterprise watch if one exists, otherwise create a fresh synchronized watch.
            ent = self.enterprise_state if self.enterprise_state and not self.enterprise_state.evaluated else None
            self.shipboard_state = create_shipboard_walk_state(ent)
            self.enterprise_state = self.shipboard_state.enterprise
        st = self.shipboard_state

        root = ttk.Frame(self.body)
        root.grid(sticky="nsew")
        root.columnconfigure(0, weight=5)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(2, weight=1)

        banner = self.panel(root, 0, 0, colspan=2, padx=0, pady=(0, 7))
        banner.columnconfigure(0, weight=1)
        ttk.Label(banner, text="SHIPBOARD MOVEMENT MODE • USS ENTERPRISE (CV-6)", style="Hero.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            banner,
            text=("WASD moves • ←/→ turns • E operates nearby equipment/hatches • R runs/pauses the historical clock. "
                  "v0.6 adds watertight access control, moving watchstanders, equipment drill faults, and objective navigation. "
                  "The interior remains a training schematic; the Midway timeline and station-duty events remain historically locked."),
            background=COLORS["panel"], foreground=COLORS["warn"], wraplength=1000, justify="left",
            font=("Segoe UI Semibold", 9),
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(banner, text="RESET POSITION", command=self._shipwalk_reset_position).grid(row=0, column=1, rowspan=2, padx=(10, 0))
        ttk.Button(banner, text="END / EVALUATE", command=self._shipwalk_finish, style="Accent.TButton").grid(row=0, column=2, rowspan=2, padx=(7, 0))

        metrics = self.panel(root, 1, 0, colspan=2, padx=0, pady=7)
        metrics.columnconfigure(tuple(range(8)), weight=1)
        self._sw_metric = {}
        for col, (label, key) in enumerate([
            ("SIM TIME", "clock"), ("WATCH", "watch"), ("DECK", "deck"), ("LOCATION", "zone"),
            ("OPEN DUTY", "open"), ("QUALIFIED", "qual"), ("SHIP READY", "ready"), ("ALARM", "alarm"),
        ]):
            box = ttk.Frame(metrics, style="Panel2.TFrame", padding=(10, 8))
            box.grid(row=0, column=col, sticky="nsew", padx=3)
            ttk.Label(box, text=label, background=COLORS["panel2"], foreground=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            lbl = ttk.Label(box, text="--", background=COLORS["panel2"], foreground=COLORS["text"], font=("Segoe UI Semibold", 11))
            lbl.pack(anchor="w", pady=(2, 0))
            self._sw_metric[key] = lbl

        view_panel = self.panel(root, 2, 0, padx=(0, 7), pady=0)
        view_panel.columnconfigure(0, weight=1)
        view_panel.rowconfigure(1, weight=1)
        topbar = ttk.Frame(view_panel, style="Panel.TFrame")
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 7))
        topbar.columnconfigure(0, weight=1)
        self._sw_prompt = ttk.Label(topbar, text="", style="Section.TLabel", wraplength=760, justify="left")
        self._sw_prompt.grid(row=0, column=0, sticky="w")
        self._sw_run = ttk.Button(topbar, text="RUN CLOCK (R)", command=self._shipwalk_toggle_clock, style="Accent.TButton")
        self._sw_run.grid(row=0, column=1, padx=(8, 0))
        ttk.Button(topbar, text="+5 MIN", command=lambda: self._shipwalk_advance(5)).grid(row=0, column=2, padx=(5, 0))

        self._sw_view = tk.Canvas(view_panel, bg="#070b10", highlightthickness=1, highlightbackground=COLORS["line"])
        self._sw_view.grid(row=1, column=0, sticky="nsew")
        controls = ttk.Label(
            view_panel,
            text="MOVE: W/S forward/back • A/D strafe • LEFT/RIGHT turn • E interact/open/shut/restore • R run/pause clock • Follow the objective cue and physically report to stations",
            style="Muted.TLabel", wraplength=900, justify="left",
        )
        controls.grid(row=2, column=0, sticky="ew", pady=(7, 0))

        side = self.panel(root, 2, 1, padx=(7, 0), pady=0)
        side.columnconfigure(0, weight=1)
        side.rowconfigure(4, weight=1)
        ttk.Label(side, text="LOCAL INTERACTION", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self._sw_nearby = ttk.Label(side, text="", style="Muted.TLabel", wraplength=360, justify="left")
        self._sw_nearby.grid(row=1, column=0, sticky="ew", pady=(5, 7))
        ttk.Button(side, text="INTERACT / OPERATE (E)", command=self._shipwalk_interact, style="Accent.TButton").grid(row=2, column=0, sticky="ew")

        notebook = ttk.Notebook(side)
        notebook.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        map_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        qual_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=7)
        air_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=7)
        duty_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        systems_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        crew_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        log_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=5)
        notebook.add(map_tab, text="Deck Plan")
        notebook.add(qual_tab, text="Quals")
        notebook.add(air_tab, text="Aircraft")
        notebook.add(duty_tab, text="Duty")
        notebook.add(systems_tab, text="Systems")
        notebook.add(crew_tab, text="Crew")
        notebook.add(log_tab, text="Log")

        self._sw_map = tk.Canvas(map_tab, bg="#080d13", height=250, highlightthickness=0)
        self._sw_map.pack(fill="both", expand=True)
        ttk.Label(map_tab, text="Training schematic — not an exact 1942 compartment plan.", background=COLORS["panel"], foreground=COLORS["warn"], wraplength=330).pack(anchor="w", pady=(5, 0))

        self._sw_qual_text = tk.Text(qual_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Consolas", 8))
        self._sw_qual_text.pack(fill="both", expand=True)
        self._sw_air_text = tk.Text(air_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Consolas", 8))
        self._sw_air_text.pack(fill="both", expand=True)
        self._sw_duty_text = tk.Text(duty_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Consolas", 8))
        self._sw_duty_text.pack(fill="both", expand=True)
        self._sw_systems_text = tk.Text(systems_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Consolas", 8))
        self._sw_systems_text.pack(fill="both", expand=True)
        self._sw_crew_text = tk.Text(crew_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Consolas", 8))
        self._sw_crew_text.pack(fill="both", expand=True)
        self._sw_log_text = tk.Text(log_tab, bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat", wrap="word", font=("Consolas", 8))
        self._sw_log_text.pack(fill="both", expand=True)

        def key_press(event):
            key = event.keysym.lower()
            if key == "e":
                self._shipwalk_interact()
                return
            if key == "r":
                self._shipwalk_toggle_clock()
                return
            self._ship_keys.add(key)

        def key_release(event):
            self._ship_keys.discard(event.keysym.lower())

        self.bind("<KeyPress>", key_press)
        self.bind("<KeyRelease>", key_release)
        self.focus_force()
        self._shipwalk_render()

        def movement_loop():
            if self._screen_name != "USS ENTERPRISE (CV-6) — SHIPBOARD WALKTHROUGH" or not self.shipboard_state:
                return
            st = self.shipboard_state
            # Holding movement keys produces continuous collision-checked motion.
            if "left" in self._ship_keys:
                move_player(st, turn=-1)
            if "right" in self._ship_keys:
                move_player(st, turn=1)
            if "w" in self._ship_keys or "up" in self._ship_keys:
                move_player(st, forward=1)
            if "s" in self._ship_keys or "down" in self._ship_keys:
                move_player(st, forward=-1)
            if "a" in self._ship_keys:
                move_player(st, strafe=-1)
            if "d" in self._ship_keys:
                move_player(st, strafe=1)
            update_crew_movement(st, 0.055)
            self._shipwalk_render()
            self.later(55, movement_loop)

        def clock_loop():
            if self._screen_name != "USS ENTERPRISE (CV-6) — SHIPBOARD WALKTHROUGH" or not self.shipboard_state:
                return
            if self.shipboard_state.running and not self.shipboard_state.completed:
                before = len(open_tasks(self.shipboard_state.enterprise))
                advance_shipboard(self.shipboard_state, self.shipboard_state.enterprise.speed)
                after = len(open_tasks(self.shipboard_state.enterprise))
                if after > before:
                    self.shipboard_state.running = False
            self._shipwalk_render()
            self.later(750, clock_loop)

        movement_loop()
        clock_loop()

    def _shipwalk_reset_position(self):
        if not self.shipboard_state:
            return
        self.shipboard_state.deck = "ISLAND"
        self.shipboard_state.x = 7.0
        self.shipboard_state.y = 4.0
        self.shipboard_state.angle = 0.0
        self._shipwalk_render()

    def _shipwalk_toggle_clock(self):
        if not self.shipboard_state or self.shipboard_state.completed:
            return
        self.shipboard_state.running = not self.shipboard_state.running
        self._shipwalk_render()

    def _shipwalk_advance(self, minutes):
        if not self.shipboard_state or self.shipboard_state.completed:
            return
        advance_shipboard(self.shipboard_state, minutes)
        self._shipwalk_render()

    def _shipwalk_interact(self):
        if not self.shipboard_state:
            return
        ok, msg = interact(self.shipboard_state)
        if hasattr(self, "_sw_prompt"):
            self._sw_prompt.config(text=msg, foreground=COLORS["good"] if ok else COLORS["danger"])
        self._shipwalk_render()

    def _shipwalk_finish(self):
        if not self.shipboard_state:
            return
        score = evaluate_shipboard(self.shipboard_state)
        summary = shipboard_summary(self.shipboard_state)
        apply_shipboard_walk_result(self.profile, score, summary, self.shipboard_state.qualified_this_run)
        self.save_now(silent=True)
        passed = score >= 72
        messagebox.showinfo(
            "Enterprise Shipboard Duty Evaluation",
            f"Evaluation: {score:.0f}% — {'PASS' if passed else 'NOT YET PASSED'}\n\n"
            f"Station practicals completed: {summary['qualified_stations']} / {len(QUALIFICATION_REQUIREMENTS)}\n"
            f"Aircraft packages prepared: {summary['aircraft_ready_packages']}\n"
            f"Aircraft packages spotted/launched: {summary['aircraft_spotted_packages']}\n"
            f"Duty tasks complete: {summary['tasks_complete']}\n"
            f"Duty tasks missed: {summary['tasks_missed']}\n"
            f"Ship readiness: {summary['station_readiness']:.0f}%\n"
            f"Movement distance: {summary['movement_distance']:.1f} deck units\n"
            f"Training faults restored: {summary['training_faults_resolved']} • unresolved: {summary['training_faults_open']}\n"
            f"Objective actions completed: {summary['objective_completions']}\n\n"
            "Historical lock remained active. Any v0.6 equipment fault is explicitly a simulated training inject; the movement geometry is a gameplay training schematic, not an exact Enterprise deck-plan claim."
        )
        self.shipboard_state = None
        self.enterprise_state = None
        self.show_dashboard()

    def _shipwalk_render(self):
        if not self.shipboard_state or not hasattr(self, "_sw_view"):
            return
        st = self.shipboard_state
        ent = st.enterprise
        summary = shipboard_summary(st)
        zone = current_zone(st)
        station = current_station(st)
        eq = nearby_equipment(st)
        hatch = nearby_hatch(st)
        ac = nearby_aircraft(st)
        objective = active_objective(st)

        self._sw_metric["clock"].config(text=st.clock)
        self._sw_metric["watch"].config(text=st.watch_period)
        self._sw_metric["deck"].config(text=DECK_NAMES[st.deck].replace(" / ", "/"))
        self._sw_metric["zone"].config(text=zone[:18])
        self._sw_metric["open"].config(text=str(summary["tasks_open"]))
        self._sw_metric["qual"].config(text=f"{summary['qualified_stations']}/{len(QUALIFICATION_REQUIREMENTS)}")
        self._sw_metric["ready"].config(text=f"{summary['station_readiness']:.0f}%")
        alarm = ship_alarm_state(st)
        self._sw_metric["alarm"].config(text=alarm.replace("ACTION STATIONS", "ACTION").replace("URGENT ACTION", "URGENT").replace("TRAINING CASUALTY", "DRILL"))
        self._sw_run.config(text="PAUSE CLOCK (R)" if st.running else "RUN CLOCK (R)")

        if hatch:
            status = "OPEN" if st.hatches.get(hatch.key, True) else "SHUT"
            near = f"NEARBY HATCH: {hatch.name}\nStatus: {status}\nPress E to {'shut' if status == 'OPEN' else 'open'} and verify indication."
        elif eq:
            near = f"NEARBY: {eq.name}\n{eq.detail}\nPress E to operate."
        elif ac:
            near = f"NEARBY AIRCRAFT: {ac.label}\n{ac.count} × {ac.aircraft_type} • {ac.status}\nPress E to select/inspect."
        else:
            near = f"{zone}\n" + (f"Station: {STATION_DEFS[station]['name']}\n" if station else "") + "Move near a highlighted equipment control."
        self._sw_nearby.config(text=near)
        if not self._sw_prompt.cget("text") or str(self._sw_prompt.cget("text")).startswith("OBJECTIVE:"):
            self._sw_prompt.config(text=objective_navigation(st), foreground=COLORS["warn"] if objective else COLORS["text"])

        # First-person ray-cast viewport.
        cv = self._sw_view
        cv.delete("all")
        w = max(520, cv.winfo_width())
        h = max(360, cv.winfo_height())
        horizon = h * 0.48
        cv.create_rectangle(0, 0, w, horizon, fill="#0b1018", outline="")
        cv.create_rectangle(0, horizon, w, h, fill="#11151b", outline="")
        rays = raycast(st, rays=180)
        strip = w / max(1, len(rays))
        for i, (dist, side) in enumerate(rays):
            wall_h = min(h * 0.93, h / max(0.22, dist * 0.72))
            top = horizon - wall_h / 2
            bottom = horizon + wall_h / 2
            shade = max(30, min(145, int(150 - dist * 7)))
            if side == "ew":
                shade = max(22, shade - 18)
            color = f"#{shade:02x}{min(165, shade+12):02x}{min(185, shade+24):02x}"
            x1 = i * strip
            cv.create_rectangle(x1, top, x1 + strip + 1, bottom, fill=color, outline="")

        # Project visible equipment as simple HUD markers.
        fov = math.radians(68)
        for node, off, dist in visible_equipment(st, fov=fov):
            sx = w * (0.5 + off / fov)
            sy = horizon + min(h * 0.18, dist * 5.0)
            size = max(5, min(22, 38 / max(0.7, dist)))
            cv.create_oval(sx-size, sy-size, sx+size, sy+size, outline=COLORS["accent"], width=2)
            if dist < 6.0:
                cv.create_text(sx, sy-size-9, text=node.name, fill=COLORS["text"], font=("Segoe UI Semibold", 8), anchor="s")
        for av, off, dist in visible_crew(st, fov=fov):
            sx = w * (0.5 + off / fov)
            floor_y = horizon + min(h * 0.31, 28 + dist * 10.0)
            body_h = max(18, min(86, 95 / max(0.8, dist)))
            cv.create_oval(sx-body_h*0.13, floor_y-body_h, sx+body_h*0.13, floor_y-body_h*0.72, fill="#b7c4d2", outline="")
            cv.create_rectangle(sx-body_h*0.18, floor_y-body_h*0.72, sx+body_h*0.18, floor_y, fill="#34475a", outline="#5f7892")
            if dist < 5.0:
                crew = ent.crew.get(av.key)
                cv.create_text(sx, floor_y-body_h-5, text=crew.name if crew else av.key, fill=COLORS["good"], font=("Segoe UI", 7), anchor="s")
        cv.create_line(w/2-10, h/2, w/2+10, h/2, fill=COLORS["accent"], width=2)
        cv.create_line(w/2, h/2-10, w/2, h/2+10, fill=COLORS["accent"], width=2)
        cv.create_text(12, 12, anchor="nw", text=f"{DECK_NAMES[st.deck]}  |  {zone}\nPOS {st.x:.1f},{st.y:.1f}  HDG {math.degrees(st.angle)%360:03.0f}°", fill=COLORS["muted"], font=("Consolas", 9))
        cv.create_text(w-12, 12, anchor="ne", text=f"{st.clock}\nHISTORICAL LOCK\n{ship_alarm_state(st)}", fill=COLORS["warn"], font=("Consolas", 9), justify="right")
        cv.create_text(w/2, h-18, anchor="s", text=objective_navigation(st), fill=COLORS["warn"], font=("Consolas", 8), width=int(w*0.8), justify="center")

        # Minimap.
        mm = self._sw_map
        mm.delete("all")
        mw = max(280, mm.winfo_width()); mh = max(210, mm.winfo_height())
        grid = DECK_MAPS[st.deck]
        tw, th = mw / len(grid[0]), mh / len(grid)
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell == "#":
                    mm.create_rectangle(x*tw, y*th, (x+1)*tw, (y+1)*th, fill="#24303d", outline="")
        for node in EQUIPMENT.values():
            if node.deck == st.deck:
                mm.create_oval(node.x*tw-2, node.y*th-2, node.x*tw+2, node.y*th+2, fill=COLORS["accent"], outline="")
        for air in st.aircraft.values():
            if air.deck == st.deck and not air.launched:
                mm.create_rectangle(air.x*tw-2, air.y*th-2, air.x*tw+2, air.y*th+2, outline=COLORS["good"])
        for key, hnode in HATCHES.items():
            if hnode.deck == st.deck:
                hc = COLORS["good"] if st.hatches.get(key, True) else COLORS["danger"]
                mm.create_rectangle(hnode.x*tw-3, hnode.y*th-3, hnode.x*tw+3, hnode.y*th+3, fill=hc, outline="white")
        for av in st.crew_avatars.values():
            if av.deck == st.deck:
                mm.create_oval(av.x*tw-2, av.y*th-2, av.x*tw+2, av.y*th+2, fill="#8ea9c2", outline="")
        if objective and objective["deck"] == st.deck:
            ox, oy = objective["x"]*tw, objective["y"]*th
            mm.create_polygon(ox, oy-6, ox+6, oy, ox, oy+6, ox-6, oy, outline=COLORS["warn"], fill="")
        px, py = st.x*tw, st.y*th
        mm.create_oval(px-4, py-4, px+4, py+4, fill=COLORS["danger"], outline="white")
        mm.create_line(px, py, px+math.cos(st.angle)*12, py+math.sin(st.angle)*12, fill="white", width=2)
        mm.create_text(6, 6, anchor="nw", text=DECK_NAMES[st.deck], fill=COLORS["text"], font=("Segoe UI Semibold", 8))

        # Qualification checklist.
        self._sw_qual_text.config(state="normal")
        self._sw_qual_text.delete("1.0", "end")
        for skey in STATION_DEFS:
            done, total, complete = qualification_status(st, skey)
            persisted = self.profile.station_qualifications.get(skey, False)
            flag = "QUALIFIED" if persisted else ("PRACTICAL COMPLETE" if complete else f"{done}/{total}")
            self._sw_qual_text.insert("end", f"{STATION_DEFS[skey]['name']}\n  {flag}\n")
            req = QUALIFICATION_REQUIREMENTS[skey]
            progress = set(st.qualification_progress.get(skey, []))
            self._sw_qual_text.insert("end", "  " + " • ".join(("✓" if r in progress else "○") + r for r in req) + "\n\n")
        self._sw_qual_text.config(state="disabled")

        # Aircraft state.
        self._sw_air_text.config(state="normal")
        self._sw_air_text.delete("1.0", "end")
        self._sw_air_text.insert("end", "AIRCRAFT HANDLING PACKAGES\n\n")
        for air in st.aircraft.values():
            self._sw_air_text.insert("end", f"{air.label}\n  {air.count} × {air.aircraft_type}\n  {air.deck} • {air.status}\n  Fuel {'YES' if air.fueled else 'NO'} • Arm {'YES' if air.armed else 'NO'} • Spot {'YES' if air.spotted else 'NO'}\n\n")
        self._sw_air_text.insert("end", f"Elevators: " + ", ".join(f"#{k} {v}" for k,v in st.elevators.items()))
        self._sw_air_text.config(state="disabled")

        # Duty queue.
        self._sw_duty_text.config(state="normal")
        self._sw_duty_text.delete("1.0", "end")
        self._sw_duty_text.insert("end", f"WATCH {st.watch_period} • {st.clock}\n\n")
        tasks = open_tasks(ent)
        if not tasks:
            self._sw_duty_text.insert("end", "No currently open shipboard tasks. Continue the historical clock or work station qualifications.\n")
        for task in tasks[:15]:
            self._sw_duty_text.insert("end", f"[{STATION_DEFS[task.station]['short']}] {task.title}\n  Deadline {ent.clock if task.deadline_minute <= ent.current_minute else ''}{task.deadline_minute//60:02d}:{task.deadline_minute%60:02d} • {task.points} pts\n  {task.detail}\n\n")
        self._sw_duty_text.config(state="disabled")

        self._sw_systems_text.config(state="normal")
        self._sw_systems_text.delete("1.0", "end")
        self._sw_systems_text.insert("end", f"SHIPBOARD ACCESS / EQUIPMENT\nAlarm: {ship_alarm_state(st)}\n\nHATCHES\n")
        for key, hnode in HATCHES.items():
            self._sw_systems_text.insert("end", f"  {hnode.name}: {'OPEN' if st.hatches.get(key, True) else 'SHUT'}\n")
        self._sw_systems_text.insert("end", "\nEQUIPMENT\n")
        for key, runtime in st.equipment_runtime.items():
            if runtime.fault or runtime.health < 99:
                self._sw_systems_text.insert("end", f"  {EQUIPMENT[key].name}: {runtime.health:.0f}% • {runtime.fault or 'SERVICEABLE'}\n")
        if not any(rt.fault or rt.health < 99 for rt in st.equipment_runtime.values()):
            self._sw_systems_text.insert("end", "  All tracked training equipment serviceable.\n")
        self._sw_systems_text.insert("end", "\nSIMULATED drill faults are intentionally separated from the historical Midway event record.\n")
        self._sw_systems_text.config(state="disabled")

        self._sw_crew_text.config(state="normal")
        self._sw_crew_text.delete("1.0", "end")
        self._sw_crew_text.insert("end", "LIVE WATCHSTANDERS\n\n")
        for key, av in st.crew_avatars.items():
            crew = ent.crew.get(key)
            if not crew:
                continue
            self._sw_crew_text.insert("end", f"{crew.name}\n  {crew.rating}\n  {STATION_DEFS[av.station]['name']} • {DECK_NAMES[av.deck]}\n  Fatigue {crew.fatigue:.0f}% • Stress {crew.stress:.0f}%\n\n")
        self._sw_crew_text.config(state="disabled")

        self._sw_log_text.config(state="normal")
        self._sw_log_text.delete("1.0", "end")
        for line in st.action_log[:80]:
            self._sw_log_text.insert("end", line + "\n")
        for line in ent.action_log[:40]:
            self._sw_log_text.insert("end", line + "\n")
        self._sw_log_text.config(state="disabled")

    def show_timeline(self):
        self._clear_body("HISTORICAL TIMELINE")
        root=self.panel(self.body)
        ttk.Label(root,text="Human Military History Catalog",style="Hero.TLabel").pack(anchor="w")
        ttk.Label(root,text="The master design spans ancient warfare through modern cyber and space operations. Historically sourced scenarios unlock here only after their timeline, environment, orders of battle, and information limits are traceable to research sources.",style="Muted.TLabel",wraplength=1050).pack(anchor="w",pady=(5,8))
        ready=ttk.Frame(root,style="Panel2.TFrame",padding=12);ready.pack(fill="x",pady=(0,10))
        ttk.Label(ready,text="READY TO PLAY • Battle of Midway — 4 June 1942 Operations Watch",background=COLORS["panel2"],foreground=COLORS["good"],font=("Segoe UI Semibold",11)).pack(side="left")
        ttk.Button(ready,text="LAUNCH HISTORICAL SCENARIO",command=self.show_historical_ops,style="Accent.TButton").pack(side="right")
        canvas=tk.Canvas(root,bg=COLORS["panel"],highlightthickness=0)
        sb=ttk.Scrollbar(root,orient="vertical",command=canvas.yview)
        scroll=ttk.Frame(canvas,style="Panel.TFrame")
        scroll.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=scroll,anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        for era,items in ERAS.items():
            ef=ttk.Frame(scroll,style="Panel2.TFrame",padding=14); ef.pack(fill="x",pady=6,padx=4)
            ttk.Label(ef,text=era,background=COLORS["panel2"],foreground=COLORS["accent"],font=("Segoe UI Semibold",13)).pack(anchor="w")
            ttk.Label(ef,text="  •  ".join(items),background=COLORS["panel2"],foreground=COLORS["muted"],wraplength=980,justify="left").pack(anchor="w",pady=(5,0))

    def show_crew(self):
        self._clear_body("CREW SIMULATION")
        root=self.panel(self.body)
        ttk.Label(root,text="Persistent Crew Model",style="Section.TLabel").pack(anchor="w")
        ttk.Label(root,text="NPCs carry age, rank, experience, morale, fatigue, stress, injuries, training, relationships, family history, personality, decision-making, voice, memory, and career record.",style="Muted.TLabel",wraplength=1100).pack(anchor="w",pady=(4,12))
        cols=("name","rank","age","xp","morale","fatigue","stress","training","decision","personality")
        tree=ttk.Treeview(root,columns=cols,show="headings")
        headings={"name":"Name","rank":"Rank","age":"Age","xp":"Exp","morale":"Morale","fatigue":"Fatigue","stress":"Stress","training":"Training","decision":"Decision","personality":"Personality"}
        widths={"name":150,"rank":145,"age":45,"xp":60,"morale":65,"fatigue":65,"stress":60,"training":65,"decision":70,"personality":100}
        for c in cols:
            tree.heading(c,text=headings[c]);tree.column(c,width=widths[c],anchor="w")
        for m in generate_crew(self.profile,12):
            tree.insert("", "end", values=(m.name,m.rank,m.age,m.experience,f"{m.morale:.0f}",f"{m.fatigue:.0f}",f"{m.stress:.0f}",f"{m.training:.0f}",f"{m.decision_making:.0f}",m.personality))
        tree.pack(fill="both",expand=True)
        ttk.Label(root,text="Leadership modifies morale and relationships; later builds will preserve individual memories, casualties, assignments, and promotion records across deployments.",style="Muted.TLabel",wraplength=1050).pack(anchor="w",pady=(12,0))

    def show_service_record(self):
        self._clear_body("SERVICE RECORD")
        root=ttk.Frame(self.body);root.grid(sticky="nsew");root.columnconfigure(0,weight=1);root.columnconfigure(1,weight=1);root.rowconfigure(0,weight=1)
        left=self.panel(root,0,0)
        ttk.Label(left,text="Career",style="Section.TLabel").pack(anchor="w")
        for label,value in [("Name",self.profile.name),("Branch",self.profile.branch),("Era",self.profile.era),("Rank",self.profile.rank),("Next Rank",self.profile.next_rank),("Experience",f"{self.profile.xp} XP"),("Duty Periods",self.profile.duty_periods),("Historical Watches",self.profile.historical_runs),("Historical Best",f"{self.profile.historical_best:.0f}%"),("Enterprise Walkthroughs",self.profile.shipboard_walk_runs),("Walkthrough Best",f"{self.profile.shipboard_walk_best:.0f}%"),("Station Practicals",sum(1 for v in self.profile.station_qualifications.values() if v))]:
            r=ttk.Frame(left,style="Panel.TFrame");r.pack(fill="x",pady=3);ttk.Label(r,text=label,style="Muted.TLabel").pack(side="left");ttk.Label(r,text=str(value),style="Panel.TLabel").pack(side="right")
        ttk.Separator(left).pack(fill="x",pady=12)
        ttk.Label(left,text="Qualifications",style="Section.TLabel").pack(anchor="w")
        if self.profile.qualifications:
            for q,v in self.profile.qualifications.items():
                ttk.Label(left,text=f"{'✓' if v else '○'} {q}",style="Good.TLabel" if v else "Muted.TLabel").pack(anchor="w",pady=2)
        else:
            ttk.Label(left,text="No qualifications earned yet.",style="Muted.TLabel").pack(anchor="w")
        right=self.panel(root,0,1)
        ttk.Label(right,text="Mission / Evaluation History",style="Section.TLabel").pack(anchor="w")
        if not self.profile.mission_history:
            ttk.Label(right,text="No completed mission evaluations yet.",style="Muted.TLabel").pack(anchor="w",pady=8)
        for m in self.profile.mission_history[:12]:
            box=ttk.Frame(right,style="Panel2.TFrame",padding=10);box.pack(fill="x",pady=4)
            ttk.Label(box,text=m.get("mission","Mission"),background=COLORS["panel2"],foreground=COLORS["text"],font=("Segoe UI Semibold",10)).pack(anchor="w")
            ttk.Label(box,text=f"Score {m.get('score',0)}% • Crew survival {m.get('crew_survival',0)}% • Efficiency {m.get('efficiency',0)}% • Professionalism {m.get('professionalism',0)}%",background=COLORS["panel2"],foreground=COLORS["muted"]).pack(anchor="w",pady=(2,0))
        ttk.Separator(right).pack(fill="x",pady=12)
        ttk.Label(right,text="Rank Ladder",style="Section.TLabel").pack(anchor="w")
        ttk.Label(right,text=" → ".join(NAVAL_RANKS),style="Muted.TLabel",wraplength=520,justify="left").pack(anchor="w",pady=(4,0))

    def on_close(self):
        try:
            self.save_now(silent=True)
        except Exception:
            pass
        self.destroy()
