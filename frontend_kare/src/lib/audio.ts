/** Mic capture -> 16 kHz mono PCM16 frames, and WAV playback helpers. */

const TARGET_RATE = 16000;

export class MicRecorder {
  private ctx: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private processor: ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private onFrame: (pcm: ArrayBuffer) => void;
  private inRate = 48000;

  constructor(onFrame: (pcm: ArrayBuffer) => void) {
    this.onFrame = onFrame;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
    });
    this.ctx = new AudioContext();
    this.inRate = this.ctx.sampleRate;
    this.source = this.ctx.createMediaStreamSource(this.stream);
    this.processor = this.ctx.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      const down = downsample(input, this.inRate, TARGET_RATE);
      this.onFrame(floatTo16BitPCM(down));
    };
    this.source.connect(this.processor);
    this.processor.connect(this.ctx.destination); // required for onaudioprocess to fire
  }

  stop() {
    this.processor?.disconnect();
    this.source?.disconnect();
    this.stream?.getTracks().forEach((t) => t.stop());
    this.ctx?.close().catch(() => {});
    this.ctx = this.processor = this.source = this.stream = null;
  }
}

function downsample(buf: Float32Array, from: number, to: number): Float32Array {
  if (to >= from) return buf;
  const ratio = from / to;
  const out = new Float32Array(Math.round(buf.length / ratio));
  let o = 0;
  let i = 0;
  while (o < out.length) {
    const next = Math.round((o + 1) * ratio);
    let sum = 0;
    let count = 0;
    for (; i < next && i < buf.length; i++) {
      sum += buf[i];
      count++;
    }
    out[o++] = count ? sum / count : 0;
  }
  return out;
}

function floatTo16BitPCM(input: Float32Array): ArrayBuffer {
  const out = new DataView(new ArrayBuffer(input.length * 2));
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]));
    out.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return out.buffer;
}

/** Sequential playback of WAV Blobs/ArrayBuffers so sentences don't overlap. */
export class AudioQueue {
  private queue: string[] = [];
  private playing = false;
  private el: HTMLAudioElement;
  onDone?: () => void;

  constructor(el: HTMLAudioElement) {
    this.el = el;
    this.el.onended = () => this.next();
  }

  push(data: ArrayBuffer | Blob) {
    const blob = data instanceof Blob ? data : new Blob([data], { type: 'audio/wav' });
    this.queue.push(URL.createObjectURL(blob));
    if (!this.playing) this.next();
  }

  private next() {
    const url = this.queue.shift();
    if (!url) {
      this.playing = false;
      this.onDone?.();
      return;
    }
    this.playing = true;
    this.el.src = url;
    this.el.play().catch(() => this.next());
  }

  clear() {
    this.queue = [];
    this.el.pause();
    this.playing = false;
  }
}
