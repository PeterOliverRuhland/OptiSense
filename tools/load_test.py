"""Load test: simulated students use OptiSense at the same time, as in a lecture.

Each simulated student talks to the app like a browser does (page load, then the websocket): loads the example or
enters a model, optimises, edits constraints, switches the value range, runs the sensitivity analysis, downloads
graphs, solves exercises on “Learn & practise” and reads the guide, with pauses in between. Every few minutes all
students change their model and click “Optimise” within a few seconds (“now everybody solves task 3”).
It measures the time from each click until the app has answered: what the students feel.

    cd shiny_files && shiny run app.py --port 8000        # or test the server directly
    python tools/load_test.py http://127.0.0.1:8000 --users 40 --minutes 25
    python tools/load_test.py https://app-optisense.com --users 40 --minutes 25 --csv load.csv

Needs only `websockets` (installed with shiny).
"""

import argparse
import asyncio
import csv
import http.cookiejar
import json
import os
import random
import re
import ssl
import statistics
import sys
import time
import urllib.request

import websockets

MAX_CONSTRAINTS = 5          # as in shiny_files/optisense/config.py
TIMEOUT = 30                 # seconds; a click without an answer by then counts as failed
WORK_OUTPUTS = ("plot", "problem_list", "problem_type", "solve_hint")
TAB_OUTPUTS = {"solution": "solution_view", "sensitivity": "sensitivity_view", "description": "description_view"}
DPI = (("150", 0.8), ("300", 0.15), ("600", 0.05))


def ssl_context():
    """Python from python.org on macOS brings no CA certificates of its own; then use the system's."""
    ctx = ssl.create_default_context()
    if not ctx.get_ca_certs() and os.path.exists("/etc/ssl/cert.pem"):
        ctx.load_verify_locations("/etc/ssl/cert.pem")
    return ctx


SSL = ssl_context()


class Hub:
    """Shared by all students: the measurements and the signal for the “everybody now” moments."""

    def __init__(self, args):
        self.args = args
        self.start = time.monotonic()
        self.end = self.start + args.minutes * 60
        self.rows = []               # (seconds since start, student, action, ms, ok)
        self.burst_no = 0
        self.burst_times = []
        self.online = 0

    def now(self):
        return time.monotonic() - self.start

    def add(self, student, action, ms, ok=True):
        self.rows.append((round(self.now(), 2), student, action, round(ms), ok))


