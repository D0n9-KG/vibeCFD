"use client";

import Link from "next/link";
import { MessageSquareIcon, SearchIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Input } from "@/components/ui/input";
import {
  WorkspaceSurfaceCard,
  WorkspaceSurfaceMain,
  WorkspaceSurfacePage,
} from "@/components/workspace/workspace-container";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import { useI18n } from "@/core/i18n/hooks";
import { useThreads } from "@/core/threads/hooks";
import { pathOfThread, titleOfThread } from "@/core/threads/utils";
import { formatTimeAgo } from "@/core/utils/datetime";

const CHAT_SURFACE_LABEL = "对话";

export default function ChatsPage() {
  const { t } = useI18n();
  const { data: threads = [], isLoading, error } = useThreads();
  const [search, setSearch] = useState("");

  useEffect(() => {
    document.title = `${t.pages.chats} - ${t.pages.appName}`;
  }, [t.pages.chats, t.pages.appName]);

  const filteredThreads = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    if (!normalized) {
      return threads;
    }

    return threads.filter((thread) =>
      titleOfThread(thread).toLowerCase().includes(normalized),
    );
  }, [search, threads]);

  return (
    <WorkspaceSurfacePage data-surface-label={CHAT_SURFACE_LABEL}>
      <WorkspaceSurfaceMain className="max-w-[1840px]">
        <WorkspaceSurfaceCard className="overflow-hidden">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="min-w-0 flex-1">
              <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
                {CHAT_SURFACE_LABEL}
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-stone-900">
                {t.pages.chats}
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-stone-600">
                {t.chats.overviewDescription}
              </p>
            </div>

            <div className="w-full xl:max-w-md">
              <div className="relative">
                <SearchIcon className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-stone-400" />
                <Input
                  type="search"
                  className="h-12 rounded-2xl border-stone-200 bg-white pl-11 text-base shadow-sm"
                  placeholder={t.chats.searchChats}
                  autoFocus
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
            </div>
          </div>
        </WorkspaceSurfaceCard>

        {error ? (
          <WorkspaceStatePanel
            state="update-failed"
            actions={[
              {
                label: t.workspace.retryUpdate,
                onClick: () => window.location.reload(),
              },
            ]}
          />
        ) : isLoading ? (
          <WorkspaceSurfaceCard>
            <div className="flex min-h-[16rem] items-center justify-center text-sm text-stone-500">
              {t.common.loading}
            </div>
          </WorkspaceSurfaceCard>
        ) : filteredThreads.length === 0 && threads.length === 0 ? (
          <WorkspaceStatePanel
            state="first-run"
            actions={[
              {
                label: t.sidebar.newChat,
                href: "/workspace/chats/new",
              },
            ]}
          />
        ) : filteredThreads.length === 0 ? (
          <WorkspaceSurfaceCard>
            <div className="flex min-h-[16rem] flex-col items-center justify-center gap-3 text-center">
              <div className="flex size-14 items-center justify-center rounded-full bg-stone-100 text-stone-500">
                <MessageSquareIcon className="size-6" />
              </div>
              <div className="space-y-1">
                <div className="text-base font-semibold text-stone-900">
                  {t.chats.emptySearchTitle}
                </div>
                <p className="text-sm leading-6 text-stone-500">
                  {t.chats.emptySearchDescription}
                </p>
              </div>
            </div>
          </WorkspaceSurfaceCard>
        ) : (
          <WorkspaceSurfaceCard className="min-h-0 overflow-hidden p-0">
            <div className="border-b border-stone-200/80 px-5 py-4">
              <div className="text-sm font-medium text-stone-900">
                {t.common.threadCount(filteredThreads.length)}
              </div>
              <div className="mt-1 text-sm text-stone-500">
                {t.chats.listDescription}
              </div>
            </div>

            <div className="divide-y divide-stone-200/80">
              {filteredThreads.map((thread) => (
                <Link
                  key={thread.thread_id}
                  href={pathOfThread(thread.thread_id)}
                  className="group flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-stone-50/80"
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-stone-900">
                      {titleOfThread(thread)}
                    </div>
                    <div className="mt-1 truncate text-sm text-stone-500">
                      {thread.updated_at
                        ? formatTimeAgo(thread.updated_at)
                        : t.chats.recentlyUpdated}
                    </div>
                  </div>
                  <div className="rounded-full border border-stone-200/80 px-3 py-1 text-xs font-medium text-stone-500 transition-colors group-hover:border-stone-300 group-hover:text-stone-700">
                    {t.common.open}
                  </div>
                </Link>
              ))}
            </div>
          </WorkspaceSurfaceCard>
        )}
      </WorkspaceSurfaceMain>
    </WorkspaceSurfacePage>
  );
}
