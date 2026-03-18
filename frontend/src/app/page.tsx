
"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/services/api";


type FeatureMode = 
  | "archaeology"    
  | "socratic"       
  | "shadow"         
  | "resonance"      
  | "contagion"      
  | "memory";        

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  feature?: FeatureMode;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

type GenericRecord = Record<string, unknown>;
type APIShape = {
  data?: unknown;
  demo_mode?: boolean;
};

const FEATURES: { id: FeatureMode; label: string; icon: string; color: string; description: string }[] = [
  { id: "archaeology", label: "🔍 Archaeology", icon: "🔍", color: "blue", description: "When did I last feel this confused?" },
  { id: "socratic", label: "👻 Socratic", icon: "👻", color: "purple", description: "Question my misconceptions" },
  { id: "shadow", label: "👤 Shadow", icon: "👤", color: "green", description: "Predict my next struggle" },
  { id: "resonance", label: "🔗 Resonance", icon: "🔗", color: "orange", description: "Find hidden connections" },
  { id: "contagion", label: "🌐 Contagion", icon: "🌐", color: "pink", description: "Learn from peer patterns" },
  { id: "memory", label: "🧠 Memory", icon: "🧠", color: "indigo", description: "View what you remember" },
];

const FEATURE_ACCENTS: Record<FeatureMode, { ring: string; soft: string }> = {
  archaeology: { ring: "ring-cyan-300/35", soft: "bg-cyan-400/10 text-cyan-100" },
  socratic: { ring: "ring-violet-300/35", soft: "bg-violet-400/10 text-violet-100" },
  shadow: { ring: "ring-emerald-300/35", soft: "bg-emerald-400/10 text-emerald-100" },
  resonance: { ring: "ring-amber-300/35", soft: "bg-amber-400/10 text-amber-100" },
  contagion: { ring: "ring-rose-300/35", soft: "bg-rose-400/10 text-rose-100" },
  memory: { ring: "ring-indigo-300/35", soft: "bg-indigo-400/10 text-indigo-100" },
};

const QUICK_PROMPTS: Record<FeatureMode, string[]> = {
  archaeology: [
    "I keep missing recursion base cases",
    "I get confused with dynamic programming states",
    "Why do I mix up BFS and DFS?",
  ],
  socratic: [
    "I think recursion is just looping",
    "Binary search works on any list",
    "Memoization and tabulation are the same",
  ],
  shadow: [
    "Predict my next weak area",
    "What am I likely to struggle with this week?",
    "Show early warning signs from my pattern",
  ],
  resonance: [
    "Find links between recursion and trees",
    "How does graph thinking relate to DP?",
    "Connect sorting intuition to greedy methods",
  ],
  contagion: [
    "base_case_missing",
    "stack_overflow",
    "off_by_one",
  ],
  memory: [
    "Refresh my memory profile",
    "Show latest study memories",
    "What patterns are stored for me?",
  ],
};

