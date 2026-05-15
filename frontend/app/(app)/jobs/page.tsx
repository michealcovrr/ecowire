"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatNaira } from "@/lib/utils";
import { Briefcase, MapPin, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";

interface Job {
  job_id: string;
  employer_user_id: string;
  job_description_raw: string;
  job_tags: string[];
  location_address: string | null;
  budget_naira: number | null;
  status: string;
  created_at: string;
}

interface MyApp {
  application_id: string;
  job_id: string;
  status: string;
  applied_at: string;
}

interface Applicant {
  worker_id: string;
  user_id: string;
  full_name: string;
  application_id: string;
  status: string;
  score?: number;
}

type Tab = "feed" | "post" | "mine";

const STATUS_BADGE: Record<string, "default" | "success" | "accent" | "gold" | "destructive" | "warning" | "secondary"> = {
  open: "success",
  matched: "accent",
  agreement_locked: "gold",
  funded: "warning",
  active: "default",
  completed: "secondary",
  disputed: "destructive",
  applied: "accent",
  shortlisted: "gold",
  accepted: "default",
  rejected: "destructive",
};

export default function JobsPage() {
  const [tab, setTab] = useState<Tab>("feed");

  return (
    <div className="flex flex-col min-h-dvh pb-6">
      {/* Header */}
      <div className="bg-blue-700 px-5 pt-12 pb-5">
        <h1 className="text-xl font-extrabold text-white">Jobs</h1>
        <p className="text-sm text-blue-200 mt-0.5">Find work or hire someone near you</p>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-border/60 flex">
        {(["feed", "mine", "post"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "flex-1 py-3 text-xs font-bold transition-colors border-b-2",
              tab === t
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {t === "feed" ? "Browse" : t === "mine" ? "My Jobs" : "Post Job"}
          </button>
        ))}
      </div>

      <div className="flex-1">
        {tab === "feed" && <JobFeed />}
        {tab === "mine" && <MyJobs />}
        {tab === "post" && <PostJob onSuccess={() => setTab("mine")} />}
      </div>
    </div>
  );
}

function JobFeed() {
  const { toast } = useToast();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState<string | null>(null);

  useEffect(() => {
    api.get<{ jobs: Job[] }>("/jobs/feed")
      .then((r) => setJobs(r.data.jobs ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function apply(jobId: string) {
    setApplying(jobId);
    try {
      await api.post(`/jobs/${jobId}/apply`, {});
      toast("Application sent!", "success");
      setJobs((prev) => prev.filter((j) => j.job_id !== jobId));
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to apply", "error");
    } finally {
      setApplying(null);
    }
  }

  if (loading) return <LoadingSkeleton />;

  if (jobs.length === 0) return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50">
        <Briefcase className="h-8 w-8 text-blue-600" />
      </div>
      <p className="text-sm font-bold text-foreground">No jobs near you yet</p>
      <p className="text-xs text-muted-foreground mt-1">Add skills to your profile to get matched.</p>
    </div>
  );

  return (
    <div className="px-4 pt-4 space-y-3">
      {jobs.map((job) => (
        <JobCard key={job.job_id} job={job} onApply={() => apply(job.job_id)} applying={applying === job.job_id} />
      ))}
    </div>
  );
}

function JobCard({ job, onApply, applying }: { job: Job; onApply: () => void; applying: boolean }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-2xl bg-white border border-border/40 shadow-card overflow-hidden">
      <button className="w-full text-left p-4" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-foreground line-clamp-2">{job.job_description_raw}</p>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              {job.location_address && (
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <MapPin className="h-3 w-3" /> {job.location_address}
                </span>
              )}
              {job.budget_naira && (
                <span className="text-xs font-bold text-primary">
                  {formatNaira(job.budget_naira * 100)}
                </span>
              )}
            </div>
            {job.job_tags?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {job.job_tags.slice(0, 4).map((tag) => (
                  <Badge key={tag} variant="secondary">{tag}</Badge>
                ))}
              </div>
            )}
          </div>
          <ChevronRight className={cn("h-4 w-4 text-muted-foreground flex-shrink-0 mt-1 transition-transform", expanded && "rotate-90")} />
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-border/40 pt-3">
          <p className="text-xs text-muted-foreground mb-3 leading-relaxed">{job.job_description_raw}</p>
          <Button className="w-full bg-blue-600 hover:bg-blue-700" size="sm" onClick={onApply} loading={applying}>
            Apply Now
          </Button>
        </div>
      )}
    </div>
  );
}

