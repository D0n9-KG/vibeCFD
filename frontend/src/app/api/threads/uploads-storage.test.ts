import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";

const storageModule = await import(
  new URL("./[thread_id]/uploads/storage.ts", import.meta.url).href
);

void test("sanitizeUploadFilename rejects traversal-like names", () => {
  assert.throws(() => storageModule.sanitizeUploadFilename("../secret.txt"));
  assert.throws(() => storageModule.sanitizeUploadFilename("..\\secret.txt"));
  assert.equal(storageModule.sanitizeUploadFilename("safe.stl"), "safe.stl");
});

void test("upload storage routes files into the backend thread uploads directory", async () => {
  const threadId = "upload-test-thread";
  const filename = "demo.stl";
  const threadDir = path.resolve(
    process.cwd(),
    "..",
    "backend",
    ".deer-flow",
    "threads",
    threadId,
  );
  const uploadsDir = path.join(threadDir, "user-data", "uploads");

  await fs.rm(threadDir, {
    recursive: true,
    force: true,
  });

  const file = new File(["solid demo"], filename, {
    type: "model/stl",
  });

  const response = await storageModule.saveUploadedFiles(threadId, [file]);
  assert.equal(response.success, true);
  assert.equal(
    response.files[0]?.virtual_path,
    `/mnt/user-data/uploads/${filename}`,
  );

  const persisted = await fs.readFile(path.join(uploadsDir, filename), "utf8");
  assert.equal(persisted, "solid demo");

  const list = await storageModule.listThreadUploads(threadId);
  assert.equal(list.count, 1);
  assert.equal(list.files[0]?.filename, filename);

  const deleted = await storageModule.deleteThreadUpload(threadId, filename);
  assert.equal(deleted.success, true);

  const listAfterDelete = await storageModule.listThreadUploads(threadId);
  assert.equal(listAfterDelete.count, 0);

  await fs.rm(threadDir, {
    recursive: true,
    force: true,
  });
});

void test("upload storage rejects files above the per-file size limit", async () => {
  const hugeFile = new File(
    [new Uint8Array(25 * 1024 * 1024 + 1)],
    "oversized.stl",
    {
      type: "model/stl",
    },
  );

  await assert.rejects(
    () => storageModule.saveUploadedFiles("upload-test-thread", [hugeFile]),
    /File too large/i,
  );
});

void test("upload storage rejects blocked executable extensions", async () => {
  const blockedFile = new File(["echo nope"], "payload.exe", {
    type: "application/octet-stream",
  });

  await assert.rejects(
    () => storageModule.saveUploadedFiles("upload-test-thread", [blockedFile]),
    /File type is not allowed/i,
  );
});

void test("upload storage rejects thread budgets that exceed the configured count or size quota", () => {
  assert.throws(
    () =>
      storageModule.assertThreadUploadQuota({
        existingFiles: [
          { filename: "a.stl", size: 4 },
          { filename: "b.stl", size: 4 },
        ],
        incomingFiles: [{ filename: "c.stl", size: 2 }],
        maxFileCount: 2,
        maxTotalBytes: 20,
      }),
    /Too many uploaded files/i,
  );

  assert.throws(
    () =>
      storageModule.assertThreadUploadQuota({
        existingFiles: [{ filename: "a.stl", size: 8 }],
        incomingFiles: [{ filename: "b.stl", size: 5 }],
        maxFileCount: 4,
        maxTotalBytes: 10,
      }),
    /Total upload quota exceeded/i,
  );
});
