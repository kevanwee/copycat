"""Bound incoming bodies before multipart parsing; authenticate uploads early."""

from fastapi import HTTPException
from starlette.responses import JSONResponse
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.access import require_case


class RequestLimits:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") not in {
            "POST",
            "PUT",
            "PATCH",
        }:
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        path = scope.get("path", "")
        upload = path.startswith("/api/v1/cases/") and path.endswith("/artifacts")
        settings = get_settings()
        limit = (
            max(settings.max_text_mb, settings.max_image_mb, settings.max_video_mb)
            * 1024
            * 1024
            if upload
            else 0
        ) + 256 * 1024
        if upload:
            try:
                with SessionLocal() as db:
                    require_case(
                        db,
                        path.split("/")[4],
                        headers.get(b"x-case-token", b"").decode(
                            "ascii", errors="ignore"
                        ),
                    )
            except HTTPException as exc:
                return await JSONResponse(
                    {"detail": exc.detail}, status_code=exc.status_code
                )(scope, receive, send)
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse(
                {"detail": "Invalid content length"}, status_code=400
            )(scope, receive, send)
        if declared > limit:
            return await JSONResponse(
                {"detail": "Request exceeds the server upload limit"}, status_code=413
            )(scope, receive, send)
        total, exceeded = 0, False

        async def bounded_receive():
            nonlocal total, exceeded
            message = await receive()
            total += len(message.get("body", b""))
            if total > limit:
                exceeded = True
                raise HTTPException(413, "Request exceeds the server upload limit")
            return message

        async def checked_send(message):
            if not exceeded:
                await send(message)

        await self.app(scope, bounded_receive, checked_send)
        if exceeded:
            await JSONResponse(
                {"detail": "Request exceeds the server upload limit"}, status_code=413
            )(scope, receive, send)