function MyJobs() {
  const { toast } = useToast();
  const [myPosted, setMyPosted] = useState<Job[]>([]);
  const [myApps, setMyApps] = useState<MyApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"posted" | "applied">("posted");
  const [accepting, setAccepting] = useState<string | null>(null);
  const [applicants, setApplicants] = useState<Record<string, Applicant[]>>({});

  useEffect(() => {
    Promise.all([
      api.get<{ jobs: Job[] }>("/jobs/my/posted").then((r) => setMyPosted(r.data.jobs ?? [])),
      api.get<{ applications: MyApp[] }>("/jobs/my/applications").then((r) => setMyApps(r.data.applications ?? [])),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function loadApplicants(jobId: string) {
    if (applicants[jobId]) return;
    try {
      const res = await api.get<{ applicants: Applicant[] }>(`/jobs/${jobId}/applicants`);
      setApplicants((prev) => ({ ...prev, [jobId]: res.data.applicants ?? [] }));
    } catch {}
  }

  async function acceptWorker(jobId: string, workerId: string) {
    setAccepting(workerId);
    try {
      await api.post(`/jobs/${jobId}/accept/${workerId}`, {});
      toast("Worker accepted! Start chatting to agree on terms.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    } finally {
      setAccepting(null);
    }
  }

  if (loading) return <LoadingSkeleton />;

  return (
    <div className="flex flex-col">
      {/* Sub-tabs */}
      <div className="flex mx-4 mt-4 rounded-xl overflow-hidden border border-border/60">
        {(["posted", "applied"] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={cn(
              "flex-1 py-2 text-xs font-bold transition-colors",
              view === v ? "bg-blue-600 text-white" : "bg-white text-muted-foreground"
            )}
          >
            {v === "posted" ? `Posted (${myPosted.length})` : `Applied (${myApps.length})`}
          </button>
        ))}
      </div>

      <div className="px-4 pt-4 space-y-3">
        {view === "posted" ? (
          myPosted.length === 0 ? (
            <EmptyState text="You haven't posted any jobs yet." />
          ) : (
            myPosted.map((job) => (
              <div key={job.job_id} className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-bold text-foreground flex-1 line-clamp-2">{job.job_description_raw}</p>
                  <Badge variant={STATUS_BADGE[job.status] ?? "secondary"}>{job.status.replace(/_/g, " ")}</Badge>
                </div>
                {job.budget_naira && (
                  <p className="text-xs font-bold text-primary mt-1">{formatNaira(job.budget_naira * 100)}</p>
                )}
                <Button
                  size="sm" variant="outline" className="mt-3 w-full text-xs border-blue-200 text-blue-600 hover:bg-blue-50"
                  onClick={() => loadApplicants(job.job_id)}
                >
                  View Applicants
                </Button>
                {applicants[job.job_id]?.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {applicants[job.job_id].map((app) => (
                      <div key={app.worker_id} className="flex items-center justify-between rounded-xl bg-muted/50 px-3 py-2 border border-border/40">
                        <div>
                          <p className="text-xs font-bold text-foreground">{app.full_name}</p>
                          <p className="text-[10px] text-muted-foreground">Score: {app.score}</p>
                        </div>
                        <Button
                          size="sm"
                          className="text-xs h-7 px-3 bg-blue-600 hover:bg-blue-700"
                          loading={accepting === app.worker_id}
                          onClick={() => acceptWorker(job.job_id, app.worker_id)}
                        >
                          Accept
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )
        ) : (
          myApps.length === 0 ? (
            <EmptyState text="You haven't applied to any jobs yet." />
          ) : (
            myApps.map((app) => (
              <div key={app.application_id} className="rounded-2xl bg-white border border-border/40 shadow-card p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground font-mono">{app.job_id.slice(0, 8)}…</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Applied {new Date(app.applied_at).toLocaleDateString("en-NG")}
                  </p>
                </div>
                <Badge variant={STATUS_BADGE[app.status] ?? "secondary"}>{app.status.replace(/_/g, " ")}</Badge>
              </div>
            ))
          )
        )}
      </div>
    </div>
  );
}

function PostJob({ onSuccess }: { onSuccess: () => void }) {
  const { toast } = useToast();
  const [description, setDescription] = useState("");
  const [address, setAddress] = useState("");
  const [budgetNaira, setBudgetNaira] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;
    setLoading(true);
    try {
      await api.post("/jobs", {
        job_description: description,
        location_address: address || null,
        budget_kobo: budgetNaira ? Math.round(parseFloat(budgetNaira) * 100) : null,
      });
      toast("Job posted! Workers will be matched shortly.", "success");
      onSuccess();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to post", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="px-4 pt-5 space-y-4 pb-6">
      <div>
        <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide mb-2 block">
          Describe the job
        </label>
        <textarea
          className="w-full rounded-2xl border-2 border-border bg-white p-4 text-sm text-foreground focus:border-primary focus:outline-none resize-none placeholder:text-muted-foreground/60"
          rows={5}
          placeholder="e.g. I need someone to fix the wiring in my shop, also paint the walls. Should take about 2 days."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />
        <p className="text-[11px] text-muted-foreground mt-1.5">
          Write naturally — AI extracts the skills and details
        </p>
      </div>

      <Input
        label="Location (optional)"
        placeholder="e.g. Surulere, Lagos"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
      />

      <Input
        label="Budget in ₦ (optional)"
        type="number"
        inputMode="decimal"
        placeholder="e.g. 15000"
        value={budgetNaira}
        onChange={(e) => setBudgetNaira(e.target.value)}
      />

      <Button
        type="submit"
        className="w-full bg-blue-600 hover:bg-blue-700"
        size="lg"
        loading={loading}
        disabled={!description.trim()}
      >
        Post Job
      </Button>
    </form>
  );
}

function LoadingSkeleton() {
  return (
    <div className="px-4 pt-4 space-y-3">
      {[1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-2xl bg-white border border-border/40 shadow-card p-8 text-center">
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  );
}
