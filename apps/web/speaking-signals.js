"use strict";
// Align the latest ASR snapshot to a script prefix. Unspoken trailing words
// remain pending until the recording ends; partial Turn revisions replace it.
function speakingAlignment(script, words, final=false) {
  const tokens=script.match(/\S+/g)||[];
  const clean=s=>s.toLowerCase().replace(/[’]/g,"'").replace(/[^a-z0-9']/g,'');
  const a=tokens.map(clean), b=words.map(w=>clean(w.text));
  const dp=Array.from({length:a.length+1},()=>new Uint16Array(b.length+1));
  for(let i=0;i<=a.length;i++)dp[i][0]=i;
  for(let j=0;j<=b.length;j++)dp[0][j]=j;
  for(let i=1;i<=a.length;i++)for(let j=1;j<=b.length;j++)
    dp[i][j]=Math.min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+(a[i-1]===b[j-1]?0:1));
  let end=a.length;
  if(!final) {
    end=0;
    for(let i=1;i<=a.length;i++)if(dp[i][b.length]<dp[end][b.length])end=i;
  }
  const result=tokens.map(text=>({text,state:'pending'})), extras=[];
  let i=end,j=b.length;
  while(i||j) {
    if(i&&j&&dp[i][j]===dp[i-1][j-1]+(a[i-1]===b[j-1]?0:1)){
      result[i-1]={text:tokens[i-1],state:a[i-1]===b[j-1]?'matched':'different',heard:words[j-1].text,index:j-1};i--;j--;
    }else if(j&&dp[i][j]===dp[i][j-1]+1){extras.unshift(j-1);j--;}
    else {result[i-1]={text:tokens[i-1],state:'missing'};i--;}
  }
  return {tokens:result,extras};
}
// Mirror server thresholds; recompute from the latest Turn snapshot, never
// accumulate partial transcript versions as if they were new words.
function speakingSignals(words) {
  const events=[], clean=w=>w.text.toLowerCase().replace(/[^a-z']/g,'');
  words.forEach((w,i)=>{
    if(['um','uh','erm','er','hmm','uhh','umm'].includes(clean(w)))
      events.push({kind:'filler',index:i,start:w.start,end:w.end});
    if(i && w.start-words[i-1].end>=1200)
      events.push({kind:'pause',index:i,start:words[i-1].end,end:w.start});
    if(i && clean(w) && clean(w)===clean(words[i-1]))
      events.push({kind:'repetition',index:i,start:words[i-1].start,end:w.end});
    if(w.end-w.start>=1200)
      events.push({kind:'long_word',index:i,start:w.start,end:w.end});
  });
  return events;
}
