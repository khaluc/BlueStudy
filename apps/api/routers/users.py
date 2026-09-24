from fastapi import APIRouter, Depends
from apps.api.dependencies import current_user, get_db
from apps.api.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserOut)
def me(user=Depends(current_user)):
    return user


@router.patch('/me', response_model=UserOut)
def update_me(body: UserUpdate, user=Depends(current_user), db=Depends(get_db)):
    user.display_name = body.display_name
    user.language_level = body.language_level
    user.learning_preference = body.learning_preference
    db.commit()
    return user
