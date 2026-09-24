from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class UploadBodyLimit:
    """Bound multipart payload including requests without Content-Length."""
    def __init__(self, app, max_bytes=10 * 1024 * 1024 + 65536):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'].rstrip('/') != '/uploads':
            return await self.app(scope, receive, send)
        length = dict(scope['headers']).get(b'content-length')
        if length:
            try:
                if int(length) > self.max_bytes or int(length) < 0:
                    raise ValueError()
            except ValueError:
                return await JSONResponse({'detail': 'File/request quá lớn.'}, status_code=413)(scope, receive, send)
        total = 0
        async def bounded_receive():
            nonlocal total
            message = await receive()
            total += len(message.get('body', b''))
            if total > self.max_bytes:
                raise HTTPException(413, 'File/request quá lớn.')
            return message
        return await self.app(scope, bounded_receive, send)
