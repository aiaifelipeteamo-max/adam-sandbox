import { useCallback, useEffect, useState } from "react";
import { Download, KeyRound, Monitor, OctagonX, Send, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { BACKEND_URL, errMsg, useApi } from "@/lib/api";
import PageHeader from "@/components/adam/PageHeader";

const card = "p-5 rounded-xl bg-[#2A2A2A] border border-white/[0.07]";
const STATUS = { queued: "Na fila", running: "Executando", done: "Concluída", stopped: "Parada", error: "Erro" };
const STEPS = [
  <>Baixe o <code className="text-zinc-100">adam-desktop.zip</code> e extraia em uma pasta.</>,
  <>Windows: dois cliques em <b>Iniciar-Adam.bat</b>. macOS/Linux: rode <code className="text-zinc-100">./iniciar.sh</code>.</>,
  <>Clique em <b>Gerar código</b> abaixo e digite o código no programa.</>,
  <>Mande uma tarefa. O programa pede sua permissão antes de cada ação e registra tudo em <code className="text-zinc-100">adam_log.txt</code>.</>,
];

function Pairing({ api, onChange }) {
  const [code, setCode] = useState(null);
  const gen = async () => {
    try { setCode((await api.post("/desktop/pair-code")).data.code); onChange(); } catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <div className={card}>
      <p className="font-display mb-1">Parear um computador</p>
      <p className="text-xs text-zinc-500 mb-4">O código vale 10 minutos e só funciona uma vez.</p>
      {code && <p className="font-mono text-3xl tracking-[0.3em] mb-4" data-testid="desktop-pair-code">{code}</p>}
      <button onClick={gen} data-testid="desktop-generate-code-button" className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/15 text-sm">
        <KeyRound className="w-4 h-4" /> {code ? "Gerar outro código" : "Gerar código"}
      </button>
    </div>
  );
}

function TaskLog({ t, onStop }) {
  const live = t.status === "queued" || t.status === "running";
  return (
    <div className={card} data-testid={`desktop-task-${t.id}`}>
      <div className="flex items-start gap-3 mb-3">
        <p className="flex-1 text-sm">{t.task}</p>
        <span className={`text-xs px-2 py-0.5 rounded ${live ? "bg-amber-500/15 text-amber-300" : "bg-white/5 text-zinc-400"}`} data-testid={`desktop-task-status-${t.id}`}>{STATUS[t.status] || t.status}</span>
        {live && <button onClick={() => onStop(t.id)} data-testid={`desktop-task-stop-${t.id}`} className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 hover:bg-rose-500/30">Parar</button>}
      </div>
      <div className="space-y-1 max-h-56 overflow-y-auto scroll-thin text-xs font-mono text-zinc-400">
        {t.logs.slice(1).map((l, i) => (
          <p key={i} className={l.kind === "adam" || l.kind === "done" ? "text-zinc-200" : l.kind === "error" ? "text-rose-300" : ""}>
            <span className="text-zinc-600">{new Date(l.t).toLocaleTimeString()} </span>{l.text}
          </p>
        ))}
        {live && <p className="text-zinc-500">Aguardando o computador…</p>}
      </div>
    </div>
  );
}

export default function DesktopPage() {
  const api = useApi();
  const [devices, setDevices] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [device, setDevice] = useState("");
  const [task, setTask] = useState("");
  const load = useCallback(async () => {
    try {
      const [d, t] = await Promise.all([api.get("/desktop/devices"), api.get("/desktop/tasks")]);
      setDevices(d.data); setTasks(t.data);
      setDevice((cur) => cur || d.data[0]?.id || "");
    } catch (e) { /* silent poll */ }
  }, [api]);
  useEffect(() => { load(); const i = setInterval(load, 2500); return () => clearInterval(i); }, [load]);

  const download = async () => {
    try {
      const r = await api.get("/desktop/download", { params: { server: BACKEND_URL }, responseType: "blob" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(r.data); a.download = "adam-desktop.zip"; a.click();
    } catch (e) { toast.error(errMsg(e)); }
  };
  const send = async (e) => {
    e.preventDefault();
    if (!task.trim() || !device) return;
    try { await api.post("/desktop/tasks", { device_id: device, task }); setTask(""); load(); } catch (err) { toast.error(errMsg(err)); }
  };
  const stop = async (id) => { await api.post(`/desktop/tasks/${id}/stop`).catch(() => {}); load(); };
  const stopAll = async () => { const r = await api.post("/desktop/stop-all"); toast.success(`${r.data.stopped} tarefa(s) parada(s)`); load(); };
  const remove = async (id) => { await api.delete(`/desktop/devices/${id}`).catch((e) => toast.error(errMsg(e))); setDevice(""); load(); };
  const online = (d) => Date.now() - new Date(d.last_seen).getTime() < 20000;

  return (
    <div className="flex-1 overflow-y-auto scroll-thin">
      <div className="max-w-5xl mx-auto px-5 sm:px-8 py-10">
        <PageHeader eyebrow="Desktop Agent · Windows, macOS, Linux" title="O Adam no seu computador"
          subtitle="Um pequeno programa no seu PC faz a ponte com o Adam: ele vê a tela, usa mouse, teclado, programas e o navegador — sempre pedindo sua permissão antes de cada ação.">
          <button onClick={download} data-testid="desktop-download-button"
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white text-black text-sm font-medium hover:bg-zinc-200 transition-colors">
            <Download className="w-4 h-4" /> Baixar Adam Desktop
          </button>
        </PageHeader>
        <ol className="grid sm:grid-cols-2 gap-3 mb-8" data-testid="desktop-steps">
          {STEPS.map((s, i) => (
            <li key={i} className="flex gap-4 p-4 rounded-xl bg-[#2A2A2A] border border-white/[0.07] text-sm text-zinc-300">
              <span className="font-mono text-zinc-100 w-6 shrink-0">{String(i + 1).padStart(2, "0")}</span><span>{s}</span>
            </li>
          ))}
        </ol>
        <div className="grid md:grid-cols-2 gap-3 mb-8">
          <Pairing api={api} onChange={load} />
          <div className={card} data-testid="desktop-devices">
            <p className="font-display mb-3">Computadores pareados</p>
            {devices.length === 0 && <p className="text-xs text-zinc-500">Nenhum ainda.</p>}
            {devices.map((d) => (
              <div key={d.id} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0" data-testid={`desktop-device-${d.id}`}>
                <Monitor className="w-4 h-4 text-zinc-400" />
                <div className="flex-1 text-sm">{d.name}<p className="text-xs text-zinc-500">{d.os}</p></div>
                <span className={`w-2 h-2 rounded-full ${online(d) ? "bg-emerald-400" : "bg-zinc-600"}`} title={online(d) ? "Online" : "Offline"} />
                <button onClick={() => remove(d.id)} data-testid={`desktop-device-remove-${d.id}`} className="p-1.5 rounded hover:bg-white/10" title="Desconectar"><Trash2 className="w-4 h-4 text-zinc-400" /></button>
              </div>
            ))}
          </div>
        </div>
        <form onSubmit={send} className="flex flex-col sm:flex-row gap-2 mb-3">
          <select value={device} onChange={(e) => setDevice(e.target.value)} data-testid="desktop-device-select"
            className="px-3 py-3 rounded-xl bg-[#303030] border border-white/10 text-sm sm:w-56">
            {devices.length === 0 && <option value="">Pareie um computador</option>}
            {devices.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <input value={task} onChange={(e) => setTask(e.target.value)} placeholder="Ex.: abra o Bloco de Notas e escreva uma lista de compras"
            data-testid="desktop-task-input" className="flex-1 px-4 py-3 rounded-xl bg-[#303030] border border-white/10 outline-none focus:border-white/20 text-sm" />
          <button type="submit" disabled={!device || !task.trim()} data-testid="desktop-task-send-button"
            className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-white text-black text-sm font-medium disabled:opacity-40"><Send className="w-4 h-4" /> Enviar</button>
        </form>
        <button onClick={stopAll} data-testid="desktop-emergency-stop-button"
          className="w-full flex items-center justify-center gap-2 py-3 mb-6 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-sm font-medium transition-colors">
          <OctagonX className="w-4 h-4" /> Parar tudo (emergência)
        </button>
        <div className="space-y-3" data-testid="desktop-task-list">
          {tasks.map((t) => <TaskLog key={t.id} t={t} onStop={stop} />)}
        </div>
      </div>
    </div>
  );
}
