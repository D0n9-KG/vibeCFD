import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./api.ts", import.meta.url), "utf8");

void test("runtime config api reads the canonical backend summary endpoint", () => {
  assert.match(source, /\/api\/runtime-config/);
  assert.match(source, /getBackendBaseURL/);
});

void test("runtime config api exposes a canonical update endpoint for persisted overrides", () => {
  assert.match(source, /method:\s*"PUT"/);
  assert.match(source, /JSON\.stringify/);
});

void test("runtime config api also exposes runtime model registry CRUD helpers", () => {
  assert.match(source, /\/api\/runtime-models/);
  assert.match(source, /export async function loadRuntimeModels/);
  assert.match(source, /export async function createRuntimeModel/);
  assert.match(source, /export async function updateRuntimeModel/);
  assert.match(source, /export async function deleteRuntimeModel/);
  assert.match(source, /method:\s*"POST"/);
  assert.match(source, /method:\s*"DELETE"/);
  assert.match(source, /clear_api_key/);
});
