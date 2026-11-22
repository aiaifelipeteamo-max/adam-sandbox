import { useSearchParams } from "react-router-dom";
import VSCodePage from "@/pages/VSCodePage";
import ExtensionPage from "@/pages/ExtensionPage";
import DesktopPage from "@/pages/DesktopPage";

const TABS = [["vscode", "VS Code"], ["chrome", "Chrome"], ["pc", "Computador"]];

export default function ExtensionsPage() {
  const [params, setParams] = useSearchParams();
  const tab = ["chrome", "pc"].includes(params.get("tab")) ? params.get("tab") : "vscode";
  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="shrink-0 pl-14 md:pl-8 pr-5 pt-4 flex items-center gap-4">
        <h1 className="text-[15px] font-medium" data-testid="extensions-title">Extensões</h1>
        <div className="flex gap-1 p-1 rounded-lg bg-[#2A2A2A]" data-testid="extensions-tabs">
          {TABS.map(([k, l]) => (
            <button key={k} onClick={() => setParams({ tab: k })} data-testid={`extensions-tab-${k}`}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${tab === k ? "bg-[#424242] text-white" : "text-zinc-400 hover:text-white"}`}>{l}</button>
          ))}
        </div>
      </div>
      {tab === "vscode" ? <VSCodePage /> : tab === "chrome" ? <ExtensionPage /> : <DesktopPage />}
    </div>
  );
}
