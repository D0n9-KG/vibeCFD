import type { Skill } from "./type";

export function getSkillNameFromArchivePath(path: string) {
  const filename = path.split("/").at(-1) ?? "";
  if (!filename.endsWith(".skill")) {
    return null;
  }

  const skillName = filename.slice(0, -".skill".length).trim();
  return skillName.length > 0 ? skillName : null;
}

export function isInstalledSkillArchive(
  path: string,
  skills: Array<Pick<Skill, "name">>,
) {
  const skillName = getSkillNameFromArchivePath(path);
  if (!skillName) {
    return false;
  }

  return skills.some((skill) => skill.name === skillName);
}

export function isAlreadyInstalledSkillConflict(input: {
  status: number;
  detail?: string | null;
  path: string;
}) {
  if (input.status !== 409) {
    return null;
  }

  const detail = input.detail?.trim();
  if (!detail || !/already exists/i.test(detail)) {
    return null;
  }

  const skillMatch = /Skill '([^']+)' already exists/i.exec(detail);
  const skillName = skillMatch?.[1] ?? getSkillNameFromArchivePath(input.path);

  if (!skillName) {
    return null;
  }

  return {
    alreadyInstalled: true as const,
    skillName,
  };
}
