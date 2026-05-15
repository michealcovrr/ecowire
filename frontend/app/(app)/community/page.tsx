"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Users, MapPin, Star, ChevronRight } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useRouter } from "next/navigation";

interface CommunityMember {
  user_id: string;
  full_name: string;
  skill_tags: string[];
  recommendation_count: number;
  connection_degree: number | null;
  distance_km: number | null;
}

interface CommunityGroup {
  group_id: string;
  group_name: string;
  lga: string;
  member_count: number;
}

export default function CommunityPage() {
  useAuthStore();
  const router = useRouter();
  const [nearbyUsers, setNearbyUsers] = useState<CommunityMember[]>([]);
  const [groups, setGroups] = useState<CommunityGroup[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<{ members: CommunityMember[] }>("/community/nearby").then((r) => setNearbyUsers(r.data.members ?? [])),
      api.get<{ groups: CommunityGroup[] }>("/community/groups").then((r) => setGroups(r.data.groups ?? [])),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col pb-6">
      {/* Header */}
      <div className="bg-blue-700 px-5 pt-12 pb-5">
        <h1 className="text-xl font-extrabold text-white">Community</h1>
        <p className="text-sm text-blue-200 mt-0.5">Your local trusted network</p>
      </div>

      <div className="px-4 mt-5 space-y-5">
        {/* My groups */}
        <section>
          <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-3">
            My Circles
          </h2>
          {loading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => <Skeleton key={i} className="h-14" />)}
            </div>
          ) : groups.length === 0 ? (
            <div className="rounded-2xl bg-white border border-border/40 shadow-card p-6 text-center">
              <Users className="h-8 w-8 text-muted mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No community groups yet.</p>
              <p className="text-xs text-muted-foreground mt-0.5">Groups are assigned based on your location.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {groups.map((g) => (
                <div key={g.group_id} className="flex items-center gap-3 rounded-2xl bg-white border border-border/40 shadow-card p-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 flex-shrink-0">
                    <Users className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-foreground">{g.group_name}</p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <MapPin className="h-3 w-3" /> {g.lga} · {g.member_count} members
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Nearby workers */}
        <section>
          <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-3">
            People Near You
          </h2>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)}
            </div>
          ) : nearbyUsers.length === 0 ? (
            <div className="rounded-2xl bg-white border border-border/40 shadow-card p-6 text-center">
              <p className="text-sm text-muted-foreground">No nearby members found yet.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {nearbyUsers.map((member) => (
                <button
                  key={member.user_id}
                  onClick={() => router.push(`/profile/${member.user_id}`)}
                  className="flex w-full items-center gap-3 rounded-2xl bg-white border border-border/40 shadow-card p-4 text-left hover:shadow-card-md transition-shadow"
                >
                  <Avatar size="md">
                    <AvatarFallback>
                      {member.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-bold text-foreground truncate">{member.full_name}</p>
                      {member.connection_degree && (
                        <Badge variant="accent" className="text-[10px]">
                          {member.connection_degree}° connection
                        </Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {member.skill_tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="secondary">{tag}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    {member.recommendation_count > 0 && (
                      <span className="flex items-center gap-0.5 text-[10px] font-bold text-gold-dark">
                        <Star className="h-3 w-3 fill-gold text-gold" />
                        {member.recommendation_count}
                      </span>
                    )}
                    {member.distance_km && (
                      <span className="text-[10px] text-muted-foreground">
                        {member.distance_km.toFixed(1)}km
                      </span>
                    )}
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
