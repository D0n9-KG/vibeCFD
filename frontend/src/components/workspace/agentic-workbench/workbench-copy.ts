export const WORKBENCH_COPY = {
  common: {
    negotiationRailTitle: "协商区",
    negotiationHint:
      "可随时在协商区输入修改意见，主智能体会停止当前推进并重新协商。",
    pendingLabel: "待确认事项",
    latestJudgementLabel: "最新判断",
    openRailLabel: "展开协商区",
    closeRailLabel: "收起协商区",
    detailsDrawerLabel: "查看详情",
  },
  submarine: {
    modules: {
      proposal: "方案生成",
      decision: "方案敲定",
      delegation: "子代理分工",
      skills: "技能调用",
      execution: "实际计算",
      postprocessMethod: "后处理方法",
      postprocessResult: "后处理结果",
      report: "最终报告",
    },
  },
  skillStudio: {
    modules: {
      intent: "技能意图",
      draft: "技能草案",
      evaluation: "验证与试跑",
      releasePrep: "发布准备",
      lifecycle: "版本与回退",
      graph: "关系网络",
    },
  },
} as const;