class Student:
    def __init__(self, n, hub):
        self.n, self.hub = n, hub
        self.rng = random.Random(hub.args.seed * 1000 + n)
        self.base = hub.args.url.rstrip("/") + "/"
        self.ws_url = re.sub(r"^http", "ws", self.base) + "websocket/"
        self.pixelratio = self.rng.choice((1, 2))                 # Windows laptop or MacBook
        self.plot_size = (self.rng.randint(640, 900), self.rng.randint(560, 720))
        # cookies like a browser: Caddy keeps each student on one app container with a cookie
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar),
                                                  urllib.request.HTTPSHandler(context=SSL))

    # ------------------------------------------------------------------ talking to the app
    def reset_state(self):
        self.inbox = asyncio.Queue()
        self.is_busy = False
        self.ws = self.reader_task = None
        self.buttons = {}            # action buttons count up like in the browser
        self.next_id = 0             # mirrors the app's ids of objective functions and constraints
        self.objectives, self.constraints = {}, {}
        self.vt = {"x1": "con", "x2": "con"}
        self.solved = False
        self.page, self.tab = "work", "solution"
        self.req_id = 0
        self.last_burst = self.hub.burst_no

    async def reader(self):
        try:
            async for message in self.ws:
                msg = json.loads(message)
                if "busy" in msg:
                    self.is_busy = msg["busy"] == "busy"
                self.inbox.put_nowait(msg)
        except websockets.ConnectionClosed:
            pass

    async def send(self, data):
        """Input changes the app answers without visible work (tabs, pages, file name): not measured."""
        await self.ws.send(json.dumps({"method": "update", "data": data}))

    def click(self, button):
        self.buttons[button] = self.buttons.get(button, 0) + 1
        return {button: self.buttons[button]}

    async def act(self, action, data):
        """Send input changes; wait for the app's answer (busy … idle, then the output values).
        The changes must make the app do something, otherwise no answer comes."""
        waited = time.monotonic()
        while self.is_busy and time.monotonic() - waited < TIMEOUT:     # an earlier page or tab change still drawing
            await asyncio.sleep(0.02)
        while not self.inbox.empty():
            self.inbox.get_nowait()
        start = time.monotonic()
        await self.ws.send(json.dumps({"method": "update", "data": data}))
        got, busy = [], False
        try:
            while True:
                msg = await asyncio.wait_for(self.inbox.get(), TIMEOUT - (time.monotonic() - start))
                got.append(msg)
                busy = busy or "busy" in msg
                if busy and "values" in msg:
                    break
            ok = not any(m.get("errors") for m in got)
        except asyncio.TimeoutError:
            ok = False
        self.hub.add(self.n, action, 1000 * (time.monotonic() - start), ok)
        return got

    def hidden(self, visible):
        names = WORK_OUTPUTS + tuple(TAB_OUTPUTS.values()) + ("guide_view", "m_preview", "m_errors")
        return {f".clientdata_output_{o}_hidden": o not in visible for o in names}

    def visible_now(self):
        if self.page == "work":
            return set(WORK_OUTPUTS) | {TAB_OUTPUTS[self.tab]}
        return {"guide_view"} if self.page == "guide" else set()

    async def think(self, lo, hi, interruptible=True):
        """Pause like a person; an “everybody now” moment interrupts the pause (not while typing in a dialog)."""
        until = time.monotonic() + self.rng.uniform(lo, hi) * self.hub.args.pace
        while time.monotonic() < until:
            if interruptible and self.hub.burst_no != self.last_burst:
                self.last_burst = self.hub.burst_no
                await asyncio.sleep(self.rng.uniform(0, 2))           # reaction time
                await self.burst()
                return
            await asyncio.sleep(min(0.25, max(0, until - time.monotonic())))

    async def http(self, path):
        def get():
            req = urllib.request.Request(self.base + path, headers={"Accept-Encoding": "gzip", "User-Agent": "optisense-load-test"})
            with self.opener.open(req, timeout=TIMEOUT) as resp:
                return resp.read()
        return await asyncio.to_thread(get)

    # ------------------------------------------------------------------ what students do
    async def page_load(self):
        start = time.monotonic()
        try:
            html = (await self.http("")).decode("utf-8", "replace")
            assets = re.findall(r'<(?:script[^>]*src|link[^>]*href)="([^"]+\.(?:js|css)[^"]*)"', html)
            sem = asyncio.Semaphore(6)                                 # browsers load 6 files at a time

            async def one(path):
                async with sem:
                    await self.http(path)
            await asyncio.gather(*(one(a) for a in assets if not a.startswith("http")))
            self.hub.add(self.n, "Seite laden", 1000 * (time.monotonic() - start))
        except Exception:  # noqa: BLE001
            self.hub.add(self.n, "Seite laden", 1000 * (time.monotonic() - start), ok=False)

    async def connect(self):
        self.reset_state()
        tls = {"ssl": SSL} if self.ws_url.startswith("wss:") else {}
        cookies = "; ".join(f"{c.name}={c.value}" for c in self.jar)
        self.ws = await websockets.connect(self.ws_url, max_size=None, open_timeout=TIMEOUT,
                                           additional_headers={"Cookie": cookies} if cookies else None, **tls)
        self.sid = json.loads(await self.ws.recv())["config"]["sessionId"]
        self.reader_task = asyncio.create_task(self.reader())
        await self.ws.send(json.dumps({"method": "init", "data": {
            "lang": "de", "page": "work", "results_tabs": "solution", "ui_scale": 1.0, "ui_phone": False,
            "vt_x1": "con", "vt_x2": "con", ".clientdata_pixelratio": self.pixelratio,
            ".clientdata_output_plot_width": self.plot_size[0], ".clientdata_output_plot_height": self.plot_size[1],
            **self.hidden(self.visible_now())}}))

    async def go(self, page):
        self.page = page
        await self.send({"page": page, **self.hidden(self.visible_now())})

    async def load_example(self):
        await self.act("Beispiel laden", self.click("btn_example"))
        self.objectives = {self.next_id + 1: {"name": "F", "c1": 10, "c2": 20, "sense": "max"}}
        self.constraints = {self.next_id + 2: {"name": "Rohstoff", "a1": 6, "a2": 9, "op": "≤", "b": 720},
                            self.next_id + 3: {"name": "Montage", "a1": 0, "a2": 1, "op": "≤", "b": 60}}
        self.next_id += 3
        self.solved = False

    async def dialog(self, kind, item_id, values, changes):
        """Open the dialog (new or edit), type the changes one by one, save."""
        if item_id is None:
            await self.act("Dialog öffnen", {"add_click": {"kind": kind, "n": time.time_ns()}})
        else:
            await self.act("Dialog öffnen", {"row_click": {"kind": kind, "id": item_id, "n": time.time_ns()}})
        fields = {"f_name": values["name"], "f_a1": values["a1" if kind == "con" else "c1"],
                  "f_a2": values["a2" if kind == "con" else "c2"]}
        fields.update({"f_op": values["op"], "f_b": values["b"]} if kind == "con" else {"f_sense": values["sense"]})
        # what the dialog shows when it opens: the item, or the app's defaults
        old = (self.constraints if kind == "con" else self.objectives).get(item_id)
        if old is not None:
            bound = {"f_name": old["name"], "f_a1": old["a1" if kind == "con" else "c1"],
                     "f_a2": old["a2" if kind == "con" else "c2"]}
            bound.update({"f_op": old["op"], "f_b": old["b"]} if kind == "con" else {"f_sense": old["sense"]})
        else:
            bound = {"f_name": "Neu", "f_a1": 1, "f_a2": 1, **({"f_op": "≤", "f_b": 10} if kind == "con" else {"f_sense": "max"})}
        await self.act("Tippen", {**bound, ".clientdata_output_m_preview_hidden": False,
                                  ".clientdata_output_m_errors_hidden": False})
        for key in changes:
            if fields[key] != bound[key]:
                await self.think(0.8, 2.5, interruptible=False)
                await self.act("Tippen", {key: fields[key]})
                bound[key] = fields[key]
        await self.think(0.5, 1.5, interruptible=False)
        await self.act("Speichern", {**self.click("m_save"), ".clientdata_output_m_preview_hidden": True,
                                     ".clientdata_output_m_errors_hidden": True})
        if item_id is None:
            self.next_id += 1
            item_id = self.next_id
        (self.constraints if kind == "con" else self.objectives)[item_id] = values
        self.solved = False

    def random_constraint(self):
        k = len(self.constraints) + 1
        return {"name": f"NB{k}_{self.next_id}", "a1": self.rng.randint(1, 9), "a2": self.rng.randint(1, 9),
                "op": "≤", "b": self.rng.randint(4, 30) * 10}

    async def enter_model(self):
        obj = {"name": "G", "c1": self.rng.randint(1, 20), "c2": self.rng.randint(1, 20), "sense": "max"}
        await self.dialog("obj", None, obj, ("f_name", "f_a1", "f_a2"))
        for _ in range(self.rng.randint(2, 3)):
            await self.think(2, 6)
            await self.dialog("con", None, self.random_constraint(), ("f_name", "f_a1", "f_a2", "f_b"))

    async def optimize(self, label="Optimieren"):
        await self.act(label, self.click("btn_opt"))
        self.solved = True

    async def edit_constraint(self):
        cid = self.rng.choice(list(self.constraints))
        values = dict(self.constraints[cid], b=self.rng.randint(4, 40) * 10)
        await self.dialog("con", cid, values, ("f_b",))
        if self.rng.random() < 0.7:
            await self.think(1, 3)
            await self.optimize()

    async def toggle_constraint(self):
        cid = self.rng.choice(list(self.constraints))
        await self.act("NB an/aus", {"row_toggle": {"kind": "con", "id": cid, "on": False, "n": time.time_ns()}})
        await self.think(2, 5)
        await self.act("NB an/aus", {"row_toggle": {"kind": "con", "id": cid, "on": True, "n": time.time_ns()}})
        self.solved = False

    async def value_range(self):
        var = self.rng.choice(("x1", "x2"))
        self.vt[var] = "int" if self.vt[var] == "con" else "con"
        await self.act("Wertebereich", {f"vt_{var}": self.vt[var]})
        self.solved = False
        await self.think(1, 3)
        await self.optimize()

    async def sensitivity(self):
        if not self.solved:
            await self.optimize()
            await self.think(2, 5)
        self.tab = "sensitivity"
        await self.send({"results_tabs": "sensitivity", **self.hidden(self.visible_now())})
        await self.act("Sensitivität", self.click("btn_sens"))
        await self.think(5, 15)
        self.tab = self.rng.choice(("solution", "description"))
        await self.send({"results_tabs": self.tab, **self.hidden(self.visible_now())})

    async def download_png(self):
        if not self.solved:
            await self.optimize()
        await self.act("Dialog öffnen", self.click("btn_png"))
        dpi = self.rng.choices([d for d, _ in DPI], [w for _, w in DPI])[0]
        await self.send({"png_name": "graph", "png_dpi": dpi})
        await self.think(1, 3, interruptible=False)
        start = time.monotonic()
        try:
            ok = (await self.http(f"session/{self.sid}/download/dl_png?w=")).startswith(b"\x89PNG")
        except Exception:  # noqa: BLE001
            ok = False
        self.hub.add(self.n, f"PNG {dpi} dpi", 1000 * (time.monotonic() - start), ok)

    async def learn(self):
        await self.go("learn")
        await self.think(3, 8)
        options = {"mode": "practice", "form": self.rng.choice(("text", "math")),
                   "difficulty": self.rng.choice(("easy", "medium")), "kind": self.rng.choice(("LP", "ILP", "MILP"))}
        data = await self.learn_req("Aufgabe erstellen", "create", options=options)
        steps = (data or {}).get("steps") or []
        answers = {}
        for step in steps[:self.rng.randint(3, 6)]:
            await self.think(10, 30)
            if time.monotonic() >= self.hub.end:
                return
            answers[step["id"]] = {q["key"]: str(self.rng.randint(0, 60)) for q in step.get("questions", [])}
            await self.learn_req("Antwort prüfen", "check", step=step["id"], answers=answers)
            if self.rng.random() < 0.3:
                await self.think(2, 6)
                await self.learn_req("Tipp", "hint", step=step["id"], answers=answers)
            if self.rng.random() < 0.2:
                await self.think(2, 6)
                await self.learn_req("Lösung", "solution", step=step["id"], answers=answers)
        if steps:
            await self.think(3, 8)
            await self.learn_req("Abgeben", "submit", answers=answers)
            await self.think(5, 15)
        await self.go("work")

    async def learn_req(self, label, action, **payload):
        self.req_id += 1
        got = await self.act(label, {"learn_req": {"id": self.req_id, "action": action, "lang": "de", **payload}})
        for msg in got:
            reply = msg.get("custom", {}).get("os-learn")
            if reply and reply.get("id") == self.req_id:
                return reply.get("data")
        return None

    async def guide(self):
        await self.go("guide")
        await self.think(15, 40)
        await self.go("work")

    async def burst(self):
        """“Now everybody: change the model and optimise.”"""
        page = self.page
        if page != "work":
            await self.go("work")
        if not self.constraints:
            await self.load_example()
        var = self.rng.choice(("x1", "x2"))
        self.vt[var] = "int" if self.vt[var] == "con" else "con"
        await self.act("Alle gleichzeitig: Wertebereich", {f"vt_{var}": self.vt[var]})
        await asyncio.sleep(self.rng.uniform(0.5, 1.5))
        await self.optimize("Alle gleichzeitig: Optimieren")
        if page != "work":
            await self.go(page)

    # ------------------------------------------------------------------ one student's two hours, compressed
    async def session(self):
        await self.page_load()
        await self.connect()
        await self.think(2, 6)
        if self.rng.random() < 0.4:
            await self.load_example()
        else:
            await self.enter_model()
        await self.think(2, 5)
        await self.optimize()
        actions = ((self.optimize, 12), (self.edit_constraint, 18), (self.toggle_constraint, 8), (self.value_range, 10),
                   (self.sensitivity, 12), (self.download_png, 6), (self.learn, self.hub.args.learn_weight), (self.guide, 3),
                   (self.add_constraint, 5))
        while time.monotonic() < self.hub.end:
            await self.think(4, 15)
            if time.monotonic() >= self.hub.end:
                break
            action = self.rng.choices([a for a, _ in actions], [w for _, w in actions])[0]
            await action()

    async def add_constraint(self):
        if len(self.constraints) < MAX_CONSTRAINTS:
            await self.dialog("con", None, self.random_constraint(), ("f_name", "f_a1", "f_a2", "f_b"))
        else:
            await self.edit_constraint()

    async def run(self):
        await asyncio.sleep(self.rng.uniform(0, self.hub.args.ramp))     # students arrive one after the other
        while time.monotonic() < self.hub.end:
            try:
                self.hub.online += 1
                await self.session()
                return
            except (websockets.ConnectionClosed, OSError, asyncio.TimeoutError, KeyError) as exc:
                self.hub.add(self.n, f"Verbindung verloren ({type(exc).__name__})", 0, ok=False)
                await asyncio.sleep(5)                                    # the student reloads the page
            finally:
                self.hub.online -= 1
                if getattr(self, "reader_task", None) is not None:
                    self.reader_task.cancel()
                if getattr(self, "ws", None) is not None:
                    await self.ws.close()


