"""Observable timing signals, not phoneme or pronunciation assessment."""
import re

LESSONS = {
    'explain': 'Explain an academic concept',
    'opinion': 'Support an opinion with evidence',
    'compare': 'Compare two approaches to learning',
    'presentation': 'Give a short research presentation',
}


def analyse_timing(words):
    events = []
    previous = None
    for i, word in enumerate(words):
        clean = re.sub(r'[^a-z\x27]', '', word['text'].lower())
        if clean in {'um', 'uh', 'erm', 'er', 'hmm', 'uhh', 'umm'}:
            events.append({'kind':'filler', 'index':i, 'start':word['start'], 'end':word['end']})
        if previous:
            if word['start'] - previous['end'] >= 1200:
                events.append({'kind':'pause', 'index':i, 'start':previous['end'], 'end':word['start']})
            if clean and clean == re.sub(r'[^a-z\x27]', '', previous['text'].lower()):
                events.append({'kind':'repetition', 'index':i, 'start':previous['start'], 'end':word['end']})
        if word['end'] - word['start'] >= 1200:
            events.append({'kind':'long_word', 'index':i, 'start':word['start'], 'end':word['end']})
        previous = word
    span = words[-1]['end'] - words[0]['start'] if words else 0
    return {'word_count':len(words), 'duration_seconds':round(span / 1000, 2),
            'words_per_minute':round(len(words) * 60000 / span, 1) if span else None,
            'events':events, 'basis':'transcript_and_word_timestamps',
            'pronunciation_score':None, 'pronunciation_status':'requires_acoustic_assessment'}
