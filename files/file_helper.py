"""Find local files to be uploaded to remote host."""
from os import walk
from typing import List


def fetch_local_files(local_file_dir: str) -> List[str]:
    """
    Generate list of file paths.

    :param str local_file_dir: Local filepath of assets to SCP to host.

    :returns: List[str]
    """
    for root, dirs, files in walk(local_file_dir):
        return [f"{root}/{file}" for file in files]
