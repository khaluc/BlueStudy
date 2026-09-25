"""Deterministic intent routing; no claim that a model performed classification."""
import re
import unicodedata


def wants_quiz(message, action='auto'):
    if action != 'auto':
        return action == 'quiz'
    text = ''.join(c for c in unicodedata.normalize('NFD', message.lower()) if not unicodedata.combining(c))
    if re.search(r'\b(khong|dung|don.t|no)\b.{0,20}\b(quiz|trac nghiem)\b', text):
        return False
    return bool(re.search(r'\b(quiz\s+(me|on)|quiz$|tao.{0,50}(quiz|trac nghiem)|'
                          r'(make|create|generate).{0,40}quiz|kiem tra.{0,15}(minh|tui|toi))\b', text))


def quiz_trace(language='vi'):
    if language == 'en':
        return [
            {'agent':'Classifier Agent','status':'done','detail':'Recognised a quiz request using intent rules.'},
            {'agent':'Source Agent','status':'pending','detail':'Waiting for source content.'},
            {'agent':'Quiz Agent','status':'pending','detail':'Waiting to generate and validate multiple-choice questions.'},
        ]
    return [
        {'agent':'Classifier Agent','status':'done','detail':'Nhận diện yêu cầu quiz bằng quy tắc.'},
        {'agent':'Source Agent','status':'pending','detail':'Đang chờ lấy nội dung để tạo câu hỏi.'},
        {'agent':'Quiz Agent','status':'pending','detail':'Đang chờ tạo và kiểm tra câu hỏi trắc nghiệm.'},
    ]
