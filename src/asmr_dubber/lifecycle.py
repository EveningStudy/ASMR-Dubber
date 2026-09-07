"""Project execution boundaries shared by CLI, UI and batch workflows."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, cast

from .errors import ProjectConflictError
from .models import DubProject, load_project
from .storage import exclusive_file_lock


def assert_revision(project: DubProject, directory: Path, expected: int | None = None) -> None:
    revision = project.revision if expected is None else expected
    manifest = directory / "project.json"
    if manifest.is_file() and load_project(manifest)[0].revision != revision:
        raise ProjectConflictError(
            "项目已被其他窗口或任务修改；请重新打开项目后再执行。未覆盖当前结果。"
        )


@contextmanager
def browser_revision_scope(manifest: str, expected: int | None) -> Iterator[None]:
    if expected is None:
        yield
        return
    project, directory = load_project(manifest)
    with exclusive_file_lock(directory / ".project.lock"):
        assert_revision(project, directory, expected)
        yield


def project_operation[F: Callable[..., Any]](function: F) -> F:
    @wraps(function)
    def guarded(project: DubProject, project_dir: Path, *args: Any, **kwargs: Any) -> Any:
        from .voice_reference import reference_selection_scope

        directory = Path(project_dir).resolve()
        with (
            exclusive_file_lock(directory / ".project.lock", timeout_seconds=10.0),
            reference_selection_scope(project),
        ):
            assert_revision(project, directory)
            return function(project, project_dir, *args, **kwargs)

    return cast(F, guarded)


def invalidate_outputs(project: DubProject, *, audio: bool = True, subtitles: bool = True) -> None:
    if audio:
        project.chinese_stem_file = None
        project.output_file = None
        project.output_video_file = None
    if subtitles:
        project.subtitle_srt_file = None
        project.subtitle_lrc_file = None
    project.subtitle_video_file = None
