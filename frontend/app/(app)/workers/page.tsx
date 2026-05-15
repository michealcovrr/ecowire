"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Search, Star, MapPin, ChevronRight, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface Worker {
  user_id: string;
  full_name: string;
  skill_tags: string[];
  recommendation_count: number;
  job_completion_count: number;
  connection_degree: number | null;
  location_lga: string | null;
  match_score?: number;
}

import { Mic, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function WorkersPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [extractedTags, setExtractedTags] = useState<string[]>([]);

  useEffect(() => {
    api.get<{ workers: Worker[] }>("/workers/browse")
      .then((r) => setWorkers(r.data.workers ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = workers.filter((w) =>
    !query ||
    w.full_name.toLowerCase().includes(query.toLowerCase()) ||
    w.skill_tags.some((t) => t.toLowerCase().includes(query.toLowerCase())) ||
    extractedTags.some((t) => w.skill_tags.includes(t))
  );

  async function handleVoiceSearch() {
    setIsRecording(true);
    toast("Listening... (Mock recording for 3s)", "success");
    
    // Simulate recording time
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    try {
      // In production, we'd upload an audio blob to Cloudinary. Mocking for demo:
      const res = await api.post<{ transcribed_text: string, extracted_tags: string[], workers: Worker[] }>("/workers/search/voice", {
        audio_url: "mock-audio-url.mp3"
      });
      
      setQuery(res.data.transcribed_text);
      setExtractedTags(res.data.extracted_tags);
      setWorkers(res.data.workers);
      toast("Voice search complete!", "success");
    } catch {
      toast("Failed to process voice search", "error");
    } finally {
      setIsRecording(false);
    }
  }

  return (
    <div className="flex flex-col pb-6">
      {/* Header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-5">
        <h1 className="text-xl font-extrabold text-white">Find Workers</h1>
        <p className="text-sm text-white/60 mt-0.5">Browse skilled people near you</p>
      </div>

      {/* Search */}
      <div className="px-4 py-3 bg-white border-b border-border/60">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <input
              className="w-full h-11 rounded-xl border-2 border-border bg-background pl-10 pr-4 text-sm focus:border-primary focus:outline-none text-foreground placeholder:text-muted-foreground/60"
              placeholder="Search by name or skill..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <button 
            onClick={handleVoiceSearch}
            disabled={isRecording}
            className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl transition-colors ${isRecording ? 'bg-destructive animate-pulse text-white' : 'bg-primary text-white hover:bg-primary/90'}`}
          >
            {isRecording ? <Loader2 className="h-5 w-5 animate-spin" /> : <Mic className="h-5 w-5" />}
          </button>
        </div>
        {extractedTags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            <span className="text-[10px] text-muted-foreground mr-1 mt-0.5">AI Intent:</span>
            {extractedTags.map(tag => (
              <Badge key={tag} variant="secondary" className="text-[9px] px-1.5 py-0">{tag}</Badge>
            ))}
          </div>
        )}
      </div>

      <div className="px-4 mt-4 space-y-2">
        {loading ? (
          [1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)
        ) : filtered.length === 0 ? (
          <div className="rounded-2xl bg-white border border-border/40 shadow-card p-8 text-center">
            <Users className="h-10 w-10 text-muted mx-auto mb-3" />
            <p className="text-sm font-bold text-foreground">No workers found</p>
            <p className="text-xs text-muted-foreground mt-1">Try a different search or check back later.</p>
          </div>
        ) : (
          filtered.map((worker) => (
            <button
              key={worker.user_id}
              onClick={() => router.push(`/profile/${worker.user_id}`)}
              className="flex w-full items-center gap-3 rounded-2xl bg-white border border-border/40 shadow-card p-4 text-left hover:shadow-card-md transition-shadow"
            >
              <Avatar size="md">
                <AvatarFallback>
                  {worker.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-bold text-foreground truncate">{worker.full_name}</p>
                  {worker.connection_degree && (
                    <Badge variant="accent" className="text-[10px]">
                      {worker.connection_degree}°
                    </Badge>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {worker.skill_tags.slice(0, 3).map((tag) => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
                  ))}
                </div>
                {worker.location_lga && (
                  <p className="flex items-center gap-1 text-[10px] text-muted-foreground mt-1">
                    <MapPin className="h-3 w-3" /> {worker.location_lga}
                  </p>
                )}
              </div>
              <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                {worker.recommendation_count > 0 && (
                  <span className="flex items-center gap-0.5 text-[11px] font-bold text-gold-dark">
                    <Star className="h-3 w-3 fill-gold text-gold" />
                    {worker.recommendation_count}
                  </span>
                )}
                <span className="text-[10px] text-muted-foreground">{worker.job_completion_count} jobs</span>
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
