"use strict";
let chatCleanup = () => {};
function disposeChat() {
  chatCleanup();
  chatCleanup = () => {};
}

function chatMarkdown(text) {
  const box = sourceEl("div");
  let list = null;
  for (const line of text.split("\n")) {
    if (!line.trim()) {
      list = null;
      continue;
    }
    let target;
    if (/^\s*[-*]\s+/.test(line)) {
      if (!list) {
        list = el("ul");
        box.append(list);
      }
      target = el("li");
      list.append(target);
    } else {
      list = null;
      target = el(/^#{1,4}\s/.test(line) ? "h4" : "p");
      box.append(target);
    }
    const clean = line.replace(/^\s*[-*]\s+/, "").replace(/^#{1,4}\s+/, "");
    for (const part of clean.split(/(\*\*[^*\n]+\*\*)/g))
      target.append(
        part.startsWith("**") && part.endsWith("**")
          ? el("strong", part.slice(2, -2))
          : document.createTextNode(part),
      );
  }
  return box;
}

async function chatWorkspace(threadId = null) {
  reset("", "");
  root.replaceChildren();
  root.className = "chat-page fade-in";
  setNav("chat");
  window.history.replaceState(null, "", "#chat");
  const ticket = generation;
  let user = null,
    threads = [],
    current = null,
    turns = [],
    session = null;
  let pendingDocument = null,
    busy = false,
    sending = false,
    timer = null,
    pollFailures = 0;
  let localMessage = "",
    monitorOpen = window.innerWidth > 950;
  const active = () => ticket === generation;
  const quizDrafts = new Map();
  const translationRequests = new Set();
  const translationErrors = new Set();
  let translatingRequest = false;
  const originalLanguage = turn => turn.provenance?.response_language || "vi";
  const translationPending = () => turns.some(turn => turn.provenance?.translation_status === "queued");
  async function queueTranslations(preferredId = null) {
    if (!active() || translatingRequest || translationPending()) return;
    const candidates = [...turns].reverse();
    const turn = candidates.find(item => (!preferredId || item.id === preferredId) &&
      item.status === "succeeded" && originalLanguage(item) !== uiLanguage &&
      !item.translations?.[uiLanguage] && !translationRequests.has(item.id + ":" + uiLanguage));
    if (!turn) return;
    const language = uiLanguage, key = turn.id + ":" + language;
    translationRequests.add(key);
    translationErrors.delete(key);
    translatingRequest = true;
    try {
      const updated = await api(`/chat/threads/${turn.thread_id}/turns/${turn.id}/translation`, {
        method:"POST", body:{response_language:language},
      });
      if (!active()) return;
      turns = turns.map(item => item.id === updated.id ? updated : item);
    } catch (error) {
      translationErrors.add(key);
      if (active()) notice.textContent = error.message;
    } finally {
      translatingRequest = false;
      if (active()) { renderMessages(false); schedulePoll(); }
    }
  }
  const onChatLanguageChange = () => {
    translationRequests.clear();
    translationErrors.clear();
    renderMessages(false);
    queueTranslations();
    if (translationPending()) schedulePoll();
  };
  let requestedAction = "auto";
  if (token) {
    [user, threads] = await Promise.all([
      api("/users/me"),
      api("/chat/threads"),
    ]);
    if (!active()) return;
    updateIdentity(user);
    const saved = sessionStorage.getItem("padayon-chat-" + user.id);
    const selected =
      threadId ||
      (threads.some((t) => t.id === saved) ? saved : threads[0]?.id);
    if (selected) {
      [current, turns] = await Promise.all([
        api("/chat/threads/" + selected),
        api("/chat/threads/" + selected + "/turns"),
      ]);
      if (!active()) return;
      if (current.session_id) {
        session = await api("/sessions/" + current.session_id);
        if (!active()) return;
      }
      sessionStorage.setItem("padayon-chat-" + user.id, current.id);

    }
  } else updateIdentity(null);
  document.querySelector("#mode-badge").textContent = user
    ? "● Chat AI"
    : "◦ Đăng nhập để chat";
  const pageHead = el("div", null, "chat-page-head"),
    headCopy = el("div"),
    headActions = el("div", null, "chat-page-actions");
  headCopy.append(
    el("span", "HỎI MỘT ĐIỀU · HIỂU THÊM MỘT CHÚT", "eyebrow"),
    el("h1", "Chat cùng BlueStudy"),
    el("p", "Hỏi bài, gửi ghi chú hoặc cùng chuẩn bị cho buổi học tiếp theo."),
  );
  const newButton = button(
    "＋ Chat mới",
    async () => {
      if (!user) return login("chat");
      const created = await api("/chat/threads", { method: "POST", body: {} });
      if (active()) await chatWorkspace(created.id);
    },
    "secondary",
  );
  const monitorButton = button(
    "◉ Hoạt động",
    () => {
      monitorOpen = !monitorOpen;
      renderMonitorVisibility();
    },
    "secondary",
  );
  monitorButton.setAttribute("aria-expanded", String(monitorOpen));
  headActions.append(newButton, monitorButton);
  pageHead.append(headCopy, headActions);
  root.append(
    pageHead,
    el(
      "div",
      "✦ Hỏi bài trực tiếp, đính kèm ảnh/PDF hoặc tạo tài liệu ôn tập từ ghi chú của bạn.",
      "chat-status-banner",
    ),
  );
  const layout = el("div", null, "chat-layout"),
    conversation = el("section", null, "chat-conversation"),
    monitor = el("aside", null, "chat-monitor");
  conversation.setAttribute("aria-label", "Cuộc trò chuyện với BlueStudy");
  monitor.setAttribute("aria-label", "Trạng thái xử lý");
  const toolbar = el("div", null, "chat-toolbar"),
    toolbarTitle = el("div", null, "chat-toolbar-title"),
    toolbarCopy = el("div");
  toolbarCopy.append(
    el("strong", "Study with BlueStudy"),
    el("small", "Nền tảng học tiếng Anh học thuật"),
  );
  toolbarTitle.append(el("span", "✦", "chat-logo"), toolbarCopy);
  const threadSelect = el("select", null, "chat-thread-select");
  threadSelect.setAttribute("aria-label", "Lịch sử trò chuyện");
  function renderThreads() {
    threadSelect.replaceChildren();
    const placeholder = el(
      "option",
      current ? "Cuộc trò chuyện hiện tại" : "Cuộc trò chuyện mới",
    );
    placeholder.value = "";
    threadSelect.append(placeholder);
    for (const t of threads) {
      const option = sourceEl("option", t.title);
      option.value = t.id;
      threadSelect.append(option);
    }
    threadSelect.value = current?.id || "";
  }
  threadSelect.onchange = () => {
    if (threadSelect.value)
      chatWorkspace(threadSelect.value).catch(
        (e) => (notice.textContent = e.message),
      );
  };
  renderThreads();
  toolbar.append(toolbarTitle, threadSelect);
  const transcript = el("div", null, "chat-transcript");
  transcript.setAttribute("role", "log");
  transcript.setAttribute("aria-label", "Tin nhắn");
  transcript.setAttribute("aria-live", "polite");
  const composeArea = el("div", null, "chat-compose-area"),
    attachment = el("div"),
    sourceActions = el("div", null, "chat-source-actions"),
    composer = el("form", null, "chat-compose-box");
  const fileInput = el("input");
  fileInput.type = "file";
  fileInput.accept = ".png,.jpg,.jpeg,.pdf";
  fileInput.hidden = true;
  fileInput.setAttribute("aria-label", "Chọn ảnh hoặc PDF để đính kèm");
  const attachButton = button(
    "＋",
    () => {
      if (!user) return login("chat");
      fileInput.click();
    },
    "chat-attach",
  );
  attachButton.type = "button";
  attachButton.setAttribute("aria-label", "Đính kèm ảnh hoặc PDF");
  const input = el("textarea");
  input.placeholder = "Hỏi bất cứ điều gì, hoặc gửi ghi chú, ảnh/PDF…";
  input.setAttribute("aria-label", "Tin nhắn cho BlueStudy");
  input.maxLength = 1500;
  input.rows = 1;
  const sendButton = el("button", "Gửi ↑", "primary chat-send");
  sendButton.type = "submit";
  const count = el("span", "0 / 1500");
  input.oninput = () => {
    count.textContent = input.value.length + " / 1500";
    input.style.height = "46px";
    input.style.height = Math.min(input.scrollHeight, 120) + "px";
  };
  input.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      composer.requestSubmit();
    }
  };
  composer.append(attachButton, input, sendButton);
  const composeFooter = el("div", null, "chat-compose-footer");
  composeFooter.append(
    el(
      "span",
      "Enter để gửi · Shift + Enter để xuống dòng · AI có thể mắc lỗi",
    ),
    count,
  );
  composeArea.append(
    attachment,
    sourceActions,
    composer,
    fileInput,
    composeFooter,
  );
  conversation.append(toolbar, transcript, composeArea);
  layout.append(conversation, monitor);
  root.append(layout);
  const reviewDialog = el("dialog", null, "chat-review-dialog");
  reviewDialog.setAttribute("aria-label", "Kiểm tra tài liệu đính kèm");
  root.append(reviewDialog);
  chatCleanup = () => {
    clearTimeout(timer);
    window.removeEventListener("ui-language-change", onChatLanguageChange);
    if (reviewDialog.open) reviewDialog.close();
  };
  function renderMonitorVisibility() {
    monitor.hidden = !monitorOpen;
    layout.classList.toggle("monitor-closed", !monitorOpen);
    monitorButton.setAttribute("aria-expanded", String(monitorOpen));
  }
  function latest() {
    return turns[turns.length - 1];
  }
  function hasPending() {
    return turns.some((t) => t.status === "queued");
  }
  function lockComposer() {
    const pending = hasPending() || sending || busy;
    sendButton.disabled = pending || !user;
    attachButton.disabled = pending;
    threadSelect.disabled = busy || sending;
    newButton.disabled = busy || sending;
    input.disabled = !user;
    input.placeholder = user
      ? "Hỏi bất cứ điều gì, hoặc gửi ghi chú, ảnh/PDF…"
      : "Đăng nhập để trò chuyện với BlueStudy…";
  }
  function renderMessages(scroll = true) {
    const nearBottom =
      transcript.scrollHeight - transcript.scrollTop - transcript.clientHeight <
      100;
    transcript.replaceChildren();
    if (!turns.length) {
      const welcome = el("div", null, "chat-welcome");
      welcome.append(
        el("div", "✦", "welcome-orbit"),
        el("h2", "Hôm nay, bạn muốn hiểu điều gì?"),
        el(
          "p",
          "Bạn có thể hỏi ngay mà không cần tải tài liệu. Nếu có ghi chú, hãy gửi ảnh hoặc PDF để mình cùng đọc nhé.",
        ),
      );
      if (!user)
        welcome.append(
          button("Đăng nhập để bắt đầu", () => login("chat"), "primary"),
        );
      else {
        const suggestions = el("div", null, "chat-suggestions");
        for (const text of [
          "Giải thích since và for",
          "Giúp mình lên kế hoạch ôn tập",
          "Cách học từ vựng hiệu quả",
        ]) {
          suggestions.append(
            button(text, () => {
              input.value = t(text);
              input.oninput();
              input.focus();
            }),
          );
        }
        welcome.append(suggestions);
      }
      transcript.append(welcome);
    }
    for (const original of turns) {
      const localized = original.translations?.[uiLanguage];
      const turn = localized ? {...original, ...localized} : original;
      const row = el("div", null, "chat-turn");
      row.append(sourceEl("div", turn.message, "chat-bubble user"));
      if (turn.image_document_id) {
        const preview = el("img", null, "chat-image-preview");
        preview.src = "/documents/" + turn.image_document_id + "/source";
        preview.alt = "Ảnh đã gửi cho Qwen-VL";
        preview.loading = "lazy";
        row.append(preview);
      }
      if (turn.status === "succeeded") {
        const answer = el("div", null, "chat-bubble assistant");
        if (originalLanguage(original) !== uiLanguage && !localized) {
          const key = turn.id + ":" + uiLanguage;
          const failed = translationErrors.has(key) ||
            (turn.provenance?.translation_status === "failed" && turn.provenance?.translation_language === uiLanguage);
          answer.append(el("p", failed ? "Chưa dịch được tin nhắn. Bấm thử lại." : "Đang chuyển câu trả lời sang ngôn ngữ bạn chọn…"));
          if (failed) answer.append(button("Thử dịch lại", () => {
            translationRequests.delete(key);
            return queueTranslations(turn.id);
          }, "secondary"));
          row.append(answer);
          transcript.append(row);
          continue;
        }
        answer.append(chatMarkdown(turn.answer || ""));
        if (turn.quiz) {
          if (!quizDrafts.has(turn.id))
            quizDrafts.set(
              turn.id,
              Array(turn.quiz.questions.length).fill(null),
            );
          answer.classList.add("with-quiz");
          answer.append(
            inlineQuiz(turn, quizDrafts.get(turn.id), async (answers) => {
              const result = await api(
                `/chat/threads/${turn.thread_id}/turns/${turn.id}/quiz-submit`,
                { method: "POST", body: { answers } },
              );
              if (!active()) return;
              original.quiz_result = result;
              await refreshTurns();
              if (!active()) return;
              renderMessages(false);
              renderMonitor();
            }),
          );
        }
        const p = turn.provenance || {};
        answer.append(
          el(
            "div",
            (p.model || "BlueStudy AI") +
              (p.fallback_reason ? " · đang dùng local dự phòng" : "") +
              " · Nội dung chưa qua giáo viên kiểm duyệt",
            "chat-answer-meta",
          ),
        );
        row.append(answer);
      } else if (turn.status === "failed") {
        const error = el("div", null, "chat-error");
        error.append(
          el("div", "Chưa trả lời được lúc này. Bạn có thể gửi lại câu hỏi."),
          button(
            "Đưa câu hỏi vào ô nhập",
            () => {
              input.value = turn.message;
              input.oninput();
              input.focus();
            },
            "secondary",
          ),
        );
        row.append(error);
      } else {
        const waiting = el("div", null, "chat-pending");
        waiting.append(
          el("span", null, "chat-pulse"),
          el("span", "Đã nhận câu hỏi · đang chờ hoặc xử lý…"),
        );
        row.append(waiting);
      }
      transcript.append(row);
    }
    if (scroll || nearBottom) {
      const quiz = transcript.querySelector(".chat-turn:last-child .inline-quiz");
      if (quiz) transcript.scrollTop += quiz.getBoundingClientRect().top - transcript.getBoundingClientRect().top - 12;
      else transcript.scrollTop = transcript.scrollHeight;
    }
    lockComposer();
  }
  function stage(code, title, text, state = "") {
    const box = el("div", null, "monitor-stage " + state);
    box.append(
      el("div", code, "stage-caption"),
      el("strong", title),
      el("p", text),
    );
    return box;
  }
  function renderMonitor() {
    const last = latest();
    monitor.replaceChildren(
      el("span", "● THEO DÕI PHIÊN HỌC", "eyebrow"),
      el("h2", "BlueStudy đang làm gì?"),
      el("p", "Trạng thái lấy từ tác vụ đang lưu trên hệ thống."),
    );
    if (last?.provenance?.agent_trace) {
      const trace = last.provenance.agent_trace;
      const completed = trace.filter((item) => item.status === "done").length;
      const progress = el("progress", null, "agent-progress");
      progress.max = trace.length;
      progress.value = completed;
      progress.setAttribute("aria-label", "Tiến độ tạo quiz");
      monitor.append(el("h3", "3 bước tạo quiz", "agent-heading"), progress);
      trace.forEach((item, index) =>
        monitor.append(
          stage(
            `${index + 1} / ${item.status === "done" ? "✓ HOÀN TẤT" : item.status === "failed" ? "CHƯA HOÀN TẤT" : "CHỜ / XỬ LÝ"}`,
            item.agent,
            item.detail,
            item.status === "failed"
              ? "failed"
              : item.status === "pending"
                ? "active"
                : "",
          ),
        ),
      );
      if (last.quiz_result)
        monitor.append(
          stage(
            "KẾT QUẢ",
            `${last.quiz_result.score} / ${last.quiz_result.total} câu đúng`,
            "Đã chấm trên máy chủ và lưu vào lịch sử chat.",
          ),
        );
    }
    if (!last?.provenance?.agent_trace) {
      monitor.append(
        stage(
          "01 / NGUỒN HỌC",
          pendingDocument
            ? "Tài liệu đính kèm"
            : session
              ? "Đã chọn đoạn nguồn"
              : "Trò chuyện tự do",
          pendingDocument
            ? pendingDocument.media_type?.startsWith("image/")
              ? "Gửi trực tiếp cho Qwen-VL local cùng câu hỏi của bạn."
              : status(pendingDocument.status)
            : session
              ? `${session.source_text.length} ký tự đã xác nhận.`
              : "Bạn có thể hỏi mà không cần tài liệu.",
          pendingDocument?.status === "queued" ? "active" : "",
        ),
      );
      monitor.append(
        stage(
          "02 / TRỢ LÝ HỘI THOẠI",
          last?.status === "queued"
            ? "Đang chờ / xử lý"
            : last?.status === "succeeded"
              ? "Đã trả lời"
              : last?.status === "failed"
                ? "Chưa hoàn tất"
                : "Sẵn sàng lắng nghe",
          last?.status === "queued"
            ? "Câu hỏi đã vào hàng đợi. Bạn có thể mở lại cuộc trò chuyện sau."
            : last?.status === "failed"
              ? "Không có câu trả lời hoàn chỉnh. Hãy thử gửi lại."
              : last?.status === "succeeded"
                ? "Câu trả lời đã được nhận và lưu."
                : "Gửi câu hỏi để bắt đầu.",
          last?.status === "queued"
            ? "active"
            : last?.status === "failed"
              ? "failed"
              : "",
        ),
      );
      monitor.append(
        stage(
          "03 / LỊCH SỬ",
          user ? "Lưu theo tài khoản" : "Chưa đăng nhập",
          turns.length
            ? `${turns.length} lượt đang hiển thị · tối đa 100 lượt gần nhất.`
            : "Lịch sử sẽ xuất hiện sau tin nhắn đầu tiên.",
        ),
      );
    }
    if (last?.provenance) {
      const meta = el("div", null, "monitor-meta");
      meta.append(
        el("div", "Mô hình trả lời"),
        el("strong", last.provenance.model || "—"),
        el(
          "div",
          last.provenance.fallback_reason
            ? "Local dự phòng · " + last.provenance.fallback_reason
            : "Nguồn: " + (last.provenance.provider || "—"),
        ),
      );
      monitor.append(el("div", null, "monitor-divider"), meta);
    }
    if (last?.finished_at)
      monitor.append(
        el(
          "div",
          "Cập nhật: " + new Date(last.finished_at).toLocaleTimeString("vi-VN"),
          "monitor-meta",
        ),
      );
    if (localMessage) monitor.append(el("p", localMessage, "monitor-note"));
    if (current)
      monitor.append(
        button(
          "Xóa cuộc trò chuyện",
          async () => {
            if (!confirm(t("Xóa cuộc trò chuyện và toàn bộ tin nhắn trong đó?")))
              return;
            await api("/chat/threads/" + current.id, { method: "DELETE" });
            sessionStorage.removeItem("padayon-chat-" + user.id);
            await chatWorkspace();
          },
          "text-button",
        ),
      );
    renderMonitorVisibility();
  }
  function renderAttachment() {
    attachment.replaceChildren();
    sourceActions.replaceChildren();
    if (pendingDocument) {
      const box = el("div", null, "chat-attachment"),
        copy = el("div");
      copy.append(
        sourceEl("strong", pendingDocument.source_name || pendingDocument.title),
        el(
          "small",
          pendingDocument.media_type?.startsWith("image/")
            ? "Qwen-VL sẽ đọc trực tiếp ảnh khi bạn bấm Gửi"
            : status(pendingDocument.status),
        ),
      );
      box.append(el("span", "▤", "attachment-symbol"), copy);
      if (pendingDocument.media_type?.startsWith("image/")) {
        const preview = el("img", null, "chat-attachment-preview");
        preview.src = "/documents/" + pendingDocument.id + "/source";
        preview.alt = "Ảnh sắp gửi";
        box.prepend(preview);
        box.append(
          button(
            "Bỏ ảnh",
            () => {
              pendingDocument = null;
              renderAttachment();
              renderMonitor();
            },
            "secondary",
          ),
        );
      } else if (pendingDocument.status !== "queued")
        box.append(button("Kiểm tra văn bản", openReview, "secondary"));
      attachment.append(box);
    } else if (session) {
      const box = el("div", null, "chat-attachment"),
        copy = el("div");
      copy.append(
        el("strong", "Đang dùng đoạn nguồn đã xác nhận"),
        el(
          "small",
          session.source_text.slice(0, 80) +
            (session.source_text.length > 80 ? "…" : ""),
        ),
      );
      box.append(
        el("span", "▤", "attachment-symbol"),
        copy,
        button(
          "Bỏ đính kèm",
          async () => {
            current = await api("/chat/threads/" + current.id, {
              method: "PATCH",
              body: { session_id: null },
            });
            session = null;
            renderAttachment();
            renderMonitor();
          },
          "secondary",
        ),
      );
      attachment.append(box);
    }
    if (session && !pendingDocument?.media_type?.startsWith("image/")) {
      sourceActions.append(
        button(
          "✦ Tạo bộ ôn tập",
          async () => {
            if (hasPending())
              throw Error("Chờ BlueStudy trả lời trước khi tạo bộ ôn tập.");
            const job = await api("/sessions/" + session.id + "/jobs", {
              method: "POST",
              body: { kind: "generate_bundle" },
            });
            notice.textContent = "Đã gửi yêu cầu tạo bộ ôn tập.";
            const result = await waitJob(job.id);
            if (result && active()) await study(session.id);
          },
          "secondary",
        ),
        button("Mở sơ đồ bài học ↗", () => study(session.id), "secondary"),
      );
    }
    lockComposer();
  }
  async function ensureThread() {
    if (current) return current;
    current = await api("/chat/threads", { method: "POST", body: {} });
    if (!active()) return current;
    threads.unshift(current);
    sessionStorage.setItem("padayon-chat-" + user.id, current.id);
    renderThreads();
    return current;
  }
  async function refreshTurns() {
    if (!current) return;
    const rows = await api("/chat/threads/" + current.id + "/turns");
    if (!active()) return;
    const changed = JSON.stringify(rows) !== JSON.stringify(turns);
    turns = rows;
    if (changed) {
      renderMessages(false);
      renderMonitor();
    }
    lockComposer();
  }
  async function poll() {
    if (!active()) return;
    try {
      if (pendingDocument?.status === "queued") {
        const doc = await api("/documents/" + pendingDocument.id);
        if (!active()) return;
        pendingDocument = doc;
        renderAttachment();
        renderMonitor();
      }
      if (hasPending() || translationPending()) await refreshTurns();
      queueTranslations();
      pollFailures = 0;
    } catch (error) {
      if (active()) {
        pollFailures++;
        notice.textContent =
          "Chưa cập nhật được trạng thái. Lịch sử đã nhận vẫn được lưu; hệ thống sẽ thử lại.";
      }
    } finally {
      if (active() && (hasPending() || translationPending() || pendingDocument?.status === "queued"))
        timer = setTimeout(poll, Math.min(10000, 1800 + pollFailures * 1500));
    }
  }
  function schedulePoll() {
    clearTimeout(timer);
    timer = setTimeout(poll, 1200);
  }
  composer.onsubmit = async (event) => {
    event.preventDefault();
    if (!user) return login("chat");
    if (sending || hasPending() || busy) return;
    const imageId = pendingDocument?.media_type?.startsWith("image/")
      ? pendingDocument.id
      : null;
    const text =
      input.value.trim() ||
      (imageId ? t("Đọc nội dung trong ảnh và giải thích giúp mình.") : "");
    const responseLanguage = uiLanguage;
    if (!text) return;
    notice.textContent = "";
    sending = true;
    lockComposer();
    try {
      await ensureThread();
      if (!active()) return;
      const turn = await api("/chat/threads/" + current.id + "/turns", {
        method: "POST",
        body: {
          message: text,
          image_document_id: imageId,
          action: requestedAction,
          response_language: responseLanguage,
        },
      });
      if (!active()) return;
      turns.push(turn);
      if (imageId && pendingDocument?.id === imageId) {
        pendingDocument = null;
        renderAttachment();
      }
      requestedAction = "auto";
      input.value = "";
      input.oninput();
      if (current.title === "Cuộc trò chuyện mới") {
        current.title = text.slice(0, 100);
        renderThreads();
      }
      renderMessages();
      renderMonitor();
      schedulePoll();
    } catch (error) {
      if (active()) notice.textContent = error.message;
    } finally {
      sending = false;
      if (active()) lockComposer();
    }
  };
  fileInput.onchange = async () => {
    const file = fileInput.files[0];
    if (!file) return;
    fileInput.value = "";
    if (file.size > 10 * 1024 * 1024) {
      notice.textContent = "Tệp tối đa 10 MB.";
      return;
    }
    busy = true;
    lockComposer();
    try {
      await ensureThread();
      if (!active()) return;
      const form = new FormData();
      form.append("file", file);
      form.append("title", file.name.slice(0, 160));
      const isImage = /\.(png|jpe?g)$/i.test(file.name);
      if (isImage) form.append("purpose", "chat_image");
      const doc = await api("/uploads", { method: "POST", body: form });
      if (!active()) return;
      pendingDocument = doc;
      localMessage = isImage
        ? "Ảnh đã sẵn sàng. Nhập câu hỏi rồi bấm Gửi; Qwen-VL sẽ xem ảnh và trả lời ngay trong chat."
        : "PDF đã lưu. Hãy kiểm tra văn bản trích xuất để dùng làm nguồn.";
      renderAttachment();
      renderMonitor();
      schedulePoll();
    } catch (error) {
      if (active()) notice.textContent = error.message;
    } finally {
      busy = false;
      if (active()) lockComposer();
    }
  };
  function openReview() {
    const doc = pendingDocument;
    if (!doc) return;
    reviewDialog.replaceChildren();
    const heading = el("div", null, "dialog-head");
    heading.append(
      el("span", "TÀI LIỆU ĐÍNH KÈM", "eyebrow"),
      button("×", () => reviewDialog.close(), "text-button"),
    );
    reviewDialog.append(
      heading,
      el("h2", "Kiểm tra trước khi cùng học"),
      el(
        "p",
        "Sửa những chỗ nhận dạng chưa đúng. Sau đó chọn đoạn tối đa 2.400 ký tự để dùng trong cuộc trò chuyện.",
        "muted",
      ),
    );
    const text = field(
      reviewDialog,
      "Văn bản trích xuất",
      "textarea",
      doc.text || "",
    );
    text.maxLength = 100000;
    const offsets = el("div", null, "row"),
      start = field(offsets, "Ký tự bắt đầu", "input", "0"),
      end = field(
        offsets,
        "Ký tự kết thúc",
        "input",
        String(Math.min(2400, doc.text?.length || 0)),
      );
    start.type = end.type = "number";
    start.min = "0";
    end.min = "1";
    reviewDialog.append(offsets);
    const errorBox = el("p", null, "chat-review-error");
    errorBox.setAttribute("role", "alert");
    reviewDialog.append(errorBox);
    const actions = el("div", null, "dialog-actions");
    actions.append(button("Để sau", () => reviewDialog.close(), "secondary"));
    const use = button(
      "Xác nhận và dùng trong chat",
      async () => {
        errorBox.textContent = "";
        try {
          if (hasPending())
            throw Error("Chờ câu trả lời hiện tại trước khi đổi tài liệu.");
          if (!text.value.trim()) throw Error("Hãy nhập văn bản nguồn.");
          const a = Number(start.value),
            b = Number(end.value);
          if (
            !Number.isInteger(a) ||
            !Number.isInteger(b) ||
            a < 0 ||
            b <= a ||
            b > text.value.length ||
            b - a > 2400
          )
            throw Error("Chọn đoạn hợp lệ từ 1 đến 2.400 ký tự.");
          let updated = pendingDocument;
          if (text.value !== updated.text) {
            updated = await api("/documents/" + doc.id + "/text", {
              method: "PATCH",
              body: { text: text.value, expected_revision: updated.revision },
            });
            pendingDocument = updated;
          }
          if (updated.status !== "confirmed") {
            updated = await api("/documents/" + doc.id + "/confirm", {
              method: "POST",
              body: { expected_revision: updated.revision },
            });
            pendingDocument = updated;
          }
          const selected = await api("/sessions", {
            method: "POST",
            body: { document_id: doc.id, start_offset: a, end_offset: b },
          });
          const thread = await api("/chat/threads/" + current.id, {
            method: "PATCH",
            body: { session_id: selected.id },
          });
          if (!active()) return;
          session = selected;
          current = thread;
          pendingDocument = null;
          reviewDialog.close();
          localMessage =
            "Nguồn đã được xác nhận. Các tin nhắn mới sẽ dùng đoạn vừa chọn.";
          renderAttachment();
          renderMonitor();
          input.focus();
        } catch (error) {
          errorBox.textContent = error.message;
        }
      },
      "primary",
    );
    actions.append(use);
    reviewDialog.append(actions);
    reviewDialog.showModal();
  }
  renderMessages();
  renderAttachment();
  renderMonitor();
  window.addEventListener("ui-language-change", onChatLanguageChange);
  queueTranslations();
  if (hasPending() || translationPending()) schedulePoll();
}

// All deferred feature scripts, including Speaking, must load before routing.
window.addEventListener('DOMContentLoaded', () => {
  startWorkspace().catch((error) => (notice.textContent = error.message));
}, {once:true});
