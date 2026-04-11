import assert from "node:assert/strict";
import test from "node:test";

const { buildSubmarineNegotiationPanelModel } = await import(
  new URL("./submarine-negotiation-panel.model.ts", import.meta.url).href,
);

void test("negotiation panel model exposes the visible confirmation callout and CTA when pending items exist", () => {
  const model = buildSubmarineNegotiationPanelModel({
    pendingApprovalCount: 2,
    interruptionVisible: true,
    question: "当前存在待你确认的研究决策，主智能体会先停在协商区。",
    summary: "当前有 2 项待确认事项，其中 2 项属于关键确认。",
    inputGuidance: "请直接在下方输入框逐项确认、补充或修订；你的消息会立即显示在本线程中。",
    pendingItems: [
      {
        id: "reference-length",
        label: "参考长度",
        detail: "需要立即确认；建议值：4.356 m。",
        kind: "plan-item",
        urgency: "immediate",
      },
      {
        id: "reference-area",
        label: "参考面积",
        detail: "需要立即确认；建议值：0.370988 m^2。",
        kind: "plan-item",
        urgency: "immediate",
      },
    ],
  });

  assert.equal(model.visible, true);
  assert.equal(model.title, "待确认事项");
  assert.equal(model.ctaLabel, "前往输入框确认");
  assert.equal(model.items.length, 2);
  assert.equal(model.items[0]?.label, "参考长度");
});

void test("negotiation panel model stays hidden when no confirmation items are present", () => {
  const model = buildSubmarineNegotiationPanelModel({
    pendingApprovalCount: 0,
    interruptionVisible: false,
    question: null,
    summary: null,
    inputGuidance: null,
    pendingItems: [],
  });

  assert.equal(model.visible, false);
  assert.equal(model.ctaLabel, null);
  assert.equal(model.items.length, 0);
});
