"use strict";
let speakingCleanup = () => {};
function disposeSpeaking() { speakingCleanup(); speakingCleanup = () => {}; }
async function speakingHome() {
  reset('Speaking Studio', ''); setNav('speaking');
  const gen = generation, active = () => generation === gen;
  const copy = (en,vi) => uiLanguage === 'en' ? en : vi;
  const lessonNames = {
    explain:['Explain an academic concept','Giải thích một khái niệm học thuật'],
    opinion:['Support an opinion','Bảo vệ quan điểm'],
    compare:['Compare approaches to learning','So sánh cách học'],
    presentation:['Present a research idea','Trình bày ý tưởng nghiên cứu']};
  const dimensions = {
    fluency:['Fluency','Độ trôi chảy'], pronunciation:['Pronunciation','Phát âm'],
    grammar:['Grammar','Ngữ pháp'], vocabulary:['Vocabulary','Từ vựng'],
    coherence:['Coherence','Mạch lạc'], relevance:['Question relevance','Đúng trọng tâm']};
  const flags = {filler:['Possible filler','Có thể là từ đệm'], pause:['Pause','Khoảng dừng'],
    repetition:['Repeated word','Lặp từ'], long_word:['Long word duration','Từ có thời lượng dài']};
  const [config, user, practiceSets] = await Promise.all([api('/speaking/config'), api('/users/me'), api('/speaking/practice-sets')]);
  if (!active()) return;
  updateIdentity(user);
  document.querySelector('#mode-badge').textContent = 'Speaking';
  let history = await api('/speaking/sessions'), selected = null, attempts = [], lesson = 'explain';
  if (!active()) return;
  let busy = false, recording = false, capture = null, transcript = '', timer, limitTimer, ticker;
  let seconds = 0, error = '', pending = null, audio = null, clipTimer;
  let packId=practiceSets[0]?.id, practiceMode='independent', liveEvents=[], liveWords=[];
  let preparing=false, prepDone=false, prepRemaining=0, prepTimer;
  let questionIndex=null, recorderOpen=false;
  const speakingLimit=()=>questionIndex!==null?60:selected?.activity?.speaking_seconds || 180;
  function beginQuestion(index, mode) {
    if(locked()||pending)return;
    recorderOpen=true;questionIndex=selected.activity?.part===1?index:null;practiceMode=mode;seconds=0;
    if(selected.activity?.preparation_seconds&&!prepDone)prepare();else start();
  }
  const locked=()=>busy||recording||preparing;
  function clearPreparation() { clearInterval(prepTimer);preparing=false;prepDone=false;prepRemaining=0; }
  function prepare() {
    stopPlayback();prepRemaining=selected.activity.preparation_seconds;
    const deadline=Date.now()+prepRemaining*1000;
    preparing=true;render();
    prepTimer=setInterval(()=>{
      prepRemaining=Math.max(0,Math.ceil((deadline-Date.now())/1000));
      if(prepRemaining<=0){clearInterval(prepTimer);preparing=false;prepDone=true;render();}
      else {const clock=document.querySelector('#speaking-prep-clock');if(clock)clock.textContent=prepRemaining+' s';}
    },1000);
  }
  async function openPack() {
    busy=true;error='';clearPreparation();stopPlayback();render();
    try {
      const rows=await api('/speaking/practice-sets/'+packId+'/sessions',{method:'POST'});
      if(!active())return;
      history=[...rows,...history];selected=rows[0];attempts=[];pending=null;transcript='';liveEvents=[];liveWords=[];practiceMode='model';questionIndex=null;recorderOpen=false;
      sessionStorage.setItem('bluestudy-speaking',selected.id);
    }catch(e){error=e.message;}
    finally{busy=false;if(active())render();}
  }
  function renderLiveSignals() {
    renderScript();
    const box=document.querySelector('#speaking-live-signals');if(!box)return;
    box.replaceChildren(text('strong',copy('Live speaking signals','Dấu hiệu khi đang nói')));
    const summary=Object.entries(flags).map(([kind,label])=>copy(...label)+': '+liveEvents.filter(e=>e.kind===kind).length).join(' · ');
    box.append(text('p',summary));
    const list=el('ul');
    liveEvents.slice(-6).forEach(e=>list.append(text('li',copy(...flags[e.kind])+' · '+(e.start/1000).toFixed(1)+'–'+(e.end/1000).toFixed(1)+'s')));
    box.append(list,text('small',copy('Approximate signals from incoming word timestamps; not confirmed pronunciation errors.','Dấu hiệu ước lượng từ timestamp nhận được; không phải lỗi phát âm đã xác nhận.')));
    const chips=el('div',null,'speaking-words');
    liveWords.slice(-80).forEach((w,i)=>{
      const index=Math.max(0,liveWords.length-80)+i, marks=liveEvents.filter(e=>e.index===index);
      const chip=text('span',w.text+' · '+(w.start/1000).toFixed(1)+'s','speaking-word'+(marks.length?' flagged':''));
      chip.title=marks.map(e=>copy(...flags[e.kind])).join(', ');chips.append(chip);
    });
    box.append(chips);
  }
  const recordings = new Map();
  function scriptBoard(script, words, final) {
    const board=el('div',null,'speaking-script-board');
    const alignment=speakingAlignment(script,words,final), events=speakingSignals(words);
    board.append(text('h4',copy('YOUR SCRIPT · FOLLOW ALONG','BÀI MẪU · ĐỌC THEO')));
    const passage=el('div',null,'speaking-script-text');
    alignment.tokens.forEach(token=>{
      const marks=events.filter(e=>e.index===token.index);
      const span=text('span',token.text+' ','script-token '+token.state+(marks.length?' hesitation':''));
      span.title=token.state==='different'?copy('Recognised: ','Nhận dạng: ')+token.heard:
        token.state==='missing'?copy('Not recognised in your speech','Không nhận dạng được trong lời nói'):
        marks.map(e=>copy(...flags[e.kind])).join(', ');
      passage.append(span);
    });
    board.append(passage,text('p',copy('Green: matched · Red underline: different / skipped · Amber: timing signal · Grey: not yet read',
      'Xanh: khớp mẫu · Gạch đỏ: khác / bỏ qua · Vàng: dấu hiệu ngập ngừng · Xám: chưa đọc'),'script-legend'));
    if(alignment.extras.length)board.append(text('p',copy('Extra words recognised: ','Từ nhận dạng thêm: ')+alignment.extras.map(i=>words[i].text).join(' '),'script-extras'));
    board.append(text('small',copy('Live recognition can change. These marks compare text, not pronunciation.',
      'Nhận dạng trực tiếp có thể thay đổi. Dấu màu so sánh văn bản, không chấm phát âm.')));
    return board;
  }
  function renderScript() {
    const host=document.querySelector('#speaking-script-live');
    if(!host)return;
    const script=questionIndex!==null?selected?.activity?.sample_segments[questionIndex]?.text:selected?.activity?.reference_answer;
    host.replaceChildren();
    if(script)host.append(scriptBoard(script,liveWords,!recording&&!busy&&liveWords.length>0));
  }
  const local = value => value?.[uiLanguage] || value?.en || '';
  const text = (tag,value,cls) => sourceEl(tag,value,cls);
  const action = (label,fn,disabled=false,cls='secondary') => {
    const b = button(label,fn,cls); b.disabled=disabled; return b;
  };
  function stopPlayback() { audio?.pause(); clearTimeout(clipTimer); window.speechSynthesis?.cancel(); }
  function fail(e) {
    capture?.release(); recording=false; busy=false;
    clearTimeout(limitTimer); clearInterval(ticker); error=e.message;
    if (active()) render();
  }
  async function refresh() {
    clearTimeout(timer);
    if (!selected || !active()) return;
    const id=selected.id;
    try {
      const result = await api('/speaking/sessions/'+id);
      if (!active() || selected?.id !== id) return;
      selected=result.session; attempts=result.attempts;
      history=history.map(s=>s.id===id?selected:s);
      if (!recording && !busy) render();
      if (selected.status==='queued' || attempts.some(a=>a.status==='queued'))
        timer=setTimeout(refresh,1800);
    } catch(e) { if(active()) {error=e.message;render();} }
  }
  async function openSession(id) {
    clearTimeout(timer); clearPreparation();stopPlayback(); error=''; pending=null; transcript='';liveEvents=[];liveWords=[];questionIndex=null;recorderOpen=false; busy=true; render();
    try {
      const result=await api('/speaking/sessions/'+id);
      if (!active()) return;
      selected=result.session; attempts=result.attempts;
      lesson=lessonNames[selected.lesson]?selected.lesson:'explain';
      if(!selected.activity)practiceMode='independent';
      sessionStorage.setItem('bluestudy-speaking',id);
    } catch(e) { error=e.message; }
    finally { busy=false; if(active()) {render();refresh();} }
  }
  async function create() {
    busy=true; error=''; clearPreparation();stopPlayback(); render();
    try {
      const row=await api('/speaking/sessions',{method:'POST',body:{lesson}});
      if (!active()) return;
      history=[row,...history]; selected=row; attempts=[]; pending=null; transcript='';practiceMode='independent';liveWords=[];liveEvents=[];questionIndex=null;recorderOpen=false;
      sessionStorage.setItem('bluestudy-speaking',row.id);
    } catch(e) {error=e.message;}
    finally {busy=false;if(active()){render();refresh();}}
  }
  async function save() {
    if (!pending || !selected) return;
    busy=true; render();
    try {
      const result=await api('/speaking/sessions/'+selected.id+'/attempts',{method:'POST',body:pending});
      if(!active())return;
      attempts=[...attempts.filter(a=>a.id!==result.id),result]; pending=null;
    } catch(e) {error=e.message;}
    finally {busy=false;if(active()){render();refresh();}}
  }
  async function finish() {
    if(!recording || busy)return;
    busy=true; clearTimeout(limitTimer);clearInterval(ticker);render();
    try {
      const result=await capture.stop(); recording=false;
      liveWords=result.words;liveEvents=speakingSignals(liveWords);transcript=liveWords.map(w=>w.text).join(' ');
      if(!active())return;
      if(!result.words.length)throw new Error(copy('No words detected. Check your microphone and try again.','Chưa nhận được lời nói. Kiểm tra mic và thử lại.'));
      const id=crypto.randomUUID();
      recordings.set(id,URL.createObjectURL(result.audio));
      pending={id,words:result.words,response_language:uiLanguage,practice_mode:practiceMode,question_index:questionIndex};
      prepDone=false;
      busy=false; await save();
    }catch(e){fail(e);}
  }
  async function start() {
    if(busy || recording)return;
    clearInterval(prepTimer);preparing=false;
    stopPlayback(); error=''; transcript='';liveEvents=[];liveWords=[]; seconds=0; busy=true; render();
    capture=new SpeakingCapture(value=>{
      transcript=value;
      const target=document.querySelector('#speaking-transcript');
      if(active() && target)target.textContent=value;
      liveWords=capture.words();liveEvents=speakingSignals(liveWords);
      if(active())renderLiveSignals();
    },fail);
    try {
      await capture.start();
      if(!active() || capture.cancelled)return;
      recording=true;busy=false;render();
      const spokenAt=Date.now();
      ticker=setInterval(()=>{
        seconds=Math.floor((Date.now()-spokenAt)/1000);
        const clock=document.querySelector('#speaking-clock');
        if(clock)clock.textContent=seconds+' / '+speakingLimit()+' s';
      },1000);
      limitTimer=setTimeout(finish,speakingLimit()*1000);
    }catch(e){fail(e);}
  }
  function play(id,start=0,end=null) {
    stopPlayback();
    const url=recordings.get(id); if(!url)return;
    audio=new Audio(url);audio.currentTime=Math.max(0,start/1000-.15);
    audio.play().catch(e=>{error=e.message;if(active())render();});
    if(end!==null)clipTimer=setTimeout(()=>audio?.pause(),end-start+450);
  }
  function sample(answer) {
    stopPlayback();
    if(!window.speechSynthesis){error=copy('Speech playback is unavailable in this browser.','Trình duyệt chưa hỗ trợ đọc mẫu.');render();return;}
    const voice=new SpeechSynthesisUtterance(answer);voice.lang='en-US';voice.rate=.9;
    voice.onerror=(event)=>{if(active()&&!['canceled','interrupted'].includes(event.error)){error=copy('Could not play the example. Try another browser voice.','Không đọc được bài mẫu. Hãy thử giọng khác trên trình duyệt.');render();}};
    window.speechSynthesis.speak(voice);
  }
  function feedback(attempt,index) {
    const section=el('section',null,'card speaking-attempt');
    section.append(text('h3',copy('Attempt ','Lần nói ')+(index+1)),
      text('p',new Date(attempt.created_at).toLocaleString(uiLanguage==='en'?'en-GB':'vi-VN'),'muted'));
    const m=attempt.metrics;
    if(m.practice_mode==='model'&&selected.activity){
      const script=m.question_index!=null?selected.activity.sample_segments[m.question_index]?.text:selected.activity.reference_answer;
      if(script)section.append(scriptBoard(script,attempt.words,true));
    }
    if(m.question_label)section.append(text('h4',m.question_label));
    section.append(text('p',m.practice_mode==='model'?copy('Guided practice with model answer','Luyện theo bài mẫu'):copy('Independent answer','Tự trả lời'),'eyebrow'));
    if(m.reference_similarity_percent!=null)section.append(text('p',copy('Word-sequence similarity to the sample: ','Độ giống chuỗi từ với bài mẫu: ')+m.reference_similarity_percent+'%'),
      text('small',copy('This measures text overlap, not pronunciation or independent speaking ability.','Chỉ đo mức trùng khớp văn bản, không phải điểm phát âm hay năng lực nói độc lập.'),'muted'));
    section.append(text('p',m.word_count+' '+copy('words','từ')+' · '+m.duration_seconds+'s · '+(m.words_per_minute ?? '—')+' '+copy('words/min','từ/phút')));
    if(recordings.has(attempt.id))section.append(action(copy('Listen to your recording','Nghe lại bản ghi'),()=>play(attempt.id),recording));
    const detail=el('details'), title=text('summary',copy('Transcript & word timestamps','Bản chép lời & timestamp từng từ'));
    detail.append(title);
    const wordList=el('div',null,'speaking-words');
    attempt.words.forEach((w,i)=>{
      const labels=m.events.filter(e=>e.index===i).map(e=>copy(...flags[e.kind]));
      const word=action(w.text+' · '+(w.start/1000).toFixed(1)+'–'+(w.end/1000).toFixed(1)+'s',()=>play(attempt.id,w.start,w.end),recording||!recordings.has(attempt.id),'speaking-word');
      if(labels.length)word.classList.add('flagged');
      word.title=labels.join(', ');wordList.append(word);
    });
    detail.append(wordList);section.append(detail);
    const signals=el('ul',null,'speaking-signals');
    m.events.slice(0,30).forEach(e=>signals.append(text('li',copy(...flags[e.kind])+' · '+(e.start/1000).toFixed(1)+'–'+(e.end/1000).toFixed(1)+'s')));
    section.append(signals,text('small',copy('Timing flags are suggestions to listen back, not confirmed mistakes. Speech recognition may omit fillers.','Dấu hiệu từ timestamp chỉ gợi ý đoạn cần nghe lại, không khẳng định lỗi. Nhận dạng có thể bỏ sót từ đệm.'),'muted'));
    if(attempt.status==='queued')section.append(text('p',copy('Speaking Coach is reviewing your answer…','Speaking Coach đang phân tích câu trả lời…')));
    if(attempt.status==='failed')section.append(text('p',copy('AI feedback could not be generated. Your transcript is saved.','Chưa tạo được nhận xét AI. Bản chép lời đã được lưu.')),
      action(copy('Retry analysis','Phân tích lại'),async()=>{
        try{await api('/speaking/sessions/'+selected.id+'/attempts/'+attempt.id+'/retry',{method:'POST'});refresh();}catch(e){error=e.message;render();}
      }));
    const c=attempt.coaching;
    if(c){
      const score=c.fluency?.score;
      const hero=el('div',null,'speaking-result-hero');
      hero.append(text('div',score==null?'—':String(Math.round(score*20)),'speaking-score-ring'),
        text('h3',copy('FLUENCY SCORE / 100','ĐIỂM TRÔI CHẢY / 100')),
        text('p',local(c.fluency?.feedback)||local(c.summary)),
        text('small',copy('AI practice estimate from transcript and timings; converted from the 0–5 fluency scale.',
          'Ước lượng luyện tập của AI từ văn bản và thời gian; quy đổi từ thang trôi chảy 0–5.')));
      section.append(hero);
      section.append(text('h3',copy('Practice score','Điểm luyện tập')+': '+(c.overall ?? '—')+' / 5'),
        text('p',copy('Provisional feedback from transcript and timings; not an IELTS or CEFR assessment.','Nhận xét tạm thời từ bản chép lời và timestamp; không phải đánh giá IELTS hay CEFR.'),'muted'),text('p',local(c.summary)));
      const grid=el('div',null,'speaking-scores');
      for(const [key,label] of Object.entries(dimensions)){
        const tile=el('div',null,'speaking-score');
        tile.append(text('strong',copy(...label)),text('h3',c[key]?.score==null?'—':c[key].score+' / 5'),
          text('p',key==='pronunciation'?copy('Not scored: pronunciation needs acoustic analysis. ASR confidence is not a pronunciation score.','Chưa chấm: phát âm cần phân tích âm thanh. Độ tin cậy nhận dạng không phải điểm phát âm.'):local(c[key]?.feedback)));
        grid.append(tile);
      }
      section.append(grid,text('h4',copy('Suggested corrections','Gợi ý sửa câu')));
      for(const correction of c.corrections){
        const block=el('div',null,'speaking-correction');
        block.append(text('p',correction.original),text('strong','→ '+correction.corrected),text('p',local(correction.explanation)));section.append(block);
      }
      section.append(text('h4',copy('Model answer — listen, then try again','Bài mẫu — nghe rồi nói lại')),text('p',c.sample_answer),
        action(copy('Listen to example','Nghe bài mẫu'),()=>sample(c.sample_answer),recording),
        text('small',copy('Uses your browser’s English voice.','Sử dụng giọng tiếng Anh của trình duyệt.'),'muted'));
      const steps=el('ol'); c.next_steps.forEach(step=>steps.append(text('li',local(step))));section.append(steps);
    }
    return section;
  }
  function render() {
    if(!active())return;
    root.replaceChildren(text('span','SPEAK · LISTEN · REFINE','eyebrow'),text('h1','Speaking Studio'),
      text('p',copy('Build confidence in academic English, one answer at a time.','Luyện nói tiếng Anh học thuật qua từng câu trả lời.')));
    root.className='speaking-page';
    if(error)root.append(text('p',error,'speaking-warning'));
    if(!config.configured)root.append(text('p',copy('Microphone unavailable: add ASSEMBLYAI_API_KEY to the server configuration.','Mic chưa sẵn sàng: thêm ASSEMBLYAI_API_KEY vào cấu hình máy chủ.'),'speaking-warning'));
    const bank=el('section',null,'card speaking-bank');
    bank.append(text('h2',copy('Three-part Speaking practice','Luyện Speaking 3 phần')),
      text('p',copy('Part 1: 3 min · Part 2: prepare 1 + speak 3 min · Part 3: prepare 1 + speak 4 min','Part 1: 3 phút · Part 2: chuẩn bị 1 + nói 3 phút · Part 3: chuẩn bị 1 + nói 4 phút')),
      text('small',copy('Authored practice sets based on your requested structure; not official or predicted exam papers. Samples are concise examples: expand them with your own details.','Đề luyện theo cấu trúc bạn cung cấp, không phải đề chính thức hay dự đoán đề thi. Bài mẫu ngắn minh họa cách trả lời; hãy phát triển thêm bằng chi tiết riêng.'),'muted'));
    const setPicker=el('select');setPicker.id='speaking-set-picker';setPicker.setAttribute('aria-label',copy('Practice set','Bộ đề luyện'));setPicker.disabled=locked();
    practiceSets.forEach(p=>{const o=text('option',p.id.toUpperCase()+' · '+p.title);o.value=p.id;setPicker.append(o);});
    setPicker.value=packId;setPicker.onchange=()=>{packId=setPicker.value;};
    const bankControls=el('div',null,'speaking-controls');
    bankControls.append(setPicker,action(copy('Open 3-part set','Mở bộ đề 3 phần'),openPack,locked(),'primary'));bank.append(bankControls);root.append(bank);
    const top=el('section',null,'card');
    let recorderHost=null;
    if(selected){
      const activity=selected.activity;
      if(activity){
        const nav=el('div',null,'speaking-controls speaking-part-nav');
        history.filter(s=>s.activity?.group_id===activity.group_id).sort((a,b)=>a.activity.part-b.activity.part).forEach(s=>{
          const b=action('Part '+s.activity.part+' · '+s.activity.title,()=>openSession(s.id),locked(),s.id===selected.id?'primary':'secondary');
          b.setAttribute('aria-current',s.id===selected.id?'step':'false');nav.append(b);
        });
        top.append(nav,text('h2','Part '+activity.part+' · '+activity.title));
        const tabs=el('div',null,'speaking-controls speaking-mode-tabs');
        tabs.setAttribute('role','group');tabs.setAttribute('aria-label',copy('Practice mode','Chế độ luyện'));
        [['model',copy('Follow the model answer','Luyện theo mẫu')],['independent',copy('Independent answer','Tự trả lời')]].forEach(([mode,label])=>{
          const tab=action(label,()=>{
            stopPlayback();clearPreparation();practiceMode=mode;questionIndex=null;recorderOpen=false;
            transcript='';liveWords=[];liveEvents=[];seconds=0;error='';render();
          },locked()||!!pending,practiceMode===mode?'primary':'secondary');
          tab.dataset.practiceMode=mode;tab.setAttribute('aria-pressed',String(practiceMode===mode));tabs.append(tab);
        });
        top.append(tabs);
        if(practiceMode==='independent'){
        if(activity.part===1){
          let qi=0;
          activity.topics.forEach(topic=>{top.append(text('h3',topic.title));const qs=el('ol');topic.questions.forEach(q=>{
            const index=qi++, row=el('li',null,'speaking-question');
            row.append(text('p',q),action(copy('Answer this question','Trả lời câu này'),()=>beginQuestion(index,'independent'),locked()||!!pending));
            if(questionIndex===index&&practiceMode==='independent')recorderHost=row;
            qs.append(row);
          });top.append(qs);});
        }else if(activity.part===2){
          top.append(text('p',activity.situation));const options=el('ol');activity.options.forEach(o=>options.append(text('li',o)));top.append(options);
        }else{
          top.append(text('h3',activity.topic));const points=el('ul');[...activity.points,copy('Your own idea','Ý kiến riêng của bạn')].forEach(p=>points.append(text('li',p)));top.append(points);
        }
        if(activity.part!==1){
          const questionHost=el('div',null,'speaking-question');
          questionHost.append(action(copy('Answer this question','Trả lời câu này'),()=>beginQuestion(null,'independent'),locked()||!!pending,'primary'));
          top.append(questionHost);
          if(practiceMode==='independent')recorderHost=questionHost;
        }
        }
        if(practiceMode==='model'){
        const examples=el('details');examples.className='speaking-model';examples.open=practiceMode==='model';
        examples.append(text('summary',copy('Read & listen to the model before speaking','Đọc & nghe bài mẫu trước khi nói')));
        examples.append(action(copy('Listen to the full model','Nghe toàn bộ bài mẫu'),()=>sample(activity.reference_answer),locked()),
          action(copy('Stop listening','Dừng nghe'),stopPlayback));
        activity.sample_segments.forEach((segment,index)=>{
          const block=el('section',null,'speaking-sample-segment');
          block.append(text('h4',segment.label),text('p',segment.text),
            action(copy('Listen to this answer','Nghe câu trả lời này'),()=>sample(segment.text),locked()),
            action(copy('Start speaking','Bắt đầu nói'),()=>beginQuestion(index,'model'),locked()||!!pending,'primary'));
          if(practiceMode==='model'&&(questionIndex===index||activity.part!==1))recorderHost=block;
          examples.append(block);
        });
        examples.append(text('small',copy('A sample is one possible response. Different relevant answers are welcome; memorising this text does not demonstrate independent ability.','Bài mẫu là một cách trả lời. Bạn có thể trả lời khác nếu phù hợp; thuộc bài mẫu không chứng minh năng lực nói độc lập.'),'muted'));top.append(examples);
        }
      }else{
        const questionHost=el('div',null,'speaking-question');
        questionHost.append(text('h2',selected.question || copy('AI is preparing your question…','AI đang chuẩn bị câu hỏi…')));
        if(selected.status==='ready')questionHost.append(action(copy('Answer this question','Trả lời câu này'),()=>beginQuestion(null,'independent'),locked()||!!pending,'primary'));
        top.append(questionHost);recorderHost=questionHost;
      }
      if(selected.status==='failed')top.append(text('p',copy('Could not generate a question. Please request another.','Chưa tạo được câu hỏi. Hãy thử tạo câu hỏi khác.')));
      if(selected.status==='ready'&&recorderOpen&&recorderHost){
        const recorder=el('div',null,'speaking-recorder');
        recorderHost.append(recorder);
        if(practiceMode==='model'){
          const script=el('div');script.id='speaking-script-live';recorder.append(script);
        }
        if(questionIndex!==null)recorder.append(text('strong',copy('Practising this question only · 60 seconds','Đang luyện riêng câu này · 60 giây')));
        recorder.append(text('p',copy('Speaking limit: ','Thời gian nói: ')+(speakingLimit()/60)+copy(' minutes. Audio streams to AssemblyAI; the transcript is saved and analysed by your AI coach. Recordings stay in this tab.',' phút. Âm thanh gửi tới AssemblyAI; bản chép lời được lưu và gửi AI coach phân tích. Bản ghi âm chỉ giữ trong tab này.'),'muted'));
        const needsPrep=!!activity?.preparation_seconds&&!prepDone&&!recording;
        if(preparing){
          const clock=text('p',prepRemaining+' s');clock.id='speaking-prep-clock';recorder.append(text('strong',copy('Preparation time — microphone is off','Thời gian chuẩn bị — mic đang tắt')),clock,
            action(copy('Ready — start speaking','Đã sẵn sàng — bắt đầu nói'),()=>{clearInterval(prepTimer);preparing=false;prepDone=true;start();},busy||!config.configured,'primary'),
            action(copy('Cancel preparation','Hủy chuẩn bị'),()=>{clearPreparation();render();}));
        }else{
          const clock=text('p',seconds+' / '+speakingLimit()+' s');clock.id='speaking-clock';clock.setAttribute('aria-live','off');recorder.append(clock);
          const label=recording?copy('Finish & analyse','Dừng & phân tích'):needsPrep?copy('Start 1-minute preparation','Bắt đầu chuẩn bị 1 phút'):copy(attempts.length?'Speak again':'Start microphone',attempts.length?'Nói lại':'Bắt đầu nói');
          recorder.append(action(label,recording?finish:needsPrep?prepare:start,busy||!config.configured||(!recording&&!!pending),'primary'));
        }
        if(recording)recorder.append(action(copy('Cancel recording','Hủy bản ghi'),()=>{capture?.release();recording=false;busy=false;clearTimeout(limitTimer);clearInterval(ticker);transcript='';render();},busy));
        if(busy)recorder.append(text('p',copy('Connecting / processing…','Đang kết nối / xử lý…')));
        const live=text('p',transcript || copy('Your words will appear here as you speak.','Lời nói sẽ hiện tại đây khi bạn nói.'),'speaking-transcript');live.id='speaking-transcript';live.setAttribute('aria-live','polite');recorder.append(live);
        const liveSignals=el('div',null,'speaking-live-signals');liveSignals.id='speaking-live-signals';liveSignals.setAttribute('aria-live','polite');recorder.append(liveSignals);
        if(pending)recorder.append(action(copy('Retry saving this attempt','Thử lưu lại lần nói này'),save,busy));
      }
    }
    if(selected)root.append(top);
    renderLiveSignals();
    const comparable=attempts.filter(a=>(a.metrics.practice_mode||'independent')===practiceMode&&(a.metrics.question_index??null)===questionIndex);
    if(comparable.length>=2){
      const first=comparable[0],last=comparable.at(-1),box=el('section',null,'card');
      box.append(text('h2',copy('Your progress on this question','Tiến bộ với câu hỏi này')));
      box.append(text('p',practiceMode==='model'?copy('Comparing guided practice attempts only','Chỉ so sánh các lần luyện theo mẫu'):copy('Comparing independent answers only','Chỉ so sánh các lần tự trả lời')));
      const table=el('table'),head=el('tr');
      [copy('Metric','Tiêu chí'),copy('Attempt ','Lần ')+(attempts.indexOf(first)+1),copy('Attempt ','Lần ')+(attempts.indexOf(last)+1)].forEach(v=>head.append(text('th',v)));table.append(head);
      for(const [label,a,b] of [
        [copy('Practice score / 5','Điểm luyện tập / 5'),first.coaching?.overall,last.coaching?.overall],
        [copy('Words per minute','Từ mỗi phút'),first.metrics.words_per_minute,last.metrics.words_per_minute],
        [copy('Pauses ≥ 1.2s','Khoảng dừng ≥ 1,2s'),first.metrics.events.filter(e=>e.kind==='pause').length,last.metrics.events.filter(e=>e.kind==='pause').length],
        ...Object.entries(dimensions).map(([key,label])=>[copy(...label),first.coaching?.[key]?.score,last.coaching?.[key]?.score])
      ]){const row=el('tr');[label,a??'—',b??'—'].forEach(v=>row.append(text('td',String(v))));table.append(row);}
      box.append(table,text('p',copy('Compare like-for-like answers. Faster speech is not automatically better.','So sánh các lần trả lời cùng câu hỏi. Nói nhanh hơn không đồng nghĩa tốt hơn.'),'muted'));root.append(box);
    }
    attempts.map((a,i)=>({a,i})).filter(({a})=>(a.metrics.practice_mode||'independent')===practiceMode).reverse().forEach(({a,i})=>root.append(feedback(a,i)));
    const list=el('section',null,'card');list.append(text('h2',copy('Practice history','Lịch sử luyện nói')));
    history.forEach(s=>{const row=el('div',null,'speaking-history-row');
      row.append(action(s.activity?s.activity.set_title+' · Part '+s.activity.part:s.question || copy(...lessonNames[s.lesson]),()=>openSession(s.id),locked()),
        text('small',new Date(s.created_at).toLocaleDateString(uiLanguage==='en'?'en-GB':'vi-VN')),
        action(copy('Delete','Xóa'),async()=>{
          if(!window.confirm(copy('Delete this question and all its attempts?','Xóa câu hỏi và mọi lần nói của câu hỏi này?')))return;
          try {await api('/speaking/sessions/'+s.id,{method:'DELETE'});history=history.filter(h=>h.id!==s.id);
            if(selected?.id===s.id){selected=null;attempts=[];clearTimeout(timer);sessionStorage.removeItem('bluestudy-speaking');}render();
          }catch(e){error=e.message;render();}
        },locked()));list.append(row);
    });root.append(list);
  }
  const languageChange=()=>render();window.addEventListener('ui-language-change',languageChange);
  speakingCleanup=()=>{
    capture?.release();clearPreparation();clearTimeout(timer);clearTimeout(limitTimer);clearInterval(ticker);stopPlayback();
    recordings.forEach(url=>URL.revokeObjectURL(url));
    window.removeEventListener('ui-language-change',languageChange);
  };
  render();
  const saved=sessionStorage.getItem('bluestudy-speaking');
  if(history.some(h=>h.id===saved))await openSession(saved);
}
