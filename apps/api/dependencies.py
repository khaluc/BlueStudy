from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from apps.api.services.auth import authenticate

bearer = HTTPBearer(auto_error=False)


def get_db(request: Request):
    with request.app.state.sessions() as db:
        yield db


def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(get_db)):
    token = credentials.credentials if credentials else None
    if not token and request.app.state.local_access_file:
        check_local_origin(request)
        token = request.cookies.get('padayon-local')
    user = authenticate(db, token) if token else None
    if user is None:
        raise HTTPException(401, 'Token không hợp lệ.', headers={'WWW-Authenticate': 'Bearer'})
    return user


def check_local_origin(request: Request):
    if request.url.hostname not in ('localhost', '127.0.0.1', 'testserver'):
        raise HTTPException(403, 'Local access only')
    origin = request.headers.get('origin')
    if origin and origin != str(request.base_url).rstrip('/'):
        raise HTTPException(403, 'Invalid origin')
    if request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Invalid origin')