# ---------------------------------------------------------------------- report
def pct(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))] if values else 0


def line(label, rows):
    ms = [r[3] for r in rows if r[4]]
    failed = sum(1 for r in rows if not r[4])
    if not ms:
        return f"{label:34} {len(rows):6}   (alle fehlgeschlagen)"
    slow1 = 100 * sum(1 for m in ms if m > 1000) / len(ms)
    slow3 = 100 * sum(1 for m in ms if m > 3000) / len(ms)
    return (f"{label:34} {len(rows):6} {statistics.median(ms):8.0f} {pct(ms, 95):8.0f} {max(ms):8.0f}"
            f" {slow1:6.1f}% {slow3:6.1f}% {failed:6}")


GRAPH_ACTIONS = ("Optimieren", "Speichern", "NB an/aus", "Wertebereich", "Beispiel laden")
HEADER = f"{'':34} {'Anzahl':>6} {'Median':>8} {'95 %':>8} {'Max':>8} {'>1 s':>7} {'>3 s':>7} {'Fehler':>6}   (ms)"


async def progress(hub):
    shown = 0
    while time.monotonic() < hub.end + 60:
        await asyncio.sleep(30)
        rows = hub.rows[shown:]
        shown += len(rows)
        clicks = [r for r in rows if not r[2].startswith(("Seite laden", "Verbindung"))]
        ms = [r[3] for r in clicks if r[4]]
        print(f"[{hub.now() / 60:5.1f} min] online {hub.online:3}  Klicks {len(clicks):5}  "
              f"Median {statistics.median(ms) if ms else 0:6.0f} ms  95 % {pct(ms, 95):6.0f} ms  "
              f"Max {max(ms) if ms else 0:6.0f} ms  Fehler {sum(1 for r in rows if not r[4])}", flush=True)


