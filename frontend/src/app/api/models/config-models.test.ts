import assert from "node:assert/strict";
import fs from "node:fs/promises";
import test from "node:test";

const moduleUnderTest = await import(
  new URL("./config-models.ts", import.meta.url).href
);

void test("parseModelsFromSource extracts the checked-in chat models from config.yaml", async () => {
  const source = await fs.readFile(
    new URL("../../../../../config.yaml", import.meta.url),
    "utf8",
  );

  const models = moduleUnderTest.parseModelsFromSource(source);

  assert.deepEqual(
    models.map((model) => model.name),
    ["gpt-5.4", "claude-sonnet-4-6"],
  );
  assert.equal(models[0]?.supports_reasoning_effort, true);
  assert.equal(models[1]?.display_name, "Claude Sonnet 4.6");
});
