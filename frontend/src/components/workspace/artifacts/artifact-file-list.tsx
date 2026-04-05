import { DownloadIcon, LoaderIcon, PackageIcon } from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { urlOfArtifact } from "@/core/artifacts/utils";
import { useI18n } from "@/core/i18n/hooks";
import { installSkill } from "@/core/skills/api";
import {
  getFileExtensionDisplayName,
  getFileIcon,
  getFileName,
} from "@/core/utils/files";
import { cn } from "@/lib/utils";

import { useThread } from "../messages/context";

import { useArtifacts } from "./context";

export function ArtifactFileList({
  className,
  files,
  threadId,
}: {
  className?: string;
  files: string[];
  threadId: string;
}) {
  const { t } = useI18n();
  const { select: selectArtifact, setOpen } = useArtifacts();
  const { isMock } = useThread();
  const [installingFile, setInstallingFile] = useState<string | null>(null);

  const handleClick = useCallback(
    (filepath: string) => {
      selectArtifact(filepath);
      setOpen(true);
    },
    [selectArtifact, setOpen],
  );

  const handleInstallSkill = useCallback(
    async (event: React.MouseEvent, filepath: string) => {
      event.stopPropagation();
      event.preventDefault();

      if (installingFile) {
        return;
      }

      setInstallingFile(filepath);
      try {
        const result = await installSkill({
          thread_id: threadId,
          path: filepath,
        });
        if (result.success) {
          toast.success(result.message);
        } else {
          toast.error(result.message || "Failed to install skill");
        }
      } catch (error) {
        console.error("Failed to install skill:", error);
        toast.error("Failed to install skill");
      } finally {
        setInstallingFile(null);
      }
    },
    [installingFile, threadId],
  );

  return (
    <ul className={cn("flex w-full flex-col gap-4", className)}>
      {files.map((file) => (
        <li key={file}>
          <Card
            className="relative cursor-pointer border-slate-200/80 bg-white/88 p-3 shadow-[0_12px_32px_rgba(15,23,42,0.06)] transition-all hover:border-sky-200/80 hover:shadow-[0_18px_44px_rgba(14,165,233,0.10)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/60 dark:border-slate-800/80 dark:bg-slate-950/72 dark:hover:border-sky-900/70"
          >
            <CardHeader className="pr-2 pl-1">
              <button
                type="button"
                className="col-start-1 row-span-2 row-start-1 min-w-0 text-left"
                onClick={() => handleClick(file)}
              >
                <CardTitle className="relative pl-8">
                  <div>{getFileName(file)}</div>
                  <div className="absolute top-2 -left-0.5">
                    {getFileIcon(file, "size-6")}
                  </div>
                </CardTitle>
                <CardDescription className="pl-8 text-xs">
                  {getFileExtensionDisplayName(file)} 文件
                </CardDescription>
              </button>
              <CardAction className="flex items-center gap-1">
                {file.endsWith(".skill") && (
                  <Button
                    variant="ghost"
                    disabled={installingFile === file}
                    onClick={(event) => handleInstallSkill(event, file)}
                  >
                    {installingFile === file ? (
                      <LoaderIcon className="size-4 animate-spin" />
                    ) : (
                      <PackageIcon className="size-4" />
                    )}
                    {t.common.install}
                  </Button>
                )}
                <a
                  href={urlOfArtifact({
                    filepath: file,
                    threadId,
                    download: true,
                    isMock,
                  })}
                  target="_blank"
                  rel="noreferrer"
                  onClick={(event) => event.stopPropagation()}
                >
                  <Button variant="ghost">
                    <DownloadIcon className="size-4" />
                    {t.common.download}
                  </Button>
                </a>
              </CardAction>
            </CardHeader>
          </Card>
        </li>
      ))}
    </ul>
  );
}
