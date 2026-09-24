"use strict";
function inlineQuiz(turn, draft, submit) {
  const card = el("section", null, "inline-quiz");
  card.setAttribute("aria-label", "Quiz trắc nghiệm");
  card.append(
    el("span", "QUICK QUIZ · TỰ KIỂM TRA", "eyebrow"),
    sourceEl("h3", turn.quiz.title),
  );
  const result = turn.quiz_result;
  const choices = result ? [...result.answers] : draft;
  const progress = el("p", "", "quiz-selection-count");
  card.append(progress);
  const form = el("form");
  const error = el("p", "", "chat-review-error");
  error.setAttribute("role", "alert");
  const send = el("button", "Nộp bài", "primary");
  send.type = "submit";
  const update = () => {
    const answered = choices.filter((value) => Number.isInteger(value)).length;
    progress.textContent = result
      ? `Kết quả: ${result.score} / ${result.total} câu đúng`
      : `Đã chọn ${answered} / ${turn.quiz.questions.length} câu`;
    send.disabled = answered !== turn.quiz.questions.length;
  };
  turn.quiz.questions.forEach((question, index) => {
    const fieldset = el("fieldset", null, "inline-quiz-question");
    fieldset.append(sourceEl("legend", `${index + 1}. ${question.question}`));
    const feedback = result?.feedback[index];
    question.options.forEach((option, optionIndex) => {
      const label = el("label", null, "inline-quiz-option");
      const radio = el("input");
      radio.type = "radio";
      radio.name = `quiz-${turn.id}-${index}`;
      radio.value = String(optionIndex);
      radio.checked = choices[index] === optionIndex;
      radio.disabled = !!result;
      radio.onchange = () => {
        choices[index] = optionIndex;
        update();
      };
      label.append(
        radio,
        el("span", String.fromCharCode(65 + optionIndex), "option-letter"),
        sourceEl("span", option),
      );
      if (feedback) {
        if (feedback.correct === optionIndex) {
          label.classList.add("correct");
          label.append(el("span", "✓ Đúng", "quiz-verdict"));
        } else if (feedback.selected === optionIndex) {
          label.classList.add("incorrect");
          label.append(el("span", "✕ Đã chọn", "quiz-verdict"));
        }
      }
      fieldset.append(label);
    });
    if (feedback)
      fieldset.append(sourceEl("p", feedback.explanation, "quiz-explanation"));
    form.append(fieldset);
  });
  if (!result) form.append(error, send);
  else
    form.append(
      el(
        "p",
        "Đã lưu kết quả. Bạn có thể tạo quiz mới để luyện tiếp.",
        "quiz-saved",
      ),
    );
  form.onsubmit = async (event) => {
    event.preventDefault();
    if (send.disabled || result) return;
    send.disabled = true;
    form.querySelectorAll("input").forEach((input) => (input.disabled = true));
    error.textContent = "";
    try {
      await submit([...choices]);
    } catch (err) {
      error.textContent = err.message;
      form
        .querySelectorAll("input")
        .forEach((input) => (input.disabled = false));
      update();
    }
  };
  update();
  card.append(form);
  return card;
}
