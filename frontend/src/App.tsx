// App.tsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import {
  Menu, Send, Mic, MicOff, Moon, Sun, RotateCcw, Trash2, History, X, Plus,
  Copy, Check, MoreVertical, SquarePen, ChevronDown, BookOpen
} from "lucide-react";

// ---------- Types ----------
interface Message { id: string; role: "user" | "assistant"; content: string; ts: number }
interface SourceDoc { title: string; snippet: string; url?: string; score?: number }
interface ChatAPIResponse {
  answer: string; intent?: string; confidence?: number; template?: string;
  latency_ms?: number; sources?: SourceDoc[]; citations?: number[];
  resolved_profile?: string; resolved_mode?: string;
}
type ProfileId = "auto" | "krishna" | "tejuu";
interface ProfileCfg { id: ProfileId; name: string; title: string; color: string; initials: string }

const PROFILES: ProfileCfg[] = [
  { id: "auto", name: "Auto",    title: "Auto-detect Profile",     color: "from-blue-600 to-pink-600", initials: "AI" },
  { id: "krishna", name: "Krishna", title: "Data Engineer & ML",     color: "from-blue-600 to-indigo-600", initials: "KS" },
  { id: "tejuu", name: "Tejuu",   title: "Business Analyst & BI",   color: "from-rose-600 to-fuchsia-600", initials: "TJ" },
];

const PROFILE_MODES: Record<ProfileId, { id: string; name: string }[]> = {
  auto:   [{ id: "auto", name: "Auto-detect Mode" }],
  krishna:[{ id: "de", name: "Data Engineering" }, { id: "ai", name: "AI/ML/GenAI" }, { id: "plsql", name: "Oracle PL/SQL" }],
  tejuu:  [{ id: "bi", name: "Business Intelligence" }, { id: "ae", name: "Analytics Engineer" }],
};

// ---------- Helpers ----------
const API_URL = (process.env.REACT_APP_API_URL || "http://localhost:8000").replace(/\/$/, "");
const cls = (...xs: (string | false | undefined)[]) => xs.filter(Boolean).join(" ");
const welcome = (p: ProfileId, mode: string) =>
  p === "auto"
    ? `Hey, I’m Kish. Ask me anything—I'll auto-detect if you need DE, AI/ML, BI, or AE help.`
    : `Hey! I’m Kish—your ${p === "krishna" ? (mode === "ai" ? "AI/ML" : mode === "plsql" ? "Oracle PL/SQL" : "Data Engineering") : (mode === "ae" ? "Analytics Engineering" : "BI")} assistant. How can I help today?`;

function useLocalStorage<T>(key: string, init: T) {
  const [v, setV] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) as T : init;
    } catch (error) {
      console.warn(`Failed to parse localStorage value for key "${key}":`, error);
      return init;
    }
  });
  useEffect(() => { localStorage.setItem(key, JSON.stringify(v)); }, [key, v]);
  return [v, setV] as const;
}

