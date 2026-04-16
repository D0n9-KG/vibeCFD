import { useQueryClient } from "@tanstack/react-query";
import { DownloadIcon, EyeIcon, LoaderIcon, PackageIcon } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
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
import { useSkills } from "@/core/skills/hooks";
import {
  getSkillNameFromArchivePath,
  isInstalledSkillArchive,
} from "@/core/skills/install-utils";
import {
  getFileExtensionDisplayName,
  getFileIcon,
} from "@/core/utils/files";
import { cn } from "@/lib/utils";

import { useThread } from "../messages/context";

import { useArtifacts } from "./context";
import { buildArtifactListSections, getArtifactDisplayName } from "./display";

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
  const queryClient = useQueryClient();
  const hasSkillArchives = useMemo(
    () => files.some((file) => file.endsWith(".skill")),
    [files],
  );
  const sections = useMemo(() => buildArtifactListSections(files), [files]);
  const { skills } = useSkills({ enabled: hasSkillArchives });
  const [installingFile, setInstallingFile] = useState<string | null>(null);
  const [installedFiles, setInstalledFiles] = useState<string[]>([]);
  const installedFileSet = useMemo(
    () => new Set(installedFiles),
    [installedFiles],
  );

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

      if (
        installingFile ||
        installedFileSet.has(filepath) ||
        isInstalledSkillArchive(filepath, skills)
      ) {
        return;
      }

      setInstallingFile(filepath);
      try {
        const result = await installSkill({
          thread_id: threadId,
          path: filepath,
        });
        if (result.success) {
          setInstalledFiles((current) =>
            current.includes(filepath) ? current : [...current, filepath],
          );
          void queryClient.invalidateQueries({ queryKey: ["skills"] });
          const skillName =
            (result.skill_name
              ? result.skill_name
              : getSkillNameFromArchivePath(filepath)) ??
            t.common.installed;
          toast.success(
            result.already_installed
              ? t.toolCalls.skillAlreadyInstalledMessage(skillName)
              : t.toolCalls.skillInstallSuccessMessage(skillName),
          );
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
    [installingFile, installedFileSet, queryClient, skills, t, threadId],
  );

  return (
    <div className={cn("flex w-full flex-col gap-6", className)}>
      {sections.map((section) => (
        <section key={section.id} className="flex flex-col gap-3">
          <div className="px-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-slate-900">{section.title}</h3>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                {section.files.length} 项
              </span>
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-500">{section.description}</p>
          </div>
          <ul className="flex flex-col gap-4">
            {section.files.map((file) => {
              const isSkillInstalled =
                installedFileSet.has(file) || isInstalledSkillArchive(file, skills);

              return (
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
                          <div>{getArtifactDisplayName(file)}</div>
                          <div className="absolute top-2 -left-0.5">
                            {getFileIcon(file, "size-6")}
                          </div>
                        </CardTitle>
                        <CardDescription className="pl-8 text-xs">
                          {getFileExtensionDisplayName(file)} 文件
                        </CardDescription>
                      </button>
                      <CardAction className="flex items-center gap-1">
                        <Button variant="ghost" onClick={() => handleClick(file)}>
                          <EyeIcon className="size-4" />
                          预览
                        </Button>
                        {file.endsWith(".skill") && (
                          <Button
                            variant="ghost"
                            disabled={installingFile === file || isSkillInstalled}
                            onClick={(event) => handleInstallSkill(event, file)}
                          >
                            {installingFile === file ? (
                              <LoaderIcon className="size-4 animate-spin" />
                            ) : (
                              <PackageIcon className="size-4" />
                            )}
                            {isSkillInstalled ? t.common.installed : t.common.install}
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
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
