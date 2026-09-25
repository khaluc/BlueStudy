from datetime import datetime
from typing import Literal, Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, field_validator, StrictInt, computed_field
from sqlalchemy import select
from apps.api.dependencies import current_user, get_db
from apps.api.routers.sessions import owned_session
from apps.api.routers.documents import owned_document
from apps.api.schemas.common import Input, Output
from packages.db.models import ChatThread, ChatTurn
from apps.chat.agents.quiz_intent_agent import wants_quiz, quiz_trace
from packages.db.base import utcnow

router=APIRouter(prefix='/chat',tags=['chat'])


class ThreadInput(Input):
    session_id: UUID | None = None


class MessageInput(Input):
    response_language: Literal['vi', 'en'] = 'vi'
    action: Literal['auto','chat','quiz'] = 'auto'
    image_document_id: UUID | None = None
    message: str = Field(min_length=1,max_length=1500)

    @field_validator('message')
    @classmethod
    def printable(cls,value):
        if any(ord(char)<32 and char not in '\n\t' for char in value):
            raise ValueError('Invalid control characters')
        return value


class ThreadOut(Output):
    id: str
    title: str
    session_id: str | None
    created_at: datetime


class TurnOut(Output):
    work_context:dict|None=Field(default=None,exclude=True)
    quiz: dict | None
    quiz_result: dict | None
    image_document_id: str | None
    id: str
    thread_id: str
    source_session_id: str | None
    message: str
    answer: str | None
    status: str
    provenance: dict | None
    error_code: str | None
    created_at: datetime
    finished_at: datetime | None

    @computed_field
    @property
    def translations(self)->dict:
        localized={}
        for language,item in (self.work_context or {}).get('translations',{}).items():
            if item.get('version',0)<2:continue
            quiz=item.get('quiz')
            result=None
            if self.quiz_result and quiz:
                result={**self.quiz_result,'feedback':[
                    {**row,'question':q['question'],'options':q['options'],'explanation':q['explanation']}
                    for row,q in zip(self.quiz_result['feedback'],quiz['questions'],strict=True)]}
            localized[language]={'answer':item['answer'],
                'quiz':self.hide_answer_key(quiz),'quiz_result':result}
        return localized

    @field_validator('quiz', mode='before')
    @classmethod
    def hide_answer_key(cls, value):
        if not value:return None
        return {'title':value['title'],'questions':[
            {'question':q['question'],'options':q['options']} for q in value['questions']]}


def owned_thread(db,thread_id,owner_id,lock=False):
    query=select(ChatThread).where(ChatThread.id==str(thread_id),ChatThread.owner_id==owner_id)
    if lock:query=query.with_for_update()
    thread=db.scalar(query)
    if thread is None:raise HTTPException(404,'Không tìm thấy cuộc trò chuyện.')
    return thread


def require_idle(db,thread):
    if db.scalar(select(ChatTurn.id).where(ChatTurn.thread_id==thread.id,ChatTurn.status=='queued').limit(1)):
        raise HTTPException(409,'BlueStudy đang xử lý tin nhắn trước. Hãy chờ câu trả lời.')


@router.post('/threads',response_model=ThreadOut,status_code=201)
def create(body:ThreadInput,user=Depends(current_user),db=Depends(get_db)):
    if body.session_id:owned_session(db,body.session_id,user.id)
    thread=ChatThread(owner_id=user.id,session_id=str(body.session_id) if body.session_id else None)
    db.add(thread);db.commit();return thread


@router.get('/threads',response_model=list[ThreadOut])
def listing(limit:int=Query(50,ge=1,le=100),user=Depends(current_user),db=Depends(get_db)):
    return db.scalars(select(ChatThread).where(ChatThread.owner_id==user.id)
        .order_by(ChatThread.created_at.desc(),ChatThread.id).limit(limit)).all()


@router.get('/threads/{thread_id}',response_model=ThreadOut)
def get(thread_id:UUID,user=Depends(current_user),db=Depends(get_db)):
    return owned_thread(db,thread_id,user.id)


@router.patch('/threads/{thread_id}',response_model=ThreadOut)
def attach(thread_id:UUID,body:ThreadInput,user=Depends(current_user),db=Depends(get_db)):
    thread=owned_thread(db,thread_id,user.id,lock=True);require_idle(db,thread)
    if body.session_id:owned_session(db,body.session_id,user.id)
    thread.session_id=str(body.session_id) if body.session_id else None
    db.commit();return thread


@router.delete('/threads/{thread_id}',status_code=204)
def delete(thread_id:UUID,user=Depends(current_user),db=Depends(get_db)):
    thread=owned_thread(db,thread_id,user.id,lock=True);require_idle(db,thread)
    db.delete(thread);db.commit()


