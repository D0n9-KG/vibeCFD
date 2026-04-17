export type WorkspaceSurfaceId =
  | "submarine"
  | "skill-studio"
  | "agents"
  | "control-center";

export type WorkspaceSurface = {
  id: WorkspaceSurfaceId;
  label: string;
  defaultHref: string;
  pathPrefixes: readonly string[];
  primaryNavigation: boolean;
};

export type WorkspaceSurfaceHrefOptions = {
  isMock?: boolean;
  staticWebsiteOnly?: boolean;
};

export const WORKSPACE_SURFACES: readonly WorkspaceSurface[] = [
  {
    id: "submarine",
    label: "仿真工作台",
    defaultHref: "/workspace/submarine/new",
    pathPrefixes: ["/workspace/submarine"],
    primaryNavigation: true,
  },
  {
    id: "skill-studio",
    label: "技能工作台",
    defaultHref: "/workspace/skill-studio/new",
    pathPrefixes: ["/workspace/skill-studio"],
    primaryNavigation: true,
  },
  {
    id: "agents",
    label: "智能体",
    defaultHref: "/workspace/agents",
    pathPrefixes: ["/workspace/agents"],
    primaryNavigation: false,
  },
  {
    id: "control-center",
    label: "管理中心",
    defaultHref: "/workspace/control-center",
    pathPrefixes: ["/workspace/control-center"],
    primaryNavigation: true,
  },
] as const;

export const PRIMARY_WORKSPACE_SURFACES = WORKSPACE_SURFACES.filter(
  (surface) => surface.primaryNavigation,
);

export function getWorkspaceSurfaceById(id: WorkspaceSurfaceId) {
  const surface = WORKSPACE_SURFACES.find((entry) => entry.id === id);
  if (!surface) {
    throw new Error(`Unknown workspace surface: ${id}`);
  }
  return surface;
}

export function getWorkspaceSurfaceHref(
  id: WorkspaceSurfaceId,
  options: WorkspaceSurfaceHrefOptions = {},
) {
  const surface = getWorkspaceSurfaceById(id);
  if (
    surface.id === "skill-studio" &&
    (options.isMock || options.staticWebsiteOnly)
  ) {
    return `${surface.defaultHref}?mock=true`;
  }
  return surface.defaultHref;
}

export function isWorkspaceSurfaceActive(
  surface: WorkspaceSurface | WorkspaceSurfaceId,
  pathname: string,
) {
  const target =
    typeof surface === "string" ? getWorkspaceSurfaceById(surface) : surface;
  return target.pathPrefixes.some((prefix) => pathname.startsWith(prefix));
}

export function matchWorkspaceSurface(pathname: string) {
  return (
    WORKSPACE_SURFACES.find((surface) =>
      isWorkspaceSurfaceActive(surface, pathname),
    ) ?? getWorkspaceSurfaceById("submarine")
  );
}
