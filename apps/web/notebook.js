"use strict";

// A clearly labelled, local-only example. It never creates documents or scores.
const SAMPLE_SOURCE =
  "In our local community, volunteers help older neighbours. The library lends books for free. A firefighter puts out fires. A gardener plants trees in the public park. People take the bus to reduce traffic. Students clean the park every Sunday.";
const SAMPLE_FACTS = [
  [
    "Tình nguyện viên",
    "Ai giúp đỡ hàng xóm lớn tuổi?",
    "Các tình nguyện viên — volunteers.",
    "volunteers help older neighbours",
  ],
  [
    "Thư viện",
    "Thư viện mang đến điều gì cho cộng đồng?",
    "Thư viện cho mượn sách miễn phí.",
    "The library lends books for free",
  ],
  [
    "Lính cứu hỏa",
    "A firefighter làm công việc gì?",
    "Lính cứu hỏa dập lửa. Cụm động từ: put out fires.",
    "A firefighter puts out fires",
  ],
  [
    "Người làm vườn",
    "Người làm vườn làm gì ở công viên?",
    "Trồng cây trong công viên công cộng.",
    "A gardener plants trees in the public park",
  ],
  [
    "Giao thông xanh",
    "Vì sao mọi người đi xe buýt?",
    "Để giảm lượng xe lưu thông — reduce traffic.",
    "People take the bus to reduce traffic",
  ],
  [
    "Ngày Chủ nhật",
    "Khi nào học sinh dọn dẹp công viên?",
    "Vào mỗi Chủ nhật. Every Sunday diễn tả một hoạt động lặp lại.",
    "Students clean the park every Sunday",
  ],
  [
    "Từ vựng cộng đồng",
    "Local community nghĩa là gì?",
    "Cộng đồng địa phương: những người cùng sinh sống trong một khu vực.",
    "In our local community",
  ],
];
const SAMPLE = {
  id: null,
  content: {
    summary:
      "Một cộng đồng tốt đẹp bắt đầu từ những việc nhỏ. Cùng học cách gọi tên những người giúp ích cho nơi mình sống và kể về công việc của họ bằng tiếng Anh.",
    notes: [
      "Volunteer: tình nguyện viên giúp đỡ hàng xóm.",
      "Library: thư viện cho mượn sách miễn phí.",
      "Firefighter: lính cứu hỏa dập lửa.",
      "Đi xe buýt và dọn công viên là những việc làm cho cộng đồng.",
    ],
    cards: SAMPLE_FACTS.map(([title, front, back, quote]) => ({
      title,
      front,
      back,
      quote,
    })),
    quiz: [
      {
        question: "Ai giúp đỡ những người hàng xóm lớn tuổi?",
        options: [
          "Tình nguyện viên",
          "Khách du lịch",
          "Người bán vé",
          "Phi công",
        ],
        correct: 0,
        explanation: "Volunteers là các tình nguyện viên.",
        quote: SAMPLE_FACTS[0][3],
      },
      {
        question: "Thư viện cho mượn sách như thế nào?",
        options: [
          "Chỉ vào Chủ nhật",
          "Miễn phí",
          "Chỉ cho giáo viên",
          "Với giá rất cao",
        ],
        correct: 1,
        explanation: "For free nghĩa là miễn phí.",
        quote: SAMPLE_FACTS[1][3],
      },
      {
        question: "Put out fires là công việc của ai?",
        options: ["Người làm vườn", "Học sinh", "Lính cứu hỏa", "Tài xế"],
        correct: 2,
        explanation: "A firefighter puts out fires: lính cứu hỏa dập lửa.",
        quote: SAMPLE_FACTS[2][3],
      },
      {
        question: "Tại sao mọi người đi xe buýt?",
        options: [
          "Để thi đấu",
          "Để trồng cây",
          "Để mượn sách",
          "Để giảm lượng xe lưu thông",
        ],
        correct: 3,
        explanation: "To reduce traffic nêu mục đích của việc đi xe buýt.",
        quote: SAMPLE_FACTS[4][3],
      },
      {
        question: "Học sinh dọn công viên vào ngày nào?",
        options: ["Mỗi Chủ nhật", "Mỗi thứ Hai", "Mỗi thứ Sáu", "Mỗi thứ Bảy"],
        correct: 0,
        explanation: "Every Sunday nghĩa là mỗi Chủ nhật.",
        quote: SAMPLE_FACTS[5][3],
      },
    ],
  },
};
let notebookCleanup = () => {};
function disposeNotebook() {
  notebookCleanup();
  notebookCleanup = () => {};
}
function padNumber(value) {
  return String(value).padStart(2, "0");
}
function setNav(view) {
  document
    .querySelectorAll("nav button")
    .forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  document.querySelector("#breadcrumb").textContent =
    {
      map: "Sơ đồ bài học",
      chat: "Chat AI",
      exams: "Đề thi & ôn tập",
      roadmap: "Lộ trình học",
      library: "Tủ tài liệu",
      progress: "Sổ tiến bộ",
      profile: "Hồ sơ học tập",
      history: "Phiên học gần đây",
    }[view] || "Góc học tập";
}
function openNotebook() {
  return token ? show("library") : login();
}
function masthead(title, description) {
  const head = el("div", null, "masthead");
  const heading = el("h1", title);
  heading.append(el("span", "✳", "asterisk"));
  const add = button("Mở cuốn vở mới", openNotebook, "new-notebook");
  add.prepend(el("span", "+"));
  head.append(
    el("span", "SỔ TAY HỌC TẬP / BlueStudy", "eyebrow"),
    heading,
    el("p", description),
    add,
  );
  return head;
}
function stat(symbol, title, value, unit, color) {
  const box = el("div", null, "stat"),
    details = el("div"),
    number = el("div", String(value), "stat-value");
  box.style.setProperty("--accent", color);
  number.append(el("span", unit, "stat-unit"));
  details.append(el("div", title, "stat-caption"), number);
  box.append(el("span", symbol, "stat-symbol"), details);
  return box;
}
function updateIdentity(user) {
  document.querySelector("#username").setAttribute("translate", user ? "no" : "yes");
  document.querySelector("#mode-badge").textContent = token ? "● Góc học tập" : "◦ Vở mẫu";
  document.querySelector("#username").textContent = user
    ? user.display_name
    : "Khám phá một cuốn vở mẫu";
  document.querySelector("#avatar").textContent = user
    ? user.display_name.slice(0, 1).toUpperCase()
    : "P";
  document.querySelector("#logout").textContent = token
    ? "Đăng xuất"
    : "Đăng nhập";
  document.querySelector("#logout").hidden = token === "local";
}
async function study(id) {
  return notebookDashboard(id);
}

