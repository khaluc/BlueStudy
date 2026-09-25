"use strict";
class SpeakingCapture {
  constructor(onTranscript, onError) {
    this.onTranscript = onTranscript; this.onError = onError;
    this.turns = new Map(); this.frames = []; this.cancelled = false;
  }
  words() {
    return [...this.turns.entries()].sort((a,b) => a[0]-b[0]).flatMap(([,t]) => t.words || [])
      .map(w => ({text:w.text, start:w.start, end:w.end, confidence:w.confidence ?? null}));
  }
  transcript() {
    return [...this.turns.entries()].sort((a,b) => a[0]-b[0]).map(([,t]) => t.transcript).join(' ');
  }
  async start() {
    if (!navigator.mediaDevices?.getUserMedia || !window.AudioWorkletNode)
      throw new Error('Microphone requires HTTPS or localhost and a modern browser.');
    this.stream = await navigator.mediaDevices.getUserMedia({audio:{channelCount:1, echoCancellation:true, noiseSuppression:true}});
    if (this.cancelled) { this.release(); return; }
    this.context = new AudioContext({sampleRate:16000});
    await this.context.resume();
    const auth = await api('/speaking/token', {method:'POST'});
    if (this.cancelled) { this.release(); return; }
    const query = new URLSearchParams({sample_rate:'16000', encoding:'pcm_s16le',
      speech_model:auth.speech_model, token:auth.token,
      prompt:'Transcribe English speech verbatim, including filler words and repeated words. Do not correct grammar.'});
    this.socket = new WebSocket('wss://streaming.assemblyai.com/v3/ws?' + query);
    await new Promise((resolve,reject) => {
      const timeout = setTimeout(() => reject(new Error('AssemblyAI connection timed out.')), 15000);
      this.socket.onmessage = event => {
        let msg;
        try { msg = JSON.parse(event.data); } catch { return; }
        if (msg.type === 'Begin') { clearTimeout(timeout); resolve(); }
        if (msg.type === 'Turn') {
          this.turns.set(msg.turn_order, msg); this.onTranscript(this.transcript());
        }
        if (msg.type === 'Termination') this.finished?.();
        if (msg.type === 'Error' || msg.error) {
          clearTimeout(timeout); reject(new Error('AssemblyAI could not transcribe this recording.'));
          if (!this.cancelled && !this.stopping) this.onError(new Error('AssemblyAI transcription failed.'));
        }
      };
      this.socket.onerror = () => { clearTimeout(timeout); reject(new Error('AssemblyAI connection failed.')); };
      this.socket.onclose = () => {
        clearTimeout(timeout);
        reject(new Error('AssemblyAI connection closed.'));
        if (!this.cancelled && !this.stopping) this.onError(new Error('Connection lost. Please record again.'));
      };
    });
    if (this.cancelled) { this.release(); return; }
    await this.context.audioWorklet.addModule('/app/speaking-worklet.js');
    if (this.cancelled) { this.release(); return; }
    this.source = this.context.createMediaStreamSource(this.stream);
    this.node = new AudioWorkletNode(this.context, 'speaking-pcm');
    this.node.port.onmessage = ({data}) => {
      if (data === 'flushed') { this.flushed?.(); return; }
      if (this.socket?.readyState !== WebSocket.OPEN || this.cancelled) return;
      if (this.socket.bufferedAmount > 256000) {
        this.onError(new Error('Connection too slow. Please record again.')); return;
      }
      this.frames.push(data); this.socket.send(data);
    };
    this.source.connect(this.node); this.node.connect(this.context.destination);
  }
  async stop() {
    this.stopping = true;
    this.source?.disconnect();
    if (this.node) await new Promise(resolve => {
      const timer = setTimeout(resolve, 500);
      this.flushed = () => { clearTimeout(timer); resolve(); };
      this.node.port.postMessage('flush');
    });
    this.node?.disconnect();
    this.stream?.getTracks().forEach(t => t.stop());
    try {
      if (this.socket?.readyState !== WebSocket.OPEN) throw new Error('Connection lost. Please record again.');
      await new Promise((resolve,reject) => {
        const timeout = setTimeout(() => reject(new Error('Final transcript did not arrive. Please record again.')), 12000);
        this.finished = () => { clearTimeout(timeout); resolve(); };
        this.socket.send(JSON.stringify({type:'Terminate'}));
      });
      return {words:this.words(), audio:this.wav()};
    } finally { this.release(); }
  }
  wav() {
    const size = this.frames.reduce((sum, frame) => sum + frame.byteLength, 0);
    const header = new ArrayBuffer(44), v = new DataView(header);
    const text = (offset, s) => [...s].forEach((c,i) => v.setUint8(offset+i,c.charCodeAt(0)));
    text(0,'RIFF'); v.setUint32(4,36+size,true); text(8,'WAVE'); text(12,'fmt ');
    v.setUint32(16,16,true); v.setUint16(20,1,true); v.setUint16(22,1,true);
    v.setUint32(24,16000,true); v.setUint32(28,32000,true); v.setUint16(32,2,true);
    v.setUint16(34,16,true); text(36,'data'); v.setUint32(40,size,true);
    return new Blob([header,...this.frames], {type:'audio/wav'});
  }
  release() {
    this.cancelled = true;
    this.source?.disconnect(); this.node?.disconnect();
    this.stream?.getTracks().forEach(t => t.stop());
    if (this.context?.state !== 'closed') this.context?.close().catch(() => {});
    if (this.socket?.readyState === WebSocket.OPEN) {
      try { this.socket.send(JSON.stringify({type:'Terminate'})); } catch {}
    }
    this.socket?.close();
  }
}
