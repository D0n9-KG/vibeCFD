export function buildSkillGraphRequestURL({
  backendBaseURL,
  skillName,
}: {
  backendBaseURL: string;
  skillName?: string;
}) {
  if (!backendBaseURL) {
    const searchParams = new URLSearchParams();
    if (skillName) {
      searchParams.set("skill_name", skillName);
    }

    const search = searchParams.toString();
    return search ? `/api/skills/graph?${search}` : "/api/skills/graph";
  }

  const url = new URL("/api/skills/graph", backendBaseURL);
  if (skillName) {
    url.searchParams.set("skill_name", skillName);
  }
  return url.toString();
}
