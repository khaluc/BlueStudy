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
      speaking: "Speaking",
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

// Compatibility entry for links saved before the learning map redesign.
async function notebookDashboard() {
  return learningMap();
}
function documentQuery(selector) {
  return document.querySelector(selector);
}
async function roadmap() { return learningMap(); }
if (documentQuery("#add-notebook")) documentQuery("#add-notebook").onclick = () => openNotebook();
documentQuery("#profile-shortcut").onclick = () => show("profile").catch(error => notice.textContent = error.message);
documentQuery("#help").onclick = () =>
  documentQuery("#help-dialog").showModal();
documentQuery("#close-help").onclick = () =>
  documentQuery("#help-dialog").close();
