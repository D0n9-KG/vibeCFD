"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo } from "react";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { useI18n } from "@/core/i18n/hooks";
import { cn } from "@/lib/utils";

import { GithubIcon } from "./github-icon";
import { Tooltip } from "./tooltip";

export function WorkspaceContainer({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div className={cn("flex h-screen w-full flex-col", className)} {...props}>
      {children}
    </div>
  );
}

export function WorkspaceHeader({
  className,
  children,
  ...props
}: React.ComponentProps<"header">) {
  const { t } = useI18n();
  const pathname = usePathname();
  const segments = useMemo(() => {
    const parts = pathname?.split("/") || [];
    if (parts.length > 0) {
      return parts.slice(1, 3);
    }
  }, [pathname]);
  return (
    <header
      className={cn(
        "top-0 right-0 left-0 z-20 flex h-16 shrink-0 items-center justify-between gap-2 border-b backdrop-blur-sm transition-[width,height] ease-out group-has-data-[collapsible=icon]/sidebar-wrapper:h-12",
        className,
      )}
      {...props}
    >
      <div className="flex items-center gap-2 px-4">
        <Breadcrumb>
          <BreadcrumbList>
            {segments?.[0] && (
              <BreadcrumbItem className="hidden md:block">
                <BreadcrumbLink asChild>
                  <Link href={`/${segments[0]}`}>
                    {nameOfSegment(segments[0], t)}
                  </Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
            )}
            {segments?.[1] && (
              <>
                <BreadcrumbSeparator className="hidden md:block" />
                <BreadcrumbItem>
                  {segments.length >= 2 ? (
                    <BreadcrumbLink asChild>
                      <Link href={`/${segments[0]}/${segments[1]}`}>
                        {nameOfSegment(segments[1], t)}
                      </Link>
                    </BreadcrumbLink>
                  ) : (
                    <BreadcrumbPage>
                      {nameOfSegment(segments[1], t)}
                    </BreadcrumbPage>
                  )}
                </BreadcrumbItem>
              </>
            )}
            {children && (
              <>
                <BreadcrumbSeparator />
                {children}
              </>
            )}
          </BreadcrumbList>
        </Breadcrumb>
      </div>
      <div className="pr-4">
        <Tooltip content={t.workspace.githubTooltip}>
          <a
            href="https://github.com/bytedance/deer-flow"
            target="_blank"
            rel="noopener noreferrer"
            className="opacity-75 transition hover:opacity-100"
          >
            <GithubIcon className="size-6" />
          </a>
        </Tooltip>
      </div>
    </header>
  );
}

export function WorkspaceBody({
  className,
  children,
  ...props
}: React.ComponentProps<"main">) {
  return (
    <main
      className={cn(
        "relative flex min-h-0 w-full flex-1 flex-col items-center",
        className,
      )}
      {...props}
    >
      <div className="flex h-full w-full flex-col items-center">{children}</div>
    </main>
  );
}

export function WorkspaceSurfacePage({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "workspace-surface-page flex size-full min-h-0 flex-col overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.08),_transparent_28%),linear-gradient(180deg,_rgba(247,244,238,0.96),_rgba(255,255,255,0.98))]",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function WorkspaceSurfaceMain({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "mx-auto flex w-full max-w-[1600px] flex-1 min-h-0 flex-col gap-4 overflow-y-auto px-4 py-4",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function WorkspaceSurfaceCard({
  className,
  children,
  ...props
}: React.ComponentProps<"section">) {
  return (
    <section
      className={cn(
        "rounded-[28px] border border-stone-200/80 bg-white/92 p-5 shadow-[0_18px_44px_rgba(15,23,42,0.06)]",
        className,
      )}
      {...props}
    >
      {children}
    </section>
  );
}

function nameOfSegment(
  segment: string | undefined,
  t: ReturnType<typeof useI18n>["t"],
) {
  if (!segment) return t.common.home;
  if (segment === "workspace") return t.breadcrumb.workspace;
  if (segment === "chats") return t.breadcrumb.chats;
  return segment[0]?.toUpperCase() + segment.slice(1);
}
