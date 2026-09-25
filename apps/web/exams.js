"use strict";
let examTimer = null;
let examLanguageCleanup = () => {};
function disposeExam() {
  clearTimeout(examTimer);
  examLanguageCleanup();
  examLanguageCleanup = () => {};
}
window.addEventListener("hashchange", () => {
  if (!token) return;
  let navigation;
  if (location.hash.startsWith("#exam=")) navigation = examView(location.hash.slice(6));
  else if (location.hash === "#exams") navigation = show("exams");
  else if (location.hash === "#chat") navigation = show("chat");
  else if (location.hash === "#speaking") navigation = show("speaking");
  else if (location.hash === "#home" || location.hash === "") navigation = show("home");
  else if (location.hash === "#map") navigation = show("map");
  if (navigation) navigation.catch(error => notice.textContent = error.message);
});
const examStatus = (status) =>
  ({
    queued: "Đang trích xuất PDF",
    analyzing: "AI đang phân loại câu hỏi",
    ready: "Sẵn sàng luyện tập",
    needs_review: "Cần kiểm tra câu bị thiếu",
    failed: "Chưa xử lý được",
  })[status] || status;
async function examHome() {
  reset(
    "Đề thi & ôn tập",
    "Giữ nguyên đề gốc · Phân loại từng câu · Ôn theo kết quả làm bài",
  );
  setNav("exams");
  const ticket = generation;
  window.history.replaceState(null, "", "#exams");
  const user = await api("/users/me");
  if (ticket !== generation) return;
  updateIdentity(user);
  const upload = el("div", null, "card");
  upload.append(
    el("h2", "PDF → đề thi có cấu trúc"),
    el(
      "p",
      "Tải PDF tối đa 10 MB, 20 trang. Giữ câu hỏi, lựa chọn A–D và đoạn đọc dùng chung; không tạo câu hỏi về mã đề hay thời gian thi.",
    ),
  );
  const file = field(upload, "Chọn PDF đề thi");
  file.type = "file";
  file.accept = ".pdf";
  upload.append(
    button(
      "Chuyển thành đề thi",
      async () => {
        if (!file.files[0]) throw Error("Hãy chọn PDF đề thi.");
        const data = new FormData();
        data.append("file", file.files[0]);
        data.append("title", file.files[0].name.slice(0, 160));
        const doc = await api("/uploads", { method: "POST", body: data });
        const exam = await api("/exams", {
          method: "POST",
          body: { document_id: doc.id },
        });
        if (ticket === generation) await examView(exam.id);
      },
      "primary",
    ),
  );
  root.append(upload, el("h2", "Đề thi của bạn"));
  const exams = await api("/exams");
  if (ticket !== generation) return;
  const grid = el("div", null, "grid");
  for (const exam of exams) {
    const box = el("div", null, "card");
    box.append(
      sourceEl("h3", exam.title),
      el("p", examStatus(exam.status)),
      el(
        "small",
        `${exam.structure?.questions.length || 0} câu · ${exam.classified_count} câu đã phân loại`,
      ),
      button("Mở đề thi", () => examView(exam.id), "secondary"),
    );
    grid.append(box);
  }
  if (!exams.length)
    grid.append(el("p", "Chưa có đề thi. Hãy tải PDF để bắt đầu.", "empty"));
  root.append(grid);
}

