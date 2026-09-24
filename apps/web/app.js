"use strict";
async function topicSelector(id, selected) {
  const box = el("div", null, "card"),
    select = field(box, "Chủ đề học (bạn tự xác nhận)", "select");
  const unknown = el("option", "Chưa xác định");
  unknown.value = "";
  select.append(unknown);
  const topics = await api("/curriculum");
  for (const t of topics) {
    const option = el("option", "Unit " + t.unit + " · " + t.title);
    option.value = t.id;
    select.append(option);
  }
  select.value = selected || "";
  const source = el("a", "Nguồn chủ đề: HEID / Global Success");
  source.href = topics[0].source_url;
  source.target = "_blank";
  source.rel = "noopener noreferrer";
  box.append(
    button(
      "Lưu chủ đề",
      async () => {
        await api("/sessions/" + id + "/curriculum", {
          method: "PATCH",
          body: { topic_id: select.value || null },
        });
        notice.textContent = "Đã lưu lựa chọn chủ đề của bạn.";
      },
      "secondary",
    ),
    source,
  );
  root.append(box);
}
async function topicProgress(progress) {
  const grid = el("div", null, "grid");
  for (const t of progress.topics.filter((t) => t.attempts)) {
    const c = el("div", null, "card");
    c.append(
      el("h3", t.title),
      el("p", t.average_percent + "% · " + t.attempts + " lượt"),
      el(
        "small",
        {
          insufficient_data: "Chưa đủ lượt để nhận xét",
          needs_practice: "Nên dành thêm thời gian ôn",
          stronger: "Kết quả luyện tập tốt",
          practising: "Tiếp tục luyện tập",
        }[t.status],
      ),
    );
    grid.append(c);
  }
  root.append(grid);
  const mistakes = await api("/users/me/review");
  if (mistakes.length) {
    const box = el("div", null, "card");
    box.append(el("h2", "Những câu cần ôn lại"));
    for (const q of mistakes) {
      const d = el("details");
      d.append(
        el("summary", q.question),
        el("p", q.options[q.correct] + " — " + q.explanation),
        sourceEl("blockquote", q.quote),
        button("Mở bộ học", () => study(q.session_id), "secondary"),
      );
      box.append(d);
    }
    root.append(box);
  }
}
const root = document.querySelector("#content");
const notice = document.querySelector("#notice");
let token = sessionStorage.getItem("padayon-token") || "";
let generation = 0;
const el = (tag, text, cls) => {
  const n = document.createElement(tag);
  if (text != null) n.textContent = text;
  if (cls) n.className = cls;
  return n;
};
const sourceEl = (tag, text, cls) => {
  const node = el(tag, text, cls);
  node.setAttribute("translate", "no");
  return node;
};
const button = (text, action, cls) => {
  const b = el("button", text, cls);
  b.onclick = async () => {
    b.disabled = true;
    notice.textContent = "";
    try {
      await action();
    } catch (e) {
      notice.textContent = e.message;
    } finally {
      b.disabled = false;
    }
  };
  return b;
};
function field(parent, title, tag = "input", value = "") {
  const l = el("label", title),
    n = el(tag);
  n.value = value;
  l.append(n);
  parent.append(l);
  return n;
}
function reset(title, description) {
  if (typeof disposeExam === "function") disposeExam();
  if (typeof disposeNotebook === "function") disposeNotebook();
  if (typeof disposeChat === "function") disposeChat();
  generation++;
  root.className = "fade-in";
  root.replaceChildren(el("h1", title), el("p", description, "muted"));
  notice.textContent = "";
}
async function api(path, options = {}) {
  const headers = { ...(token && token !== "local" ? {Authorization: "Bearer " + token} : {}), ...options.headers };
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.body);
  }
  const r = await fetch(path, { ...options, headers });
  if (!r.ok) {
    if (r.status === 401) {
      token = "";
      sessionStorage.removeItem("padayon-token");
      notice.textContent = "Phiên học đã hết hạn. Tải lại trang để tiếp tục.";
    }
    const d = await r.json().catch(() => ({}));
    throw new Error(
      typeof d.detail === "string"
        ? d.detail
        : typeof d.detail?.message === "string"
          ? d.detail.message
          : Array.isArray(d.detail)
            ? "Dữ liệu chưa hợp lệ: " + d.detail.map(item => item.msg || "Kiểm tra trường dữ liệu").join("; ")
            : `Không thể thực hiện (HTTP ${r.status}). Hãy thử lại.`,
    );
  }
  return r.status === 204 ? null : r.json();
}
async function openLocalSession() {
  const response = await fetch("/local-session", {method: "POST"});
  if (!response.ok) throw new Error("Không mở được góc học tập. Kiểm tra API và tài khoản mặc định trên máy.");
  token = "local";
  sessionStorage.removeItem("padayon-token");
}
async function startWorkspace() {
  await openLocalSession();
  if (location.hash.startsWith("#exam=")) return examView(location.hash.slice(6));
  if (location.hash === "#exams") return show("exams");
  await show(location.hash === "#chat" ? "chat" : "map");
}
async function login(afterView = "library") {
  await openLocalSession();
  await show(afterView);
}
async function show(view) {
  window.history.replaceState(null, "", view === "chat" ? "#chat" : location.pathname);
  setNav(view);
  if (view === "exams") { window.history.replaceState(null,"","#exams"); return examHome(); }
  if (view === "chat") return chatWorkspace();
  if (!token) {
    updateIdentity(null);
    if (view === "map") return notebookDashboard();
    if (view === "roadmap") return roadmap();
    return login();
  }
  const u = await api("/users/me");
  updateIdentity(u);
  document
    .querySelectorAll("nav button")
    .forEach((n) => n.classList.toggle("active", n.dataset.view === view));
  if (view === "library") return library();
  if (view === "history") return sessionHistory();
  if (view === "progress") return progress();
  if (view === "profile") return profile(u);
  if (view === "map") return notebookDashboard();
  if (view === "roadmap") return roadmap();
}
async function library() {
  reset(
    "Hôm nay, mình học gì?",
    "Biến ghi chú của bạn thành những bước học nhỏ, dễ hiểu.",
  );
  const hero = el("div", null, "hero");
  hero.append(
    el("div", "01 / BẮT ĐẦU TỪ TÀI LIỆU CỦA BẠN", "label"),
    el("h2", "Ghi chú lộn xộn? Để BlueStudy giúp bạn."),
    el(
      "p",
      "Thêm ảnh, PDF hoặc dán ghi chú. Kiểm tra nội dung rồi tạo bộ ôn tập của riêng mình.",
    ),
  );
  const grid = el("div", null, "grid"),
    paste = el("div", null, "card"),
    upload = el("div", null, "card");
  const title = field(paste, "Tên ghi chú"),
    text = field(paste, "Nội dung (tối đa 2.400 ký tự)", "textarea");
  text.maxLength = 2400;
  title.maxLength = 160;
  paste.append(
    button("Lưu ghi chú", async () => {
      const d = await api("/documents", {
        method: "POST",
        body: { title: title.value, text: text.value },
      });
      await documentView(d.id);
    }),
  );
  upload.append(
    el("h3", "Tải ảnh hoặc PDF"),
    el("p", "PNG, JPG, PDF · tối đa 10 MB, 20 trang", "muted"),
  );
  const f = field(upload, "Chọn tài liệu");
  f.type = "file";
  f.accept = ".png,.jpg,.jpeg,.pdf";
  upload.append(
    button("Tải lên", async () => {
      if (!f.files[0]) throw Error("Hãy chọn một tài liệu.");
      const data = new FormData();
      data.append("file", f.files[0]);
      data.append("title", f.files[0].name.slice(0, 160));
      const d = await api("/uploads", { method: "POST", body: data });
      await documentView(d.id);
    }),
  );
  grid.append(paste, upload);
  hero.append(grid);
  root.append(hero, el("h2", "Thư viện của bạn"));
  const docs = await api("/documents?limit=100");
  const list = el("div", null, "grid document-grid");
  for (const d of docs) {
    const c = el("div", null, "card document-card");
    const actions = el("div", null, "document-card-actions");
    actions.append(
      el("span", status(d.status), "pill"),
      button("Mở tài liệu →", async () => {
        await documentView(d.id);
        window.scrollTo({ top: 0, behavior: "instant" });
      }, "secondary"),
    );
    c.append(
      el(
        "div",
        d.media_type === "text/plain" ? "GHI CHÚ" : "TÀI LIỆU",
        "label",
      ),
      sourceEl("h3", d.title),
      actions,
    );
    list.append(c);
  }
  root.append(list);
  if (!docs.length)
    root.append(
      el("p", "Tài liệu đầu tiên của bạn sẽ xuất hiện ở đây.", "empty"),
    );
}
function status(s) {
  return (
    {
      queued: "Đang xử lý",
      review_required: "Cần kiểm tra",
      confirmed: "Sẵn sàng học",
      failed: "Xử lý chưa thành công",
    }[s] || s
  );
}
async function documentView(id) {
  const d = await api("/documents/" + id);
  reset(d.title, status(d.status));
  const box = el("div", null, "card");
  root.append(box);
  if (d.media_type === "application/pdf") box.append(button("Chuyển thành đề thi có cấu trúc", async () => {
    const exam = await api("/exams", {method:"POST",body:{document_id:id}});
    await examView(exam.id);
  }, "secondary"));
  box.append(
    button(
      "Tải bản gốc",
      async () => {
        const r = await fetch("/documents/" + id + "/source", {
          headers: token === "local" ? {} : { Authorization: "Bearer " + token },
        });
        if (!r.ok) throw Error("Không tải được bản gốc.");
        const url = URL.createObjectURL(await r.blob()),
          a = el("a");
        a.href = url;
        a.download = d.source_name;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      },
      "secondary",
    ),
  );
  if (d.status === "queued") {
    box.append(
      el("p", "Bạn có thể quay lại thư viện trong lúc BlueStudy đọc tài liệu."),
    );
    const g = generation;
    setTimeout(() => {
      if (g === generation)
        documentView(id).catch((e) => (notice.textContent = e.message));
    }, 3000);
    return;
  }
  if (d.status === "failed") {
    box.append(
      el(
        "p",
        "Không đọc được tài liệu. Bạn có thể thử lại hoặc nhập văn bản bên dưới.",
      ),
      button("Thử đọc lại", async () => {
        await api("/documents/" + id + "/retry", {
          method: "POST",
          body: { expected_revision: d.revision },
        });
        await documentView(id);
      }),
    );
  }
  const text = field(
    box,
    "Kiểm tra và sửa văn bản trích xuất",
    "textarea",
    d.text,
  );
  text.maxLength = 100000;
  box.append(
    button("Lưu và xác nhận nội dung", async () => {
      let current = d;
      if (text.value !== d.text)
        current = await api("/documents/" + id + "/text", {
          method: "PATCH",
          body: { text: text.value, expected_revision: d.revision },
        });
      await api("/documents/" + id + "/confirm", {
        method: "POST",
        body: { expected_revision: current.revision },
      });
      await documentView(id);
    }),
  );
  if (d.status === "confirmed") {
    const start = field(box, "Bắt đầu từ ký tự", "input", "0"),
      end = field(
        box,
        "Kết thúc tại ký tự (đoạn học tối đa 2.400 ký tự)",
        "input",
        String(Math.min(d.text.length, 2400)),
      );
    start.type = end.type = "number";
    box.append(
      button("Bắt đầu học →", async () => {
        if (text.value !== d.text) {
          throw Error(
            "Hãy lưu và xác nhận phần văn bản vừa sửa trước khi học.",
          );
        }
        const s = await api("/sessions", {
          method: "POST",
          body: {
            document_id: id,
            start_offset: Number(start.value),
            end_offset: Number(end.value),
          },
        });
        await study(s.id);
      }),
    );
  }
  box.append(
    button(
      "Xóa tài liệu",
      async () => {
        if (!confirm(t("Xóa tài liệu cùng các bộ học và điểm liên quan?"))) return;
        await api("/documents/" + id, { method: "DELETE" });
        await library();
      },
      "danger",
    ),
  );
}
async function sessionHistory() {
  reset("Tiếp tục bước nhỏ của bạn", "Mở lại phiên học và bộ ôn tập đã lưu.");
  const rows = await api("/sessions");
  for (const s of rows) {
    const c = el("div", null, "card");
    c.append(
      el("p", s.source_text.slice(0, 180)),
      button("Tiếp tục học", () => study(s.id)),
    );
    root.append(c);
  }
  if (!rows.length)
    root.append(
      el("p", "Chưa có phiên học. Hãy bắt đầu từ thư viện.", "empty"),
    );
}
async function waitJob(id) {
  const g = generation;
  for (let i = 0; i < 150; i++) {
    if (g !== generation) return null;
    const j = await api("/jobs/" + id);
    if (j.status === "succeeded") return j.result;
    if (j.status === "failed")
      throw Error(
        "Chưa tạo được nội dung (" +
          j.error_code +
          "). Hãy thử lại với đoạn nguồn rõ hơn.",
      );
    notice.textContent =
      "BlueStudy đang chuẩn bị nội dung. Bạn có thể quay lại phiên học sau.";
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw Error("Tác vụ vẫn đang xử lý. Mở lại phiên học sau.");
}
async function progress() {
  reset(
    "Mỗi bước nhỏ đều đáng ghi nhận.",
    "Điểm tự luyện giúp bạn nhìn lại quá trình, không thay thế đánh giá của giáo viên.",
  );
  const p = await api("/users/me/progress");
  await topicProgress(p);
  const c = el("div", null, "hero");
  c.append(
    el("div", "100 LƯỢT LÀM BÀI GẦN NHẤT", "label"),
    el(
      "p",
      p.average_percent == null ? "Chưa có điểm" : p.average_percent + "%",
      "score",
    ),
    el("p", p.attempt_count + " lượt làm bài"),
  );
  const bar = el("progress");
  bar.max = 100;
  bar.value = p.average_percent || 0;
  bar.setAttribute("aria-label", "Điểm trung bình");
  c.append(bar);
  root.append(c);
  for (const a of p.attempts) {
    const row = el("div", null, "card");
    row.append(
      el(
        "p",
        new Date(a.created_at).toLocaleString("vi-VN") + " · " + a.score + "/5",
      ),
      button(
        "Ôn lại bộ học",
        async () => {
          const m = await api("/materials/" + a.material_id);
          await study(m.session_id);
        },
        "secondary",
      ),
    );
    root.append(row);
  }
  root.append(
    button(
      "Xóa lịch sử điểm",
      async () => {
        if (!confirm(t("Xóa toàn bộ lịch sử điểm của bạn?"))) return;
        await api("/users/me/progress", { method: "DELETE" });
        await progress();
      },
      "danger",
    ),
  );
}
function profile(u) {
  reset(
    "Cách học phù hợp với bạn",
    "Bạn có thể thay đổi mức hỗ trợ ngôn ngữ bất cứ lúc nào.",
  );
  const c = el("div", null, "card"),
    name = field(c, "Tên hiển thị", "input", u.display_name),
    level = field(c, "Mức hỗ trợ tiếng Anh", "select");
  for (const [value, text] of [
    ["support", "Giải thích kỹ bằng tiếng Việt"],
    ["basic", "Cơ bản"],
    ["confident", "Tự tin với tiếng Anh"],
  ]) {
    const o = el("option", text);
    o.value = value;
    level.append(o);
  }
  level.value = u.language_level;
  name.maxLength = 80;
  const preference = field(c, "Hoạt động bạn thích", "select");
  for (const [value, text] of [
    ["notes", "Đọc ghi chú"],
    ["flashcards", "Ôn flashcard"],
    ["quiz", "Làm quiz"],
  ]) {
    const o = el("option", text);
    o.value = value;
    preference.append(o);
  }
  preference.value = u.learning_preference;
  c.append(
    button("Lưu hồ sơ", async () => {
      await api("/users/me", {
        method: "PATCH",
        body: {
          display_name: name.value,
          language_level: level.value,
          learning_preference: preference.value,
        },
      });
      notice.textContent = "Đã lưu hồ sơ học tập.";
    }),
  );
  root.append(c);
}
document
  .querySelectorAll("[data-view]")
  .forEach(
    (b) =>
      (b.onclick = () =>
        show(b.dataset.view)
          .then(() => window.scrollTo({ top: 0, behavior: "instant" }))
          .catch((e) => (notice.textContent = e.message))),
  );
document.querySelector("#logout").onclick = () => {
  if (!token) return login();
  token = "";
  sessionStorage.removeItem("padayon-token");
  updateIdentity(null);
  login();
};
