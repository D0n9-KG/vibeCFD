"use client";

import { useMemo } from "react";
import type { AnchorHTMLAttributes } from "react";
import type { HTMLAttributes, ReactNode } from "react";

import {
  MessageResponse,
  type MessageResponseProps,
} from "@/components/ai-elements/message";
import { localizeWorkspaceToolName } from "@/core/i18n/workspace-display";
import { streamdownPlugins } from "@/core/streamdown";
import { cn } from "@/lib/utils";

import { CitationLink } from "../citations/citation-link";

function isExternalUrl(href: string | undefined): boolean {
  return !!href && /^https?:\/\//.test(href);
}

function localizeInlineCode(children: ReactNode) {
  if (typeof children !== "string") {
    return children;
  }

  const trimmed = children.trim();
  if (!trimmed || trimmed.includes("\n")) {
    return children;
  }

  const localized = localizeWorkspaceToolName(trimmed);
  return localized === trimmed ? children : localized;
}

export type MarkdownContentProps = {
  content: string;
  isLoading: boolean;
  rehypePlugins: MessageResponseProps["rehypePlugins"];
  className?: string;
  remarkPlugins?: MessageResponseProps["remarkPlugins"];
  components?: MessageResponseProps["components"];
};

/** Renders markdown content. */
export function MarkdownContent({
  content,
  rehypePlugins,
  className,
  remarkPlugins = streamdownPlugins.remarkPlugins,
  components: componentsFromProps,
}: MarkdownContentProps) {
  const components = useMemo(() => {
    return {
      a: (props: AnchorHTMLAttributes<HTMLAnchorElement>) => {
        if (typeof props.children === "string") {
          const match = /^citation:(.+)$/.exec(props.children);
          if (match) {
            const [, text] = match;
            return <CitationLink {...props}>{text}</CitationLink>;
          }
        }
        const { className, target, rel, ...rest } = props;
        const external = isExternalUrl(props.href);
        return (
          <a
            {...rest}
            className={cn("text-primary underline decoration-primary/30 underline-offset-2 hover:decoration-primary/60 transition-colors", className)}
            target={target ?? (external ? "_blank" : undefined)}
            rel={rel ?? (external ? "noopener noreferrer" : undefined)}
          />
        );
      },
      code: (props: HTMLAttributes<HTMLElement>) => {
        const { children, className, ...rest } = props;
        const shouldLocalizeInlineCode =
          !className?.includes("language-") &&
          !className?.includes("hljs") &&
          !className?.includes("shiki");

        return (
          <code {...rest} className={className}>
            {shouldLocalizeInlineCode ? localizeInlineCode(children) : children}
          </code>
        );
      },
      ...componentsFromProps,
    };
  }, [componentsFromProps]);

  if (!content) return null;

  return (
    <MessageResponse
      className={className}
      remarkPlugins={remarkPlugins}
      rehypePlugins={rehypePlugins}
      components={components}
    >
      {content}
    </MessageResponse>
  );
}