@router.post('/threads/{thread_id}/turns',response_model=TurnOut,status_code=202)
def send(thread_id:UUID,body:MessageInput,user=Depends(current_user),db=Depends(get_db)):
    thread=owned_thread(db,thread_id,user.id,lock=True);require_idle(db,thread)
    if thread.session_id:owned_session(db,thread.session_id,user.id)
    if body.image_document_id:
        document = owned_document(db, body.image_document_id, user.id)
        if document.media_type not in ('image/png', 'image/jpeg'):
            raise HTTPException(422, 'Chỉ gửi ảnh PNG hoặc JPEG trực tiếp cho Qwen-VL.')
    if thread.title=='Cuộc trò chuyện mới':thread.title=body.message[:100]
    turn=ChatTurn(thread_id=thread.id,source_session_id=None if body.image_document_id else thread.session_id,
                  message=body.message,image_document_id=str(body.image_document_id) if body.image_document_id else None,
                  provenance={'response_language':body.response_language,
                              **({'input_kind':'image'} if body.image_document_id else {})})
    if wants_quiz(body.message, body.action):
        turn.provenance = {**(turn.provenance or {}),'request_kind':'quiz','agent_trace':quiz_trace(body.response_language)}
    db.add(turn);db.commit();return turn


@router.get('/threads/{thread_id}/turns',response_model=list[TurnOut])
def turns(thread_id:UUID,user=Depends(current_user),db=Depends(get_db)):
    owned_thread(db,thread_id,user.id)
    rows=db.scalars(select(ChatTurn).where(ChatTurn.thread_id==str(thread_id))
        .order_by(ChatTurn.created_at.desc(),ChatTurn.id.desc()).limit(100)).all()
    return list(reversed(rows))


class QuizSubmission(Input):
    answers: list[Annotated[StrictInt, Field(ge=0,le=3)]] = Field(min_length=5,max_length=5)


class TranslationRequest(Input):
    response_language:Literal['vi','en']


@router.post('/threads/{thread_id}/turns/{turn_id}/translation',response_model=TurnOut,status_code=202)
def translate_saved_turn(thread_id:UUID,turn_id:UUID,body:TranslationRequest,user=Depends(current_user),db=Depends(get_db)):
    owned_thread(db,thread_id,user.id)
    turn=db.scalar(select(ChatTurn).where(ChatTurn.id==str(turn_id),ChatTurn.thread_id==str(thread_id)).with_for_update())
    if not turn:raise HTTPException(404,'Không tìm thấy tin nhắn.')
    if turn.status!='succeeded':raise HTTPException(409,'Tin nhắn chưa sẵn sàng.')
    metadata=dict(turn.provenance or {})
    if (metadata.get('response_language','vi')==body.response_language
        or (turn.work_context or {}).get('translations',{}).get(body.response_language,{}).get('version',0)>=2
        or metadata.get('translation_status')=='queued'):return turn
    metadata.update(translation_status='queued',translation_language=body.response_language)
    metadata.pop('translation_error',None)
    turn.provenance=metadata
    db.commit()
    return turn


@router.post('/threads/{thread_id}/turns/{turn_id}/quiz-submit')
def submit_quiz(thread_id:UUID,turn_id:UUID,body:QuizSubmission,user=Depends(current_user),db=Depends(get_db)):
    owned_thread(db,thread_id,user.id)
    turn = db.scalar(select(ChatTurn).where(ChatTurn.id==str(turn_id),ChatTurn.thread_id==str(thread_id)).with_for_update())
    if turn is None:raise HTTPException(404,'Không tìm thấy quiz.')
    if turn.status!='succeeded' or not turn.quiz:raise HTTPException(409,'Quiz chưa sẵn sàng.')
    if turn.quiz_result:
        if turn.quiz_result['answers'] != body.answers:
            raise HTTPException(409,'Bài này đã nộp. Hãy tạo quiz mới để luyện tiếp.')
        return turn.quiz_result
    questions = turn.quiz['questions']
    feedback = [{'question':q['question'],'options':q['options'],'selected':answer,
                 'correct':q['correct'],'is_correct':answer==q['correct'],'explanation':q['explanation']}
                for answer,q in zip(body.answers,questions,strict=True)]
    turn.quiz_result = {'score':sum(row['is_correct'] for row in feedback),'total':len(questions),
                        'answers':body.answers,'feedback':feedback,'submitted_at':utcnow().isoformat()}
    db.commit()
    return turn.quiz_result
