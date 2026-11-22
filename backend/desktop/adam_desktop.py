"""Adam Desktop: ponte entre o Adam (nuvem) e este computador. Cada ação pede sua permissão."""
import base64
import io
import json
import os
import platform
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import pyautogui
import pyperclip
import requests

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
PERMS = HERE / "permissoes.json"
LOG = HERE / "adam_log.txt"
SERVER = (HERE / "server.txt").read_text(encoding="utf-8").strip().rstrip("/")
API = f"{SERVER}/api/desktop"
OS = platform.system()
MAX_W = 1280
NEVER_AUTO = {"executar_comando"}
DEFAULT_PERMS = {
    "permitidas": ["clicar", "digitar", "tecla", "rolar", "mover_mouse", "abrir", "executar_comando", "ver_tela", "aguardar"],
    "sem_confirmacao": ["ver_tela", "aguardar"],
}

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15

try:
    import tkinter as tk
    from tkinter import simpledialog
except Exception:
    tk = None


class Stopped(Exception):
    pass


def log(msg: str):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(p: Path, default: dict) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def ask(title: str, text: str, allow_all: bool) -> str:
    """Returns 'sim', 'nao' or 'todas'."""
    if tk is None:
        opts = "[s]im / [n]ão" + (" / [t]odas nesta tarefa" if allow_all else "")
        r = input(f"\n{title}\n{text}\n{opts}: ").strip().lower()[:1]
        return {"s": "sim", "t": "todas" if allow_all else "nao"}.get(r, "nao")
    res = {"v": "nao"}
    root = tk.Tk()
    root.title(title)
    root.attributes("-topmost", True)
    root.resizable(False, False)
    tk.Label(root, text=text, justify="left", wraplength=520, padx=18, pady=14, font=("Segoe UI", 10)).pack()
    row = tk.Frame(root, padx=12, pady=12)
    row.pack()

    def pick(v):
        res["v"] = v
        root.destroy()

    tk.Button(row, text="Permitir", width=12, command=lambda: pick("sim")).pack(side="left", padx=4)
    if allow_all:
        tk.Button(row, text="Permitir todas nesta tarefa", command=lambda: pick("todas")).pack(side="left", padx=4)
    tk.Button(row, text="Negar", width=12, command=lambda: pick("nao")).pack(side="left", padx=4)
    root.protocol("WM_DELETE_WINDOW", lambda: pick("nao"))
    root.after(120000, lambda: pick("nao"))
    root.lift()
    root.focus_force()
    root.mainloop()
    return res["v"]


def ask_code() -> str:
    msg = "Digite o código de 6 dígitos gerado no Adam (Extensões → Computador):"
    if tk is None:
        return input(msg + " ").strip()
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    code = simpledialog.askstring("Parear com o Adam", msg, parent=root) or ""
    root.destroy()
    return code.strip()


