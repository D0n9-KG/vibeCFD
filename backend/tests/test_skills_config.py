from deerflow.config import skills_config as skills_config_module
from deerflow.config.skills_config import SkillsConfig


def test_get_skills_path_resolves_relative_paths_from_process_start_dir(tmp_path, monkeypatch):
    start_dir = tmp_path / "backend"
    start_dir.mkdir(parents=True)
    monkeypatch.setattr(skills_config_module, "_PROCESS_START_DIR", start_dir)

    def _blocked_cwd():
        raise AssertionError("get_skills_path should not call Path.cwd at runtime")

    monkeypatch.setattr(skills_config_module.Path, "cwd", _blocked_cwd)

    config = SkillsConfig(path="skills")

    assert config.get_skills_path() == start_dir / "skills"
