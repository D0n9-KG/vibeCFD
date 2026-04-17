import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./runtime-config-tab.tsx", import.meta.url),
  "utf8",
);

void test("runtime config tab consumes runtime config plus runtime model registry hooks and renders model-centric controls", () => {
  assert.match(source, /useRuntimeConfig/);
  assert.match(source, /useUpdateRuntimeConfig/);
  assert.match(source, /useRuntimeModels/);
  assert.match(source, /useCreateRuntimeModel/);
  assert.match(source, /useUpdateRuntimeModel/);
  assert.match(source, /useDeleteRuntimeModel/);
  assert.match(source, /lead_agent/);
  assert.match(source, /stage_roles/);
  assert.match(source, /provider_key/);
  assert.match(source, /base_url/);
  assert.match(source, /api_key/);
  assert.match(source, /clear_api_key/);
  assert.match(source, /type="password"/);
  assert.match(source, /模型注册表|模型目录/);
  assert.match(source, /主代理默认模型|路由规则/);
  assert.match(source, /SelectTrigger/);
  assert.match(source, /Button/);
  assert.match(source, /Dialog/);
  assert.match(source, /Switch/);
  assert.match(source, /WorkspaceStatePanel/);
});
