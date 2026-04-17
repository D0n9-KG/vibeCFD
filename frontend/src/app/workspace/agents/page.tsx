import { redirect } from "next/navigation";

export default function AgentsPage() {
  redirect("/workspace/control-center?tab=agents");
}
