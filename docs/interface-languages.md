# Interface languages

The top bar provides **EN** (English) and **TV** (Vietnamese). Vietnamese is the
default. The choice is stored in `localStorage` as `padayon-ui-language` and also
sets the HTML document language, page title and accessible UI labels.

Switching updates the current screen without reloading: chat drafts, file inputs,
quiz answers and exam selections remain intact. The dictionary and dynamic label
patterns live in `apps/web/i18n.js`. Newly rendered UI is translated automatically.
Native browser file-picker labels follow the browser's language.

This setting translates the interface, not saved learner content. Original
documents, exam passages and options, messages, AI replies and generated learning
materials retain their original language. Use `sourceEl()` or `translate="no"`
when rendering such content. Do not send document text to a translation service
for an interface language change. English support level in the learning profile
is a separate preference.

Add new UI text to `UI_EN`; for interpolated labels add a narrowly scoped pattern
in `t()`. Keep editable values and option IDs unchanged. Confirmation dialogs use
`t()` directly because they are outside the document DOM.

Run `python scripts/smoke_ui_language.py` with the local stack running to check
both languages, persistence, draft/answer preservation and mobile layout. It does
not submit exam answers or request model generation.
