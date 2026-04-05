"use client";

import { BotIcon, MessageSquareIcon, Trash2Icon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useDeleteAgent } from "@/core/agents";
import type { Agent } from "@/core/agents";
import {
  getAgentDisplayName,
  getAgentModelLabel,
  getAgentToolGroupLabel,
} from "@/core/agents/display";
import { useI18n } from "@/core/i18n/hooks";

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const { t } = useI18n();
  const router = useRouter();
  const deleteAgent = useDeleteAgent();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const displayName = getAgentDisplayName(agent);

  function handleChat() {
    router.push(`/workspace/agents/${agent.name}/chats/new`);
  }

  async function handleDelete() {
    try {
      await deleteAgent.mutateAsync(agent.name);
      toast.success(t.agents.deleteSuccess);
      setDeleteOpen(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <>
      <Card className="group flex h-full flex-col border-slate-200/80 bg-white/88 shadow-[0_18px_44px_rgba(15,23,42,0.06)] transition-all duration-200 hover:-translate-y-0.5 hover:border-cyan-200/80 hover:shadow-[0_24px_60px_rgba(8,145,178,0.12)] dark:border-slate-800/80 dark:bg-slate-950/72 dark:hover:border-cyan-900/70">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-cyan-200/70 bg-cyan-50/80 text-cyan-700 dark:border-cyan-900/70 dark:bg-cyan-950/35 dark:text-cyan-300">
                <BotIcon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <CardTitle className="truncate text-base text-slate-950 dark:text-slate-50">
                  {displayName}
                </CardTitle>
                {agent.model && (
                  <Badge variant="secondary" className="mt-1 text-xs">
                    {getAgentModelLabel(agent.model)}
                  </Badge>
                )}
              </div>
            </div>
          </div>
          {agent.description && (
            <CardDescription className="mt-2 line-clamp-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {agent.description}
            </CardDescription>
          )}
        </CardHeader>

        {agent.tool_groups && agent.tool_groups.length > 0 && (
          <CardContent className="pt-0 pb-3">
            <div className="flex flex-wrap gap-1">
              {agent.tool_groups.map((group) => (
                <Badge
                  key={group}
                  variant="outline"
                  className="border-slate-200/80 bg-white/70 text-xs text-slate-700 dark:border-slate-700/70 dark:bg-slate-900/60 dark:text-slate-300"
                >
                  {getAgentToolGroupLabel(group)}
                </Badge>
              ))}
            </div>
          </CardContent>
        )}

        <CardFooter className="mt-auto flex items-center justify-between gap-2 pt-3">
          <Button size="sm" className="flex-1" onClick={handleChat}>
            <MessageSquareIcon className="mr-1.5 h-3.5 w-3.5" />
            {t.agents.chat}
          </Button>
          <div className="flex gap-1">
            <Button
              size="icon"
              variant="ghost"
              className="text-destructive hover:text-destructive h-8 w-8 shrink-0"
              onClick={() => setDeleteOpen(true)}
              aria-label={t.agents.delete}
              title={t.agents.delete}
            >
              <Trash2Icon className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardFooter>
      </Card>

      {/* Delete Confirm */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t.agents.delete}</DialogTitle>
            <DialogDescription>{t.agents.deleteConfirm}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteOpen(false)}
              disabled={deleteAgent.isPending}
            >
              {t.common.cancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteAgent.isPending}
            >
              {deleteAgent.isPending ? t.common.loading : t.common.delete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
