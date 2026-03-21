import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export type TimelineEntry = {
  session_id: number;
  timestamp: string;
  type: string;
  source: string;
  topic: string;
  confidence: number;
  content_preview: string;
};

type MemoryTimelineProps = {
  entries: TimelineEntry[];
  loading: boolean;
};

const formatLabel = (value: string) => value.replace(/_/g, " ");

export function MemoryTimeline({ entries, loading }: MemoryTimelineProps) {
  return (
    <Card className="border-zinc-700/60 bg-zinc-950/40 transition-all duration-300">
      <CardHeader className="pb-3">
        <CardTitle className="text-zinc-100">Memory Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="h-16 rounded-lg border border-zinc-700/60 bg-zinc-900/60 animate-pulse" />
            ))}
          </div>
        ) : entries.length === 0 ? (
          <div className="rounded-lg border border-dashed border-zinc-700 p-5 text-sm text-zinc-400">
            No timeline entries yet. Start studying to see your learning history grow in real time.
          </div>
        ) : (
          <div className="max-h-[340px] space-y-3 overflow-y-auto pr-1">
            {entries.map((entry) => {
              const dateLabel = new Date(entry.timestamp).toLocaleString();
              const confidencePct = Math.round(Math.max(0, Math.min(1, entry.confidence)) * 100);
              return (
                <div
                  key={`${entry.session_id}-${entry.timestamp}`}
                  className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-3 transition-all duration-300 hover:border-purple-500/50"
                >
                  <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
                    <span className="rounded-full bg-purple-500/20 px-2 py-1 text-purple-300">
                      {formatLabel(entry.type)}
                    </span>
                    <span className="rounded-full bg-indigo-500/20 px-2 py-1 text-indigo-300">
                      {formatLabel(entry.source)}
                    </span>
                    <span className="rounded-full bg-emerald-500/20 px-2 py-1 text-emerald-300">
                      {confidencePct}% confidence
                    </span>
                  </div>
                  <p className="text-sm font-medium text-zinc-200">{formatLabel(entry.topic || "general")}</p>
                  <p className="mt-1 text-xs text-zinc-400">{entry.content_preview || "No preview available"}</p>
                  <p className="mt-2 text-[11px] text-zinc-500">{dateLabel}</p>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
