from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, StrictInt
from sqlalchemy import select
from apps.api.dependencies import current_user,get_db
from apps.api.schemas.common import Input
from apps.api.routers.documents import owned_document
from packages.db.models import Exam,ExamAttempt
from packages.core.exam import TOPICS,SKILLS,grade_exam

router=APIRouter(prefix='/exams',tags=['structured exams'])


def owned_exam(db,id,owner,lock=False):
    query=select(Exam).where(Exam.id==str(id),Exam.owner_id==owner)
    if lock:query=query.with_for_update()
    exam=db.scalar(query)
    if not exam:raise HTTPException(404,'Không tìm thấy đề thi.')
    return exam


def public_exam(exam):
    return {'id':exam.id,'document_id':exam.document_id,'title':exam.title,'status':exam.status,
            'structure':exam.structure,'error_code':exam.error_code,'created_at':exam.created_at,
            'classified_count':len(exam.analysis),'answer_key_status':'ai_unverified',
            'classification':[{'number':q['number'],'topic':q['topic'],'skill':q['skill']} for q in exam.analysis],
            'topic_labels':TOPICS,'skill_labels':SKILLS}


class ExamInput(Input):
    document_id:UUID


@router.post('',status_code=202)
def create(body:ExamInput,user=Depends(current_user),db=Depends(get_db)):
    doc=owned_document(db,body.document_id,user.id,lock=True)
    existing=db.scalar(select(Exam).where(Exam.document_id==doc.id,Exam.owner_id==user.id).order_by(Exam.created_at.desc()).limit(1))
    if existing and existing.status not in ('failed','needs_review'):return public_exam(existing)
    exam=Exam(owner_id=user.id,document_id=doc.id,title=doc.title)
    db.add(exam);db.commit();return public_exam(exam)


@router.get('')
def listing(limit:int=Query(50,ge=1,le=100),user=Depends(current_user),db=Depends(get_db)):
    return [public_exam(e) for e in db.scalars(select(Exam).where(Exam.owner_id==user.id).order_by(Exam.created_at.desc()).limit(limit))]


@router.get('/{exam_id}')
def get(exam_id:UUID,user=Depends(current_user),db=Depends(get_db)):
    return public_exam(owned_exam(db,exam_id,user.id))


class Submission(Input):
    answers:list[Annotated[StrictInt,Field(ge=0,le=3)]|None]=Field(min_length=1,max_length=100)


@router.post('/{exam_id}/attempts',status_code=201)
def submit(exam_id:UUID,body:Submission,user=Depends(current_user),db=Depends(get_db)):
    exam=owned_exam(db,exam_id,user.id)
    if exam.status!='ready':raise HTTPException(409,'Đề đang được xử lý hoặc cần kiểm tra.')
    if len(body.answers)!=len(exam.structure['questions']):raise HTTPException(422,'Số đáp án không khớp số câu.')
    attempt=ExamAttempt(owner_id=user.id,exam_id=exam.id,answers=body.answers,
                        result=grade_exam(exam.structure,exam.analysis,body.answers))
    db.add(attempt);db.commit();return attempt


@router.get('/{exam_id}/attempts')
def attempts(exam_id:UUID,user=Depends(current_user),db=Depends(get_db)):
    owned_exam(db,exam_id,user.id)
    return db.scalars(select(ExamAttempt).where(ExamAttempt.exam_id==str(exam_id),ExamAttempt.owner_id==user.id)
        .order_by(ExamAttempt.created_at.desc()).limit(20)).all()
