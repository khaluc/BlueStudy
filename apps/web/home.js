"use strict";
let homeCleanup=()=>{};
function disposeHome(){homeCleanup();homeCleanup=()=>{};}
function homePage(){
  reset('','');setNav('home');
  const copy=(en,vi)=>uiLanguage==='en'?en:vi;
  function render(){
    root.className='home-page';
    root.replaceChildren();
    document.querySelector('#breadcrumb').textContent=copy('Home','Trang chủ');
    document.querySelector('#mode-badge').textContent='BlueStudy';
    const hero=el('section',null,'home-hero');
    hero.append(sourceEl('p',copy('YOUR SPACE TO LEARN & SPEAK','KHÔNG GIAN HỌC TẬP & LUYỆN NÓI'),'eyebrow'));
    const title=sourceEl('h1',copy('Find your words.','Tìm lời để nói.'));
    title.append(el('br'),sourceEl('em',copy('Build your confidence.','Thêm tự tin mỗi ngày.')));
    hero.append(title,sourceEl('p',copy('Practise academic English, make sense of your mistakes, and discover what to learn next. One small step at a time.',
      'Luyện tiếng Anh học thuật, hiểu những lỗi cần sửa và biết mình nên học gì tiếp theo. Bắt đầu từ một bước nhỏ.'),'home-intro'));
    const actions=el('div',null,'home-actions');
    actions.append(button(copy('Start speaking →','Bắt đầu luyện nói →'),()=>show('speaking'),'primary'),
      button(copy('How it works ↓','Học như thế nào? ↓'),()=>document.querySelector('#home-process').scrollIntoView({behavior:'smooth',block:'start'}),'secondary'));
    hero.append(actions,sourceEl('p',copy('SPEAKING · EXAM REVISION · YOUR LEARNING MAP','LUYỆN NÓI · ÔN THI · LỘ TRÌNH CỦA BẠN'),'home-caption'));
    root.append(hero);
    const process=el('section',null,'home-section');process.id='home-process';
    process.append(sourceEl('p',copy('A LITTLE PRACTICE, A CLEARER DIRECTION','LUYỆN TẬP TỪNG CHÚT, HIỂU RÕ HƯỚNG ĐI'),'eyebrow'),
      sourceEl('h2',copy('Three steps. A stronger voice.','Ba bước để tự tin hơn.')));
    const steps=el('div',null,'home-grid');
    [
      ['01',copy('Choose your question.','Chọn câu hỏi.'),copy('Try a three-part Speaking set. Follow a model answer or respond in your own words.','Chọn bộ Speaking 3 phần. Luyện theo bài mẫu hoặc tự trả lời theo cách của bạn.')],
      ['02',copy('See your words.','Nhìn thấy lời nói.'),copy('Watch your transcript appear as you speak. Spot differences from the script, repeated words and pauses.','Theo dõi lời nói hiện trực tiếp. Nhận biết từ khác bài mẫu, từ lặp và những khoảng ngừng.')],
      ['03',copy('Learn what comes next.','Biết bước học tiếp theo.'),copy('Review your AI feedback, practise again and use your learning map to focus your next session.','Xem nhận xét AI, luyện lại và dùng lộ trình học để chọn trọng tâm cho buổi tiếp theo.')]
    ].forEach(([n,t,d])=>{const card=el('article',null,'home-step');card.append(sourceEl('span',n,'eyebrow'),sourceEl('h3',t),sourceEl('p',d));steps.append(card);});
    process.append(steps);root.append(process);
    const demo=el('section',null,'home-demo');
    const about=el('div');
    about.append(sourceEl('p',copy('NOTICE IT. PRACTISE IT.','NHẬN RA. LUYỆN LẠI.'),'eyebrow'),
      sourceEl('h2',copy('Make your practice visible.','Nhìn rõ từng lần luyện tập.')),
      sourceEl('p',copy('Small signals help you find the moments worth listening to again. Your coach turns practice into specific next steps.',
        'Những dấu hiệu nhỏ giúp bạn tìm đúng đoạn cần nghe lại. AI coach gợi ý bước luyện tiếp dựa trên bài của bạn.')),
      button(copy('Explore Speaking →','Khám phá Speaking →'),()=>show('speaking'),'secondary'));
    const paper=el('div',null,'home-demo-paper');
    paper.append(sourceEl('p',copy('ILLUSTRATION · NOT A LIVE RECORDING','MINH HỌA · KHÔNG PHẢI BẢN GHI TRỰC TIẾP'),'eyebrow'));
    const quote=sourceEl('p',null,'home-demo-quote');
    quote.append(document.createTextNode('I enjoy '),sourceEl('mark','um','home-filler'),document.createTextNode(' learning English because it helps me '),sourceEl('mark','connect connect','home-repeat'),document.createTextNode(' with people.'));
    paper.append(quote,sourceEl('p',copy('Possible filler · Repeated word','Có thể là từ đệm · Từ lặp'),'home-caption'),
      sourceEl('small',copy('Recognition and timing signals are practice cues, not confirmed pronunciation errors.',
        'Dấu hiệu nhận dạng và thời gian là gợi ý luyện tập, không xác nhận lỗi phát âm.')));
    demo.append(about,paper);root.append(demo);
    const explore=el('section',null,'home-section');
    explore.append(sourceEl('p',copy('MAKE ROOM FOR YOUR NEXT STEP','DÀNH CHỖ CHO BƯỚC TIẾP THEO'),'eyebrow'),
      sourceEl('h2',copy('What would you like to work on?','Hôm nay bạn muốn học gì?')));
    const cards=el('div',null,'home-grid home-tools');
    [
      ['chat',copy('Ask. Understand.','Hỏi để hiểu.'),copy('Talk through an idea, share your notes or create a quiz with your AI study companion.','Thảo luận ý tưởng, gửi ghi chú hoặc tạo câu hỏi ôn tập cùng trợ lý AI.'),copy('Open Chat AI →','Mở Chat AI →')],
      ['exams',copy('Revise with purpose.','Ôn thi có trọng tâm.'),copy('Take an exam and review the questions and skills that need more attention.','Làm bài thi và xem lại câu hỏi, kỹ năng cần dành thêm thời gian.'),copy('Open exam revision →','Mở đề thi & ôn tập →')],
      ['map',copy('Know your next step.','Biết mình nên học gì.'),copy('Bring your Speaking and exam results together in a personal learning roadmap.','Kết nối kết quả Speaking và bài thi thành lộ trình học của riêng bạn.'),copy('View learning map →','Xem lộ trình học →')]
    ].forEach(([view,t,d,label])=>{const card=el('article',null,'home-tool');card.append(sourceEl('h3',t),sourceEl('p',d),button(label,()=>show(view),'secondary'));cards.append(card);});
    explore.append(cards);root.append(explore);
    const end=el('section',null,'home-finish');
    end.append(sourceEl('h2',copy('Your next chapter starts with a question.','Chặng học mới bắt đầu từ một câu hỏi.')),
      sourceEl('p',copy('Choose a topic. Take a breath. Give it a try.','Chọn một chủ đề. Hít thở nhẹ. Bắt đầu thử nhé.')),
      button(copy('Start my practice →','Bắt đầu luyện tập →'),()=>show('speaking'),'primary'));
    root.append(end);
  }
  render();window.addEventListener('ui-language-change',render);
  homeCleanup=()=>window.removeEventListener('ui-language-change',render);
}
