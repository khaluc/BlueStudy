# Exam assessment and study plan

Submitting an exam queues structured AI feedback. The result screen shows answered,
incorrect and unanswered counts, an assessment and a plan of short study sessions.
Each session includes a skill, duration, goal, activities, a self-check target and
links to relevant exam questions. Plans are stored with the original attempt and
remain available after reload and from attempt history.

`POST /exams/{exam_id}/attempts` accepts `response_language: "en" | "vi"` (default
`vi`). The frontend sends the selected EN/TV language. Existing attempts can request
a new assessment through `POST /exams/{exam_id}/attempts/{attempt_id}/coaching` with
the same language field, without resubmitting answers or changing scores. Queued
requests are not duplicated. Failed generations expose only a sanitised error code
and can be retried with the result screen's generation button.

Switching EN/TV on an existing assessment automatically requests a translation
using `translate_existing: true` on the same endpoint. The original and translated
versions are cached per attempt. Translation updates narrative text only; scores,
answers, skill codes, study days, durations and question references remain unchanged.
The frontend shows a translation status instead of displaying the wrong language.
Legacy assessments with only a summary and practice list are supported too.

Metrics separate answered mistakes from skipped and ungraded questions. AI receives
aggregate evidence, not a learner identity, and is instructed not to infer mastery,
CEFR levels or weaknesses from unanswered questions. Plans validate skill IDs,
question references, activity lengths and day/duration bounds. Original AI answer
keys and resulting scores remain provisional. Feedback generation uses the
structured-generation model budget instead of the shorter conversational budget.

Tests: `tests/unit/test_exam_coaching.py`, `tests/integration/test_exams.py`.
`scripts/repair_exam_coaching.py` retries an existing failed assessment with the real
configured model and verifies saved scores, question navigation and mobile layout.