async function examView(id, chosenAttempt = null) {
  reset("Đang mở đề thi…", "");
  setNav("exams");
  window.history.replaceState(null, "", "#exam=" + id);
  const ticket = generation,
    active = () => ticket === generation;
  const user = await api("/users/me");
  if (!active()) return;
  updateIdentity(user);
  let exam = await api("/exams/" + id);
  if (!active()) return;
  let attempts = await api("/exams/" + id + "/attempts");
  if (!active()) return;
  let attempt = chosenAttempt
    ? attempts.find((item) => item.id === chosenAttempt)
    : attempts[0] || null;
  let answers = Array(exam.structure?.questions.length || 0).fill(null),
    submitting = false;
  const cacheKey = "padayon-exam-draft-" + id;
  let languageRequest = false;
  const requestedLanguages = new Set();
  const coachingLanguage = item => item?.coaching?.response_language ||
    (item?.result?.coaching_mode === "translate" ? "vi" : item?.result?.response_language) || "vi";
  async function ensureCoachingLanguage(force = false) {
    if (!active() || !attempt?.coaching || attempt.status === "queued" || languageRequest ||
        coachingLanguage(attempt) === uiLanguage) return;
    const requestedId = attempt.id;
    const key = requestedId + ":" + uiLanguage;
    if (!force && requestedLanguages.has(key)) return;
    requestedLanguages.add(key);
    languageRequest = true;
    try {
      const updated = await api(`/exams/${id}/attempts/${requestedId}/coaching`, {
        method:"POST", body:{response_language:uiLanguage, translate_existing:true},
      });
      if (!active()) return;
      attempts = attempts.map(item => item.id === updated.id ? updated : item);
      if (attempt?.id === requestedId) attempt = updated;
    } catch (error) {
      if (active()) notice.textContent = error.message;
    } finally {
      languageRequest = false;
      if (active()) { render(); schedule(); }
    }
  }
  const onLanguageChange = () => {
    if (attempt) requestedLanguages.delete(attempt.id + ":" + uiLanguage);
    render(); ensureCoachingLanguage();
  };
  window.addEventListener("ui-language-change", onLanguageChange);
  examLanguageCleanup = () => window.removeEventListener("ui-language-change", onLanguageChange);
  try {
    const saved = JSON.parse(sessionStorage.getItem(cacheKey));
    if (
      Array.isArray(saved) &&
      saved.length === answers.length &&
      saved.every((x) => x === null || (Number.isInteger(x) && x >= 0 && x < 4))
    )
      answers = saved;
  } catch {}
  function render() {
    root.replaceChildren();
    root.className = "exam-page fade-in";
    root.append(
      button("← Danh sách đề thi", examHome, "text-button"),
      sourceEl("h1", exam.title),
      el("p", examStatus(exam.status), "exam-status"),
    );
    const warning = el(
      "div",
      "Đáp án do AI đề xuất, chưa có đáp án chính thức được đối chiếu. Điểm và gợi ý ôn tập chỉ tạm tính; câu AI chưa xác định được sẽ không tính điểm.",
      "exam-key-warning",
    );
    root.append(warning);
    const stages = el("div", null, "exam-stages");
    stages.append(
      el(
        "div",
        `01 · Trích xuất: ${exam.structure?.questions.length || 0}/${exam.structure?.expected_count || "?"} câu`,
      ),
      el(
        "div",
        `02 · AI phân loại: ${exam.classified_count}/${exam.structure?.questions.length || "?"} câu`,
      ),
      el(
        "div",
        attempt
          ? `03 · Phân tích kết quả: ${attempt.status === "ready" ? "Hoàn tất" : attempt.status === "failed" ? "Đã chấm; chưa có gợi ý AI" : "Đang chuẩn bị gợi ý"}`
          : "03 · Làm bài để nhận gợi ý ôn tập",
      ),
    );
    root.append(stages);
    if (exam.structure?.warnings.length) {
      const warnings = el("div", null, "card");
      for (const text of exam.structure.warnings)
        warnings.append(el("p", text));
      root.append(warnings);
    }
    if (["failed", "needs_review"].includes(exam.status)) {
      root.append(
        el(
          "p",
          "Cần kiểm tra nội dung trích xuất trước khi chấm bài; hệ thống không tự bịa câu bị thiếu.",
        ),
        button(
          "Mở tài liệu để kiểm tra",
          () => documentView(exam.document_id),
          "secondary",
        ),
        button(
          "Thử chuyển đổi lại",
          async () => {
            const retry = await api("/exams", {
              method: "POST",
              body: { document_id: exam.document_id },
            });
            if (active()) await examView(retry.id);
          },
          "secondary",
        ),
      );
    }
    if (!exam.structure) return;
    root.append(button("Tải đề có cấu trúc (JSON)", () => {
      const data = {title:exam.title,structure:exam.structure,classification:exam.classification,answer_key_status:exam.answer_key_status};
      const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json;charset=utf-8"}));
      const link=el("a");link.href=url;link.download="bluestudy-exam-"+exam.id+".json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }, "secondary"));
    if (answers.length !== exam.structure.questions.length)
      answers = Array(exam.structure.questions.length).fill(null);
    if (attempt) {
      const result = attempt.result,
        box = el("section", null, "exam-results card");
      box.append(
        el("h2", `Điểm tạm tính: ${result.score} / ${result.graded_total}`),
        el(
          "p",
          `${result.ungraded} câu chưa có đáp án để chấm · ${result.total} câu trong đề`,
        ),
      );
      const metrics = el("div", null, "exam-review-metrics");
      const answered = result.feedback.filter(row => row.selected !== null).length;
      const wrong = result.feedback.filter(row => row.selected !== null && row.is_correct === false).length;
      for (const [label, value] of [["Đã trả lời", `${answered}/${result.total}`],
        ["Câu trả lời sai", wrong], ["Câu bỏ trống", result.total - answered]]) {
        const metric = el("div");
        metric.append(el("strong", String(value)), el("span", label));
        metrics.append(metric);
      }
      box.append(metrics, el("p", "Câu bỏ trống không được dùng để kết luận bạn yếu kỹ năng đó.", "muted"));
      const table = el("table");
      const head = el("tr");
      for (const text of ["Kỹ năng", "Đúng / đã chấm", "Câu cần ôn"])
        head.append(el("th", text));
      table.append(head);
      for (const skill of result.skills) {
        const row = el("tr");
        row.append(
          el("td", skill.label),
          el("td", `${skill.correct} / ${skill.total}`),
          el("td", skill.questions.join(", ") || "—"),
        );
        table.append(row);
      }
      box.append(table);
      const coaching = el("section", null, "exam-coaching");
      coaching.setAttribute("aria-label", "Đánh giá và lộ trình học tập");
      coaching.append(el("h3", "Đánh giá và lộ trình học tập"));
      table.before(coaching);
      const matchingLanguage = coachingLanguage(attempt) === uiLanguage;
      if (attempt.coaching && matchingLanguage) {
        coaching.append(
          sourceEl("p", attempt.coaching.summary),
        );
        if (attempt.coaching.roadmap?.length) {
          const path = el("ol", null, "exam-study-plan");
          for (const step of attempt.coaching.roadmap) {
            const card = el("li", null, "exam-study-step");
            card.append(el("span", `Ngày ${step.day} · ${step.minutes} phút`, "eyebrow"),
              el("span", exam.skill_labels[step.skill] || step.skill, "pill"),
              sourceEl("h4", step.goal));
            const activities = el("ul");
            for (const activity of step.activities) activities.append(sourceEl("li", activity));
            const check = el("div", null, "exam-plan-check");
            check.append(el("strong", "Mục tiêu tự kiểm tra"), sourceEl("p", step.success_criteria));
            card.append(activities, check);
            if (step.question_numbers.length) {
              const links = el("div", null, "exam-plan-links");
              links.append(el("span", "Ôn lại câu:"));
              for (const number of step.question_numbers) links.append(button(String(number), () => {
                const question = root.querySelector(`#exam-question-${number}`);
                question?.scrollIntoView({block:"start", behavior:"smooth"});
                question?.focus({preventScroll:true});
              }, "secondary"));
              card.append(links);
            }
            path.append(card);
          }
          coaching.append(path);
        } else {
          const list = el("ol");
          for (const step of attempt.coaching.practice || []) list.append(sourceEl("li", step));
          coaching.append(list);
        }
        coaching.append(el("small", `${attempt.coaching.model || "AI"} · Nội dung chưa qua giáo viên kiểm duyệt`, "muted"));
      } else
        coaching.append(
          el(
            "p",
            attempt.coaching && !matchingLanguage
              ? (attempt.status === "failed" ? "Chưa chuyển được ngôn ngữ. Bấm thử lại." : "Đang chuyển nhận xét và lộ trình sang ngôn ngữ bạn chọn…")
              : attempt.status === "failed"
              ? "Chưa tạo được nhận xét AI. Bạn vẫn có thể ôn theo bảng kỹ năng và giải thích từng câu."
              : "AI đang phân tích kết quả để gợi ý ôn tập…",
          ),
        );
      if (attempt.coaching && !matchingLanguage && attempt.status !== "queued") coaching.append(button(
        "Thử chuyển ngôn ngữ lại", () => ensureCoachingLanguage(true), "secondary",
      ));
      else if (attempt.status !== "queued") coaching.append(button(
        attempt.coaching?.roadmap ? "Tạo lại lộ trình" : "Tạo đánh giá và lộ trình",
        async () => {
          const refreshed = await api(`/exams/${id}/attempts/${attempt.id}/coaching`, {
            method:"POST", body:{response_language:uiLanguage},
          });
          if (!active()) return;
          attempt = refreshed;
          attempts = attempts.map(item => item.id === refreshed.id ? refreshed : item);
          render();
          schedule();
          ensureCoachingLanguage();
        }, "secondary",
      ));
      box.append(
        button(
          "Làm lại đề",
          () => {
            attempt = null;
            answers = Array(answers.length).fill(null);
            sessionStorage.removeItem(cacheKey);
            render();
          },
          "secondary",
        ),
      );
      root.append(box);
    }
    if (attempts.length) {
      const select = field(root, "Lịch sử làm bài", "select");
      const empty = el("option", "Chọn kết quả đã lưu");
      empty.value = "";
      select.append(empty);
      for (const a of attempts) {
        const option = el(
          "option",
          `${new Date(a.created_at).toLocaleString("vi-VN")} · ${a.result.score}/${a.result.graded_total}`,
        );
        option.value = a.id;
        select.append(option);
      }
      select.value = attempt?.id || "";
      select.onchange = () => {
        if (select.value) {
          attempt = attempts.find((a) => a.id === select.value);
          render();
          schedule();
        }
      };
    }
    const classifications = new Map(
      exam.classification.map((item) => [item.number, item]),
    );
    const form = el("form", null, "exam-form"),
      count = el("span"),
      submit = el("button", "Nộp bài và phân tích kết quả", "primary");
    submit.type = "submit";
    const update = () => {
      count.textContent = `Đã chọn ${answers.filter((x) => x !== null).length}/${answers.length} câu`;
      submit.disabled = exam.status !== "ready" || submitting;
    };
    for (const passage of exam.structure.passages) {
      const group = el("section", null, "exam-section");
      const questions = exam.structure.questions.filter(
        (q) => q.passage_id === passage.id,
      );
      if (!questions.length) continue;
      group.append(
        el("h2", `Câu ${questions[0].number}–${questions.at(-1).number}`),
      );
      const context = el("details", null, "exam-passage");
      context.open = true;
      context.append(
        el("summary", "Đoạn đọc / hướng dẫn dùng chung"),
        sourceEl("p", passage.text),
      );
      group.append(context);
      for (const q of questions) {
        const index = exam.structure.questions.findIndex(
            (item) => item.number === q.number,
          ),
          skill = classifications.get(q.number),
          feedback = attempt?.result.feedback.find(
            (item) => item.number === q.number,
          );
        const box = el("fieldset", null, "inline-quiz-question");
        box.id = `exam-question-${q.number}`;
        box.tabIndex = -1;
        const legend = el("legend");
        legend.append(el("span", `Câu ${q.number}. `));
        legend.append(q.stem
          ? sourceEl("span", q.stem)
          : el("span", "Chọn đáp án theo đoạn đọc/hướng dẫn phía trên."));
        box.append(legend);
        if (skill)
          box.append(
            el(
              "small",
              `${exam.topic_labels[skill.topic]} · ${exam.skill_labels[skill.skill]}`,
              "exam-skill",
            ),
          );
        q.options.forEach((option, choice) => {
          const label = el("label", null, "inline-quiz-option"),
            radio = el("input");
          radio.type = "radio";
          radio.name = "exam-q-" + q.number;
          radio.value = choice;
          radio.checked =
            (attempt ? attempt.answers[index] : answers[index]) === choice;
          radio.disabled = !!attempt || exam.status !== "ready";
          radio.onchange = () => {
            answers[index] = choice;
            sessionStorage.setItem(cacheKey, JSON.stringify(answers));
            update();
          };
          label.append(
            radio,
            el("span", String.fromCharCode(65 + choice), "option-letter"),
            sourceEl("span", option),
          );
          if (feedback?.correct === choice) label.classList.add("correct");
          else if (
            feedback &&
            feedback.selected === choice &&
            feedback.correct !== null
          )
            label.classList.add("incorrect");
          box.append(label);
        });
        if (feedback) {
          box.append(
            el(
              "p",
              feedback.correct === null
                ? "Chưa xác định được đáp án — không tính điểm."
                : feedback.is_correct
                  ? "✓ Khớp đáp án AI đề xuất"
                  : "✕ Chưa khớp đáp án AI đề xuất",
              "quiz-explanation",
            ),
            sourceEl("p", feedback.explanation),
          );
          if (feedback.evidence)
            box.append(sourceEl("blockquote", feedback.evidence));
        }
        group.append(box);
      }
      form.append(group);
    }
    if (!attempt) {
      const bar = el("div", null, "exam-submit-bar");
      bar.append(count, submit);
      form.append(bar);
      update();
    }
    form.onsubmit = async (event) => {
      event.preventDefault();
      if (attempt || submitting || exam.status !== "ready") return;
      if (
        answers.some((x) => x === null) &&
        !confirm(t("Bạn còn câu chưa chọn. Nộp bài với các câu đó để trống?"))
      )
        return;
      submitting = true;
      update();
      try {
        const result = await api("/exams/" + id + "/attempts", {
          method: "POST",
          body: { answers, response_language: uiLanguage },
        });
        if (!active()) return;
        attempt = result;
        attempts.unshift(result);
        sessionStorage.removeItem(cacheKey);
        render();
        root.querySelector(".exam-results")?.scrollIntoView({ block: "start" });
        schedule();
      } catch (error) {
        notice.textContent = error.message;
      } finally {
        submitting = false;
        update();
      }
    };
    root.append(form);
  }
  async function poll() {
    if (!active()) return;
    try {
      if (["queued", "analyzing"].includes(exam.status)) {
        exam = await api("/exams/" + id);
        if (!active()) return;
        render();
      }
      if (attempt?.status === "queued") {
        attempts = await api("/exams/" + id + "/attempts");
        if (!active()) return;
        attempt = attempts.find((a) => a.id === attempt.id) || attempt;
        render();
      }
    } catch (error) {
      if (active())
        notice.textContent =
          "Chưa cập nhật được trạng thái. Hệ thống sẽ thử lại.";
    } finally {
      schedule();
    }
  }
  function schedule() {
    clearTimeout(examTimer);
    if (
      active() &&
      (["queued", "analyzing"].includes(exam.status) ||
        attempt?.status === "queued")
    )
      examTimer = setTimeout(poll, 2500);
    if (active() && attempt?.status !== "queued" && !languageRequest)
      queueMicrotask(() => ensureCoachingLanguage());
  }
  render();
  schedule();
}
