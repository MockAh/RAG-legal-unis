from pathlib import Path

from legisuni.config import Settings


def test_settings_carga_desde_env_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LEGISUNI_USER_AGENT=LegisUni/0.1 (+https://example.org; contacto@example.org)\n"
        "LEGISUNI_MODELO_LLM=claude-3-5-sonnet\n"
        "LEGISUNI_ANTHROPIC_API_KEY=sk-test-123\n"
    )

    settings = Settings()

    assert settings.user_agent == "LegisUni/0.1 (+https://example.org; contacto@example.org)"
    assert settings.modelo_llm == "claude-3-5-sonnet"
    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == "sk-test-123"


def test_settings_ignora_variable_ajena(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LEGISUNI_USER_AGENT=LegisUni/0.1 (+https://example.org; contacto@example.org)\n"
        "OTRA_COSA=1\n"
    )

    settings = Settings()

    assert settings.user_agent == "LegisUni/0.1 (+https://example.org; contacto@example.org)"
