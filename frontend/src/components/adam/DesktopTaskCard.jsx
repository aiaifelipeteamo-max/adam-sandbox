import { useEffect, useState } from "react";
import { Monitor, OctagonX } from "lucide-react";
import { useApi } from "@/lib/api";

const STATUS = { queued: "Na fila", running: "Executando", done: "Concluída", stopped: "Parada", error: "Erro" };
const isLive = (t) => t && (t.status === "queued" || t.status === "running");

function LiveScreen({ api, taskId, live }) {
  const [img, setImg] = useState(null);
  useEffect(() => {
    let alive = true;
    const load = () => api.get(`/desktop/tasks/${taskId}/screen`).then((r) => alive && r.data.image && setImg(r.data)).catch(() => {});
    load();
    if (!live) return () => { alive = false; };
    const i = setInterval(load, 2500);
    return () => { alive = false; clearInterval(i); };
  }, [api, taskId, live]);
  if (!img) return live ? <div className="aspect-video rounded-lg bg-black/30 grid place-items-center text-xs text-zinc-500 mb-3" data-testid={`desktop-screen-empty-${taskId}`}>Aguardando a primeira captura do PC…</div> : null;
  return (
    <div className="relative mb-3" data-testid={`desktop-screen-${taskId}`}>
      <img src={`data:image/jpeg;base64,${img.image}`} alt="Tela do computador" className="w-full rounded-lg border border-white/10" />
      <span className="absolute top-2 left-2 text-[10px] px-1.5 py-0.5 rounded bg-black/70 text-zinc-300">
        {live && <span className="inline-block w-1.5 h-1.5 rounded-full bg-rose-500 mr-1 animate-pulse" />}{new Date(img.at).toLocaleTimeString()}
      </span>
    </div>
  );
}

export default function DesktopTaskCard({ task, taskId, compact }) {
  const api = useApi();
  const [own, setOwn] = useState(null);
  const t = task || own;
  const id = taskId || task?.id;
  useEffect(() => {
    if (task) return;
    let alive = true, timer;
    const load = () => api.get(`/desktop/tasks/${id}`).then((r) => {
      if (!alive) return;
      setOwn(r.data);
      if (isLive(r.data)) timer = setTimeout(load, 2500);
    }).catch(() => {});
    load();
    return () => { alive = false; clearTimeout(timer); };
  }, [api, id, task]);
  const [showScreen, setShowScreen] = useState(!compact);
  if (!t) return null;
  const live = isLive(t);
  const stop = () => api.post(`/desktop/tasks/${t.id}/stop`).catch(() => {});
  const logs = t.logs.slice(1);
  return (
    <div className="p-4 rounded-xl bg-[#2A2A2A] border border-white/[0.07] w-full" data-testid={`desktop-task-${t.id}`}>
      <div className="flex items-start gap-3 mb-3">
        <Monitor className="w-4 h-4 text-zinc-400 mt-0.5 shrink-0" />
        <p className="flex-1 text-sm">{t.task}</p>
        <span className={`text-xs px-2 py-0.5 rounded shrink-0 ${live ? "bg-amber-500/15 text-amber-300" : "bg-white/5 text-zinc-400"}`} data-testid={`desktop-task-status-${t.id}`}>{STATUS[t.status] || t.status}</span>
        {live && <button onClick={stop} data-testid={`desktop-task-stop-${t.id}`} className="flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 shrink-0"><OctagonX className="w-3 h-3" /> Parar</button>}
      </div>
      {showScreen ? <LiveScreen api={api} taskId={t.id} live={live} /> : (
        <button onClick={() => setShowScreen(true)} data-testid={`desktop-task-show-screen-${t.id}`} className="text-xs text-zinc-400 hover:text-white mb-2">Ver tela</button>
      )}
      <div className={`space-y-1 overflow-y-auto scroll-thin text-xs font-mono text-zinc-400 ${compact ? "max-h-32" : "max-h-56"}`}>
        {(compact ? logs.slice(-6) : logs).map((l, i) => (
          <p key={i} className={l.kind === "adam" || l.kind === "done" ? "text-zinc-200" : l.kind === "error" ? "text-rose-300" : ""}>
            <span className="text-zinc-600">{new Date(l.t).toLocaleTimeString()} </span>{l.text}
          </p>
        ))}
        {live && <p className="text-zinc-500">{t.status === "queued" ? "Aguardando o Adam Desktop no PC…" : "Trabalhando… aprove as ações no seu PC."}</p>}
      </div>
    </div>
  );
}
