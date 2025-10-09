import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import {
  Menu,
  Send,
  Mic,
  MicOff,
  Moon,
  Sun,
  Trash2,
  History,
  X,
  Plus,
} from "lucide-react";

/**
 * Claude‑style, modern chat UI — fully responsive for mobile & desktop
 * Drop-in replacement for your current App.tsx
 *
 * Requires packages:
 *   npm i framer-motion react-markdown rehype-highlight highlight.js lucide-react
 *
 * Tailwind is assumed to be configured. Keep your index.css/tailwind.css as-is.
 */

// ---------- Types ----------
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: number;
}

type ProfileId = "krishna" | "tejuu";

interface ProfileCfg {
  id: ProfileId;
  name: string;
  title: string;
  color: string; // Tailwind bg-
  initials: string;
}

const PROFILES: ProfileCfg[] = [
  { id: "krishna", name: "Krishna", title: "Data Engineer & ML", color: "bg-blue-600", initials: "KS" },
  { id: "tejuu", name: "Tejuu", title: "Business Analyst & BI", color: "bg-pink-600", initials: "TJ" },
];

const PROFILE_MODES: Record<ProfileId, { id: string; name: string }[]> = {
  krishna: [
    { id: "de", name: "Data Engineering" },
    { id: "ai", name: "AI/ML/GenAI" },
  ],
  tejuu: [
    { id: "bi", name: "Business Intelligence" },
    { id: "ae", name: "Analytics Engineer" },
  ],
};

// ---------- Helpers ----------
const API_URL = (process.env.REACT_APP_API_URL || "http://localhost:8000").replace(/\/$/, "");
const cls = (...xs: (string | false | undefined)[]) => xs.filter(Boolean).join(" ");
const welcome = (p: ProfileId, mode: string) =>
  `Hello ${PROFILES.find(x => x.id === p)?.name}! I'm Kish — your ${
    p === "krishna" 
      ? (mode === "ai" ? "AI/ML/GenAI" : "Data Engineer") 
      : (mode === "ae" ? "Analytics Engineer" : "Business Intelligence")
  } assistant. How can I help today?`;

