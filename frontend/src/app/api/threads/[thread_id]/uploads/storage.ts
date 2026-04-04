import fs from "node:fs/promises";
import path from "node:path";

export type UploadedFileInfo = {
  filename: string;
  size: number;
  path: string;
  virtual_path: string;
  artifact_url: string;
  extension?: string;
  modified?: number;
};

const SAFE_THREAD_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

function assertSafeThreadId(threadId: string) {
  if (!SAFE_THREAD_ID_PATTERN.test(threadId)) {
    throw new UploadStorageError(400, "Invalid thread id.");
  }
}

function uploadsDirForThread(threadId: string) {
  assertSafeThreadId(threadId);
  return path.resolve(
    process.cwd(),
    "..",
    "backend",
    ".deer-flow",
    "threads",
    threadId,
    "user-data",
    "uploads",
  );
}

function toRelativeHostPath(threadId: string, filename: string) {
  return path.posix.join(
    ".deer-flow",
    "threads",
    threadId,
    "user-data",
    "uploads",
    filename,
  );
}

function toVirtualPath(filename: string) {
  return `/mnt/user-data/uploads/${filename}`;
}

function toArtifactUrl(threadId: string, filename: string) {
  return `/api/threads/${threadId}/artifacts/mnt/user-data/uploads/${encodeURIComponent(filename)}`;
}

export class UploadStorageError extends Error {
  readonly status: number;

  constructor(
    status: number,
    message: string,
  ) {
    super(message);
    this.name = "UploadStorageError";
    this.status = status;
  }
}

export function sanitizeUploadFilename(filename: string) {
  const rawFilename = (filename ?? "").trim();
  if (rawFilename.includes("/") || rawFilename.includes("\\")) {
    throw new UploadStorageError(400, "Invalid filename.");
  }

  const safeFilename = path.basename(rawFilename).trim();
  if (
    !safeFilename ||
    safeFilename === "." ||
    safeFilename === ".." ||
    safeFilename.includes("/") ||
    safeFilename.includes("\\")
  ) {
    throw new UploadStorageError(400, "Invalid filename.");
  }
  return safeFilename;
}

async function ensureUploadsDir(threadId: string) {
  const uploadsDir = uploadsDirForThread(threadId);
  await fs.mkdir(uploadsDir, { recursive: true });
  return uploadsDir;
}

async function toUploadedFileInfo(
  threadId: string,
  filename: string,
): Promise<UploadedFileInfo> {
  const uploadsDir = uploadsDirForThread(threadId);
  const filePath = path.join(uploadsDir, filename);
  const stat = await fs.stat(filePath);
  return {
    filename,
    size: stat.size,
    path: toRelativeHostPath(threadId, filename),
    virtual_path: toVirtualPath(filename),
    artifact_url: toArtifactUrl(threadId, filename),
    extension: path.extname(filename),
    modified: stat.mtimeMs,
  };
}

export async function saveUploadedFiles(threadId: string, files: File[]) {
  if (files.length === 0) {
    throw new UploadStorageError(400, "No files provided.");
  }

  const uploadsDir = await ensureUploadsDir(threadId);
  const uploadedFiles: UploadedFileInfo[] = [];

  for (const file of files) {
    const filename = sanitizeUploadFilename(file.name);
    const outputPath = path.join(uploadsDir, filename);
    const buffer = Buffer.from(await file.arrayBuffer());
    await fs.writeFile(outputPath, buffer);
    uploadedFiles.push(await toUploadedFileInfo(threadId, filename));
  }

  return {
    success: true,
    files: uploadedFiles,
    message: `Successfully uploaded ${uploadedFiles.length} file(s)`,
  };
}

export async function listThreadUploads(threadId: string) {
  const uploadsDir = uploadsDirForThread(threadId);
  try {
    const entries = await fs.readdir(uploadsDir, { withFileTypes: true });
    const files = await Promise.all(
      entries
        .filter((entry) => entry.isFile())
        .sort((left, right) => left.name.localeCompare(right.name))
        .map((entry) => toUploadedFileInfo(threadId, entry.name)),
    );

    return {
      files,
      count: files.length,
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return {
        files: [],
        count: 0,
      };
    }
    throw error;
  }
}

export async function deleteThreadUpload(threadId: string, filename: string) {
  const safeFilename = sanitizeUploadFilename(filename);
  const uploadsDir = uploadsDirForThread(threadId);
  const filePath = path.join(uploadsDir, safeFilename);

  try {
    await fs.unlink(filePath);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      throw new UploadStorageError(404, `File not found: ${safeFilename}`);
    }
    throw error;
  }

  return {
    success: true,
    message: `Deleted ${safeFilename}`,
  };
}