async def bursts(hub):
    t = hub.args.burst_first * 60
    while hub.start + t < hub.end:
        await asyncio.sleep(max(0, hub.start + t - time.monotonic()))
        hub.burst_no += 1
        hub.burst_times.append(hub.now())
        print(f"[{hub.now() / 60:5.1f} min] >>> Alle gleichzeitig: Wertebereich ändern und Optimieren", flush=True)
        t += hub.args.burst_every * 60


def report(hub):
    rows = hub.rows
    print("\n" + "=" * 100)
    print(f"Ergebnis: {hub.args.users} Studierende, {hub.args.minutes} min, {hub.args.url}\n")
    print(HEADER)
    clicks = [r for r in rows if not r[2].startswith(("Seite laden", "Verbindung", "Alle gleichzeitig"))]
    print(line("Alle normalen Klicks", clicks))
    print(line("Klicks, die den Graphen zeichnen", [r for r in rows if r[2] in GRAPH_ACTIONS]))
    print(line("Alle gleichzeitig (Optimieren)", [r for r in rows if r[2] == "Alle gleichzeitig: Optimieren"]))
    print()
    for action in sorted({r[2] for r in rows}):
        print(line(action, [r for r in rows if r[2] == action]))
    if hub.burst_times:
        print("\n„Alle gleichzeitig“ einzeln (Optimieren):")
        for i, t in enumerate(hub.burst_times):
            nxt = hub.burst_times[i + 1] if i + 1 < len(hub.burst_times) else float("inf")
            print(line(f"  Welle {i + 1} ({t / 60:.1f} min)",
                       [r for r in rows if r[2] == "Alle gleichzeitig: Optimieren" and t <= r[0] < nxt]))
    if hub.args.csv:
        with open(hub.args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["sekunde", "student", "aktion", "ms", "ok"])
            w.writerows(rows)
        print(f"\nAlle Messungen: {hub.args.csv}")