export default function ChatPage() {
  const [activeFeature, setActiveFeature] = useState<FeatureMode>("archaeology");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastDemoMode, setLastDemoMode] = useState<boolean | null>(null);
  const [backendState, setBackendState] = useState<"checking" | "online" | "offline">("checking");
  const [context, setContext] = useState<{ topic?: string; confusion?: number; errorPattern?: string }>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

 
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  
  useEffect(() => {
    setMessages([{
      id: "welcome",
      role: "system",
      content: `🧠 **Cogni** — Your Metacognitive Study Companion\n\nSelect a feature above to start. I remember your learning journey and adapt to how *you* learn.`,
      timestamp: new Date()
    }]);
  }, []);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await api.health();
        setBackendState("online");
      } catch {
        setBackendState("offline");
      }
    };
    checkBackend();
  }, []);

  const handleSend = async () => {
    const requiresInput = ["archaeology", "socratic", "resonance", "contagion"].includes(activeFeature);
    if ((requiresInput && !input.trim()) || loading) return;

    if (requiresInput) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: input,
        feature: activeFeature,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
    }
    setInput("");
    setLoading(true);

    try {
      let response;

      switch (activeFeature) {
        case "archaeology":
       
          const topic = context.topic || extractTopic(input);
          const confusion = context.confusion || 3;
          response = await api.getArchaeology(topic, confusion);
          break;

        case "socratic":
          const concept = context.topic || extractTopic(input);
          response = await api.askSocratic(concept, input);
          break;

        case "shadow":
          response = await api.getShadowPrediction(7);
          break;

        case "resonance":
          const resonanceTopic = context.topic || extractTopic(input);
          response = await api.getResonance(resonanceTopic);
          break;

        case "contagion":
          const pattern = context.errorPattern || extractErrorPattern(input);
          response = await api.getContagion(pattern);
          break;

        case "memory":
          response = await api.getMemories(10);
          break;

        default:
          response = { data: { result: { recommendation: "Select a feature to get started!" } } };
      }

      if (typeof response?.demo_mode === "boolean") {
        setLastDemoMode(response.demo_mode);
      }

      
      const assistantMessage = formatResponse(response, activeFeature);

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: assistantMessage.content,
        feature: activeFeature,
        timestamp: new Date(),
        metadata: assistantMessage.metadata
      }]);

    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "⚠️ Sorry, I encountered an error. Please try again.",
        feature: activeFeature,
        timestamp: new Date()
      }]);
      console.error("API Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleContextUpdate = (key: string, value: string | number) => {
    setContext(prev => ({ ...prev, [key]: value }));
  };

  const clearChat = () => {
    setMessages([{
      id: "welcome",
      role: "system",
      content: `🧠 Chat cleared. Select a feature to continue.`,
      timestamp: new Date()
    }]);
    setContext({});
  };

  const handleQuickPrompt = (prompt: string) => {
    if (activeFeature === "shadow" || activeFeature === "memory") {
      void handleSend();
      return;
    }
    if (activeFeature === "contagion") {
      setContext((prev) => ({ ...prev, errorPattern: prompt }));
    }
    if (activeFeature === "archaeology" || activeFeature === "socratic" || activeFeature === "resonance") {
      setContext((prev) => ({ ...prev, topic: extractTopic(prompt) }));
    }
    setInput(prompt);
  };

  return (
    <div className="study-shell min-h-[100dvh] px-2 py-2 sm:px-4 sm:py-4 md:px-8 md:py-8">
      <div className={`mx-auto flex h-[96dvh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl border border-slate-200/20 bg-slate-950/65 shadow-2xl backdrop-blur-xl ring-1 ${FEATURE_ACCENTS[activeFeature].ring} transition-all duration-300 md:h-[90vh] md:rounded-3xl`}>
        <header className="border-b border-slate-700/60 bg-slate-900/60 px-4 py-4 md:px-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-slate-100 md:text-2xl">Cogni Study Companion</h1>
              <p className="mt-1 hidden text-sm text-slate-300 sm:block">A single learning cockpit with memory-aware assistance.</p>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className={`rounded-full border px-3 py-1 ${
                backendState === "online"
                  ? "border-emerald-400/40 bg-emerald-500/15 text-emerald-200"
                  : backendState === "offline"
                    ? "border-rose-400/40 bg-rose-500/15 text-rose-200"
                    : "border-slate-500/40 bg-slate-800/70 text-slate-200"
              }`}>
                Backend: {backendState === "checking" ? "Checking" : backendState === "online" ? "Online" : "Offline"}
              </span>
              <span className={`rounded-full border px-3 py-1 ${lastDemoMode === false ? "border-emerald-400/40 bg-emerald-500/15 text-emerald-200" : "border-amber-400/40 bg-amber-500/15 text-amber-200"}`}>
                {lastDemoMode === null ? "Mode Pending" : lastDemoMode === false ? "Live Memory" : "Demo Fallback"}
              </span>
              <span className="rounded-full border border-slate-500/40 bg-slate-800/70 px-3 py-1 text-slate-200">
                {loading ? "Thinking" : "Ready"}
              </span>
            </div>
          </div>
        </header>

        <div className="border-b border-slate-700/60 bg-slate-900/50 px-3 py-3 md:px-4">
          <div className="no-scrollbar flex snap-x snap-mandatory gap-2 overflow-x-auto">
            {FEATURES.map((feature) => {
              const isActive = activeFeature === feature.id;
              return (
                <button
                  key={feature.id}
                  onClick={() => setActiveFeature(feature.id)}
                  aria-pressed={isActive}
                  className={`shrink-0 snap-start whitespace-nowrap rounded-full border px-4 py-2 text-sm transition-all ${
                    isActive
                      ? "border-cyan-300/50 bg-cyan-300/20 text-cyan-100"
                      : "border-slate-500/40 bg-slate-800/70 text-slate-300 hover:bg-slate-700/80"
                  }`}
                >
                  <span className="mr-1">{feature.icon}</span>
                  <span>{feature.label.replace(feature.icon, "").trim()}</span>
                </button>
              );
            })}
          </div>
          <div className="mt-2 flex items-center justify-between gap-2">
            <p className="text-xs text-slate-400">{FEATURES.find((f) => f.id === activeFeature)?.description}</p>
            <span className={`rounded-full px-2 py-1 text-[11px] ${FEATURE_ACCENTS[activeFeature].soft}`}>
              Active: {FEATURES.find((f) => f.id === activeFeature)?.label.replace(FEATURES.find((f) => f.id === activeFeature)?.icon || "", "").trim()}
            </span>
          </div>
        </div>

        <div className="border-b border-slate-700/60 bg-slate-900/30 px-4 py-3 md:px-6">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            {(activeFeature === "archaeology" || activeFeature === "socratic" || activeFeature === "resonance") && (
              <div>
                <label className="text-xs uppercase tracking-wide text-slate-400">Topic</label>
                <input
                  type="text"
                  value={context.topic || ""}
                  onChange={(e) => handleContextUpdate("topic", e.target.value)}
                  placeholder="e.g., recursion"
                  className="mt-1 w-full rounded-lg border border-slate-500/40 bg-slate-900/90 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-300/60"
                />
              </div>
            )}

            {activeFeature === "archaeology" && (
              <div>
                <label className="text-xs uppercase tracking-wide text-slate-400">Confusion: {context.confusion || 3}/5</label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={context.confusion || 3}
                  onChange={(e) => handleContextUpdate("confusion", Number(e.target.value))}
                  className="mt-2 w-full"
                />
              </div>
            )}

            {activeFeature === "contagion" && (
              <div>
                <label className="text-xs uppercase tracking-wide text-slate-400">Error Pattern</label>
                <select
                  value={context.errorPattern || "base_case_missing"}
                  onChange={(e) => handleContextUpdate("errorPattern", e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-500/40 bg-slate-900/90 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-300/60"
                >
                  <option value="base_case_missing">Base Case Missing</option>
                  <option value="stack_overflow">Stack Overflow</option>
                  <option value="off_by_one">Off-by-One</option>
                </select>
              </div>
            )}

            <div className="flex items-end md:justify-end">
              <button
                onClick={clearChat}
                className="w-full rounded-lg border border-slate-500/40 bg-slate-800/70 px-3 py-2 text-sm text-slate-200 transition hover:bg-slate-700 md:w-auto"
              >
                Clear Chat
              </button>
            </div>
          </div>
        </div>

        <main className="flex-1 overflow-y-auto px-3 py-4 md:px-6 md:py-5">
          <div className="space-y-4">
            {messages.length <= 1 && !loading && (
              <div className="rounded-2xl border border-slate-600/40 bg-slate-900/45 p-4">
                <h3 className="text-sm font-semibold text-slate-100">Quick Start</h3>
                <p className="mt-1 text-xs text-slate-400">Tap any prompt to start faster with realistic study companion flows.</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {QUICK_PROMPTS[activeFeature].map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => handleQuickPrompt(prompt)}
                      className="rounded-full border border-slate-500/40 bg-slate-800/70 px-3 py-1.5 text-xs text-slate-200 transition hover:bg-slate-700/80"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <div className="h-2 w-2 animate-bounce rounded-full bg-cyan-300" />
                <div className="h-2 w-2 animate-bounce rounded-full bg-cyan-300 [animation-delay:120ms]" />
                <div className="h-2 w-2 animate-bounce rounded-full bg-cyan-300 [animation-delay:240ms]" />
                <span>Cogni is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        <div className="safe-bottom border-t border-slate-700/60 bg-slate-900/60 px-3 py-3 md:px-6 md:py-4">
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={getPlaceholder(activeFeature)}
              rows={1}
              className="flex-1 max-h-32 resize-none rounded-xl border border-slate-500/40 bg-slate-950/80 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-300/60"
              disabled={loading || activeFeature === "memory" || activeFeature === "shadow"}
            />
            <button
              onClick={handleSend}
              disabled={loading || (["archaeology", "socratic", "resonance", "contagion"].includes(activeFeature) && !input.trim())}
              className="rounded-xl bg-cyan-500 px-4 font-medium text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400 md:px-6"
            >
              {loading ? "..." : activeFeature === "memory" ? "Refresh" : activeFeature === "shadow" ? "Predict" : "Send"}
            </button>
          </div>
          <p className="mt-2 text-center text-xs text-slate-400">Press Enter to send - Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  );
}


function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="max-w-lg rounded-2xl border border-slate-600/40 bg-slate-800/65 px-4 py-3 text-center text-sm text-slate-200">
          {message.content.split("\n").map((line, i) => (
            <p key={i} className={i > 0 ? "mt-1" : ""}>{line}</p>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`message-enter flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 ${
          isUser
            ? "rounded-br-md bg-cyan-500 text-slate-950"
            : "rounded-bl-md border border-slate-600/40 bg-slate-800/70 text-slate-100"
        }`}
      >
       
        {!isUser && message.feature && (
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
            {FEATURES.find(f => f.id === message.feature)?.icon} {message.feature}
          </div>
        )}

       
        <div className="max-w-none text-sm leading-relaxed">
          {message.content.split("\n").map((line, i) => (
            <p key={i} className={i > 0 ? "mt-2" : ""}>
              {renderRichLine(line)}
            </p>
          ))}
        </div>

        
        {message.metadata && Object.keys(message.metadata).length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-600 text-xs space-y-1">
            {(() => {
              const md = message.metadata as Record<string, unknown>;
              return md.similar_moments !== undefined;
            })() && (
              <p>
                📊 Found {String((message.metadata as Record<string, unknown>).similar_moments)} similar moments
              </p>
            )}
            {(() => {
              const md = message.metadata as Record<string, unknown>;
              return md.confidence !== undefined;
            })() && (
              <p>
                🎯 Confidence: {Math.round(Number((message.metadata as Record<string, unknown>).confidence || 0) * 100)}%
              </p>
            )}
            {(() => {
              const md = message.metadata as Record<string, unknown>;
              return md.community_size !== undefined;
            })() && (
              <p>
                👥 {String((message.metadata as Record<string, unknown>).community_size)} peers with similar patterns
              </p>
            )}
            {(message.metadata as Record<string, unknown>).demo_mode === true && (
              <p className="text-yellow-400">🎭 Demo Mode response</p>
            )}
          </div>
        )}

     
        <div className="text-xs text-slate-400 mt-2 text-right">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </div>
      </div>
    </div>
  );
}

function renderRichLine(line: string): React.ReactNode {
  const parts = line.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={idx}>{part.slice(2, -2)}</strong>;
    }
    return <span key={idx}>{part}</span>;
  });
}