class Agent:
    def __init__(self):
        self.cfg = load_json(CONFIG, {})
        if not PERMS.exists():
            PERMS.write_text(json.dumps(DEFAULT_PERMS, indent=2, ensure_ascii=False), encoding="utf-8")
        self.perms = load_json(PERMS, DEFAULT_PERMS)
        self.scale = 1.0
        self.http = requests.Session()

    def h(self):
        return {"X-Device-Token": self.cfg.get("token", "")}

    def pair(self):
        while not self.cfg.get("token"):
            code = ask_code()
            if not code:
                sys.exit("Pareamento cancelado.")
            r = self.http.post(f"{API}/pair", json={"code": code, "name": platform.node() or "Meu PC", "os": f"{OS} {platform.release()}"}, timeout=30)
            if r.status_code != 200:
                log(f"Falha no pareamento: {r.json().get('detail', r.text)}")
                continue
            self.cfg = {"token": r.json()["token"], "device_id": r.json()["device_id"]}
            CONFIG.write_text(json.dumps(self.cfg), encoding="utf-8")
            log(f"Pareado como '{r.json()['name']}'.")

    def screen(self) -> dict:
        img = pyautogui.screenshot()
        w, h = img.size
        self.scale = w / MAX_W if w > MAX_W else 1.0
        if self.scale != 1.0:
            img = img.resize((MAX_W, round(h / self.scale)))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=60)
        return {"image": base64.b64encode(buf.getvalue()).decode(), "width": img.size[0], "height": img.size[1], "os": OS}

    def xy(self, a):
        return round(int(a["x"]) * self.scale), round(int(a["y"]) * self.scale)

    def keys(self, combo: str):
        alias = {"win": "command" if OS == "Darwin" else "win", "cmd": "command", "ctrl": "ctrl", "control": "ctrl",
                 "enter": "enter", "esc": "esc", "escape": "esc", "del": "delete", "pgdn": "pagedown", "pgup": "pageup"}
        parts = [alias.get(p.strip().lower(), p.strip().lower()) for p in combo.replace(" ", "").split("+") if p.strip()]
        pyautogui.hotkey(*parts)

    def open_target(self, alvo: str):
        if alvo.startswith(("http://", "https://")):
            webbrowser.open(alvo)
        elif OS == "Windows":
            try:
                os.startfile(alvo)
            except OSError:
                subprocess.Popen(alvo, shell=True)
        elif OS == "Darwin":
            subprocess.Popen(["open", alvo] if os.path.exists(alvo) else ["open", "-a", alvo])
        else:
            subprocess.Popen(["xdg-open", alvo] if os.path.exists(alvo) else alvo, shell=not os.path.exists(alvo))

    def run_cmd(self, cmd: str) -> str:
        args = ["powershell", "-NoProfile", "-Command", cmd] if OS == "Windows" else ["bash", "-lc", cmd]
        p = subprocess.run(args, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
        return (f"(código {p.returncode})\n" + (p.stdout or "") + (p.stderr or ""))[-3000:]

    def execute(self, name: str, a: dict) -> str:
        if name == "clicar":
            x, y = self.xy(a)
            pyautogui.click(x, y, clicks=2 if a.get("duplo") else 1, button="right" if a.get("botao") == "direito" else "left")
        elif name == "mover_mouse":
            pyautogui.moveTo(*self.xy(a), duration=0.2)
        elif name == "digitar":
            pyperclip.copy(a.get("texto", ""))
            pyautogui.hotkey("command" if OS == "Darwin" else "ctrl", "v")
        elif name == "tecla":
            self.keys(a.get("teclas", ""))
        elif name == "rolar":
            n = max(1, min(20, int(a.get("quantidade") or 5)))
            pyautogui.scroll((-1 if a.get("direcao") == "baixo" else 1) * n * 100)
        elif name == "abrir":
            self.open_target(a.get("alvo", ""))
        elif name == "executar_comando":
            return self.run_cmd(a.get("comando", ""))
        elif name == "aguardar":
            time.sleep(max(1, min(30, int(a.get("segundos") or 2))))
        elif name != "ver_tela":
            raise ValueError(f"Ação desconhecida: {name}")
        return ""

    def describe(self, name: str, a: dict) -> str:
        shown = {k: v for k, v in a.items() if k != "motivo"}
        return f"Ação: {name}\nDetalhes: {json.dumps(shown, ensure_ascii=False)[:600]}\n\nMotivo: {a.get('motivo', '—')}"

    def stopped(self, tid: str) -> bool:
        r = self.http.get(f"{API}/device/tasks/{tid}/status", headers=self.h(), timeout=30)
        return r.status_code != 200 or r.json().get("status") != "running"

    def run_task(self, t: dict):
        tid = t["id"]
        log(f"Tarefa recebida: {t['task']}")
        if ask("Adam — nova tarefa", f"O Adam quer executar esta tarefa no seu computador:\n\n{t['task']}\n\n"
               "Ele vai ver capturas da sua tela e pedir permissão antes de cada ação.\n"
               "Parada de emergência: leve o mouse ao canto superior esquerdo da tela, feche esta janela "
               "(Ctrl+C) ou clique em Parar no Adam.", False) != "sim":
            self.http.post(f"{API}/device/tasks/{tid}/reject", headers=self.h(), timeout=30)
            log("Tarefa recusada.")
            return
        r = self.http.post(f"{API}/device/tasks/{tid}/start", headers=self.h(), json={"screen": self.screen()}, timeout=180).json()
        auto_all = False
        while r.get("action"):
            act = r["action"]
            name, a = act["name"], act.get("args") or {}
            if r.get("message"):
                log(f"Adam: {r['message']}")
            result = {"action": {"name": name, "args": {k: v for k, v in a.items() if k != "motivo"}}}
            if name not in self.perms.get("permitidas", []):
                result["denied"] = True
                log(f"NEGADA (fora da lista permitida): {name} {a}")
            else:
                auto = name not in NEVER_AUTO and (auto_all or name in self.perms.get("sem_confirmacao", []))
                choice = "sim" if auto else ask("Adam — pedir permissão", self.describe(name, a), name not in NEVER_AUTO)
                if choice == "todas":
                    auto_all = True
                if choice == "nao":
                    result["denied"] = True
                    log(f"NEGADA pelo usuário: {name} {a}")
                elif self.stopped(tid):
                    raise Stopped()
                else:
                    try:
                        out = self.execute(name, a)
                        if out:
                            result["output"] = out
                        log(f"EXECUTADA: {name} {a}")
                        time.sleep(0.8)
                    except pyautogui.FailSafeException:
                        raise
                    except Exception as e:
                        result["error"] = str(e)
                        log(f"ERRO: {name}: {e}")
            if not result.get("denied"):
                result["screen"] = self.screen()
            r = self.http.post(f"{API}/device/tasks/{tid}/step", headers=self.h(),
                               json={"tool_call_id": act["id"], "result": result}, timeout=180).json()
        if r.get("stopped"):
            raise Stopped()
        log(f"Concluída: {r.get('message') or r.get('detail', '')}")

    def loop(self):
        self.pair()
        log(f"Adam Desktop conectado a {SERVER}. Aguardando tarefas… (Ctrl+C para sair)")
        while True:
            try:
                r = self.http.get(f"{API}/device/poll", headers=self.h(), timeout=30)
                if r.status_code == 401:
                    log("Este PC foi desconectado do Adam. Pareie novamente.")
                    CONFIG.unlink(missing_ok=True)
                    self.cfg = {}
                    self.pair()
                    continue
                t = r.json().get("task")
                if t:
                    try:
                        self.run_task(t)
                    except Stopped:
                        log("Tarefa parada (botão de emergência).")
                    except pyautogui.FailSafeException:
                        log("PARADA DE EMERGÊNCIA: mouse no canto da tela.")
                        self.http.post(f"{API}/device/tasks/{t['id']}/reject", headers=self.h(), json={"reason": "failsafe"}, timeout=30)
                        time.sleep(3)
            except requests.RequestException as e:
                log(f"Sem conexão com o Adam ({e.__class__.__name__}). Tentando de novo…")
                time.sleep(5)
            time.sleep(3)


if __name__ == "__main__":
    try:
        Agent().loop()
    except KeyboardInterrupt:
        log("Adam Desktop encerrado pelo usuário.")
