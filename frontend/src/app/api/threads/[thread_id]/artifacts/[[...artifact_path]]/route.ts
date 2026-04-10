import fs from "node:fs/promises";
import path from "node:path";

import type { NextRequest } from "next/server";

import { requireThreadRouteSession } from "../../../_auth";

function buildCandidatePaths(threadId: string, artifactPath: string) {
  if (!artifactPath.startsWith("mnt/user-data/")) {
    return [];
  }

  const relativeArtifactPath = artifactPath.replace(/^mnt\/user-data\//, "user-data/");
  return [
    path.resolve(
      process.cwd(),
      "..",
      "backend",
      ".deer-flow",
      "threads",
      threadId,
      relativeArtifactPath,
    ),
    path.resolve(
      process.cwd(),
      "public",
      "demo",
      "threads",
      threadId,
      relativeArtifactPath,
    ),
  ];
}

function contentTypeFor(filePath: string) {
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".md")) return "text/markdown; charset=utf-8";
  if (filePath.endsWith(".txt") || filePath.endsWith(".log")) {
    return "text/plain; charset=utf-8";
  }
  if (filePath.endsWith(".csv")) return "text/csv; charset=utf-8";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".webp")) return "image/webp";
  if (filePath.endsWith(".pdf")) return "application/pdf";
  if (filePath.endsWith(".mp4")) return "video/mp4";
  return "application/octet-stream";
}

export async function GET(
  request: NextRequest,
  context: {
    params: Promise<{
      thread_id: string;
      artifact_path?: string[] | undefined;
    }>;
  },
) {
  const unauthorizedResponse = await requireThreadRouteSession();
  if (unauthorizedResponse) {
    return unauthorizedResponse;
  }

  const { thread_id: threadId, artifact_path: artifactPathSegments } =
    await context.params;
  const artifactPath = artifactPathSegments?.join("/") ?? "";

  for (const candidatePath of buildCandidatePaths(threadId, artifactPath)) {
    try {
      const fileBuffer = await fs.readFile(candidatePath);
      const headers = new Headers({
        "Content-Type": contentTypeFor(candidatePath),
        "Cache-Control": "no-store",
      });

      if (request.nextUrl.searchParams.get("download") === "true") {
        headers.set(
          "Content-Disposition",
          `attachment; filename="${path.basename(candidatePath)}"`,
        );
      }

      return new Response(fileBuffer, {
        status: 200,
        headers,
      });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
        throw error;
      }
    }
  }

  return Response.json({ detail: "Artifact not found." }, { status: 404 });
}