async function notebookDashboard(requestedSession = null) {
  reset("", "");
  root.replaceChildren();
  root.className = "notebook-page fade-in";
  setNav("map");
  const ticket = generation;
  root.append(
    masthead(
      "Cuốn vở tri thức của bạn",
      "Ghi lại điều hay. Nối những ý tưởng. Hiểu thêm mỗi ngày.",
    ),
  );
  let sessions = [],
    documents = [],
    progressData = { attempt_count: 0, average_percent: null },
    session = null,
    sourceDocument = null,
    materials = [],
    jobs = [];
  if (token) {
    const data = await Promise.all([
      api("/sessions?limit=100"),
      api("/documents?limit=100"),
      api("/users/me/progress"),
    ]);
    if (ticket !== generation) return;
    [sessions, documents, progressData] = data;
    const sessionId = requestedSession || sessions[0]?.id;
    if (sessionId) {
      session = await api("/sessions/" + sessionId);
      [sourceDocument, materials, jobs] = await Promise.all([
        api("/documents/" + session.document_id),
        api("/sessions/" + sessionId + "/materials"),
        api("/sessions/" + sessionId + "/jobs"),
      ]);
      if (ticket !== generation) return;
    }
  }
  const demo = !session;
  const learningEl = demo ? el : sourceEl;
  const material = demo ? SAMPLE : materials[0] || null;
  const title = demo ? "Local community" : sourceDocument.title;
  const sourceText = demo ? SAMPLE_SOURCE : session.source_text;
  const cards = material?.content.cards || [];
  const titleFor = (index) =>
    index === 0 ? title : cards[index - 1].title || cards[index - 1].front;
  const mode = documentQuery("#mode-badge");
  mode.textContent = demo ? "◦ Vở mẫu · trải nghiệm" : "● Cuốn vở của bạn";
  const stats = el("div", null, "stats");
  stats.append(
    stat(
      "◎",
      "Trang kiến thức",
      cards.length + (material ? 1 : 0),
      "trang trong vở",
      "#98a68b",
    ),
    stat(
      "⌁",
      "Tài liệu nguồn",
      demo ? 1 : documents.length,
      demo ? "nguồn mẫu" : "tài liệu",
      "#9cbbc1",
    ),
    stat(
      "✧",
      "Lượt tự kiểm tra",
      progressData.attempt_count,
      "lượt đã lưu",
      "#c4b27c",
    ),
    stat(
      "↗",
      "Điểm luyện tập",
      progressData.average_percent ?? "—",
      progressData.average_percent == null ? "chưa có điểm" : "% trung bình",
      "#baa3aa",
    ),
  );
  root.append(stats);
  const bookList = documentQuery("#notebook-list");
  bookList.replaceChildren();
  if (sessions.length) {
    for (const s of sessions.slice(0, 5)) {
      const book = button(
        documents.find((d) => d.id === s.document_id)?.title ||
          "Phiên học đã lưu",
        () => study(s.id),
      );
      book.prepend(el("span", null, "book-icon"));
      book.setAttribute("translate", "no");
      bookList.append(book);
    }
  } else {
    const book = button("Local community", () => notebookDashboard());
    book.prepend(el("span", null, "book-icon"));
    bookList.append(book);
  }
  const layout = el("div", null, "notebook-layout"),
    left = el("div", null, "map-column"),
    reader = el("section", null, "reader paper-panel");
  reader.setAttribute("aria-label", "Nội dung trang học");
  const panel = el("section", null, "paper-panel"),
    mapHead = el("div", null, "map-heading"),
    mapInfo = el("div");
  const mapTitle = learningEl("h2", title);
  if (demo) mapTitle.append(el("span", "VỞ MẪU", "tiny-badge"));
  mapInfo.append(
    el("div", "01 / KẾT NỐI Ý TƯỞNG", "eyebrow"),
    mapTitle,
    el(
      "small",
      `1 đoạn nguồn · ${cards.length + 1} trang học · Cứ tò mò, cứ khám phá.`,
    ),
  );
  const mapActions = el("div", null, "map-heading-actions");
  let listMode = false,
    zoom = 1,
    selected = 0,
    tab = "lesson",
    quizIndex = 0,
    result = null,
    timer = null;
  const answers = new Array(material?.content.quiz.length || 0).fill(null);
  const chatEntries = jobs
    .filter((j) => j.kind === "teach" && j.status === "succeeded")
    .reverse()
    .map((j) => j.result.content.answer);
  let chatDraft = "";
  const canvas = el("div", null, "map-canvas"),
    world = el("div", null, "map-world"),
    mapList = el("div", null, "map-list");
  mapList.hidden = true;
  const toolbar = el("div", null, "map-toolbar"),
    search = el("input", null, "map-search");
  search.placeholder = "⌕  Tìm trong bài học…";
  search.setAttribute("aria-label", "Tìm trong sơ đồ");
  const zoomControls = el("div", null, "zoom-controls"),
    zoomValue = el("output", "100%");
  zoomValue.setAttribute("aria-label", "Mức thu phóng");
  function setZoom(value) {
    zoom = Math.min(1.4, Math.max(0.75, value));
    world.style.transform = `scale(${zoom})`;
    zoomValue.value = Math.round(zoom * 100) + "%";
  }
  const smaller = button("−", () => setZoom(zoom - 0.1));
  smaller.setAttribute("aria-label", "Thu nhỏ sơ đồ");
  const bigger = button("+", () => setZoom(zoom + 0.1));
  bigger.setAttribute("aria-label", "Phóng to sơ đồ");
  const fit = button("↺", () => {
    setZoom(1);
    canvas.scrollLeft = 0;
  });
  fit.setAttribute("aria-label", "Đặt lại sơ đồ");
  zoomControls.append(smaller, zoomValue, bigger, fit);
  toolbar.append(search, zoomControls);
  canvas.append(
    toolbar,
    world,
    mapList,
    el("span", "Mỗi ý tưởng đều có một sợi dây kết nối…", "canvas-caption"),
  );
  const positions = [
    [50, 48],
    [19, 24],
    [49, 13],
    [81, 25],
    [19, 68],
    [81, 66],
    [49, 84],
    [81, 91],
  ];
  const colors = [
    "#f8edb9",
    "#e7eedb",
    "#e3edf3",
    "#f6e8ce",
    "#f2dfe0",
    "#e9e2f1",
    "#dfedeb",
    "#eeecd7",
  ];
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 100 100");
  svg.setAttribute("preserveAspectRatio", "none");
  svg.classList.add("map-lines");
  svg.setAttribute("aria-hidden", "true");
  world.append(svg);
  const nodes = [],
    listButtons = [],
    paths = [];
  function selectNode(index, scroll = false) {
    selected = index;
    tab = "lesson";
    nodes.forEach((n, i) => {
      n.classList.toggle("active", i === index);
      n.setAttribute("aria-pressed", String(i === index));
    });
    listButtons.forEach((n, i) => n.classList.toggle("active", i === index));
    paths.forEach((p, i) => p.classList.toggle("selected", i + 1 === index));
    renderReader();
    if (scroll && window.innerWidth < 1001)
      reader.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  for (let i = 0; i <= cards.length; i++) {
    const [x, y] = positions[i] || [50, 85];
    if (i) {
      const path = document.createElementNS(svg.namespaceURI, "path");
      path.setAttribute(
        "d",
        `M 50 48 Q ${(50 + x) / 2 + 4} ${(48 + y) / 2} ${x} ${y}`,
      );
      svg.append(path);
      paths.push(path);
    }
    const node = button(
      "",
      () => selectNode(i, true),
      "map-node" + (i === 0 ? " root-node active" : ""),
    );
    node.style.setProperty("--x", x);
    node.style.setProperty("--y", y);
    node.style.setProperty("--node-color", colors[i % colors.length]);
    node.style.setProperty("--tilt", (i % 2 ? 1 : -1) + "deg");
    node.title = titleFor(i);
    node.setAttribute("aria-pressed", String(i === 0));
    node.setAttribute(
      "aria-label",
      "Mở trang " + padNumber(i + 1) + ": " + titleFor(i),
    );
    node.append(
      el("span", padNumber(i + 1), "node-number"),
      learningEl("span", titleFor(i), "node-title"),
      el(
        "span",
        i ? "• chạm để khám phá" : "• bắt đầu từ đây",
        "node-subtitle",
      ),
    );
    world.append(node);
    nodes.push(node);
    const listButton = button("", () => selectNode(i, true));
    listButton.append(
      el("span", padNumber(i + 1), "eyebrow"),
      learningEl("span", titleFor(i)),
    );
    mapList.append(listButton);
    listButtons.push(listButton);
  }
  search.oninput = () => {
    const query = search.value.toLocaleLowerCase("vi").trim();
    nodes.forEach((n, i) =>
      n.classList.toggle(
        "dimmed",
        !titleFor(i).toLocaleLowerCase("vi").includes(query),
      ),
    );
    listButtons.forEach(
      (n, i) =>
        (n.hidden = !titleFor(i).toLocaleLowerCase("vi").includes(query)),
    );
  };
  const toggleList = button(
    "☷ Danh sách",
    () => {
      listMode = !listMode;
      world.hidden = listMode;
      mapList.hidden = !listMode;
      zoomControls.hidden = listMode;
      toggleList.textContent = listMode ? "⌘ Sơ đồ" : "☷ Danh sách";
      canvas.querySelector(".canvas-caption").hidden = listMode;
    },
    "small-button",
  );
  toggleList.setAttribute("aria-label", "Đổi cách xem sơ đồ");
  mapActions.append(toggleList);
  mapHead.append(mapInfo, mapActions);
  const legend = el("div", null, "map-legend"),
    firstLegend = el("span", "Trang kiến thức");
  firstLegend.prepend(el("i", null, "legend-square"));
  legend.append(
    firstLegend,
    el("span", "┄┄ Cùng một đoạn nguồn"),
    el("span", "── Trang đang đọc"),
  );
  const controls = el("div", null, "map-controls");
  const play = button("▷ Khám phá từng bước", () => {
    if (timer) stopPlay();
    else {
      play.textContent = "Ⅱ Tạm dừng";
      play.classList.add("playing");
      selectNode((selected + 1) % nodes.length);
      timer = setInterval(
        () => selectNode((selected + 1) % nodes.length),
        3000,
      );
    }
  });
  function stopPlay() {
    clearInterval(timer);
    timer = null;
    play.textContent = "▷ Khám phá từng bước";
    play.classList.remove("playing");
  }
  notebookCleanup = stopPlay;
  controls.append(
    play,
    button("↪ Trang tiếp", () => {
      stopPlay();
      selectNode((selected + 1) % nodes.length, true);
    }),
    el("span", "⌕ Chọn một ghi chú"),
  );
  panel.append(mapHead, canvas, legend, controls);
  left.append(panel);
  const next = el("div", null, "next-step"),
    nextText = el("div");
  nextText.append(
    el("div", "MỘT VIỆC NHỎ HÔM NAY", "eyebrow"),
    el(
      "h3",
      material
        ? `Tìm hiểu “${title.length > 45 ? title.slice(0, 45) + "…" : title}”`
        : "Biến ghi chú thành những trang học",
    ),
    el(
      "p",
      material
        ? "Đọc một trang, thử 5 câu hỏi, rồi tiến thêm một chút."
        : "Tạo tóm tắt, flashcard và quiz từ đoạn nguồn đã xác nhận.",
    ),
  );
  next.append(
    el("span", "☑", "next-step-symbol"),
    nextText,
    button(material ? "Học tiếp →" : "Tạo bộ ôn tập", async () => {
      if (material) {
        tab = "quiz";
        renderReader();
        reader.scrollIntoView({ behavior: "smooth", block: "start" });
      } else await generateBundle();
    }),
  );
  left.append(next);
  if (session) {
    const tools = el("details", null, "topic-details");
    tools.append(el("summary", "Chủ đề, nguồn & bộ học đã lưu"));
    const toolsBody = el("div", null, "card");
    const curriculum = await api("/curriculum");
    if (ticket !== generation) return;
    const topic = field(toolsBody, "Chủ đề học (bạn tự xác nhận)", "select");
    const empty = el("option", "Chưa xác định");
    empty.value = "";
    topic.append(empty);
    curriculum.forEach((t) => {
      const option = el("option", `Unit ${t.unit} · ${t.title}`);
      option.value = t.id;
      topic.append(option);
    });
    topic.value = session.topic_id || "";
    toolsBody.append(
      button(
        "Lưu chủ đề",
        async () => {
          await api("/sessions/" + session.id + "/curriculum", {
            method: "PATCH",
            body: { topic_id: topic.value || null },
          });
          notice.textContent = "Đã lưu lựa chọn chủ đề của bạn.";
        },
        "secondary",
      ),
    );
    toolsBody.append(
      button(
        "Mở tài liệu gốc",
        () => documentView(sourceDocument.id),
        "secondary",
      ),
    );
    if (material)
      toolsBody.append(
        button("Tạo bộ ôn tập mới", generateBundle, "secondary"),
      );
    tools.append(toolsBody);
    left.append(tools);
  }
  const relatedTitle = el("div", null, "related-title");
  relatedTitle.append(
    el("h2", "Lật thêm vài trang"),
    el("small", "Có thể bạn cũng muốn biết"),
  );
  left.append(relatedTitle);
  const related = el("div", null, "related-grid");
  cards.slice(0, 3).forEach((card, i) => {
    const b = button("", () => selectNode(i + 1, true), "related-card"),
      copy = el("div"),
      icon = el("span", null, "book-icon");
    icon.style.background = colors[i + 1];
    copy.append(
      learningEl("strong", card.title || card.front),
      el("small", "Mở trang · " + padNumber(i + 2)),
    );
    b.append(icon, copy, el("span", "↗"));
    related.append(b);
  });
  if (!cards.length)
    related.append(
      el(
        "p",
        "Các trang kiến thức sẽ xuất hiện sau khi tạo bộ ôn tập.",
        "muted",
      ),
    );
  left.append(related);
  layout.append(left, reader);
  root.append(layout);
  renderReader();
  requestAnimationFrame(() => {
    if (ticket === generation)
      canvas.scrollLeft = Math.max(
        0,
        (world.scrollWidth - canvas.clientWidth) / 2,
      );
  });
  async function generateBundle() {
    if (!session) return openNotebook();
    const job = await api("/sessions/" + session.id + "/jobs", {
      method: "POST",
      body: { kind: "generate_bundle" },
    });
    if (await waitJob(job.id)) await study(session.id);
  }
  function renderReader() {
    reader.replaceChildren();
    const heading = el("div", null, "reader-heading"),
      meta = el("div", null, "reader-meta"),
      tags = el("div", null, "tags");
    meta.append(
      el("span", "GHI CHÉP BÀI HỌC"),
      el("span", "TRANG " + padNumber(selected + 1)),
    );
    tags.append(
      el("span", "Tiếng Anh 9"),
      el("span", demo ? "◦ Vở mẫu" : "◦ Từ tài liệu của bạn"),
    );
    heading.append(
      meta,
      el("div", padNumber(selected + 1), "page-circle"),
      learningEl("h2", titleFor(selected)),
      tags,
    );
    const tabs = el("div", null, "reader-tabs");
    tabs.setAttribute("role", "tablist");
    tabs.setAttribute("aria-label", "Hoạt động học");
    const body = el("div", null, "reader-body");
    body.id = "reader-content";
    body.setAttribute("role", "tabpanel");
    for (const [key, label] of [
      ["lesson", "Bài học"],
      ["chat", "Hỏi BlueStudy"],
      ["quiz", "Luyện tập"],
    ]) {
      const b = button(label, () => {
        stopPlay();
        tab = key;
        renderReader();
        documentQuery("#reader-tab-" + key)?.focus({ preventScroll: true });
      });
      b.id = "reader-tab-" + key;
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", String(tab === key));
      b.setAttribute("aria-controls", body.id);
      b.tabIndex = tab === key ? 0 : -1;
      b.onkeydown = (e) => {
        if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(e.key)) return;
        e.preventDefault();
        const keys = ["lesson", "chat", "quiz"];
        tab =
          e.key === "Home"
            ? keys[0]
            : e.key === "End"
              ? keys[2]
              : keys[
                  (keys.indexOf(key) + (e.key === "ArrowRight" ? 1 : 2)) % 3
                ];
        stopPlay();
        renderReader();
        documentQuery("#reader-tab-" + tab).focus({ preventScroll: true });
      };
      tabs.append(b);
    }
    body.setAttribute("aria-labelledby", "reader-tab-" + tab);
    if (tab === "lesson") renderLesson(body);
    else if (tab === "chat") renderChat(body);
    else renderQuiz(body);
    const footer = el("div", null, "reader-footer"),
      prev = button("← Bài trước", () => {
        stopPlay();
        selectNode(Math.max(0, selected - 1));
      }),
      next = button("Bài tiếp →", () => {
        stopPlay();
        selectNode(Math.min(cards.length, selected + 1));
      });
    prev.disabled = selected === 0;
    next.disabled = selected === cards.length;
    footer.append(
      prev,
      el("span", `${selected + 1} / ${cards.length + 1}`),
      next,
    );
    reader.append(heading, tabs, body, footer);
  }
  function renderLesson(body) {
    if (selected > 0) {
      const card = cards[selected - 1];
      body.append(
        el("span", "MỘT CÂU HỎI NHỎ", "eyebrow"),
        learningEl("h3", card.front),
      );
      const answer = el("div", null, "card-answer");
      answer.hidden = true;
      answer.append(learningEl("p", card.back), sourceEl("blockquote", card.quote));
      const flip = button(
        "Lật thẻ · xem lời giải",
        () => {
          answer.hidden = !answer.hidden;
          flip.textContent = answer.hidden
            ? "Lật thẻ · xem lời giải"
            : "Gấp lại · tự nhớ thử";
        },
        "secondary",
      );
      body.append(flip, answer);
    } else if (material) {
      body.append(
        el("span", "Ý CHÍNH CẦN NHỚ", "eyebrow"),
        learningEl("p", material.content.summary),
      );
      const notes = el("ul");
      material.content.notes.forEach((n) => notes.append(learningEl("li", n)));
      body.append(notes);
    } else {
      body.append(
        el("span", "TRANG GIẤY ĐANG CHỜ BẠN", "eyebrow"),
        el(
          "p",
          "Đoạn nguồn đã sẵn sàng. Tạo bộ ôn tập để có ghi chú rõ ràng, thẻ ghi nhớ và 5 câu tự kiểm tra.",
        ),
        button("Tạo bộ ôn tập", generateBundle, "primary"),
      );
    }
    const source = el("details", null, "source-details");
    source.append(
      el("summary", "Đọc đoạn nguồn tiếng Anh"),
      sourceEl("blockquote", sourceText),
    );
    body.append(source);
    body.append(
      el(
        "p",
        demo
          ? "Vở mẫu biên soạn sẵn · điểm luyện tập không được lưu."
          : "Nội dung AI chưa được giáo viên kiểm duyệt. Hãy đối chiếu với tài liệu gốc.",
        "sample-note",
      ),
    );
    if (material?.provenance?.fallback_reason)
      body.append(
        el("small", "Bộ học này được tạo bằng mô hình local dự phòng."),
      );
    if (jobs.some((j) => j.status === "queued"))
      body.append(
        button(
          "Cập nhật tác vụ đang chạy",
          () => study(session.id),
          "secondary",
        ),
      );
  }
  function renderChat(body) {
    body.append(
      el("span", "CÙNG GỠ RỐI MỘT CHÚT", "eyebrow"),
      el("p", "Chỗ nào khiến bạn băn khoăn? Mình sẽ cùng nhìn lại đoạn nguồn."),
    );
    if (demo) {
      body.append(
        el("p", "Đăng nhập và mở tài liệu của bạn để trò chuyện với BlueStudy."),
        button("Mở góc học tập", openNotebook, "primary"),
      );
      return;
    }
    const question = field(
      body,
      "Bạn muốn hiểu thêm điều gì?",
      "textarea",
      chatDraft,
    );
    question.maxLength = 500;
    question.oninput = () => (chatDraft = question.value);
    body.append(
      button(
        "Hỏi BlueStudy",
        async () => {
          const text = question.value.trim();
          if (!text) throw Error("Hãy viết câu hỏi của bạn.");
          const job = await api("/sessions/" + session.id + "/jobs", {
            method: "POST",
            body: { kind: "teach", question: text },
          });
          const answer = await waitJob(job.id);
          if (answer && ticket === generation) {
            notice.textContent = "";
            chatEntries.push(answer.content.answer);
            chatDraft = "";
            if (tab === "chat") renderReader();
          }
        },
        "primary",
      ),
    );
    for (const entry of chatEntries) body.append(sourceEl("blockquote", entry));
  }
  function renderQuiz(body) {
    if (!material) {
      body.append(
        el("p", "Tạo bộ ôn tập để bắt đầu tự kiểm tra."),
        button("Tạo bộ ôn tập", generateBundle, "primary"),
      );
      return;
    }
    const questions = material.content.quiz;
    if (result) {
      body.append(
        el(
          "span",
          demo ? "KẾT QUẢ THỬ · KHÔNG LƯU ĐIỂM" : "ĐÃ LƯU VÀO SỔ TIẾN BỘ",
          "eyebrow",
        ),
        el("p", result.score + " / " + questions.length, "score"),
      );
      const feedback = el("div", null, "quiz-feedback");
      result.feedback.forEach((q, i) => {
        const d = el("details");
        d.append(
          el(
            "summary",
            `${answers[i] === q.correct ? "✓" : "○"} Câu ${i + 1} · ${answers[i] === q.correct ? "Chính xác" : "Cùng ôn lại"}`,
          ),
          learningEl("p", q.options[q.correct] + " — " + q.explanation),
          sourceEl("blockquote", q.quote),
        );
        feedback.append(d);
      });
      body.append(
        feedback,
        button(
          "Luyện lại một lượt",
          () => {
            result = null;
            answers.fill(null);
            quizIndex = 0;
            renderReader();
          },
          "secondary",
        ),
      );
      return;
    }
    body.append(
      el(
        "span",
        demo ? "QUIZ MẪU · 5 CÂU NHỎ" : "TỰ KIỂM TRA · 5 CÂU NHỎ",
        "eyebrow",
      ),
    );
    const bar = el("div", null, "quiz-progress"),
      fill = el("span");
    fill.style.width =
      (answers.filter((a) => a !== null).length / questions.length) * 100 + "%";
    bar.append(fill);
    body.append(
      bar,
      el(
        "span",
        `CÂU ${quizIndex + 1} / ${questions.length} · ${answers.filter((a) => a !== null).length} CÂU ĐÃ CHỌN`,
        "eyebrow",
      ),
      learningEl("p", questions[quizIndex].question),
    );
    const options = el("div", null, "quiz-options");
    questions[quizIndex].options.forEach((text, i) => {
      const option = button(
        "",
        () => {
          answers[quizIndex] = i;
          renderReader();
          reader.querySelectorAll(".quiz-option")[i]?.focus({ preventScroll: true });
        },
        "quiz-option" + (answers[quizIndex] === i ? " selected" : ""),
      );
      option.setAttribute("aria-pressed", String(answers[quizIndex] === i));
      option.append(el("span", "ABCD"[i], "choice-letter"), learningEl("span", text));
      options.append(option);
    });
    body.append(options);
    const numbers = el("div", null, "quiz-numbers");
    questions.forEach((_, i) => {
      const b = button(
        String(i + 1),
        () => {
          quizIndex = i;
          renderReader();
        },
        (answers[i] !== null ? "answered " : "") +
          (i === quizIndex ? "current" : ""),
      );
      b.setAttribute("aria-label", "Đến câu " + (i + 1));
      numbers.append(b);
    });
    body.append(numbers);
    if (quizIndex < questions.length - 1)
      body.append(
        button(
          "Câu tiếp →",
          () => {
            quizIndex++;
            renderReader();
          },
          "primary",
        ),
      );
    if (quizIndex === questions.length - 1 || answers.every((a) => a !== null))
      body.append(
        button(
          "Nộp bài và xem giải thích",
          async () => {
            if (answers.some((a) => a === null))
              throw Error("Bạn cần trả lời đủ 5 câu.");
            if (demo) {
              result = {
                score: questions.reduce(
                  (n, q, i) => n + Number(answers[i] === q.correct),
                  0,
                ),
                feedback: questions,
              };
            } else {
              const submitted = await api(
                "/materials/" + material.id + "/attempts",
                { method: "POST", body: { answers: [...answers] } },
              );
              if (ticket !== generation) return;
              result = submitted;
            }
            renderReader();
          },
          "primary",
        ),
      );
    if (demo)
      body.append(
        el("p", "Vở mẫu · thử thoải mái, không lưu vào hồ sơ.", "sample-note"),
      );
  }
}
function documentQuery(selector) {
  return document.querySelector(selector);
}
async function roadmap() {
  reset(
    "Lộ trình cho những bước nhỏ",
    "Mỗi trang học là một bước. Không cần vội, chỉ cần bắt đầu.",
  );
  setNav("roadmap");
  const list = el("div", null, "roadmap-list"),
    steps = [
      [
        "Gom những điều muốn học",
        "Tải ảnh, PDF hoặc dán ghi chú vào cuốn vở của bạn.",
        "Mở tủ tài liệu",
        openNotebook,
      ],
      [
        "Đọc và nối các ý tưởng",
        "Chọn một trang trên sơ đồ. Đọc nguồn và thử tự trả lời trước khi lật thẻ.",
        "Mở sơ đồ",
        () => show("map"),
      ],
      [
        "Một lượt tự kiểm tra",
        "Làm 5 câu hỏi. Sai ở đâu, mình cùng quay lại trang đó.",
        "Tiếp tục học",
        () => show("map"),
      ],
      [
        "Nhìn lại hành trình",
        "Xem điểm đã lưu và những câu cần ôn lại.",
        "Xem sổ tiến bộ",
        () => show("progress"),
      ],
    ];
  steps.forEach(([title, text, label, action], i) => {
    const row = el("div", null, "roadmap-step"),
      copy = el("div");
    copy.append(el("h3", title), el("p", text));
    row.append(
      el("div", padNumber(i + 1), "page-circle"),
      copy,
      button(label + " →", action, "secondary"),
    );
    list.append(row);
  });
  root.append(list);
  if (token) {
    root.append(el("h2", "Những trang đang đọc dở"));
    const sessions = await api("/sessions");
    for (const s of sessions.slice(0, 6)) {
      const c = el("div", null, "card");
      c.append(
        el("p", s.source_text.slice(0, 140) + "…"),
        button("Tiếp tục phiên học", () => study(s.id), "secondary"),
      );
      root.append(c);
    }
    if (!sessions.length)
      root.append(
        el("p", "Cuốn vở đầu tiên đang chờ bạn ở Tủ tài liệu.", "muted"),
      );
  }
}
documentQuery("#add-notebook").onclick = () => openNotebook();
documentQuery("#profile-shortcut").onclick = () => show("profile").catch(error => notice.textContent = error.message);
documentQuery("#help").onclick = () =>
  documentQuery("#help-dialog").showModal();
documentQuery("#close-help").onclick = () =>
  documentQuery("#help-dialog").close();
