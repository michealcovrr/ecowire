"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { Briefcase, ShoppingBag, Truck, Wrench, Wallet, ChevronRight, Check } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface QuestionOption {
  value: string | boolean;
  label: string;
}

interface Question {
  id: string;
  step: number;
  question: string;
  options: QuestionOption[];
  show_if?: Record<string, any>;
}

function getIconForValue(value: string | boolean) {
  if (typeof value === "boolean") return value ? <Check className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />;
  if (value.includes("work") || value === "service") return <Wrench className="h-5 w-5" />;
  if (value.includes("hire") || value === "business" || value === "trade") return <Briefcase className="h-5 w-5" />;
  if (value === "transport") return <Truck className="h-5 w-5" />;
  if (value.includes("financial") || value === "basic") return <Wallet className="h-5 w-5" />;
  return <ChevronRight className="h-5 w-5" />;
}

export default function IntentPage() {
  const router = useRouter();
  const { toast } = useToast();
  
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get<{ questions: Question[] }>("/intent/questions")
      .then(res => setQuestions(res.data.questions))
      .catch(() => toast("Failed to load questions", "error"))
      .finally(() => setLoadingQuestions(false));
  }, [toast]);

  // Find the next applicable question based on show_if logic
  function getNextStepIndex(currentStep: number, currentAnswers: Record<string, any>): number {
    for (let i = currentStep + 1; i < questions.length; i++) {
      const q = questions[i];
      if (!q.show_if) return i;
      
      // Check if show_if condition matches current answers
      const matches = Object.entries(q.show_if).every(([k, v]) => currentAnswers[k] === v);
      if (matches) return i;
    }
    return -1; // No more questions
  }

  function selectOption(questionId: string, value: string | boolean) {
    const newAnswers = { ...answers, [questionId]: value };
    setAnswers(newAnswers);

    const nextIndex = getNextStepIndex(step, newAnswers);
    if (nextIndex !== -1) {
      setStep(nextIndex);
    } else {
      submit(newAnswers);
    }
  }

  async function submit(finalAnswers: Record<string, any>) {
    setLoading(true);
    try {
      await api.post("/intent/submit", { answers: finalAnswers });
      toast("Profile set up!", "success");
      router.replace("/dashboard");
    } catch {
      toast("Failed to save intent", "error");
      setLoading(false);
    }
  }

  if (loadingQuestions || questions.length === 0) {
    return (
      <div className="flex min-h-dvh flex-col bg-background p-5 pt-12 space-y-4">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-16 w-full rounded-2xl" />
        <Skeleton className="h-16 w-full rounded-2xl" />
      </div>
    );
  }

  const question = questions[step];
  const progress = ((step) / questions.length) * 100;

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      {/* Header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-10">
        <div className="h-1 bg-white/20 rounded-full mb-6">
          <div
            className="h-full bg-gold rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-white/50 font-medium mb-2">
          Step {step + 1} of {questions.length}
        </p>
        <h2 className="text-2xl font-extrabold text-white">{question.question}</h2>
        <p className="text-sm text-white/50 mt-1">Choose the one that fits best</p>
      </div>

      {/* Options */}
      <div className="flex-1 rounded-t-3xl bg-background -mt-4 px-5 pt-7 pb-8 flex flex-col gap-3">
        {question.options.map((option) => (
          <button
            key={String(option.value)}
            onClick={() => selectOption(question.id, option.value)}
            disabled={loading}
            className="flex items-center gap-4 rounded-2xl bg-white border-2 border-border p-4 text-left hover:border-primary hover:bg-accent/20 transition-all active:scale-[0.98] shadow-card"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted text-primary flex-shrink-0">
              {getIconForValue(option.value)}
            </div>
            <div className="flex-1">
              <p className="text-sm font-bold text-foreground">{option.label}</p>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </button>
        ))}

        {step > 0 && (
          <button
            onClick={() => setStep(step - 1)}
            className="mt-2 text-xs font-semibold text-muted-foreground hover:text-foreground"
          >
            ← Back
          </button>
        )}

        <button
          onClick={() => router.replace("/dashboard")}
          className="mt-auto text-xs text-muted-foreground hover:text-foreground text-center"
        >
          Skip for now
        </button>
      </div>
    </div>
  );
}
