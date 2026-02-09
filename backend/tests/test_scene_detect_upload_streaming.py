"""Tests for streaming upload persistence in scene-detect router."""

import os

import pytest

from app.routers import scene_detect


class _FakeUpload:
    """Minimal async upload object for chunked-read tests."""

    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self._data = data
        self._offset = 0

    async def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._data):
            return b""

        if size is None or size < 0:
            size = len(self._data) - self._offset

        chunk = self._data[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


@pytest.mark.asyncio
async def test_save_upload_to_tempfile_streams_data_without_full_read():
    """Large uploads should be persisted via chunked reads to avoid full memory buffering."""
    original = (b"scene-detect-test-" * 1024 * 64) + b"tail"
    fake_upload = _FakeUpload("sample.mp4", original)

    temp_path = await scene_detect._save_upload_to_tempfile(fake_upload)

    try:
        with open(temp_path, "rb") as fp:
            assert fp.read() == original
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
