"""BlueStudy topic suggestions, not a school syllabus or a level assessment."""
import re

_TOPICS = [
    ('vocabulary', 'Academic vocabulary', 'vocabulary,idiom,collocation,word meaning,community,volunteer'),
    ('grammar', 'Grammar and sentence structure', 'grammar,tense,verb,preposition,sentence structure,since,for'),
    ('reading', 'Reading comprehension', 'reading,passage,main idea,inference,read the following'),
    ('writing', 'Academic writing', 'essay,thesis,argument,academic writing,paragraph'),
    ('notes', 'Summarising and note-taking', 'summary,summarise,summarize,note-taking,lecture'),
    ('research', 'Research and critical thinking', 'research,evidence,citation,methodology,hypothesis'),
    ('communication', 'Listening and presentation skills', 'listening,presentation,discussion,speaking'),
    ('exam', 'Exam preparation', 'exam,question 1,mark the letter,multiple-choice'),
]
TOPICS = [dict(id=f'ae-{key}', title=title, keywords=words.split(','),
               source_status='platform_topic', book='Academic English', source_url=None)
          for key, title, words in _TOPICS]


def suggest(text):
    matches = []
    for topic in TOPICS:
        evidence = [word for word in topic['keywords']
                    if re.search(r'\b' + re.escape(word) + r'\b', text, re.I)]
        if evidence:
            matches.append(dict(topic=topic, evidence=evidence, status='suggested'))
    return sorted(matches, key=lambda item: -len(item['evidence']))[:3]