function formatResponse(apiResponse: APIShape, feature: FeatureMode): { content: string; metadata: Record<string, unknown> } {
  const apiData = (apiResponse.data as GenericRecord | undefined) || {};
  const data = (apiData.result as GenericRecord | undefined) || apiData;
  const metadata: Record<string, unknown> = { demo_mode: apiResponse.demo_mode };

  switch (feature) {
    case "archaeology":
      const similarMoments = Number(data.similar_moments ?? 0);
      const whatHelped = Array.isArray(data.what_helped_before) ? (data.what_helped_before as GenericRecord[]) : [];
      metadata.similar_moments = similarMoments;
      metadata.confidence = whatHelped[0]?.confidence;
      
      let content = "";
      if (similarMoments > 0) {
        content = `📚 Found **${similarMoments}** similar moments in your history.\n\n`;
        if (whatHelped.length) {
          content += `✨ **What helped before**:\n`;
          whatHelped.forEach((item) => {
            const confidence = Number(item.confidence ?? 0);
            content += `• ${String(item.hint_used ?? "unknown")} (${Math.round(confidence * 100)}% confidence)\n`;
          });
          content += `\n💡 **Recommendation**: ${String(data.recommendation ?? "")}`;
        }
      } else {
        content = `📭 No similar moments found yet. Keep studying to build your learning profile!`;
      }
      return { content, metadata };

    case "socratic":
      return {
        content: `🤔 ${data.question || "Let's explore this together. What's the simplest case you can think of?"}`,
        metadata: {
          resolved_count: (data.past_history as GenericRecord | undefined)?.resolved_count,
          unresolved_count: (data.past_history as GenericRecord | undefined)?.unresolved_count
        }
      };

    case "shadow":
      metadata.confidence = data.confidence;
      const evidence = Array.isArray(data.evidence) ? (data.evidence as string[]) : [];
      return {
        content: `🔮 **Prediction**: ${String(data.prediction ?? "No prediction available yet.")}\n\n📋 **Evidence**:\n${evidence.map((e) => `• ${e}`).join("\n") || "Based on your learning patterns"}`,
        metadata
      };

    case "resonance":
      const hiddenConnections = Array.isArray(data.hidden_connections) ? (data.hidden_connections as GenericRecord[]) : [];
      return {
        content: `🔗 **Hidden Connections for "${String(data.topic || "your topic")}"**:\n\n${hiddenConnections.map((c) => `• **${String(c.topic ?? "topic").replace(/_/g, " ")}** (${Math.round(Number(c.strength ?? 0) * 100)}%): ${String(c.reason ?? "No reason available")}`).join("\n") || "No connections found yet."}\n\n💡 ${String(data.insight || "")}`,
        metadata: { connection_count: hiddenConnections.length }
      };

    case "contagion":
      metadata.community_size = data.community_size;
      metadata.success_rate = data.success_rate;
      const strategies = Array.isArray(data.additional_strategies) ? (data.additional_strategies as GenericRecord[]) : [];
      return {
        content: `🌐 **Community Insights**:\n\n🏆 **Top Strategy**: ${String(data.top_strategy ?? "unknown").replace(/_/g, " ")}\n✅ Success Rate: ${Math.round(Number(data.success_rate || 0) * 100)}%\n👥 Based on ${Number(data.community_size || 0)} students with similar patterns\n\n📋 **More Strategies**:\n${strategies.map((s) => `• ${String(s.strategy ?? "unknown")} (${Math.round(Number(s.success_rate ?? 0) * 100)}%)`).join("\n") || "No additional strategies available."}\n\n🔒 ${String(data.privacy_note || "")}`,
        metadata
      };

    case "memory":
      const memories = Array.isArray(apiData.memories) ? (apiData.memories as GenericRecord[]) : [];
      if (memories.length === 0) {
        return { content: "📭 No memories found yet. Start studying to build your cognitive profile!", metadata };
      }
      return {
        content: `🧠 **Your Memory Profile** (${memories.length} entries):\n\n${memories.slice(0, 5).map((m) => {
          const ctx = (m.context as GenericRecord | undefined) || {};
          const topic = String(ctx.topic || ctx.concept || "Untitled");
          const confidence = Math.round(Number(m.confidence || 0.8) * 100);
          return `• **${topic}**\n  ${String(m.content || "No content") }\n  🎯 Confidence: ${confidence}%\n`;
        }).join("\n")}${memories.length > 5 ? `\n...and ${memories.length - 5} more` : ""}`,
        metadata: { memory_count: memories.length }
      };

    default:
      return { content: "Select a feature to get started!", metadata };
  }
}


function extractTopic(message: string): string {
  const keywords = ["recursion", "dynamic programming", "binary tree", "graph", "sorting", "algorithm", "function", "loop"];
  const lower = message.toLowerCase();
  for (const kw of keywords) {
    if (lower.includes(kw)) return kw;
  }
  return "recursion"; 
}


function extractErrorPattern(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("base") || lower.includes("missing")) return "base_case_missing";
  if (lower.includes("stack") || lower.includes("overflow")) return "stack_overflow";
  if (lower.includes("off by one") || lower.includes("index")) return "off_by_one";
  return "base_case_missing"; 
}


function getPlaceholder(feature: FeatureMode): string {
  const placeholders: Record<FeatureMode, string> = {
    archaeology: "Describe what you're confused about (e.g., 'I don't get recursion base cases')...",
    socratic: "Share your current understanding or misconception...",
    shadow: "Ask about upcoming challenges or request a prediction...",
    resonance: "Enter a topic to find hidden conceptual connections...",
    contagion: "Describe an error pattern you're struggling with...",
    memory: "Memory view is read-only. Select another feature to chat."
  };
  return placeholders[feature];
}