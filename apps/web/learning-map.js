"use strict";
let learningMapCleanup = () => {};
function disposeLearningMap() { learningMapCleanup(); learningMapCleanup = () => {}; }
async function learningMap() {
  reset('', ''); setNav('map');
  const gen = generation;
  const data = await api('/learning-map');
  if (generation !== gen) return;
  const copy = (en, vi) => uiLanguage === 'en' ? en : vi;
  const local = value => typeof value === 'object' && value ? value[uiLanguage] || '' : '';
  const skillName = skill => uiLanguage === 'vi' ? skill.label : ({
    word_form:'Word forms', word_order:'Word order', verb_form:'Verb forms',
    preposition:'Prepositions', collocation:'Collocations', connector:'Connectors',
    determiner:'Determiners', vocabulary_context:'Vocabulary in context',
    sentence_structure:'Sentence structure', sentence_order:'Sentence ordering',
    detail:'Reading for detail', main_idea:'Main idea', inference:'Inference',
    reference:'Reference words', paraphrase:'Paraphrasing', sentence_insertion:'Sentence insertion',
    other:'Needs classification'
  }[skill.skill] || skill.skill.replaceAll('_',' '));
  const dimensions = {
    fluency: ['Fluency', 'Độ trôi chảy'], grammar: ['Grammar', 'Ngữ pháp'],
    vocabulary: ['Vocabulary', 'Từ vựng'], coherence: ['Coherence', 'Mạch lạc'],
    relevance: ['Question relevance', 'Đúng trọng tâm']
  };
  function goSpeaking(row) {
    if (row) sessionStorage.setItem('bluestudy-speaking', row.session_id);
    return show('speaking');
  }
  function bar(parent, label, value, maximum, detail) {
    const row = sourceEl('div', null, 'learning-bar');
    row.append(sourceEl('strong', label), sourceEl('span', detail));
    const track = el('div', null, 'learning-track');
    const fill = el('div'); fill.style.width = Math.max(0, Math.min(100, value / maximum * 100)) + '%';
    track.append(fill); row.append(track); parent.append(row);
  }
  function render() {
    if (generation !== gen) return;
    root.replaceChildren();
    document.querySelector('#mode-badge').textContent = copy('Learning map', 'Lộ trình học tập');
    document.querySelector('#breadcrumb').textContent = copy('Learning map', 'Lộ trình học tập');
    root.append(sourceEl('p', copy('YOUR NEXT STEP', 'BƯỚC HỌC TIẾP THEO'), 'eyebrow'),
      sourceEl('h1', copy('Your learning map', 'Lộ trình học của bạn')),
      sourceEl('p', copy('Turn Speaking practice and exam results into a focused study plan.',
        'Biến kết quả Speaking và bài thi thành kế hoạch ôn tập có trọng tâm.'), 'muted'));
    const actions = el('div', null, 'learning-actions');
    actions.append(button(copy('Practice Speaking', 'Luyện Speaking'), () => goSpeaking(), 'primary'),
      button(copy('Exam revision', 'Làm bài & ôn tập'), () => show('exams'), 'secondary'),
      button(copy('Refresh results', 'Cập nhật kết quả'), () => learningMap(), 'secondary'));
    root.append(actions);
    const independent = data.speaking.filter(a => a.mode === 'independent' && a.status === 'ready' && a.coaching);
    const guided = data.speaking.filter(a => a.mode === 'model');
    const latestSpeaking = independent[0];
    const latestExam = data.exams[0];
    const stats = el('div', null, 'learning-stats');
    for (const [value, label] of [
      [independent.length, copy('Assessed independent responses', 'Bài tự nói đã đánh giá')],
      [guided.length, copy('Guided speaking attempts', 'Lượt nói theo mẫu')],
      [data.exams.length, copy('Exam submissions', 'Lượt nộp bài thi')]
    ]) {
      const card = el('div', null, 'card'); card.append(sourceEl('h2', String(value)), sourceEl('p', label)); stats.append(card);
    }
    root.append(stats);
    const grid = el('div', null, 'learning-columns');
    const speaking = el('section', null, 'card');
    speaking.append(sourceEl('h2', copy('Speaking · skill profile', 'Speaking · Hồ sơ kỹ năng')));
    if (latestSpeaking) {
      speaking.append(sourceEl('p', copy('Latest independent response', 'Bài tự nói mới nhất') + ' · ' + new Date(latestSpeaking.date).toLocaleDateString(uiLanguage)));
      for (const [key, names] of Object.entries(dimensions)) {
        const score = latestSpeaking.coaching[key]?.score;
        bar(speaking, copy(...names), score ?? 0, 5, score == null ? copy('Insufficient evidence', 'Chưa đủ dữ liệu') : score + ' / 5');
      }
    } else speaking.append(sourceEl('p', copy('Complete an independent response to build your skill profile. Guided practice is tracked separately.',
      'Hoàn thành một bài tự nói để có hồ sơ kỹ năng. Bài nói theo mẫu được theo dõi riêng.')));
    speaking.append(sourceEl('small', copy('Practice feedback, not an official exam score. Pronunciation requires audio assessment.',
      'Điểm luyện tập, không phải điểm thi chính thức. Phát âm cần đánh giá âm thanh.')));
    const exam = el('section', null, 'card');
    exam.append(sourceEl('h2', copy('Exam · revision priorities', 'Bài thi · Kỹ năng cần ôn')));
    if (latestExam) {
      exam.append(sourceEl('p', copy('Answered', 'Đã trả lời') + ': ' + latestExam.metrics.answered + ' / ' + latestExam.total));
      const skills = [...latestExam.metrics.skills].filter(s => s.answered_graded).sort((a,b) => b.wrong_questions.length-a.wrong_questions.length);
      for (const skill of skills) bar(exam, skillName(skill), skill.correct, skill.answered_graded,
        skill.correct + ' / ' + skill.answered_graded + ' · ' + copy('correct / answered & graded', 'đúng / đã trả lời và chấm'));
      if (!skills.length) exam.append(sourceEl('p', copy('No answered, gradable questions yet.', 'Chưa có câu đã trả lời đủ điều kiện chấm.')));
      exam.append(sourceEl('small', copy('Provisional AI answer key. Blank and ungraded questions are not counted as skill errors.',
        'Đáp án AI tạm thời. Câu bỏ trống và chưa chấm không tính là lỗi kỹ năng.')));
    } else exam.append(sourceEl('p', copy('Submit an exam to discover which skills need revision.', 'Nộp một bài thi để xác định kỹ năng cần ôn.')));
    grid.append(speaking, exam); root.append(grid);
    const plan = el('section', null, 'card learning-plan');
    plan.append(sourceEl('h2', copy('What should I study next?', 'Tiếp theo nên học gì?')),
      sourceEl('p', copy('AI feedback from saved attempts, with practice suggestions based on your results.',
        'Phản hồi AI từ bài đã lưu, kèm gợi ý luyện tập dựa trên kết quả.')));
    let stepNumber = 0;
    function step(title, description, action, label) {
      const item = el('article', null, 'learning-step');
      item.append(sourceEl('span', String(++stepNumber).padStart(2, '0'), 'eyebrow'),
        sourceEl('h3', title), sourceEl('p', description), button(label, action, 'secondary'));
      plan.append(item);
    }
    if (latestSpeaking) {
      const weak = Object.keys(dimensions).filter(k => latestSpeaking.coaching[k]?.score != null)
        .sort((a,b) => latestSpeaking.coaching[a].score-latestSpeaking.coaching[b].score)[0];
      const advice = (latestSpeaking.coaching.next_steps || []).map(local).filter(Boolean).join(' ');
      step(copy('Speaking: ', 'Speaking: ') + (weak ? copy(...dimensions[weak]) : copy('Build a longer response', 'Phát triển câu trả lời')),
        advice || copy('Review your last response, prepare a short outline, then answer again independently.',
          'Xem lại bài nói, chuẩn bị dàn ý ngắn rồi tự trả lời lại.'),
        () => goSpeaking(latestSpeaking), copy('Practise this response', 'Luyện lại bài này'));
    } else step(copy('Start with Speaking', 'Bắt đầu với Speaking'),
      copy('Choose a Part 1 question. Listen to a model, then record your own answer to establish a starting point.',
        'Chọn một câu Part 1. Nghe mẫu rồi tự ghi âm câu trả lời để xác định điểm bắt đầu.'),
      () => goSpeaking(), copy('Open Speaking', 'Mở Speaking'));
    if (latestExam) {
      const coaching = latestExam.translations?.[uiLanguage] || latestExam.coaching;
      const validCoach = coaching?.response_language === uiLanguage ? coaching : null;
      const wrong = latestExam.metrics.skills.filter(s => s.wrong_questions.length);
      for (const skill of wrong.slice(0, 3)) {
        const aiStep = validCoach?.roadmap?.find(s => s.skill === skill.skill);
        step(skillName(skill),
          aiStep ? [aiStep.goal, ...(aiStep.activities || []), aiStep.success_criteria].filter(Boolean).join(' ') :
            copy('Review incorrect questions ', 'Ôn các câu làm sai ') + skill.wrong_questions.join(', ') +
            copy('. Read the explanations, note the rule, then retry before moving on.', '. Đọc giải thích, ghi lại quy tắc rồi làm lại trước khi học tiếp.'),
          () => examView(latestExam.exam_id), copy('Review exam', 'Xem lại bài thi'));
      }
      if (latestExam.metrics.unanswered) step(copy('Complete the remaining questions', 'Hoàn thành các câu còn lại'),
        latestExam.metrics.unanswered + copy(' unanswered questions. Complete them to give the coach more evidence.',
          ' câu chưa trả lời. Hoàn thành để AI có thêm dữ liệu đánh giá.'),
        () => examView(latestExam.exam_id), copy('Continue revision', 'Tiếp tục ôn tập'));
      if (!wrong.length && !latestExam.metrics.unanswered) step(copy('Consolidate and retest', 'Củng cố và kiểm tra lại'),
        copy('Review any ungraded answers and explanations, then try another exam.', 'Kiểm tra câu chưa chấm và giải thích, sau đó thử một đề khác.'),
        () => show('exams'), copy('Open exams', 'Mở đề thi'));
    } else step(copy('Establish your exam baseline', 'Xác định trình độ qua bài thi'),
      copy('Complete an exam. Your answered mistakes will guide the next revision steps.',
        'Hoàn thành một bài thi. Các câu đã trả lời sai sẽ giúp xác định nội dung ôn tiếp.'),
      () => show('exams'), copy('Open exams', 'Mở đề thi'));
    root.append(plan);
    const history = el('section', null, 'card');
    history.append(sourceEl('h2', copy('Practice over time', 'Kết quả qua các lần luyện tập')),
      sourceEl('p', copy('Latest 8 submissions per activity. Tasks may differ; these are practice results, not a measure of ability growth.',
        '8 lượt gần nhất mỗi hoạt động. Đề có thể khác nhau; đây là kết quả luyện tập, không phải mức tăng năng lực.')));
    for (const [title, rows, maximum] of [
      ['Speaking / 5', independent.filter(a => a.coaching.overall != null).slice(0,8).reverse().map(a => [a.date,a.coaching.overall]),5],
      [copy('Exam accuracy on answered questions / 100', 'Độ chính xác câu đã trả lời / 100'),
        data.exams.slice(0,8).reverse().map(a => {
          const n=a.metrics.skills.reduce((v,s)=>v+s.answered_graded,0), correct=a.metrics.skills.reduce((v,s)=>v+s.correct,0);
          return [a.date,n ? Math.round(correct/n*100):null];
        }).filter(a=>a[1]!=null),100]
    ]) {
      history.append(sourceEl('h3', title));
      if (!rows.length) history.append(sourceEl('p', copy('No scored attempts yet.', 'Chưa có lượt được chấm điểm.')));
      rows.forEach(([date,value],i)=>bar(history, (i+1)+'. '+new Date(date).toLocaleDateString(uiLanguage),value,maximum,value+' / '+maximum));
    }
    root.append(history, sourceEl('small', copy('Based on up to 50 recent attempts per activity. Refresh after AI analysis finishes.',
      'Dựa trên tối đa 50 lượt gần nhất mỗi hoạt động. Cập nhật sau khi AI phân tích xong.')));
  }
  render();
  window.addEventListener('ui-language-change', render);
  learningMapCleanup = () => window.removeEventListener('ui-language-change', render);
}
