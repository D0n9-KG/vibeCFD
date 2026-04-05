"use client";

import {
  ArrowUpRightIcon,
  MessageSquareIcon,
  SearchIcon,
  WavesIcon,
} from "lucide-react";
import Link from "next/link";
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
      titleOfThread(thread, t.pages.untitled).toLowerCase().includes(normalized),
    );
  }, [search, t.pages.untitled, threads]);

  const latestUpdatedAt = filteredThreads[0]?.updated_at
    ? formatTimeAgo(filteredThreads[0].updated_at)
    : t.chats.recentlyUpdated;

  return (
    <WorkspaceSurfacePage data-surface-label={t.pages.chats}>
      <WorkspaceSurfaceMain className="max-w-[1840px]">
        <WorkspaceSurfaceCard className="overflow-hidden">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
            <div className="min-w-0">
              <div className="workspace-kicker text-sky-700 dark:text-sky-300">
                Conversation Atlas
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
                {t.pages.chats}
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700 dark:text-slate-300">
                {t.chats.overviewDescription}
              </p>

              <div className="mt-5 flex flex-wrap gap-2">
                <div className="metric-chip">
                  <MessageSquareIcon className="size-3.5" />
                  {t.common.threadCount(threads.length)}
                </div>
                <div className="metric-chip">
                  <WavesIcon className="size-3.5" />
                  {latestUpdatedAt}
                </div>
                <div className="metric-chip">
                  <ArrowUpRightIcon className="size-3.5" />
                  {search.trim() ? t.chats.searchChats : t.chats.listDescription}
                </div>
              </div>
            </div>

            <div className="control-panel flex flex-col justify-between gap-4">
              <div>
                <div className="workspace-kicker text-slate-500 dark:text-slate-400">
                  Retrieval
                </div>
                <div className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                  搜索线程与最近上下文
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  快速定位需要继续推进、复核或导出证据链的对话线程。
                </p>
              </div>

              <div className="relative">
                <label htmlFor="workspace-chat-search" className="sr-only">
                  {t.chats.searchChats}
                </label>
                <SearchIcon className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                <Input
                  id="workspace-chat-search"
                  name="workspace-chat-search"
                  type="search"
                  aria-label={t.chats.searchChats}
                  className="h-12 rounded-2xl border-slate-200/80 bg-white/90 pl-11 text-base text-slate-900 shadow-sm shadow-slate-950/5 dark:border-slate-700/70 dark:bg-slate-950/55 dark:text-slate-100"
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
            <div className="flex min-h-[16rem] items-center justify-center text-sm text-slate-500 dark:text-slate-400">
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
              <div className="flex size-14 items-center justify-center rounded-full border border-slate-200/80 bg-slate-100/80 text-slate-500 dark:border-slate-700/70 dark:bg-slate-900/70 dark:text-slate-400">
                <MessageSquareIcon className="size-6" />
              </div>
              <div className="space-y-1">
                <div className="text-base font-semibold text-slate-950 dark:text-slate-50">
                  {t.chats.emptySearchTitle}
                </div>
                <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {t.chats.emptySearchDescription}
                </p>
              </div>
            </div>
          </WorkspaceSurfaceCard>
        ) : (
          <WorkspaceSurfaceCard className="min-h-0 overflow-hidden p-0">
            <div className="border-b border-slate-200/80 px-5 py-4 dark:border-slate-800/80">
              <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                {t.common.threadCount(filteredThreads.length)}
              </div>
              <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                {t.chats.listDescription}
              </div>
            </div>

            <ul className="divide-y divide-slate-200/80 dark:divide-slate-800/80">
              {filteredThreads.map((thread) => (
                <li key={thread.thread_id}>
                  <Link
                    href={pathOfThread(thread.thread_id)}
                    className="group flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-slate-50/80 dark:hover:bg-slate-900/40"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-slate-950 dark:text-slate-50">
                        {titleOfThread(thread, t.pages.untitled)}
                      </div>
                      <div className="mt-1 truncate text-sm text-slate-600 dark:text-slate-300">
                        {thread.updated_at
                          ? formatTimeAgo(thread.updated_at)
                          : t.chats.recentlyUpdated}
                      </div>
                    </div>
                    <div className="rounded-full border border-slate-200/80 bg-white/80 px-3 py-1 text-xs font-medium text-slate-600 transition-colors group-hover:border-sky-200 group-hover:text-sky-700 dark:border-slate-700/70 dark:bg-slate-950/60 dark:text-slate-300 dark:group-hover:border-sky-800/70 dark:group-hover:text-sky-300">
                      {t.common.open}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </WorkspaceSurfaceCard>
        )}
      </WorkspaceSurfaceMain>
    </WorkspaceSurfacePage>
  );
}
