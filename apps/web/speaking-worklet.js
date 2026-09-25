/* Mono PCM16, 16 kHz, 100 ms frames. Stateful downsampling across render blocks. */
class SpeakingPCM extends AudioWorkletProcessor {
  constructor() {
    super();
    this.frame = new Int16Array(1600); this.offset = 0;
    this.phase = 0; this.sum = 0; this.count = 0;
    this.port.onmessage = ({data}) => {
      if (data === 'flush') {
        if (this.offset) this.port.postMessage(this.frame.buffer, [this.frame.buffer]);
        this.frame = new Int16Array(1600); this.offset = 0;
        this.port.postMessage('flushed');
      }
    };
  }
  process(inputs) {
    const source = inputs[0]?.[0];
    if (!source) return true;
    for (const value of source) {
      this.sum += value; this.count++; this.phase += 16000;
      if (this.phase >= sampleRate) {
        this.phase -= sampleRate;
        const sample = Math.max(-1, Math.min(1, this.sum / this.count));
        this.sum = 0; this.count = 0;
        this.frame[this.offset++] = Math.round(sample * (sample < 0 ? 32768 : 32767));
        if (this.offset === this.frame.length) {
          this.port.postMessage(this.frame.buffer, [this.frame.buffer]);
          this.frame = new Int16Array(1600); this.offset = 0;
        }
      }
    }
    return true;
  }
}
registerProcessor('speaking-pcm', SpeakingPCM);
