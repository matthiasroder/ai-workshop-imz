"""Save finished JPGs in an existing Drive for desktop folder."""

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile


def save_jpgs(photos, directory):
    if not directory.is_dir():
        raise ValueError(f"Google Drive output folder is unavailable: {directory}")
    saved = 0
    for photo in photos:
        if photo.suffix.lower() != ".jpg":
            continue
        destination = directory / photo.name
        if destination.exists():
            if destination.read_bytes() != photo.read_bytes():
                raise ValueError(f"A different file already exists in Drive: {destination.name}")
            continue
        temporary_path = None
        try:
            with NamedTemporaryFile(dir=directory, prefix=".story-", suffix=".tmp", delete=False) as temp:
                temporary_path = Path(temp.name)
                with photo.open("rb") as source:
                    shutil.copyfileobj(source, temp)
            temporary_path.replace(destination)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        saved += 1
    return saved
