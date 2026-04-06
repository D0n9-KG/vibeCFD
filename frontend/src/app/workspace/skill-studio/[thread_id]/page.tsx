import { SkillStudioThreadRoute } from "@/components/workspace/skill-studio-workbench/thread-route";

type SkillStudioThreadPageProps = {
  params: Promise<{
    thread_id: string;
  }>;
};

export default async function SkillStudioThreadPage({
  params,
}: SkillStudioThreadPageProps) {
  const { thread_id } = await params;
  return <SkillStudioThreadRoute routeThreadId={thread_id} />;
}
