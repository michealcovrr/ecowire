"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { formatNaira } from "@/lib/utils";
import { ChevronLeft, MapPin, Briefcase, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useToast } from "@/components/ui/toast";

interface JobDetail {
  job_id: string;
  employer_user_id: string;
  job_description_raw: string;
  job_tags: string[];
  location_address: string | null;
  budget_naira: number | null;
  status: string;
  created_at: string;
  employer_name?: string;
  applicant_count?: number;
}

interface Applicant {
  worker_id: string;
  full_name: string;
  skill_tags: string[];
  score: number;
  recommendation_count: number;
}

const STATUS_BADGE: Record<string, "default" | "success" | "accent" | "gold" | "destructive" | "warning" | "secondary"> = {
  open: "success",
  matched: "accent",
  agreement_locked: "gold",
  funded: "warning",
  active: "default",
  completed: "secondary",
  disputed: "destructive",
};

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuthStore();

  const [job, setJob] = useState<JobDetail | null>(null);
  const [applicants, setApplicants] = useState<Applicant[]>([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [accepting, setAccepting] = useState<string | null>(null);

  const isEmployer = job?.employer_user_id === user?.user_id;

  useEffect(() => {
    Promise.all([
      api.get<JobDetail>(`/jobs/${id}`).then((r) => setJob(r.data)),
      api.get<{ applicants: Applicant[] }>(`/jobs/${id}/applicants`)
        .then((r) => setApplicants(r.data.applicants ?? [])),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  async function apply() {
    setApplying(true);
    try {
      await api.post(`/jobs/${id}/apply`, {});
      toast("Application sent!", "success");
      router.back();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to apply", "error");
    } finally {
      setApplying(false);
    }
  }

  async function acceptWorker(workerId: string) {
    setAccepting(workerId);
    try {
      await api.post(`/jobs/${id}/accept/${workerId}`, {});
      toast("Worker accepted! Start chatting to finalise the deal.", "success");
      router.push("/jobs");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    } finally {
      setAccepting(null);
    }
  }

  return (
    <div className="flex flex-col pb-8">
      {/* Header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-5">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-white/70 hover:text-white mb-5">
          <ChevronLeft className="h-4 w-4" /> Back
        </button>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-lg font-extrabold text-white leading-snug">Job Details</h1>
          </div>
          {job && <Badge variant={STATUS_BADGE[job.status] ?? "secondary"}>{job.status.replace(/_/g, " ")}</Badge>}
        </div>
      </div>

      <div className="px-4 mt-5 space-y-4">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}
          </div>
        ) : job ? (
          <>
            {/* Job card */}
            <div className="rounded-2xl bg-white border border-border/40 shadow-card p-5">
              <p className="text-base font-bold text-foreground leading-snug">{job.job_description_raw}</p>

              <div className="flex flex-wrap items-center gap-3 mt-3">
                {job.location_address && (
                  <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <MapPin className="h-3.5 w-3.5" /> {job.location_address}
                  </span>
                )}
                {job.budget_naira && (
                  <span className="text-sm font-extrabold text-primary">
                    {formatNaira(job.budget_naira * 100)}
                  </span>
                )}
              </div>

              {job.job_tags?.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {job.job_tags.map((tag) => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border/60 text-xs text-muted-foreground">
                {job.employer_name && (
                  <span>Posted by <span className="font-semibold text-foreground">{job.employer_name}</span></span>
                )}
                <span>{new Date(job.created_at).toLocaleDateString("en-NG", { day: "numeric", month: "short" })}</span>
                {job.applicant_count !== undefined && (
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {job.applicant_count} applied
                  </span>
                )}
              </div>
            </div>

            {/* Apply button (non-employer) */}
            {!isEmployer && job.status === "open" && (
              <Button className="w-full bg-primary hover:bg-primary/90" size="lg" onClick={apply} loading={applying}>
                Apply for this Job
              </Button>
            )}

            {/* Applicants (employer view) */}
            {isEmployer && applicants.length > 0 && (
              <div>
                <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-3">
                  Applicants ({applicants.length})
                </h2>
                <div className="space-y-2">
                  {applicants.map((app) => (
                    <div key={app.worker_id} className="flex items-center gap-3 rounded-2xl bg-white border border-border/40 shadow-card p-4">
                      <Avatar size="md">
                        <AvatarFallback>
                          {app.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-foreground">{app.full_name}</p>
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {app.skill_tags.slice(0, 3).map((tag) => (
                            <Badge key={tag} variant="secondary">{tag}</Badge>
                          ))}
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-1">
                          Match score: <span className="font-bold text-foreground">{app.score}</span>
                        </p>
                      </div>
                      <Button
                        size="sm"
                        className="bg-primary hover:bg-primary/90 flex-shrink-0"
                        loading={accepting === app.worker_id}
                        onClick={() => acceptWorker(app.worker_id)}
                      >
                        Accept
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="rounded-2xl bg-white border border-border/40 shadow-card p-8 text-center">
            <Briefcase className="h-10 w-10 text-muted mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">Job not found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
