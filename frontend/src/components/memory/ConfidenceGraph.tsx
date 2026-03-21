import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";

export type ConfidencePoint = {
  session_index: number;
  timestamp: string;
  confidence: number;
};

export type ConfidenceSeries = {
  topic: string;
  sessions_studied: number;
  current_confidence: number;
  improvement: number;
  avg_quiz_score_ratio?: number | null;
  mastery_score?: number;
  weak_signal_count?: number;
  performance_label?: string;
  points: ConfidencePoint[];
};

type ConfidenceGraphProps = {
  series: ConfidenceSeries[];
  loading: boolean;
};

const pretty = (value: string) => value.replace(/_/g, " ");
const COLORS = ["#22d3ee", "#a78bfa", "#34d399", "#f472b6", "#f59e0b", "#60a5fa"];

function buildCombinedSeries(series: ConfidenceSeries[]) {
  const byIndex: Record<number, Record<string, number | string>> = {};

  series.slice(0, 6).forEach((topicSeries) => {
    topicSeries.points.forEach((point) => {
      const idx = point.session_index;
      if (!byIndex[idx]) {
        byIndex[idx] = { session: `S${idx}` };
      }
      byIndex[idx][topicSeries.topic] = Math.round(Math.max(0, Math.min(1, point.confidence)) * 100);
    });
  });

  return Object.keys(byIndex)
    .map((idx) => Number(idx))
    .sort((a, b) => a - b)
    .map((idx) => byIndex[idx]);
}

function buildTopicPoints(points: ConfidencePoint[]) {
  return points.map((point) => ({
    session: `S${point.session_index}`,
    confidence: Math.round(Math.max(0, Math.min(1, point.confidence)) * 100),
  }));
}

export function ConfidenceGraph({ series, loading }: ConfidenceGraphProps) {
  return (
    <Card className="border-zinc-700/60 bg-zinc-950/40 transition-all duration-300">
      <CardHeader className="pb-3">
        <CardTitle className="text-zinc-100">Confidence Graph</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="grid gap-3 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="h-36 rounded-lg border border-zinc-700/60 bg-zinc-900/60 animate-pulse" />
            ))}
          </div>
        ) : series.length === 0 ? (
          <div className="rounded-lg border border-dashed border-zinc-700 p-5 text-sm text-zinc-400">
            No confidence trends available yet. Keep interacting and submitting quizzes to build trend lines.
          </div>
        ) : (
          <div className="space-y-5">
            <div className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-4">
              <p className="mb-3 text-sm font-medium text-zinc-200">Overall Trend Comparison (Top Topics)</p>
              <div className="h-72 w-full rounded-md bg-zinc-950/70 p-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={buildCombinedSeries(series)} margin={{ top: 8, right: 16, left: 4, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                    <XAxis dataKey="session" stroke="#a1a1aa" />
                    <YAxis stroke="#a1a1aa" domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{ background: "#111827", border: "1px solid #3f3f46", borderRadius: 8 }}
                      labelStyle={{ color: "#d4d4d8" }}
                    />
                    <Legend wrapperStyle={{ color: "#d4d4d8" }} />
                    {series.slice(0, 6).map((item, idx) => (
                      <Line
                        key={item.topic}
                        type="monotone"
                        dataKey={item.topic}
                        stroke={COLORS[idx % COLORS.length]}
                        strokeWidth={2.5}
                        dot={{ r: 2 }}
                        activeDot={{ r: 5 }}
                        isAnimationActive
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
            {series.slice(0, 6).map((item) => {
              const currentPct = Math.round(Math.max(0, Math.min(1, item.current_confidence)) * 100);
              const trendLabel = item.improvement > 0 ? `+${Math.round(item.improvement * 100)}%` : `${Math.round(item.improvement * 100)}%`;
              const trendClass = item.improvement > 0 ? "text-emerald-300" : item.improvement < 0 ? "text-rose-300" : "text-zinc-300";
              const masteryPct = typeof item.mastery_score === "number" ? Math.round(item.mastery_score * 100) : null;
              const quizPct = typeof item.avg_quiz_score_ratio === "number" ? Math.round(item.avg_quiz_score_ratio * 100) : null;
              const weakSignals = Number(item.weak_signal_count ?? 0);
              const topicPoints = buildTopicPoints(item.points);

              return (
                <div key={item.topic} className="rounded-lg border border-zinc-700/60 bg-zinc-900/60 p-3 transition-all duration-300 hover:border-cyan-500/50">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-medium text-zinc-200">{pretty(item.topic)}</p>
                    <span className="text-xs text-zinc-400">{item.sessions_studied} sessions</span>
                  </div>
                  <div className="h-28 w-full rounded-md bg-zinc-950/70 p-1">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={topicPoints}>
                        <XAxis dataKey="session" hide />
                        <YAxis hide domain={[0, 100]} />
                        <Tooltip
                          contentStyle={{ background: "#111827", border: "1px solid #3f3f46", borderRadius: 8 }}
                          labelStyle={{ color: "#d4d4d8" }}
                        />
                        <Line
                          type="monotone"
                          dataKey="confidence"
                          stroke="#22d3ee"
                          strokeWidth={2.5}
                          dot={{ r: 2 }}
                          activeDot={{ r: 5 }}
                          isAnimationActive
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span className="text-cyan-300">Current: {currentPct}%</span>
                    <span className={trendClass}>Trend: {trendLabel}</span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-[11px] text-zinc-300">
                    <span>Mastery: {masteryPct !== null ? `${masteryPct}%` : "N/A"}</span>
                    <span>Quiz: {quizPct !== null ? `${quizPct}%` : "N/A"}</span>
                    <span>Weak signals: {weakSignals}</span>
                    <span>State: {item.performance_label ? pretty(item.performance_label) : "developing"}</span>
                  </div>
                  <div className="mt-3 flex justify-end">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button className="h-8 rounded-md bg-zinc-800 px-3 text-xs text-zinc-100 hover:bg-zinc-700">
                          Enlarge
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl border-zinc-700 bg-zinc-900 text-zinc-100">
                        <DialogHeader>
                          <DialogTitle>{pretty(item.topic)} - Detailed Performance</DialogTitle>
                        </DialogHeader>
                        <div className="h-[420px] w-full rounded-md bg-zinc-950/70 p-2">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={topicPoints} margin={{ top: 8, right: 16, left: 4, bottom: 8 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                              <XAxis dataKey="session" stroke="#a1a1aa" />
                              <YAxis stroke="#a1a1aa" domain={[0, 100]} />
                              <Tooltip
                                contentStyle={{ background: "#111827", border: "1px solid #3f3f46", borderRadius: 8 }}
                                labelStyle={{ color: "#d4d4d8" }}
                              />
                              <Line
                                type="monotone"
                                dataKey="confidence"
                                stroke="#22d3ee"
                                strokeWidth={3}
                                dot={{ r: 3 }}
                                activeDot={{ r: 6 }}
                                isAnimationActive
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>
              );
            })}
          </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
