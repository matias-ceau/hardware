from pathlib import Path
from hardware.inventory import config


def test_resolve_db_paths_precedence(tmp_path):
    home = tmp_path / "home"
    cwd = tmp_path / "cwd"
    home.mkdir()
    cwd.mkdir()

    # global config
    (home / ".component_loader.toml").write_text("""[database]
sqlite_path = 'home.db'
jsonld_path = 'home.json'
""")
    # cwd config
    (cwd / "cfg.toml").write_text("""[database]
sqlite_path = 'cwd.db'
jsonld_path = 'cwd.json'
""")

    # CLI overrides all
    s, j = config.resolve_db_paths("cli.db", "cli.json", cwd=cwd, home=home)
    assert s == "cli.db" and j == "cli.json"

    # CWD files override configs
    (cwd / "metadata.db").touch()
    (cwd / "components.jsonld").touch()
    s, j = config.resolve_db_paths(None, None, cwd=cwd, home=home)
    assert s == str(cwd / "metadata.db")
    assert j == str(cwd / "components.jsonld")

    # CWD config when no files
    (cwd / "metadata.db").unlink()
    (cwd / "components.jsonld").unlink()
    s, j = config.resolve_db_paths(None, None, cwd=cwd, home=home)
    assert s == "cwd.db" and j == "cwd.json"

    # Global config fallback
    (cwd / "cfg.toml").unlink()
    s, j = config.resolve_db_paths(None, None, cwd=cwd, home=home)
    assert s == "home.db" and j == "home.json"
