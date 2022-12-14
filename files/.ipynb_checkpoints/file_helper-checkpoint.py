"""Find local files to be uploaded to remote host."""
from os import walk, path
from typing import List

def fetch_local_files(local_file_dir: str) -> List[str]:
    """
    Generate list of file paths.

    :param str local_file_dir: Local filepath of assets to SCP to host.

    :returns: List[str]
    """
    local_files = walk(local_file_dir)
    for root, dirs, files in local_files:
        return [f"{root}/{file}" for file in files]