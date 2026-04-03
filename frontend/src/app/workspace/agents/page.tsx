import { AgentGallery } from "@/components/workspace/agents/agent-gallery";

const AGENTS_SURFACE_LABEL = "智能体";

export default function AgentsPage() {
  return <AgentGallery surfaceLabel={AGENTS_SURFACE_LABEL} />;
}
