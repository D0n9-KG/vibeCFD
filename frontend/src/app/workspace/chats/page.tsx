import { redirect } from "next/navigation";

export default function ChatsPage() {
  redirect("/workspace/control-center?tab=threads");
}
