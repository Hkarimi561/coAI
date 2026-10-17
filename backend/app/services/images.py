"""Image attachments (screenshots of a bug): validation, storage on disk and encoding for the vision model.

Files live under UPLOADS_DIR/<conversation_id>/<image_id>.<ext>; the message only keeps {id, name, ext, ...} in `meta`.
Every upload is decoded and re-encoded (drops EXIF/GPS and any payload hidden in the file) and downscaled.
"""

import asyncio
import base64
import io
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import get_settings

ALLOWED = {"PNG": ("png", "image/png"), "JPEG": ("jpg", "image/jpeg"), "WEBP": ("webp", "image/webp"), "GIF": ("png", "image/png")}
MIME_BY_EXT = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}
_NAME_RE = re.compile(r"[^\w.\- ]+", re.UNICODE)

Image.MAX_IMAGE_PIXELS = 60_000_000  # decompression-bomb guard


class ImageError(ValueError):
    pass


@dataclass
class StoredImage:
    id: str
    name: str
    ext: str
    width: int
    height: int
    size: int

    def meta(self) -> dict[str, str | int]:
        return {"id": self.id, "name": self.name, "ext": self.ext, "width": self.width, "height": self.height, "size": self.size}


def _root(conversation_id: uuid.UUID) -> Path:
    return Path(get_settings().uploads_dir) / str(conversation_id)


def path_of(conversation_id: uuid.UUID, image_id: str, ext: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", image_id) or ext not in MIME_BY_EXT:
        raise ImageError("Invalid image reference")
    return _root(conversation_id) / f"{image_id}.{ext}"


def find(conversation_id: uuid.UUID, image_id: str) -> tuple[Path, str] | None:
    """Stored file and its MIME type for an image id, or None."""
    for ext, mime in MIME_BY_EXT.items():
        try:
            p = path_of(conversation_id, image_id, ext)
        except ImageError:
            return None
        if p.is_file():
            return p, mime
    return None


def _process(raw: bytes, filename: str) -> tuple[bytes, StoredImage]:
    s = get_settings()
    try:
        img = Image.open(io.BytesIO(raw))
        fmt = img.format or ""
        if fmt not in ALLOWED:
            raise ImageError("Only PNG, JPEG, WebP or GIF images are supported")
        img = ImageOps.exif_transpose(img)  # honour the camera orientation before the EXIF is dropped
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ImageError("The file is not a valid image") from exc

    ext, _ = ALLOWED[fmt]
    if max(img.size) > s.image_max_side:
        img.thumbnail((s.image_max_side, s.image_max_side), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    if ext == "jpg":
        img.convert("RGB").save(out, "JPEG", quality=88, optimize=True)
    elif ext == "webp":
        img.save(out, "WEBP", quality=88)
    else:
        img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB").save(out, "PNG", optimize=True)
    data = out.getvalue()
    name = _NAME_RE.sub("", Path(filename or "image").name).strip()[:80] or "image"
    return data, StoredImage(id=uuid.uuid4().hex, name=name, ext=ext, width=img.size[0], height=img.size[1], size=len(data))


async def save(conversation_id: uuid.UUID, raw: bytes, filename: str) -> StoredImage:
    """Validates, sanitises and stores one uploaded image. Raises ImageError for anything that is not a usable image."""
    s = get_settings()
    if not raw:
        raise ImageError("The file is empty")
    if len(raw) > s.max_image_mb * 1024 * 1024:
        raise ImageError(f"The image is larger than {s.max_image_mb} MB")
    data, stored = await asyncio.to_thread(_process, raw, filename)
    path = path_of(conversation_id, stored.id, stored.ext)
    await asyncio.to_thread(lambda: (path.parent.mkdir(parents=True, exist_ok=True), path.write_bytes(data)))
    return stored


def data_url(conversation_id: uuid.UUID, image_id: str) -> tuple[str, str] | None:
    """(mime, base64) of a stored image for the vision model."""
    found = find(conversation_id, image_id)
    if not found:
        return None
    path, mime = found
    return mime, base64.b64encode(path.read_bytes()).decode()
