import assert from "node:assert/strict";
import test from "node:test";

import {
  getSkillNameFromArchivePath,
  isAlreadyInstalledSkillConflict,
  isInstalledSkillArchive,
} from "./install-utils.ts";

void test("extracts the skill name from a .skill archive path", () => {
  assert.equal(
    getSkillNameFromArchivePath(
      "/mnt/user-data/outputs/submarine/skill-studio/demo-skill/demo-skill.skill",
    ),
    "demo-skill",
  );
  assert.equal(getSkillNameFromArchivePath("/mnt/user-data/outputs/demo.txt"), null);
});

void test("matches installed skills against a .skill archive path", () => {
  assert.equal(
    isInstalledSkillArchive("/mnt/user-data/outputs/demo-skill.skill", [
      { name: "demo-skill" },
      { name: "another-skill" },
    ]),
    true,
  );
  assert.equal(
    isInstalledSkillArchive("/mnt/user-data/outputs/demo-skill.skill", [
      { name: "another-skill" },
    ]),
    false,
  );
});

void test("treats skill install conflicts as already-installed no-op states", () => {
  assert.deepEqual(
    isAlreadyInstalledSkillConflict({
      status: 409,
      detail: "Skill 'demo-skill' already exists. Use overwrite=true to replace it.",
      path: "/mnt/user-data/outputs/demo-skill.skill",
    }),
    {
      alreadyInstalled: true,
      skillName: "demo-skill",
    },
  );
  assert.equal(
    isAlreadyInstalledSkillConflict({
      status: 409,
      detail: "Skill installation failed for another reason.",
      path: "/mnt/user-data/outputs/demo-skill.skill",
    }),
    null,
  );
});
