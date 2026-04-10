import assert from "node:assert/strict";
import test from "node:test";

import { buildSkillGraphRequestURL } from "./request-url.ts";

void test(
  "buildSkillGraphRequestURL keeps a same-origin relative URL when the backend base URL is empty",
  () => {
    assert.equal(
      buildSkillGraphRequestURL({
        backendBaseURL: "",
        skillName: "submarine-report",
      }),
      "/api/skills/graph?skill_name=submarine-report",
    );
  },
);
