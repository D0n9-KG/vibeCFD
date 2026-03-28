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
        role_id="result-reporting",
        title="结果整理与报告生成",
        responsibility=(
            "把几何检查、求解日志和后处理结果整理成中文报告、摘要和可展示 artifact。"
        ),
        inputs=["几何检查结果", "执行日志", "后处理结果"],
        outputs=["结果摘要", "最终报告", "artifact 清单"],
    ),
]


def get_subagent_role_boundaries() -> list[SubmarineRoleBoundary]:
    return list(ROLE_BOUNDARIES)
