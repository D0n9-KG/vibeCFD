import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./skills-tab.tsx", import.meta.url), "utf8");

void test("skills tab consumes lifecycle, graph, file tree, preview hooks, and runtime stage-role context", () => {
  assert.match(source, /useSkills/);
  assert.match(source, /useSkillLifecycleSummaries/);
  assert.match(source, /useSkillLifecycle/);
  assert.match(source, /useSkillGraph/);
  assert.match(source, /useSkillFiles/);
  assert.match(source, /useSkillFileContent/);
  assert.match(source, /useRuntimeConfig/);
  assert.match(source, /useEnableSkill/);
  assert.match(source, /useRollbackSkillRevision/);
  assert.match(source, /Button/);
  assert.match(source, /binding_targets/);
  assert.match(source, /WorkspaceStatePanel/);
  assert.match(source, /max-h-\[calc\(100vh-12rem\)\] overflow-y-auto/);
  assert.match(source, /self-start/);
  assert.match(source, /searchQuery/);
  assert.match(source, /setSearchQuery/);
  assert.match(source, /filteredSkills/);
  assert.match(source, /Input/);
  assert.match(source, /placeholder="搜索技能名称"/);
  assert.match(source, /filteredSkills\.length === 0/);
  assert.match(source, /useEffect/);
  assert.match(
    source,
    /useEffect\(\(\) => \{\s*setSelectedFilePath\(null\);\s*\}, \[resolvedSkillName\]\)/,
  );
  assert.doesNotMatch(source, /max-h-\[60vh\]/);
  assert.doesNotMatch(source, /flex-1 min-h-0 overflow-y-auto/);
});
