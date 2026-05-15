import { redirect } from "next/navigation";

// Server component — just redirect to auth entry
export default function Root() {
  redirect("/auth/phone");
}
