import { SubmarineThreadRoute } from "@/components/workspace/submarine-workbench/thread-route";

type SubmarineThreadPageProps = {
  params: Promise<{
    thread_id: string;
  }>;
};

export default async function SubmarineThreadPage({
  params,
}: SubmarineThreadPageProps) {
  const { thread_id } = await params;
  return <SubmarineThreadRoute routeThreadId={thread_id} />;
}
