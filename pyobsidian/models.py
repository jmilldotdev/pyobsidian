from pathlib import Path

from pyobsidian import const


class Scope:
    pass


class TagScope(Scope):
    pass


class PathScope(Scope):
    def __init__(self, path):
        self.path = Path(path)

    def __repr__(self):
        return f"PathScope({self.path})"

    @property
    def full_path(self):
        return const.PERSONAL_VAULT_DIR / self.path

    @property
    def md_files(self):
        return self.full_path.rglob("*.md")
