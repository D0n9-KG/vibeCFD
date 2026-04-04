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
