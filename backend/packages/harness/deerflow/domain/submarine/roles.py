"""Future-facing submarine sub-agent role boundaries."""

from .models import SubmarineRoleBoundary

ROLE_BOUNDARIES = [
    SubmarineRoleBoundary(
        role_id="task-intelligence",
        title="案例检索与任务理解",
        responsibility=(
            "将用户目标、工况和上传几何映射到最接近的潜艇 CFD 案例模板，"
            "并说明为什么选择它。"
        ),
        inputs=["任务描述", "任务类型", "几何家族线索", "案例库"],
        outputs=["候选案例列表", "推荐案例", "流程建议"],
    ),
    SubmarineRoleBoundary(
        role_id="geometry-preflight",
        title="几何检查与预处理",
        responsibility=(
            "检查 STL 输入、估计尺度、识别几何家族，"
            "并为后续求解准备可追踪的前处理产物。"
        ),
        inputs=["上传几何文件", "潜艇几何经验", "案例上下文"],
        outputs=["几何检查结果", "几何风险提示", "前处理 artifact"],
    ),
    SubmarineRoleBoundary(
        role_id="solver-dispatch",
        title="求解调度",
        responsibility=(
            "把已确认的几何和案例模板映射到受控的求解任务，"
            "后续可自然接入 OpenFOAM 或其他专业求解器。"
        ),
        inputs=["已确认几何", "案例模板", "边界条件与网格策略"],
        outputs=["求解任务描述", "执行日志", "原始求解产物"],
    ),
    SubmarineRoleBoundary(
        role_id="scientific-study",
        title="科学研究变体规划",
        responsibility=(
            "围绕 baseline run 规划网格无关性、域敏感性和时间步敏感性等研究变体，"
            "让研究证据链不只停留在单次求解。"
        ),
        inputs=["baseline 求解设置", "案例 acceptance profile", "simulation requirements"],
        outputs=["study manifest", "研究变体清单", "variant 执行建议"],
    ),
    SubmarineRoleBoundary(
        role_id="experiment-compare",
        title="实验对比整理",
        responsibility=(
            "把 baseline 与研究变体 run 整理成结构化 experiment manifest 和 compare summary，"
            "让差异分析可追踪、可复核。"
        ),
        inputs=["baseline run 记录", "study variant run 记录", "solver metrics"],
        outputs=["experiment manifest", "run compare summary", "对比结论要点"],
    ),
    SubmarineRoleBoundary(
        role_id="scientific-verification",
        title="科学核验",
        responsibility=(
            "依据 verification requirement、study evidence 和 benchmark 情况，"
            "判断当前 run 是否具备更强的科研结论资格。"
        ),
        inputs=["verification artifacts", "acceptance profile", "experiment compare summary"],
        outputs=["scientific verification assessment", "evidence gaps", "claim boundary"],
    ),
    SubmarineRoleBoundary(
        role_id="result-reporting",
        title="结果整理与报告生成",
        responsibility=(
            "把几何检查、求解日志和后处理结果整理成中文报告、摘要和可展示 artifact。"
        ),
        inputs=["几何检查结果", "执行日志", "后处理结果"],
        outputs=["结果摘要", "最终报告", "artifact 清单"],
    ),
    SubmarineRoleBoundary(
        role_id="scientific-followup",
        title="科学跟进",
        responsibility=(
            "根据 scientific remediation handoff 决定是否继续派发研究变体、刷新报告或记录人工后续动作，"
            "让科研闭环可以自然迭代。"
        ),
        inputs=["scientific remediation handoff", "scientific gate", "followup history"],
        outputs=["followup history", "自动跟进结果", "下一轮建议"],
    ),
]


def get_subagent_role_boundaries() -> list[SubmarineRoleBoundary]:
    return list(ROLE_BOUNDARIES)