async def main(args):
    hub = Hub(args)
    print(f"Start: {args.users} Studierende gegen {args.url}, {args.minutes} min "
          f"(„alle gleichzeitig“ ab Minute {args.burst_first}, alle {args.burst_every} min)", flush=True)
    helpers = [asyncio.create_task(progress(hub)), asyncio.create_task(bursts(hub))]
    await asyncio.gather(*(Student(n, hub).run() for n in range(1, args.users + 1)))
    for task in helpers:
        task.cancel()
    report(hub)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("url")
    p.add_argument("--users", type=int, default=40)
    p.add_argument("--minutes", type=float, default=25)
    p.add_argument("--ramp", type=float, default=60, help="seconds over which the students arrive")
    p.add_argument("--burst-first", type=float, default=3, help="minute of the first “everybody now” moment")
    p.add_argument("--burst-every", type=float, default=5, help="minutes between those moments")
    p.add_argument("--pace", type=float, default=1.0, help="factor for all pauses (0.5 = students click twice as fast)")
    p.add_argument("--learn-weight", type=float, default=14,
                   help="how often students pick an exercise on “Learn & practise” (other actions together: 74)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--csv")
    try:
        asyncio.run(main(p.parse_args()))
    except KeyboardInterrupt:
        sys.exit(1)