export default function App() {
  // Clean up any invalid localStorage entries on app start
  useEffect(() => {
    const keys = ["ragThemeBool", "ragProfile", "ragModeByProfile", "ragMessagesByProfileMode", "ragConversationsByProfileMode"];
    keys.forEach(key => {
      try {
        const value = localStorage.getItem(key);
        if (value && value !== "null") {
          JSON.parse(value);
        }
      } catch {
        console.warn(`Clearing invalid localStorage entry for key "${key}"`);
        localStorage.removeItem(key);
      }
    });
  }, []);

  // Theme
  const [dark, setDark] = useLocalStorage("ragThemeBool", window.matchMedia?.("(prefers-color-scheme: dark)").matches);
  useEffect(() => { document.documentElement.classList.toggle("dark", Boolean(dark)); }, [dark]);

  // Shell
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);

  // Core state
  const [profile, setProfile] = useLocalStorage<ProfileId>("ragProfile", "auto");
  const [modeByProfile, setModeByProfile] = useLocalStorage<Record<ProfileId, string>>("ragModeByProfile", { auto: "auto", krishna: "de", tejuu: "ae" });
  const [messagesByKey, setMessagesByKey] = useLocalStorage<Record<string, Message[]>>("ragMessagesByProfileMode", {});
  const [convosByKey, setConvosByKey] = useLocalStorage<Record<string, { title: string; messages: Message[]; ts: number }[]>>("ragConversationsByProfileMode", {});
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Media
  const [rec, setRec] = useState<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);

  // Meta
  const [lastMeta, setLastMeta] = useState<{ intent?: string; confidence?: number; template?: string; latencyMs?: number } | null>(null);
  const [lastSources, setLastSources] = useState<SourceDoc[]>([]);

  // Derived
  const activeMode = modeByProfile[profile];
  const key = `${profile}-${activeMode}`;
  const messages = messagesByKey[key] || [];
  const conversations = convosByKey[key] || [];
  const cfg = useMemo(() => PROFILES.find(p => p.id === profile)!, [profile]);

  // Ensure a welcome and close sources when switching contexts
  useEffect(() => {
    if ((messagesByKey[key] || []).length === 0) {
      const m: Message = { id: String(Date.now()), role: "assistant", content: welcome(profile, activeMode), ts: Date.now() };
      setMessagesByKey(prev => ({ ...prev, [key]: [m] }));
    }
    // Close sources panel when switching profiles/modes
    setSourcesOpen(false);
    // eslint-disable-next-line
  }, [key]);

  // Scroll to bottom on new messages
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messagesByKey, loading]);

  // Keyboard shortcuts
  useEffect(() => {
    const onDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const ta = document.querySelector<HTMLTextAreaElement>("#composer");
        ta?.focus();
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "enter") {
        e.preventDefault();
        send();
      }
    };
    window.addEventListener("keydown", onDown);
    return () => window.removeEventListener("keydown", onDown);
  }, [input, loading]);

  // Actions
  const clearChat = () => {
    const u = (messages || []).find(m => m.role === "user");
    const titleSrc = u?.content?.trim() || `Conversation ${new Date().toLocaleString()}`;
    const title = titleSrc.length > 60 ? titleSrc.slice(0, 60) + "…" : titleSrc;
    if (messages.length > 1) {
      setConvosByKey(prev => ({ ...prev, [key]: [{ title, messages, ts: Date.now() }, ...(prev[key] || [])].slice(0, 16) }));
    }
    const w: Message = { id: String(Date.now()), role: "assistant", content: welcome(profile, activeMode), ts: Date.now() };
    setMessagesByKey(prev => ({ ...prev, [key]: [w] }));
    setLastSources([]);
    setLastMeta(null);
    setSourcesOpen(false);
  };

  const copyToClipboard = async (txt: string) => {
    try { await navigator.clipboard.writeText(txt); return true } catch { return false }
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    const user: Message = { id: String(Date.now()), role: "user", content: text, ts: Date.now() };
    setInput("");
    setMessagesByKey(prev => ({ ...prev, [key]: [...(prev[key] || []), user] }));
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, mode: activeMode, profile, session_id: "default" })
      });
      if (!r.ok) throw new Error(await r.text());
      const data: ChatAPIResponse = await r.json();
      const bot: Message = { id: String(Date.now() + 1), role: "assistant", content: data.answer || "(no content)", ts: Date.now() };
      setMessagesByKey(prev => ({ ...prev, [key]: [...(prev[key] || []), bot] }));

      setLastMeta({ intent: data.intent, confidence: data.confidence, template: data.template, latencyMs: data.latency_ms });
      setLastSources(data.sources || []);

      if (data.resolved_profile && data.resolved_mode) {
        setProfile(data.resolved_profile as ProfileId);
        setModeByProfile(prev => ({ ...prev, [data.resolved_profile as ProfileId]: data.resolved_mode! }));
      }
    } catch {
      const err: Message = { id: String(Date.now() + 1), role: "assistant", content: "Sorry, something went wrong. Please try again.", ts: Date.now() };
      setMessagesByKey(prev => ({ ...prev, [key]: [...(prev[key] || []), err] }));
    } finally {
      setLoading(false);
    }
  };

  const sendWithText = async (textToSend: string) => {
    const text = textToSend.trim();
    if (!text || loading) return;
    const user: Message = { id: String(Date.now()), role: "user", content: text, ts: Date.now() };
    setInput("");
    setMessagesByKey(prev => ({ ...prev, [key]: [...(prev[key] || []), user] }));
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, mode: activeMode, profile, session_id: "default" })
      });
      if (!r.ok) throw new Error(await r.text());
      const data: ChatAPIResponse = await r.json();
      const bot: Message = { id: String(Date.now() + 1), role: "assistant", content: data.answer || "(no content)", ts: Date.now() };
      setMessagesByKey(prev => ({ ...prev, [key]: [...(prev[key] || []), bot] }));

      setLastMeta({ intent: data.intent, confidence: data.confidence, template: data.template, latencyMs: data.latency_ms });
      setLastSources(data.sources || []);

      if (data.resolved_profile && data.resolved_mode) {
        setProfile(data.resolved_profile as ProfileId);
        setModeByProfile(prev => ({ ...prev, [data.resolved_profile as ProfileId]: data.resolved_mode! }));
      }
    } catch {
      const err: Message = { id: String(Date.now() + 1), role: "assistant", content: "Sorry, something went wrong. Please try again.", ts: Date.now() };
      setMessagesByKey(prev => ({ ...prev, [key]: [...(prev[key] || []), err] }));
    } finally {
      setLoading(false);
    }
  };

  const removeMessage = (id: string) =>
    setMessagesByKey(prev => ({ ...prev, [key]: (prev[key] || []).filter(m => m.id !== id) }));

  const regenerateFrom = async (idx: number) => {
    const priorUser = (messages[idx]?.role === "user" ? messages[idx] : messages.slice(0, idx).reverse().find(m => m.role === "user"));
    if (!priorUser) return;
    setInput(priorUser.content);
    setTimeout(() => send(), 0);
  };

  // Audio
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];
      mr.ondataavailable = (ev) => chunks.push(ev.data);
      mr.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        await transcribe(blob);
        stream.getTracks().forEach(t => t.stop());
      };
      mr.start(); setRec(mr); setRecording(true);
    } catch { alert("Microphone access denied"); }
  };
  const stopRecording = () => { rec?.stop(); setRecording(false); };

  const transcribe = async (blob: Blob) => {
    console.log("🎤 Starting transcription...", blob.size, "bytes");
    setTranscribing(true);
    try {
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64 = reader.result?.toString().split(',')[1];
          console.log("📤 Sending to transcribe API...", base64?.length, "chars");
          const res = await fetch(`${API_URL}/api/transcribe`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ audio_data: base64 }) });
          console.log("📥 Transcribe response:", res.status, res.ok);
          if (!res.ok) {
            const errorText = await res.text();
            console.error("❌ Transcribe error:", errorText);
            throw new Error(errorText);
          }
          const data = await res.json();
          console.log("📝 Transcribe data:", data);
          const text = String(data.transcript || "").trim();
          console.log("📝 Transcribed text:", text, "length:", text.length);
          if (!text) { 
            console.log("⚠️ Empty transcript, not sending");
            setTranscribing(false); 
            return; 
          }
          setTranscribing(false);
          setInput(text);
          console.log("✅ Setting input and sending...");
          // Send immediately with the transcribed text
          sendWithText(text);
        } catch (e) { 
          console.error("❌ Transcribe error:", e); 
          alert("Transcription failed: " + (e instanceof Error ? e.message : String(e))); 
          setTranscribing(false); 
        }
      };
      reader.readAsDataURL(blob);
    } catch (e) { 
      console.error("❌ FileReader error:", e); 
      alert("Transcription failed: " + (e instanceof Error ? e.message : String(e))); 
      setTranscribing(false); 
    }
  };

  // Markdown render (preserve your behavior)
  const renderMD = (md: string) => md;

  // UI atoms
  const Badge = ({ children, tone = "gray" }: { children: React.ReactNode; tone?: "blue"|"emerald"|"amber"|"gray" }) => {
    const map: any = {
      blue: "bg-blue-600/10 text-blue-600 border-blue-600/30",
      emerald: "bg-emerald-600/10 text-emerald-500 border-emerald-600/30",
      amber: "bg-amber-600/10 text-amber-500 border-amber-600/30",
      gray: "bg-slate-600/10 text-slate-300 border-slate-600/30"
    };
    return <span className={cls("px-2 py-1 rounded-full border text-xs", map[tone])}>{children}</span>;
  };

  return (
    <div className={cls("min-h-screen w-full interface-text", dark ? "bg-surface-dark" : "bg-gray-50")}>
      {/* Top bar (mobile) */}
      <div className={cls("md:hidden sticky top-0 z-30 w-full border-b backdrop-blur supports-[backdrop-filter]:bg-white/70 dark:supports-[backdrop-filter]:bg-black/30",
        dark ? "bg-gray-900/80 border-gray-700" : "bg-white/80 border-gray-200")}>
        <div className="flex items-center justify-between px-3 py-2">
          <div className="flex items-center gap-2">
            <button onClick={() => setSidebarOpen(true)} className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]",
              dark ? "bg-gray-700 text-white" : "bg-gray-100 text-gray-800")} aria-label="Open menu"><Menu className="w-5 h-5"/></button>
            <div className="flex items-center gap-2">
              <div className={cls("w-9 h-9 rounded-full flex items-center justify-center shadow-lg text-white bg-gradient-to-r", cfg.color)}>
                <span className="text-xs font-bold">{cfg.initials}</span>
              </div>
              <div>
                <div className={cls("text-sm font-semibold", dark ? "text-white" : "text-gray-900")}>{cfg.name}</div>
                <div className={cls("text-[11px]", dark ? "text-gray-400" : "text-gray-600")}>
                  {PROFILE_MODES[profile].find(m => m.id === activeMode)?.name}
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setDark(!dark)} className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]",
              dark ? "bg-gray-700 text-white" : "bg-gray-100 text-gray-800")} aria-label="Toggle theme">
              {dark ? <Sun className="w-5 h-5"/> : <Moon className="w-5 h-5"/>}
            </button>
          </div>
        </div>
      </div>

      {/* App Shell */}
      <div className="h-[100svh] md:h-[calc(100vh-0px)] flex">
        {/* Sidebar (desktop) */}
        <aside className={cls("hidden md:flex flex-col w-78 lg:w-80 xl:w-96 border-r shrink-0",
          dark ? "bg-[#0f1115] border-gray-800" : "bg-white/90 border-gray-200 backdrop-blur")}>
          <div className={cls("p-4 border-b", dark ? "border-gray-800" : "border-gray-200")}>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 flex items-center justify-center text-xl">🤖</div>
              <h1 className={cls("font-semibold", dark ? "text-white" : "text-gray-900")}>Kish RagAIChatbot</h1>
            </div>
          </div>

          {/* Profile & Mode */}
          <div className="p-4 space-y-3">
            <div>
              <label className={cls("label-text text-xs mb-1 block", dark ? "text-gray-200" : "text-gray-800")}>Profile</label>
              <select value={profile} onChange={e => setProfile(e.target.value as ProfileId)}
                className={cls("w-full rounded-md px-3 py-2 text-sm border",
                  dark ? "bg-gray-900 border-gray-800 text-white" : "bg-white border-gray-300 text-gray-900")}>
                {PROFILES.map(p => <option key={p.id} value={p.id}>{p.name} — {p.title}</option>)}
              </select>
            </div>
            <div>
              <label className={cls("label-text text-xs mb-1 block", dark ? "text-gray-200" : "text-gray-800")}>Mode</label>
              <div className="grid grid-cols-2 gap-2">
                {PROFILE_MODES[profile].map(m => (
                  <button key={m.id}
                    onClick={() => setModeByProfile(prev => ({ ...prev, [profile]: m.id }))}
                    className={cls("px-3 py-2 rounded-md text-xs text-left transition",
                      activeMode===m.id
                        ? (dark ? "bg-gray-900 text-white border border-gray-700" : "bg-blue-50 text-blue-700 border border-blue-200")
                        : (dark ? "hover:bg-gray-900 text-gray-300 border border-transparent" : "hover:bg-gray-100 text-gray-700 border border-transparent"))}>
                    {m.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Recent */}
          <div className="flex-1 overflow-y-auto px-3 pb-4">
            <div className={cls("text-xs px-2 py-2", dark ? "text-gray-400" : "text-gray-600")}>Recent</div>
            <div className="space-y-1">
              {conversations.length === 0 && (
                <div className={cls("text-xs px-2 py-1", dark ? "text-gray-500" : "text-gray-500")}>No conversations yet</div>
              )}
              {conversations.map((c, i) => (
                <div key={i}
                  className={cls("group flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer",
                    dark ? "hover:bg-gray-900 text-gray-200" : "hover:bg-gray-100 text-gray-800")}
                  onClick={() => setMessagesByKey(prev => ({ ...prev, [key]: c.messages }))}>
                  <History className="w-4 h-4 shrink-0"/>
                  <div className="text-xs truncate flex-1">{c.title}</div>
                  <button onClick={(e) => { e.stopPropagation(); setConvosByKey(prev => ({ ...prev, [key]: (prev[key] || []).filter((_,idx)=> idx!==i) })); }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20" aria-label="Delete">
                    <Trash2 className="w-3.5 h-3.5 text-red-400"/>
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className={cls("p-3 border-t", dark ? "border-gray-800" : "border-gray-200")}>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={clearChat}
                className={cls("px-3 py-2 rounded-md text-sm flex items-center justify-center gap-2 transition",
                  dark ? "bg-gray-900 text-white hover:bg-gray-800" : "bg-gray-100 text-gray-800 hover:bg-gray-200")}>
                <RotateCcw className="w-4 h-4"/> Reset
              </button>
              <button onClick={() => {
                // Save current conversation to history before starting new chat
                const u = (messages || []).find(m => m.role === "user");
                const titleSrc = u?.content?.trim() || `Conversation ${new Date().toLocaleString()}`;
                const title = titleSrc.length > 60 ? titleSrc.slice(0, 60) + "…" : titleSrc;
                if (messages.length > 1) {
                  setConvosByKey(prev => ({ ...prev, [key]: [{ title, messages, ts: Date.now() }, ...(prev[key] || [])].slice(0, 16) }));
                }
                // Start new chat
                const w: Message = { id: String(Date.now()), role: "assistant", content: welcome(profile, activeMode), ts: Date.now() };
                setMessagesByKey(prev => ({ ...prev, [key]: [w] }));
                setLastSources([]);
                setLastMeta(null);
                setSourcesOpen(false);
              }}
                className={cls("px-3 py-2 rounded-md text-sm flex items-center justify-center gap-2 transition",
                  dark ? "bg-gray-900 text-white hover:bg-gray-800" : "bg-blue-600 text-white hover:bg-blue-700")}>
                <Plus className="w-4 h-4"/> New
              </button>
            </div>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 flex flex-col min-w-0">
          {/* Desktop header */}
          <div className={cls("hidden md:flex items-center justify-between px-5 py-3 border-b sticky top-0 z-20 backdrop-blur",
            dark ? "bg-[#0b0b0c]/70 border-gray-800" : "bg-white/70 border-gray-200")}>
            <div className="flex items-center gap-3">
              <div className={cls("w-11 h-11 rounded-full flex items-center justify-center shadow-lg text-white bg-gradient-to-r", cfg.color)}>
                <span className="text-sm font-bold">{cfg.initials}</span>
              </div>
              <div>
                <div className={cls("text-sm font-semibold", dark ? "text-white" : "text-gray-900")}>Chat with {cfg.name}</div>
                <div className={cls("text-xs", dark ? "text-gray-400" : "text-gray-600")}>
                  {cfg.title} — {PROFILE_MODES[profile].find(m => m.id === activeMode)?.name}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {lastMeta?.intent && <Badge tone="blue">intent: {lastMeta.intent}</Badge>}
              {typeof lastMeta?.confidence === "number" && <Badge tone="emerald">conf: {(lastMeta.confidence * 100).toFixed(0)}%</Badge>}
              {typeof lastMeta?.latencyMs === "number" && <Badge tone="amber">{lastMeta.latencyMs} ms</Badge>}
              <button onClick={() => setDark(!dark)}
                className={cls("p-2 rounded-md", dark ? "bg-gray-900 text-white hover:bg-gray-800" : "bg-gray-100 text-gray-800 hover:bg-gray-200")}
                aria-label="Toggle theme">
                {dark ? <Sun className="w-4 h-4"/> : <Moon className="w-4 h-4"/>}
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className={cls("flex-1 overflow-y-auto px-3 sm:px-4 lg:px-6 py-4", dark ? "bg-surface-dark" : "bg-gray-50")}>
            <div className="mx-auto w-full max-w-4xl xl:max-w-5xl space-y-4">
              {messages.map((m, idx) => (
                <motion.div key={m.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }}>
                  <div className="flex items-start gap-3 group">
                    <div className={cls("w-10 h-10 rounded-full shrink-0 flex items-center justify-center shadow",
                      m.role==="user" ? "bg-gradient-to-r from-slate-600 to-slate-800 text-white" : (dark ? "bg-gray-800" : "bg-white"))}>
                      {m.role==="assistant" ? "🤖" : <span className="text-xs font-bold">{cfg.initials}</span>}
                    </div>

                    <div className={cls(
                      "relative rounded-2xl px-4 py-3 border backdrop-blur-sm shadow-glass max-w-full lg:max-w-4xl",
                      dark ? "bg-[#111827cc] border-surface-borderDark" : "bg-white/90 border-surface-borderLight"
                    )}>
                      {/* Actions */}
                      <div className="absolute -top-2 right-2 opacity-0 group-hover:opacity-100 transition">
                        <div className="flex gap-1">
                          <button
                            onClick={async () => {
                              const ok = await copyToClipboard(m.content);
                              const el = document.getElementById(`copied-${m.id}`);
                              if (ok && el) { el.classList.remove("hidden"); setTimeout(()=>el.classList.add("hidden"), 1200); }
                            }}
                            className={cls("p-1.5 rounded-md text-xs", dark?"bg-gray-900 text-gray-300 hover:bg-gray-800":"bg-gray-100 text-gray-700 hover:bg-gray-200")}
                            aria-label="Copy message"><Copy className="w-3.5 h-3.5"/></button>
                          {m.role==="assistant" && (
                            <button
                              onClick={()=>regenerateFrom(idx)}
                              className={cls("p-1.5 rounded-md text-xs", dark?"bg-gray-900 text-gray-300 hover:bg-gray-800":"bg-gray-100 text-gray-700 hover:bg-gray-200")}
                              aria-label="Regenerate"><SquarePen className="w-3.5 h-3.5"/></button>
                          )}
                          <button onClick={()=>removeMessage(m.id)}
                            className={cls("p-1.5 rounded-md text-xs", dark?"bg-gray-900 text-gray-300 hover:bg-gray-800":"bg-gray-100 text-gray-700 hover:bg-gray-200")}
                            aria-label="Delete"><Trash2 className="w-3.5 h-3.5"/></button>
                          <span id={`copied-${m.id}`} className="hidden text-[10px] px-2 py-1 rounded-md bg-emerald-600/15 text-emerald-400">Copied</span>
                        </div>
                      </div>

                      {m.role === "assistant" ? (
                        <div className={cls("prose prose-sm max-w-none", dark ? "prose-invert" : "prose-slate")}>
                          <ReactMarkdown rehypePlugins={[rehypeHighlight]} components={{
                            a: ({ href, children, ...props }) => (
                              <a href={href} className="text-blue-500 hover:text-blue-700 underline" {...props}>{children}</a>
                            ),
                            code({inline, className, children, ...props}: any) {
                              const hasLang = /language-/.test(className || "");
                              return inline ? (
                                <code className="px-1.5 py-0.5 rounded bg-violet-500/10 border border-violet-500/20 text-violet-400" {...props}>{children}</code>
                              ) : (
                                <div className="relative">
                                  <pre className={cls("hljs rounded-md")}>
                                    <code className={className} {...props}>{children}</code>
                                  </pre>
                                  <button
                                    onClick={() => copyToClipboard(String(children))}
                                    className="absolute top-2 right-2 px-2 py-1 text-xs rounded bg-black/30 text-white hover:bg-black/50"
                                  ><Copy className="w-3.5 h-3.5 inline mr-1"/>Copy</button>
                                </div>
                              );
                            }
                          }}>
                            {renderMD(m.content)}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className={cls("text-sm leading-relaxed font-medium", dark ? "text-gray-100" : "text-gray-900")}>{m.content}</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}

              {loading && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 flex items-center justify-center text-2xl">🤖</div>
                  <div className={cls("rounded-2xl px-4 py-3 border backdrop-blur-sm shadow-sm",
                    dark ? "bg-gray-900/80 border-gray-800" : "bg-white/90 border-gray-200")}>
                    <div className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"/>
                      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{animationDelay: "0.12s"}}/>
                      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{animationDelay: "0.24s"}}/>
                    </div>
                  </div>
                </div>
              )}
              <div ref={endRef}/>
            </div>
          </div>

          {/* Bottom composer */}
          <div className={cls("px-3 sm:px-4 lg:px-6 py-3 border-t sticky bottom-0 z-10",
            dark ? "bg-[#0b0b0c]/85 border-gray-800 backdrop-blur" : "bg-white/85 border-gray-200 backdrop-blur")}>
            <div className={cls("mx-auto max-w-4xl xl:max-w-5xl rounded-2xl border shadow-glass p-2",
              dark ? "bg-[#111827cc] border-gray-800" : "bg-white/90 border-gray-200")}>
              <div className="flex items-end gap-2">
                <textarea
                  id="composer"
                  rows={1}
                  value={input}
                  onChange={(e) => {
                    const el = e.currentTarget;
                    setInput(e.target.value);
                    el.style.height = "auto"; el.style.height = Math.min(180, el.scrollHeight) + "px";
                  }}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                  placeholder={`Message ${cfg.name}…`}
                  className={cls("flex-1 resize-none bg-transparent focus:outline-none text-[15px] leading-6 max-h-44",
                    dark ? "text-white placeholder:text-gray-400" : "text-gray-900 placeholder:text-gray-500")}
                  style={{ fontSize: 16 }}
                />
                <div className="flex items-center gap-1">
                  <button
                    onClick={recording ? () => stopRecording() : () => startRecording()}
                    disabled={transcribing}
                    className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]",
                      transcribing ? "bg-amber-600 text-white" :
                      recording ? "bg-red-600 text-white" :
                      dark ? "bg-gray-900 text-white hover:bg-gray-800" : "bg-gray-100 text-gray-800 hover:bg-gray-200")}
                    aria-label="Record voice">
                    {transcribing ? <span className="inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"/> : recording ? <MicOff className="w-5 h-5"/> : <Mic className="w-5 h-5"/>}
                  </button>
                  <button
                    onClick={() => setSourcesOpen(s => !s)}
                    className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]", dark ? "bg-gray-900 text-white hover:bg-gray-800" : "bg-gray-100 text-gray-800 hover:bg-gray-200")}
                    aria-label="Toggle sources"><BookOpen className="w-5 h-5"/></button>
                  <button
                    onClick={send}
                    disabled={!input.trim() || loading}
                    className={cls("px-3 py-2 rounded-md min-h-[44px] text-sm font-medium transition",
                      !input.trim() || loading ? "opacity-50 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 text-white")}
                    aria-label="Send message">
                    <div className="flex items-center gap-2"><Send className="w-4 h-4"/><span className="hidden sm:inline">Send</span></div>
                  </button>
                </div>
              </div>

              {/* Sources tray */}
              <AnimatePresence>
                {sourcesOpen && lastSources.length > 0 && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}>
                    <div className={cls("mt-2 rounded-xl border p-3", dark ? "border-gray-800 bg-black/20" : "border-gray-200 bg-gray-50/80")}>
                      <div className="flex items-center gap-2 mb-2 text-xs font-semibold">
                        <BookOpen className="w-4 h-4"/><span>Sources</span>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-2">
                        {lastSources.map((s, i) => (
                          <a key={i} href={s.url || "#"} target="_blank" rel="noreferrer"
                             className={cls("block rounded-lg p-3 border transition",
                             dark ? "border-gray-800 hover:bg-gray-900/50" : "border-gray-200 hover:bg-white")}>
                            <div className="text-sm font-semibold line-clamp-1">
                              {s.title && s.title !== "unknown" ? s.title : 
                                (s.url ? s.url.split('/').pop()?.replace('.md', '').replace(/_/g, ' ').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : "Document")}
                            </div>
                            <div className={cls("text-xs line-clamp-2 mt-1", dark ? "text-gray-400" : "text-gray-600")}>{s.snippet}</div>
                          </a>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </main>
      </div>

      {/* Mobile Sidebar Drawer */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-40">
            <div className="absolute inset-0 bg-black/40" onClick={() => setSidebarOpen(false)} />
            <motion.aside
              initial={{ x: -320 }} animate={{ x: 0 }} exit={{ x: -320 }}
              transition={{ type: "tween", duration: 0.22 }}
              className={cls("absolute left-0 top-0 bottom-0 w-[86%] max-w-[340px] overflow-y-auto border-r",
                dark ? "bg-[#0f1115] border-gray-800" : "bg-white border-gray-200")}
            >
              <div className={cls("flex items-center justify-between p-3 border-b", dark ? "border-gray-800" : "border-gray-200")}>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 flex items-center justify-center text-xl">🤖</div>
                  <div className={cls("font-semibold", dark ? "text-white" : "text-gray-900")}>Kish RagAIChatbot</div>
                </div>
                <button onClick={() => setSidebarOpen(false)} className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]",
                  dark ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-800")} aria-label="Close menu"><X className="w-5 h-5"/></button>
              </div>

              <div className="p-3 space-y-3">
                <div>
                  <div className={cls("text-xs mb-1", dark ? "text-gray-400" : "text-gray-600")}>Profile</div>
                  <select value={profile} onChange={(e)=>setProfile(e.target.value as ProfileId)}
                    className={cls("w-full rounded-md px-3 py-2 text-sm border", dark ? "bg-gray-900 border-gray-800 text-white" : "bg-white border-gray-300 text-gray-900") }>
                    {PROFILES.map(p => <option key={p.id} value={p.id}>{p.name} — {p.title}</option>)}
                  </select>
                </div>
                <div>
                  <div className={cls("text-xs mb-1", dark ? "text-gray-400" : "text-gray-600")}>Mode</div>
                  <div className="grid grid-cols-2 gap-2">
                    {PROFILE_MODES[profile].map(m => (
                      <button key={m.id} onClick={()=>setModeByProfile(prev=>({...prev,[profile]:m.id}))}
                        className={cls("px-3 py-2 rounded-md text-xs",
                          activeMode===m.id ? (dark?"bg-gray-900 text-white border border-gray-800":"bg-blue-50 text-blue-700 border border-blue-200")
                          : (dark?"text-gray-300 hover:bg-gray-900":"text-gray-700 hover:bg-gray-100"))}>
                        {m.name}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className={cls("text-xs mb-1", dark ? "text-gray-400" : "text-gray-600")}>Recent</div>
                  <div className="space-y-1">
                    {conversations.map((c,i)=> (
                      <div key={i} onClick={()=>{setMessagesByKey(prev=>({...prev,[key]:c.messages})); setSidebarOpen(false)}}
                           className={cls("flex items-center gap-2 px-2 py-2 rounded-md",
                           dark?"hover:bg-gray-900 text-gray-200":"hover:bg-gray-100 text-gray-800")}>
                        <History className="w-4 h-4"/>
                        <div className="text-xs truncate flex-1">{c.title}</div>
                        <button onClick={(e)=>{e.stopPropagation(); setConvosByKey(prev=>({...prev,[key]:(prev[key]||[]).filter((_,idx)=>idx!==i)}));}}
                                className="p-1 rounded hover:bg-red-500/20" aria-label="Delete">
                          <Trash2 className="w-3.5 h-3.5 text-red-400"/>
                        </button>
                      </div>
                    ))}
                    {conversations.length===0 && <div className={cls("text-xs px-1", dark?"text-gray-500":"text-gray-500")}>No conversations</div>}
                  </div>
                </div>
              </div>
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
