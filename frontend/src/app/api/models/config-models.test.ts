import assert from "node:assert/strict";
import test from "node:test";

const moduleUnderTest = await import(
  new URL("./config-models.ts", import.meta.url).href
);

void test("loadConfiguredModels falls back to built-in models when config.yaml is absent", async () => {
  const previousOpenAIKey = process.env.OPENAI_API_KEY;
  const previousAnthropicKey = process.env.ANTHROPIC_API_KEY;

  process.env.OPENAI_API_KEY = "test-openai-key";
  process.env.ANTHROPIC_API_KEY = "test-anthropic-key";

  try {
    const models = await moduleUnderTest.loadConfiguredModels();

    assert.deepEqual(
      models.map((model) => model.name),
      ["gpt-5.4", "claude-sonnet-4-6"],
    );
    assert.equal(models[0]?.supports_reasoning_effort, true);
    assert.equal(models[1]?.display_name, "Claude Sonnet 4.6");
    assert.equal(models[0]?.is_available, true);
    assert.equal(models[1]?.is_available, true);
    assert.equal(models[0]?.availability_reason, null);
    assert.equal(models[1]?.availability_reason, null);
  } finally {
    process.env.OPENAI_API_KEY = previousOpenAIKey;
    process.env.ANTHROPIC_API_KEY = previousAnthropicKey;
  }
});
