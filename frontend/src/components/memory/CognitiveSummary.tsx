import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export type LearningProfile = {
  strengths: string[];
  weaknesses: string[];
  interests: string[];
  patterns: string[];
  total_sessions: number;
  topics_studied: number;
  average_confidence: number;
};

type CognitiveSummaryProps = {
  summary: string;
  profile: LearningProfile | null;
  loading: boolean;
};

const pretty = (value: string) => value.replace(/_/g, " ");

function renderPills(items: string[], tone: "green" | "rose" | "indigo") {
  if (!items.length) {
    return <span className="text-xs text-zinc-500">No signals yet</span>;
  }

  const classes =
    tone === "green"
      ? "bg-emerald-500/20 text-emerald-300"
      : tone === "rose"
      ? "bg-rose-500/20 text-rose-300"
      : "bg-indigo-500/20 text-indigo-300";

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span key={item} className={`rounded-full px-2 py-1 text-xs ${classes}`}>
          {pretty(item)}
        </span>
      ))}
    </div>
  );
}

export function CognitiveSummary({ summary, profile, loading }: CognitiveSummaryProps) {
  const confidencePct = profile ? Math.round(Math.max(0, Math.min(1, profile.average_confidence)) * 100) : 0;

  return (
    <Card className="border-zinc-700/60 bg-zinc-950/40 transition-all duration-300">
      <CardHeader className="pb-3">
        <CardTitle className="text-zinc-100">What Cogni Knows About You</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="space-y-3">
            <div className="h-16 rounded-lg border border-zinc-700/60 bg-zinc-900/60 animate-pulse" />
            <div className="h-16 rounded-lg border border-zinc-700/60 bg-zinc-900/60 animate-pulse" />
            <div className="h-16 rounded-lg border border-zinc-700/60 bg-zinc-900/60 animate-pulse" />
          </div>
        ) : !summary ? (
          <div className="rounded-lg border border-dashed border-zinc-700 p-5 text-sm text-zinc-400">
            No profile summary yet. Interact with Cogni to build your cognitive profile.
          </div>
        ) : (
          <>
            <div className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-4 text-sm leading-relaxed text-zinc-300 whitespace-pre-line">
              {summary}
            </div>

            {profile && (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-3">
                  <p className="mb-2 text-xs uppercase tracking-wide text-zinc-400">Strengths</p>
                  {renderPills(profile.strengths, "green")}
                </div>
                <div className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-3">
                  <p className="mb-2 text-xs uppercase tracking-wide text-zinc-400">Growth Areas</p>
                  {renderPills(profile.weaknesses, "rose")}
                </div>
                <div className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-3">
                  <p className="mb-2 text-xs uppercase tracking-wide text-zinc-400">Interests</p>
                  {renderPills(profile.interests, "indigo")}
                </div>
                <div className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-3 text-xs text-zinc-300">
                  <p className="uppercase tracking-wide text-zinc-400 mb-2">Snapshot</p>
                  <p>Sessions: {profile.total_sessions}</p>
                  <p>Topics: {profile.topics_studied}</p>
                  <p>Average confidence: {confidencePct}%</p>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
