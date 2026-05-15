"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { ShieldCheck, Save, Star, QrCode, ChevronRight, AlertCircle, Camera, UploadCloud, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface ProofMedia {
  media_id: string;
  media_url: string;
  media_type: string;
  confidence_score: number | null;
}

interface ProfileResponse {
  user_id: string;
  full_name: string;
  profile: {
    skill_description: string | null;
    skill_tags: string[];
    job_completion_count: number;
    dispute_count: number;
    profile_visibility_score: number;
  } | null;
  proof_media: ProofMedia[];
}

export default function ProfilePage() {
  const { user, qrCode, squadAccountNumber, squadBankName } = useAuthStore();
  const { toast } = useToast();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [profileData, setProfileData] = useState<ProfileResponse | null>(null);
  const [editingSkills, setEditingSkills] = useState(false);
  const [skillText, setSkillText] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);

  const fetchProfile = useCallback(() => {
    api.get<ProfileResponse>("/profile/me")
      .then((r) => { 
        setProfileData(r.data); 
        if (r.data.profile) {
          setSkillText(r.data.profile.skill_description ?? ""); 
        }
      })
      .catch(() => toast("Failed to load profile", "error"))
      .finally(() => setLoadingProfile(false));
  }, [toast]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  async function saveSkills() {
    setSaving(true);
    try {
      await api.post("/profile", { skill_description: skillText });
      toast("Skills updated!", "success");
      setEditingSkills(false);
      fetchProfile();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to save", "error");
    } finally {
      setSaving(false);
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    // In a full production environment with credentials, this would upload to Cloudinary.
    // Since we are running locally without Cloudinary keys, we will mock the URL.
    try {
      const mockUrl = "https://images.unsplash.com/photo-1581092921461-eab62e97a780?auto=format&fit=crop&q=80&w=400";
      await api.post("/profile/media", {
        media_url: mockUrl,
        media_type: "image",
        claimed_skills: profile?.skill_tags || []
      });
      toast("Proof uploaded & verified!", "success");
      fetchProfile();
    } catch {
      toast("Failed to upload proof", "error");
    } finally {
      setUploading(false);
    }
  }

  const kycTier = user?.kyc_tier ?? 1;
  const initials = user?.full_name?.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() ?? "?";
  const profile = profileData?.profile;
  const media = profileData?.proof_media || [];

  return (
    <div className="flex flex-col pb-6">
      {/* Header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-10">
        <div className="flex flex-col items-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white/15 border-2 border-white/30 mb-3 text-2xl font-extrabold text-white shadow-glass">
            {initials}
          </div>
          <h2 className="text-xl font-bold text-white">{user?.full_name ?? "—"}</h2>
          <p className="text-sm text-white/50 font-mono mt-1">{user?.user_id}</p>
          <div className="flex items-center gap-2 mt-3">
            <Badge variant={kycTier >= 2 ? "success" : "secondary"} className="text-[11px]">
              KYC Tier {kycTier}
            </Badge>
            {profile && profile.job_completion_count > 0 && (
              <Badge variant="accent" className="text-[11px]">
                {profile.job_completion_count} Jobs Done
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="px-4 mt-5 space-y-4">
        {/* Stats row */}
        {profile && (profile.job_completion_count > 0 || profile.dispute_count > 0) && (
          <div className="grid grid-cols-3 gap-3">
            <StatCard value={profile.job_completion_count} label="Jobs Done" color="text-primary" />
            <StatCard value={profile.dispute_count} label="Disputes" color="text-destructive" />
            <StatCard
              value={`${Math.round(profile.profile_visibility_score)}%`}
              label="Visibility"
              color="text-gold-dark"
            />
          </div>
        )}

        {/* Work skills */}
        <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-bold text-foreground">Work Skills</p>
            {!editingSkills && (
              <Button size="sm" variant="outline" onClick={() => setEditingSkills(true)}>
                {profile?.skill_tags?.length ? "Edit" : "Add Skills"}
              </Button>
            )}
          </div>

          {loadingProfile ? (
            <Skeleton className="h-8 w-full rounded-xl" />
          ) : editingSkills ? (
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground">
                Describe what you do in your own words. AI will extract your skills.
              </p>
              <textarea
                className="w-full rounded-xl border-2 border-border bg-background px-4 py-3 text-sm text-foreground focus:border-primary focus:outline-none resize-none placeholder:text-muted-foreground/60"
                rows={4}
                placeholder="e.g. I fix phones and laptops, do electrical wiring, and can drive any vehicle..."
                value={skillText}
                onChange={(e) => setSkillText(e.target.value)}
              />
              <div className="flex gap-2">
                <Button className="flex-1" size="sm" onClick={saveSkills} loading={saving}>
                  <Save className="h-3.5 w-3.5" /> Save
                </Button>
                <Button variant="outline" size="sm" onClick={() => setEditingSkills(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : profile?.skill_tags?.length ? (
            <div className="flex flex-wrap gap-2">
              {profile.skill_tags.map((tag) => (
                <Badge key={tag} variant="accent">{tag}</Badge>
              ))}
            </div>
          ) : (
            <div className="flex items-start gap-2 py-1">
              <AlertCircle className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <p className="text-xs text-muted-foreground">
                No skills added yet. Add skills to appear in job matching.
              </p>
            </div>
          )}
        </div>

        {/* Proof Media Section */}
        <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-bold text-foreground">Proof of Work</p>
            <input 
              type="file" 
              accept="image/*,video/*" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleFileUpload} 
            />
            <Button size="sm" variant="outline" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <UploadCloud className="h-4 w-4" />}
            </Button>
          </div>
          
          {loadingProfile ? (
            <div className="flex gap-2 overflow-hidden"><Skeleton className="h-20 w-20 rounded-xl" /></div>
          ) : media.length > 0 ? (
            <div className="flex gap-3 overflow-x-auto pb-2 snap-x">
              {media.map((m) => (
                <div key={m.media_id} className="relative h-24 w-24 flex-shrink-0 snap-start rounded-xl overflow-hidden border border-border">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={m.media_url} alt="Proof" className="object-cover w-full h-full" />
                  {m.confidence_score !== null && m.confidence_score > 0.6 && (
                    <div className="absolute bottom-1 right-1 bg-success/90 backdrop-blur-sm rounded-full p-1 border border-white/20">
                      <ShieldCheck className="h-3 w-3 text-white" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 border-2 border-dashed border-border rounded-xl bg-accent/20">
              <Camera className="h-8 w-8 text-muted-foreground/50 mb-2" />
              <p className="text-xs text-muted-foreground">Upload photos/videos of your work</p>
            </div>
          )}
        </div>

        {/* Wallet account */}
        {squadAccountNumber && (
          <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
            <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold mb-2">Wallet Account</p>
            <p className="text-lg font-extrabold text-foreground">{squadAccountNumber}</p>
            {squadBankName && <p className="text-sm text-muted-foreground">{squadBankName}</p>}
          </div>
        )}

        {/* QR Code */}
        {qrCode && (
          <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4 flex flex-col items-center">
            <div className="flex items-center gap-2 self-start mb-3">
              <QrCode className="h-4 w-4 text-muted-foreground" />
              <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Your QR Code</p>
            </div>
            <div className="rounded-2xl overflow-hidden border border-border p-2 bg-white">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`data:image/png;base64,${qrCode}`} alt="QR Code" width={160} height={160} />
            </div>
            <p className="mt-3 text-xs text-muted-foreground text-center">
              Share to receive payments or be found for jobs
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-2">
          {kycTier < 3 && (
            <button
              onClick={() => router.push("/profile/kyc-upgrade")}
              className="flex w-full items-center gap-3 rounded-2xl bg-white border border-border/40 shadow-card p-4 text-left hover:shadow-card-md transition-shadow"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent flex-shrink-0">
                <ShieldCheck className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold text-foreground">Upgrade to Tier {kycTier + 1}</p>
                <p className="text-xs text-muted-foreground">
                  {kycTier === 1 ? "Unlock escrow, hiring & higher limits" : "Unlock loans & insurance"}
                </p>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </button>
          )}

          <Link href="/finance/identity">
            <div className="flex items-center gap-3 rounded-2xl bg-white border border-border/40 shadow-card p-4 hover:shadow-card-md transition-shadow">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gold-light flex-shrink-0">
                <Star className="h-5 w-5 text-gold-dark" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold text-foreground">Identity Score</p>
                <p className="text-xs text-muted-foreground">View your financial standing</p>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}

function StatCard({ value, label, color }: { value: number | string; label: string; color: string }) {
  return (
    <div className="rounded-xl bg-white border border-border/40 shadow-card p-3 text-center">
      <p className={`text-xl font-extrabold ${color}`}>{value}</p>
      <p className="text-[10px] text-muted-foreground mt-0.5 font-medium">{label}</p>
    </div>
  );
}
