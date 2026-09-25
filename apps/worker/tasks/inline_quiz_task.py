"""One durable stage per transaction so polling sees real completed stages."""
import re
from sqlalchemy import select
from packages.db.models import ChatTurn
from packages.db.base import utcnow
from apps.chat.agents.inline_quiz_agent import generate_quiz


def advance_quiz(db, turn, user, source, image_doc, storage, vision, model):
    metadata = dict(turn.provenance or {})
    language = metadata.get('response_language', 'vi')
    def local(vi, en):
        return en if language == 'en' else vi
    trace = [dict(stage) for stage in metadata['agent_trace']]
    if turn.work_context is None:
        if image_doc:
            text, name = vision(storage.read(image_doc.source_key),
                'Transcribe all visible text exactly in its original language. Do not solve exercises or add knowledge. Mark illegible text as [unclear].', [], response_language=language)
            kind = 'image_transcription'
            detail = local('Đã đọc ảnh bằng '+name+'. Văn bản chưa được người học kiểm tra.',
                           'Image read using '+name+'. The transcription has not been reviewed by the learner.')
        elif source:
            text, kind = source.source_text, 'confirmed_source'
            detail = local('Đã lấy đoạn nguồn đã xác nhận.', 'Retrieved the confirmed source passage.')
        else:
            recent = db.scalars(select(ChatTurn).where(ChatTurn.thread_id==turn.thread_id,
                ChatTurn.status=='succeeded')
                .order_by(ChatTurn.created_at.desc(),ChatTurn.id.desc()).limit(10)).all()
            previous = next((item for item in recent if not item.quiz),None)
            # Chat displays **bold** as plain visible words. Feed that same text
            # to the quiz so exact evidence quotes do not fail on formatting.
            answer_text = re.sub(r'\*\*([^*\n]+)\*\*', r'\1', previous.answer or '') if previous else ''
            text = ((previous.message+'\n'+answer_text)[:4000]) if previous else ''
            kind = 'conversation' if text else 'requested_topic'
            detail = local('Đã lấy nội dung hội thoại gần nhất; chưa qua kiểm duyệt.', 'Retrieved recent conversation content; not reviewed.') if text else local('Dùng chủ đề trong yêu cầu; không có tài liệu nguồn.', 'Using the requested topic; no source document attached.')
        turn.work_context = {'source':text[:4000], 'kind':kind}
        trace[1].update(status='done',detail=detail)
        metadata['agent_trace'] = trace
        turn.provenance = metadata
        return
    quiz, name = generate_quiz(turn.work_context,turn.message,user.language_level,model,response_language=language)
    turn.quiz = quiz
    turn.answer = local('Chọn một đáp án cho mỗi câu rồi bấm Nộp bài. Mình sẽ chấm điểm và giải thích từng câu.',
                        'Choose one answer for each question, then click Submit answers. I will grade your quiz and explain each answer.')
    trace[2].update(status='done',detail=local('Đã tạo 5 câu, kiểm tra cấu trúc và trích dẫn, lưu đáp án riêng trên máy chủ.',
                                            'Created 5 questions, validated the structure and quotes, and stored the answer key privately on the server.'))
    metadata.update(model=name, **getattr(model,'last_metadata',{}), agent_trace=trace,
                    source_kind=turn.work_context['kind'], review_status='unreviewed')
    turn.provenance = metadata
    turn.work_context = None
    turn.status = 'succeeded'
    turn.finished_at = utcnow()
