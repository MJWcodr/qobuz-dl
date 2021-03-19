import logging
import logging.handlers as handlers
import os
import sys
from typing import Optional, Union

import requests
from tqdm import tqdm

from .constants import LOG_DIR, TIDAL_COVER_URL

logger = logging.getLogger(__name__)


def safe_get(d: dict, *keys, default=None):
    """A replacement for chained `get()` statements on dicts:
    >>> d = {'foo': {'bar': 'baz'}}
    >>> _safe_get(d, 'baz')
    None
    >>> _safe_get(d, 'foo', 'bar')
    'baz'
    """
    curr = d
    res = default
    for key in keys:
        res = curr.get(key, default)
        if res == default or not hasattr(res, "__getitem__"):
            return res
        else:
            curr = res
    return res


def quality_id(bit_depth: Optional[int], sampling_rate: Optional[int]):
    """Return a quality id in (5, 6, 7, 27) from bit depth and
    sampling rate. If None is provided, mp3/lossy is assumed.

    :param bit_depth:
    :type bit_depth: Optional[int]
    :param sampling_rate:
    :type sampling_rate: Optional[int]
    """
    if not (bit_depth or sampling_rate):  # is lossy
        return 5
    if bit_depth == 16:
        return 6
    elif bit_depth == 24:
        if sampling_rate <= 96:
            return 7
        else:
            return 27


def tqdm_download(url: str, filepath: str):
    """Downloads a file with a progress bar.

    :param url: url to direct download
    :param filepath: file to write
    :type url: str
    :type filepath: str
    """
    # FIXME: add the conditional to the progress_bar bool
    logger.debug(f"Downloading {url} to {filepath}")
    r = requests.get(url, allow_redirects=True, stream=True)
    total = int(r.headers.get("content-length", 0))
    logger.debug(f"File size = {total}")
    with open(filepath, "wb") as file, tqdm(
        total=total, unit="iB", unit_scale=True, unit_divisor=1024
    ) as bar:
        for data in r.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


def tidal_cover_url(uuid, size):
    possibles = (80, 160, 320, 640, 1280)
    assert size in possibles, f"size must be in {possibles}"

    return TIDAL_COVER_URL.format(uuid=uuid.replace("-", "/"), height=size, width=size)


def init_log(
    path: Optional[str] = None, level: str = "DEBUG", rotate: str = "midnight"
):
    """
    Initialize a log instance with a stream handler and a rotating file handler.
    If a path is not set, fallback to the default app log directory.

    :param path:
    :type path: Optional[str]
    :param level:
    :type level: str
    :param rotate:
    :type rotate: str
    """
    if not path:
        os.makedirs(LOG_DIR, exist_ok=True)
        path = os.path.join(LOG_DIR, "qobuz_dl.log")

    logger = logging.getLogger()
    level = logging.getLevelName(level)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(module)s.%(funcName)s.%(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    rotable = handlers.TimedRotatingFileHandler(path, when=rotate)
    printable = logging.StreamHandler()

    rotable.setFormatter(formatter)
    printable.setFormatter(formatter)

    logger.addHandler(printable)
    logger.addHandler(rotable)