export default function App() {
  // Theme & layout
  const [dark, setDark] = useState<boolean>(() => localStorage.getItem("ragTheme") === "dark");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // App state
  const [profile, setProfile] = useState<ProfileId>("krishna");
  const [modeByProfile, setModeByProfile] = useState<Record<ProfileId, string>>({ krishna: "de", tejuu: "ae" });
  const [messagesByProfile, setMessagesByProfile] = useState<Record<ProfileId, Message[]>>({ krishna: [], tejuu: [] });
  const [conversationsByProfile, setConversationsByProfile] = useState<Record<ProfileId, { title: string; messages: Message[]; ts: number }[]>>({ krishna: [], tejuu: [] });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Audio
  const [rec, setRec] = useState<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);

  // Refs
  const endRef = useRef<HTMLDivElement>(null);

  // Init
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("ragTheme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    try {
      const savedChats = JSON.parse(localStorage.getItem("ragChatHistory") || "null");
      const savedConvs = JSON.parse(localStorage.getItem("ragConversations") || "null");
      if (savedChats) setMessagesByProfile(savedChats);
      if (savedConvs) setConversationsByProfile(savedConvs);
    } catch {}
  }, []);

  const activeMessages = messagesByProfile[profile] || [];
  const activeMode = modeByProfile[profile];
  const activeConversations = conversationsByProfile[profile] || [];
  const activeProfileCfg = useMemo(() => PROFILES.find(p => p.id === profile)!, [profile]);

  // Ensure welcome message exists per profile
  useEffect(() => {
    if (activeMessages.length === 0) {
      const m: Message = { id: String(Date.now()), role: "assistant", content: welcome(profile, activeMode), ts: Date.now() };
      setMessagesByProfile(prev => ({ ...prev, [profile]: [m] }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messagesByProfile, loading]);
  useEffect(() => { localStorage.setItem("ragChatHistory", JSON.stringify(messagesByProfile)); }, [messagesByProfile]);
  useEffect(() => { localStorage.setItem("ragConversations", JSON.stringify(conversationsByProfile)); }, [conversationsByProfile]);

  // Actions
  const clearChat = () => {
    const umsgs = activeMessages.filter(m => m.role === "user");
    if (umsgs.length) {
      const titleSrc = umsgs[0].content.trim();
      const title = titleSrc.length > 60 ? titleSrc.slice(0, 60) + "…" : titleSrc || `Conversation ${new Date().toLocaleString()}`;
      setConversationsByProfile(prev => ({
        ...prev,
        [profile]: [{ title, messages: activeMessages, ts: Date.now() }, ...(prev[profile] || [])].slice(0, 12)
      }));
    }
    const w: Message = { id: String(Date.now()), role: "assistant", content: welcome(profile, activeMode), ts: Date.now() };
    setMessagesByProfile(prev => ({ ...prev, [profile]: [w] }));
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    const user: Message = { id: String(Date.now()), role: "user", content: text, ts: Date.now() };
    setInput("");
    setMessagesByProfile(prev => ({ ...prev, [profile]: [...(prev[profile] || []), user] }));
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, mode: activeMode, profile }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      const bot: Message = { id: String(Date.now() + 1), role: "assistant", content: data.answer || "(no content)", ts: Date.now() };
      setMessagesByProfile(prev => ({ ...prev, [profile]: [...(prev[profile] || []), bot] }));
    } catch (e) {
      const err: Message = { id: String(Date.now() + 1), role: "assistant", content: "Sorry, something went wrong. Please try again.", ts: Date.now() };
      setMessagesByProfile(prev => ({ ...prev, [profile]: [...(prev[profile] || []), err] }));
    } finally {
      setLoading(false);
    }
  };

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
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
      mr.start();
      setRec(mr);
      setRecording(true);
    } catch (e) {
      alert("Microphone access denied");
    }
  };
  const stopRecording = () => { rec?.stop(); setRecording(false); };

  const transcribe = async (blob: Blob) => {
    setTranscribing(true);
    try {
      const fd = new FormData();
      fd.append("audio_file", blob, "recording.webm");
      const r = await fetch(`${API_URL}/api/transcribe`, { method: "POST", body: fd });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      const text = String(data.transcript || "").trim();
      if (text) {
        setInput(text);
        setTranscribing(false); // Clear transcribing state first
        setTimeout(() => send(), 100); // Small delay to ensure state is updated
      } else {
        setTranscribing(false);
      }
    } catch (e) {
      alert("Transcription failed. Please try again.");
      setTranscribing(false);
    }
  };

  const loadConversation = (idx: number) => {
    const conv = activeConversations[idx];
    if (!conv) return;
    setMessagesByProfile(prev => ({ ...prev, [profile]: conv.messages }));
    setSidebarOpen(false);
  };
  const deleteConversation = (idx: number) => setConversationsByProfile(prev => ({
    ...prev,
    [profile]: (prev[profile] || []).filter((_, i) => i !== idx)
  }));

  // UI atoms
  const MacChrome = () => (
    <div className={cls("h-6 px-3 flex items-center", dark ? "bg-[#2A2A2A]" : "bg-gray-100")}>      
      <span className="w-3 h-3 rounded-full bg-red-500 mr-1.5" />
      <span className="w-3 h-3 rounded-full bg-yellow-500 mr-1.5" />
      <span className="w-3 h-3 rounded-full bg-green-500" />
    </div>
  );

  const TypingDots = () => (
    <div className="flex items-center gap-1">
      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" />
      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "0.12s" }} />
      <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "0.24s" }} />
    </div>
  );

  return (
    <div className={cls("min-h-screen w-full", dark ? "bg-gray-900" : "bg-gray-50")}>      
      <MacChrome />

      {/* Mobile header */}
      <div className={cls("md:hidden w-full border-b flex items-center justify-between px-3 py-2",
        dark ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200")}
      >
        <div className="flex items-center gap-2">
          <button onClick={() => setSidebarOpen(true)} className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]", dark ? "bg-gray-600 text-white" : "bg-gray-100 text-gray-700")} aria-label="Open menu"> <Menu className="w-5 h-5"/> </button>
          <div className="flex items-center gap-2">
            <div className={cls("w-10 h-10 rounded-full flex items-center justify-center shadow-lg", activeProfileCfg.color)}>
              <span className="text-white text-sm font-bold">{activeProfileCfg.initials}</span>
            </div>
            <div>
              <div className={cls("text-sm font-semibold", dark ? "text-white" : "text-gray-900")}>{activeProfileCfg.name}</div>
              <div className={cls("text-xs", dark ? "text-gray-400" : "text-gray-600")}>{PROFILE_MODES[profile].find(m => m.id === activeMode)?.name}</div>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-center gap-3">
          <button onClick={() => setDark(d => !d)} className={cls("p-2 rounded-md min-w-[44px] min-h-[44px] flex items-center justify-center", dark ? "bg-gray-600 text-white" : "bg-gray-100 text-gray-700")} aria-label="Toggle theme">{dark ? <Sun className="w-5 h-5"/> : <Moon className="w-5 h-5"/>}</button>
          <button onClick={clearChat} className={cls("p-2 rounded-md min-w-[44px] min-h-[44px] flex items-center justify-center", dark ? "bg-gray-600 text-white" : "bg-gray-100 text-gray-700")} aria-label="New chat"><Plus className="w-5 h-5"/></button>
          </div>
        </div>
        
      {/* App Shell */}
      <div className={cls("flex w-full", "h-[calc(100vh-3rem)] md:h-[calc(100vh-1.5rem)]")}>        
        {/* Sidebar (desktop) */}
        <aside className={cls(
          "hidden md:flex flex-col w-72 lg:w-80 xl:w-96 border-r shrink-0",
          dark ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200"
        )}>
          {/* Brand */}
          <div className={cls("p-4 border-b", dark ? "border-gray-700" : "border-gray-200")}>            
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 flex items-center justify-center text-xl">🤖</div>
              <h1 className={cls("font-semibold", dark ? "text-white" : "text-gray-900")}>Kish RagAIChatbot</h1>
              </div>
            </div>
            
          {/* Profile selector */}
          <div className="p-4 space-y-2">
            <label className={cls("text-xs", dark ? "text-gray-400" : "text-gray-600")}>Profile</label>
              <select 
              value={profile}
              onChange={(e) => setProfile(e.target.value as ProfileId)}
              className={cls(
                "w-full rounded-md px-3 py-2 text-sm border",
                dark ? "bg-gray-700 border-gray-600 text-white" : "bg-white border-gray-300"
              )}
            >
              {PROFILES.map(p => (
                <option key={p.id} value={p.id}>{p.name} — {p.title}</option>
                ))}
              </select>

            <label className={cls("text-xs", dark ? "text-gray-400" : "text-gray-600")}>Mode</label>
            <div className="grid grid-cols-2 gap-2">
              {PROFILE_MODES[profile].map(m => (
                  <button
                  key={m.id}
                  onClick={() => setModeByProfile(prev => ({ ...prev, [profile]: m.id }))}
                  className={cls(
                    "px-3 py-2 rounded-md text-xs text-left",
                    activeMode === m.id
                      ? dark ? "bg-gray-700 text-white" : "bg-blue-100 text-blue-700"
                      : dark ? "hover:bg-gray-700 text-gray-300" : "hover:bg-gray-100 text-gray-700"
                  )}
                >{m.name}</button>
                ))}
              </div>
            </div>
            
          {/* Recent conversations */}
          <div className="flex-1 overflow-y-auto px-3 pb-3">
            <div className={cls("text-xs px-1 py-2", dark ? "text-gray-400" : "text-gray-600")}>Recent</div>
                <div className="space-y-1">
              {activeConversations.length === 0 && (
                <div className={cls("text-xs px-2", dark ? "text-gray-500" : "text-gray-500")}>No conversations yet</div>
              )}
              {activeConversations.map((c, i) => (
                <div key={i} className={cls("group flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer",
                  dark ? "hover:bg-gray-700 text-gray-200" : "hover:bg-gray-100 text-gray-800")}
                  onClick={() => loadConversation(i)}
                >
                  <History className="w-4 h-4 shrink-0" />
                  <div className="text-xs truncate flex-1">{c.title}</div>
                      <button
                    onClick={(e) => { e.stopPropagation(); deleteConversation(i); }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20"
                    title="Delete"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-red-400" />
                      </button>
                    </div>
                  ))}
              </div>
            </div>
            
        </aside>

        {/* Main column */}
        <main className="flex-1 flex flex-col min-w-0">          
          {/* Desktop header */}
          <div className={cls("hidden md:flex items-center justify-between px-5 py-3 border-b",
            dark ? "bg-gray-900 border-gray-700" : "bg-gray-50 border-gray-200")}
          >
            <div className="flex items-center gap-3">
              <div className={cls("w-12 h-12 rounded-full flex items-center justify-center shadow-lg", activeProfileCfg.color)}>
                <span className="text-white text-base font-bold">{activeProfileCfg.initials}</span>
                </div>
              <div>
                <div className={cls("text-sm font-semibold", dark ? "text-white" : "text-gray-900")}>Chat with {activeProfileCfg.name}</div>
                <div className={cls("text-xs", dark ? "text-gray-400" : "text-gray-600")}>{activeProfileCfg.title} — {PROFILE_MODES[profile].find(m => m.id === activeMode)?.name}</div>
              </div>
                    </div>
            <div className="flex items-center gap-2">
                        <button
                onClick={() => setDark(d => !d)}
                className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]", dark ? "bg-gray-600 hover:bg-gray-500 text-white" : "bg-gray-100 hover:bg-gray-200 text-gray-700")}
                title={dark ? "Light" : "Dark"}
                aria-label="Toggle theme"
              >{dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}</button>
              <button onClick={clearChat} className={cls("p-2 rounded-md min-w-[44px] min-h-[44px] flex items-center justify-center",
                dark ? "bg-gray-600 hover:bg-gray-500 text-white" : "bg-gray-100 hover:bg-gray-200 text-gray-700")} aria-label="New chat"><Plus className="w-4 h-4"/></button>
                    </div>
                  </div>

          {/* Messages */}
          <div className={cls("flex-1 overflow-y-auto px-3 sm:px-4 lg:px-6 py-3", dark ? "bg-gray-900" : "bg-gray-50")}>            
            <div className="mx-auto w-full max-w-4xl xl:max-w-5xl 2xl:max-w-6xl space-y-4">
              {activeMessages.map(m => (
                <motion.div key={m.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }} className="flex items-start gap-3">
                  <div className={cls("w-10 h-10 rounded-full shrink-0 flex items-center justify-center shadow-md",
                    m.role === "user" ? activeProfileCfg.color : (dark ? "bg-gray-700" : "bg-gray-100"))}
                  >
                    {m.role === "user" ? (
                      <span className="text-white text-sm font-bold">{activeProfileCfg.initials}</span>
                    ) : (
                      <div className="w-10 h-10 flex items-center justify-center text-2xl">🤖</div>
                    )}
                  </div>

                  {/* Bubble */}
                  <div className={cls(
                    "rounded-2xl px-4 py-3 w-fit",
                    "border backdrop-blur-sm shadow-sm",
                    m.role === "assistant"
                      ? dark
                        ? "bg-gray-800/90 border-gray-700 shadow-lg"
                        : "bg-white/90 border-gray-200 shadow-md"
                      : dark
                        ? "bg-gray-800/90 border-gray-700 shadow-lg"
                        : "bg-white/90 border-gray-200 shadow-md",
                    "max-w-full lg:max-w-4xl xl:max-w-5xl"
                  )}>
                    {m.role === "assistant" ? (
                      <div className={cls("prose prose-sm max-w-none", dark ? "prose-invert" : "prose-slate")}>                      
                        <ReactMarkdown rehypePlugins={[rehypeHighlight]}>{m.content}</ReactMarkdown>
                      </div>
                      ) : (
                      <p className={cls("text-sm leading-relaxed font-medium", dark ? "text-gray-100" : "text-gray-900")}>{m.content}</p>
                      )}
                    </div>
                </motion.div>
              ))}

              {loading && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 flex items-center justify-center text-2xl">🤖</div>
                  <div className={cls("rounded-2xl px-4 py-3 border backdrop-blur-sm shadow-sm",
                    dark ? "bg-gray-800/90 border-gray-700 shadow-lg" : "bg-white/90 border-gray-200 shadow-md")}>                  
                    <TypingDots />
                  </div>
                </div>
              )}
              <div ref={endRef} />
            </div>
            </div>
            
          {/* Composer */}
          <div className={cls("px-3 sm:px-4 lg:px-6 py-3 border-t", dark ? "bg-gray-900 border-gray-700" : "bg-white border-gray-200")}>            
            <div className={cls(
              "mx-auto max-w-4xl xl:max-w-5xl 2xl:max-w-6xl",
              "rounded-2xl border shadow-sm p-2",
              dark ? "bg-gray-800/90 border-gray-700" : "bg-white/90 border-gray-300"
            )}>              
              <div className="flex items-end gap-2">
                <textarea
                  rows={1}
                  value={input}
                  onChange={(e) => {
                    const el = e.currentTarget;
                    setInput(e.target.value);
                    el.style.height = "auto";
                    el.style.height = Math.min(140, el.scrollHeight) + "px";
                  }}
                  onKeyDown={onKey}
                  placeholder={`Message ${activeProfileCfg.name}…`}
                  className={cls("flex-1 resize-none bg-transparent focus:outline-none text-sm leading-6 max-h-36",
                    dark ? "text-white placeholder:text-gray-400" : "text-gray-900 placeholder:text-gray-500")}
                  style={{ fontSize: 16 }} // prevent iOS zoom
                />

                <div className="flex items-center gap-1">
                  <button
                    onClick={recording ? () => stopRecording() : () => startRecording()}
                    disabled={transcribing}
                    className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]",
                      transcribing ? "bg-yellow-600 text-white" : recording ? "bg-red-600 text-white" : dark ? "bg-gray-600 text-white hover:bg-gray-500" : "bg-gray-100 text-gray-700 hover:bg-gray-200")}
                    title={transcribing ? "Transcribing…" : recording ? "Stop recording" : "Start recording"}
                    aria-label="Record voice"
                  >
                    {transcribing ? (
                      <span className="inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : recording ? <MicOff className="w-5 h-5"/> : <Mic className="w-5 h-5"/>}
                  </button>
                  
                  <button
                    onClick={send}
                    disabled={!input.trim() || loading}
                    className={cls("px-3 py-2 rounded-md min-h-[44px] text-sm font-medium",
                      !input.trim() || loading ? "opacity-50 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 text-white")}
                    title="Send"
                    aria-label="Send message"
                  >
                    <div className="flex items-center gap-2"><Send className="w-4 h-4"/> <span className="hidden sm:inline">Send</span></div>
                  </button>
                </div>
              </div>

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
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ type: "tween", duration: 0.25 }}
              className={cls("absolute left-0 top-0 bottom-0 w-[86%] max-w-[340px] overflow-y-auto border-r",
                dark ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200")}
            >
              <div className={cls("flex items-center justify-between p-3 border-b", dark ? "border-gray-700" : "border-gray-200")}>                
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 flex items-center justify-center text-xl">🤖</div>
                  <div className="font-semibold">Kish RagAIChatbot</div>
                </div>
                <button onClick={() => setSidebarOpen(false)} className={cls("p-2 rounded-md min-w-[44px] min-h-[44px]", dark ? "bg-gray-600 text-white" : "bg-gray-100 text-gray-700")} aria-label="Close menu"><X className="w-5 h-5"/></button>
            </div>

              <div className="p-3 space-y-3">
                <div>
                  <div className={cls("text-xs mb-1", dark ? "text-gray-400" : "text-gray-600")}>Profile</div>
                  <select value={profile} onChange={(e)=>setProfile(e.target.value as ProfileId)} className={cls("w-full rounded-md px-3 py-2 text-sm border", dark ? "bg-gray-700 border-gray-600 text-white" : "bg-white border-gray-300") }>
                    {PROFILES.map(p => <option key={p.id} value={p.id}>{p.name} — {p.title}</option>)}
                  </select>
                          </div>
                <div>
                  <div className={cls("text-xs mb-1", dark ? "text-gray-400" : "text-gray-600")}>Mode</div>
                  <div className="grid grid-cols-2 gap-2">
                    {PROFILE_MODES[profile].map(m => (
                      <button key={m.id} onClick={()=>setModeByProfile(prev=>({...prev,[profile]:m.id}))} className={cls("px-3 py-2 rounded-md text-xs",
                        activeMode===m.id ? (dark?"bg-gray-700 text-white":"bg-blue-100 text-blue-700") : (dark?"text-gray-300 hover:bg-gray-700":"text-gray-700 hover:bg-gray-100"))}>{m.name}</button>
                    ))}
                          </div>
                        </div>
                <div>
                  <div className={cls("text-xs mb-1", dark ? "text-gray-400" : "text-gray-600")}>Recent</div>
                  <div className="space-y-1">
                    {activeConversations.map((c,i)=> (
                      <div key={i} onClick={()=>loadConversation(i)} className={cls("flex items-center gap-2 px-2 py-2 rounded-md",
                        dark?"hover:bg-gray-700 text-gray-200":"hover:bg-gray-100 text-gray-800")}
                      >
                        <History className="w-4 h-4"/>
                        <div className="text-xs truncate flex-1">{c.title}</div>
                        <button onClick={(e)=>{e.stopPropagation(); deleteConversation(i);}} className="p-1 rounded hover:bg-red-500/20" aria-label="Delete conversation"><Trash2 className="w-3.5 h-3.5 text-red-400"/></button>
                    </div>
                  ))}
                    {activeConversations.length===0 && <div className={cls("text-xs px-1", dark?"text-gray-500":"text-gray-500")}>No conversations</div>}
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
