"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { ChevronLeft, Star, Briefcase, MessageSquare, MapPin, ThumbsUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useToast } from "@/components/ui/toast";

interface PublicProfile {
  user_id: string;
  full_name: string;
  skill_tags: string[];
  job_completion_count: number;
  dispute_count: number;
  profile_visibility_score: number;
  recommendation_count: number;
  connection_degree: number | null;
  location_lga: string | null;
}

interface Recommendation {
  recommendation_id: string;
  recommender_name: string;
  recommendation_text: string;
  created_at: string;
}

export default function PublicProfilePage() {
  const { userId } = useParams<{ userId: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuthStore();

  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<PublicProfile>(`/profile/${userId}`).then((r) => setProfile(r.data)),
      api.get<{ recommendations: Recommendation[] }>(`/profile/${userId}/recommendations`)
        .then((r) => setRecommendations(r.data.recommendations ?? [])),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [userId]);

  const isOwnProfile = user?.user_id === userId;
  const initials = profile?.full_name?.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() ?? "?";

  return (
    <div className="flex flex-col pb-6">
      {/* Header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-10">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-white/70 hover:text-white mb-6">
          <ChevronLeft className="h-4 w-4" /> Back
        </button>

        {loading ? (
          <div className="flex flex-col items-center gap-3">
            <Skeleton className="h-20 w-20 rounded-full" />
            <Skeleton className="h-6 w-40" />
          </div>
        ) : profile ? (
          <div className="flex flex-col items-center">
            <Avatar size="xl" className="border-2 border-white/30 mb-3">
              <AvatarFallback className="text-white bg-white/20 text-2xl">{initials}</AvatarFallback>
            </Avatar>
            <h2 className="text-xl font-extrabold text-white">{profile.full_name}</h2>
            <p className="text-sm text-white/50 font-mono mt-1">{profile.user_id}</p>

            <div className="flex items-center gap-3 mt-3">
              {profile.connection_degree && (
                <Badge variant="gold" className="text-[11px]">
                  {profile.connection_degree}° connection
                </Badge>
              )}
              {profile.location_lga && (
                <span className="flex items-center gap-1 text-xs text-white/60">
                  <MapPin className="h-3 w-3" /> {profile.location_lga}
                </span>
              )}
            </div>
          </div>
        ) : null}
      </div>

      <div className="px-4 mt-5 space-y-4">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}
          </div>
        ) : profile ? (
          <>
            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl bg-white border border-border/40 shadow-card p-3 text-center">
                <p className="text-xl font-extrabold text-primary">{profile.job_completion_count}</p>
                <p className="text-[10px] text-muted-foreground font-medium">Jobs Done</p>
              </div>
              <div className="rounded-xl bg-white border border-border/40 shadow-card p-3 text-center">
                <div className="flex items-center justify-center gap-1">
                  <Star className="h-4 w-4 fill-gold text-gold" />
                  <p className="text-xl font-extrabold text-gold-dark">{profile.recommendation_count}</p>
                </div>
                <p className="text-[10px] text-muted-foreground font-medium">Recs</p>
              </div>
              <div className="rounded-xl bg-white border border-border/40 shadow-card p-3 text-center">
                <p className="text-xl font-extrabold text-foreground">{profile.dispute_count}</p>
                <p className="text-[10px] text-muted-foreground font-medium">Disputes</p>
              </div>
            </div>

            {/* Skills */}
            {profile.skill_tags?.length > 0 && (
              <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
                <p className="text-sm font-bold text-foreground mb-3">Skills</p>
                <div className="flex flex-wrap gap-2">
                  {profile.skill_tags.map((tag) => (
                    <Badge key={tag} variant="accent">{tag}</Badge>
                  ))}
                </div>
              </div>
            )}

            {/* CTA buttons */}
            {!isOwnProfile && (
              <div className="grid grid-cols-2 gap-3">
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={() => toast("Chat feature available in job context", "info")}
                >
                  <MessageSquare className="h-4 w-4" /> Message
                </Button>
                <Button
                  className="gap-2"
                  onClick={() => toast("Post a job to hire this worker", "info")}
                >
                  <Briefcase className="h-4 w-4" /> Hire
                </Button>
              </div>
            )}

            {/* Recommendations */}
            <div>
              <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-3">
                Recommendations ({recommendations.length})
              </h2>
              {recommendations.length === 0 ? (
                <div className="rounded-2xl bg-white border border-border/40 shadow-card p-6 text-center">
                  <p className="text-sm text-muted-foreground">No recommendations yet.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {recommendations.map((rec) => (
                    <div key={rec.recommendation_id} className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
                      <div className="flex items-start gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gold-light flex-shrink-0">
                          <ThumbsUp className="h-4 w-4 text-gold-dark" />
                        </div>
                        <div className="flex-1">
                          <p className="text-xs font-bold text-foreground">{rec.recommender_name}</p>
                          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{rec.recommendation_text}</p>
                          <p className="text-[10px] text-muted-foreground mt-1.5">
                            {new Date(rec.created_at).toLocaleDateString("en-NG", { day: "numeric", month: "short", year: "numeric" })}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="rounded-2xl bg-white border border-border/40 shadow-card p-8 text-center">
            <p className="text-sm text-muted-foreground">Profile not found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
