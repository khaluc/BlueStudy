# Interface languages

The top bar provides **EN** (English) and **TV** (Vietnamese). Vietnamese is the
default. The choice is stored in `localStorage` as `padayon-ui-language` and also
sets the HTML document language, page title and accessible UI labels.

Switching updates the current screen without reloading: chat drafts, file inputs,
quiz answers and exam selections remain intact. The dictionary and dynamic label
patterns live in `apps/web/i18n.js`. Newly rendered UI is translated automatically.
Native browser file-picker labels follow the browser's language.

This setting translates the interface and sets the response language for **new
chat turns**. Chat requests include `response_language` (`en` or `vi`, default
`vi` for older clients). The queued turn retains that selection in its provenance,
including after a browser reload or a later language switch. Text chat, direct
image explanations, quiz titles/questions/options/explanations, submission
instructions and quiz agent status messages use that language. Image transcription
and evidence quotes preserve the source language.

Saved exam assessments and study plans automatically switch languages too: the
first switch translates the narrative, and later switches use cached EN/TV
versions. Scores, submitted answers and roadmap question references stay intact.

Saved chat answers and inline quizzes also translate automatically when opening
chat or switching EN/TV. Translations are queued through
`POST /chat/threads/{thread_id}/turns/{turn_id}/translation` and cached privately
per turn. The UI shows translation progress, with a retry button on failure.
Original responses, user messages, quiz order, correct option indices and scores
remain unchanged. Translated explanations are exposed only after submission.
`ChatTurn.work_context` stores private translation bundles for completed turns;
the public response excludes it and projects only safe `translations` fields.

Original uploaded documents, exam passages, user messages and standalone generated
study packs are not rewritten. Use `sourceEl()` or `translate="no"` to protect
them from the static UI dictionary. English support level in the learning profile
is a separate preference.

Add new UI text to `UI_EN`; for interpolated labels add a narrowly scoped pattern
in `t()`. Keep editable values and option IDs unchanged. Confirmation dialogs use
`t()` directly because they are outside the document DOM.

Run `python scripts/smoke_ui_language.py` with the local stack running to check
both languages, persistence, draft/answer preservation and mobile layout. It does
not submit exam answers or request model generation.

`python scripts/smoke_saved_chat_language.py` checks an existing saved chat with
the configured translation model, including EN/TV/EN, reload and preserved scores.
