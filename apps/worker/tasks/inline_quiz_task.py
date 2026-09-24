"""One durable stage per transaction so polling sees real completed stages."""
from sqlalchemy import select
from packages.db.models import ChatTurn
from packages.db.base import utcnow
from apps.chat.agents.inline_quiz_agent import generate_quiz


def advance_quiz(db, turn, user, source, image_doc, storage, vision, model):
    metadata = dict(turn.provenance or {})
    trace = [dict(stage) for stage in metadata['agent_trace']]
    if turn.work_context is None:
        if image_doc:
            text, name = vision(storage.read(image_doc.source_key),
                'Chép chính xác toàn bộ chữ nhìn thấy trong ảnh. Không giải bài, không thêm kiến thức. Chỗ mờ ghi [không rõ].', [])
            kind = 'image_transcription'
            detail = 'Đã đọc ảnh bằng '+name+'. Văn bản chưa được người học kiểm tra.'
        elif source:
            text, kind = source.source_text, 'confirmed_source'
            detail = 'Đã lấy đoạn nguồn đã xác nhận.'
        else:
            recent = db.scalars(select(ChatTurn).where(ChatTurn.thread_id==turn.thread_id,
                ChatTurn.status=='succeeded')
                .order_by(ChatTurn.created_at.desc(),ChatTurn.id.desc()).limit(10)).all()
            previous = next((item for item in recent if not item.quiz),None)
            text = ((previous.message+'\n'+(previous.answer or ''))[:4000]) if previous else ''
            kind = 'conversation' if text else 'requested_topic'
            detail = 'Đã lấy nội dung hội thoại gần nhất; chưa qua kiểm duyệt.' if text else 'Dùng chủ đề trong yêu cầu; không có tài liệu nguồn.'
        turn.work_context = {'source':text[:4000], 'kind':kind}
        trace[1].update(status='done',detail=detail)
        metadata['agent_trace'] = trace
        turn.provenance = metadata
        return
    quiz, name = generate_quiz(turn.work_context,turn.message,user.language_level,model)
    turn.quiz = quiz
    turn.answer = 'Chọn một đáp án cho mỗi câu rồi bấm Nộp bài. Mình sẽ chấm điểm và giải thích từng câu.'
    trace[2].update(status='done',detail='Đã tạo 5 câu, kiểm tra cấu trúc và trích dẫn, lưu đáp án riêng trên máy chủ.')
    metadata.update(model=name, **getattr(model,'last_metadata',{}), agent_trace=trace,
                    source_kind=turn.work_context['kind'], review_status='unreviewed')
    turn.provenance = metadata
    turn.work_context = None
    turn.status = 'succeeded'
    turn.finished_at = utcnow()
