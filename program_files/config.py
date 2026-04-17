from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from program_files.user_input import UserInput
from typing import List

# ----------------------------
# Helpers
# ----------------------------
def _project_root() -> Path:
    """Absolute path to the project root (parent of program_files/)."""
    return Path(__file__).resolve().parent.parent

def _config_path(config_name: str) -> Path:
    """Absolute path to the desired config file inside /config."""
    path = _project_root() / "config" / config_name
    if not path.is_file():
        raise FileNotFoundError(f"{config_name} not found at {path}")
    return path

def _load_config(config_name: str) -> ConfigParser:
    """Load a ConfigParser with ExtendedInterpolation."""
    cfg = ConfigParser(interpolation=ExtendedInterpolation())
    cfg.read(_config_path(config_name))
    return cfg

def _normalize_paths(cfg: ConfigParser) -> None:
    """Normalize [paths] section entries to absolute paths from project root."""
    if "paths" not in cfg:
        return
    root = _project_root()
    for key, val in list(cfg["paths"].items()):
        p = Path(val).expanduser()
        if not p.is_absolute():
            p = (root / p).resolve()
        cfg["paths"][key] = str(p)

# ----------------------------
# Public
# ----------------------------
def get_config(config_name: str) -> ConfigParser:
    """
    Load config/<config_name> and normalize [paths] entries to absolute paths.
    Relative paths are interpreted relative to the project root.
    """
    cfg = _load_config(config_name)
    _normalize_paths(cfg)
    return cfg


def set_config_value(config_name: str, section: str, key: str, value: str) -> None:
    """
    Update a value in config/<config_name> while preserving existing comments
    and formatting. Creates the section/key if they don't exist.
    """
    path = _config_path(config_name)
    value = str(value)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    section_header = f"[{section}]"
    in_section = False
    section_found = False
    key_found = False
    new_lines: List[str] = []

    for line in lines:
        stripped = line.strip()

        # Detect section headers
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_section and not key_found:
                new_lines.append(f"{key} = {value}\n")
                key_found = True

            in_section = (stripped == section_header)
            if in_section:
                section_found = True

            new_lines.append(line)
            continue

        if in_section:
            # Check if this line defines the key (with or without space around '=')
            if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
                new_lines.append(f"{key} = {value}\n")
                key_found = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # If section never existed, append it and the key at the end
    if not section_found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"\n[{section}]\n")
        new_lines.append(f"{key} = {value}\n")

    # If section existed but key never appeared, append key at end of that section
    elif section_found and not key_found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"{key} = {value}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def set_user_config(config_name: str, config_settings: UserInput) -> None:
    prefix_to_section = {
        "test_": "test_system",
        "prod_": "prod_system"
    }

    for key, value in config_settings.model_dump().items():
        value = str(value)
        is_path_field = key.endswith("_path") or key in {"temp_dir"}

        # PATH FIELDS
        if is_path_field:
            if not value.startswith("./"): value = "./" + value.replace("\\", "/")
            set_config_value(config_name, "paths", key, value)
            continue

        # CONSTRAINT FIELDS
        if not key.startswith(("test_", "prod_")):
            set_config_value(config_name, "constraints", key, value)

        # TEST / PROD FIELDS
        for prefix, section in prefix_to_section.items():
            if key.startswith(prefix):
                ini_key = key[len(prefix):]
                set_config_value(config_name, section, ini_key, value)