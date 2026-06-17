class RepositoryNotFoundError(Exception):
    """Repositoryで指定対象が存在しない場合の例外。"""

    pass


class RepositoryAccessError(Exception):
    """Repositoryの読み書きに失敗した場合の例外。"""

    pass
