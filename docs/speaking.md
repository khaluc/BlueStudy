# Speaking Studio

Open /app/#speaking. Choose a lesson, request a Qwen-generated question,
start the microphone, and finish to obtain bilingual coaching. Repeat the
same question to compare your first and latest attempts. History persists
per learner. Every practice session can be deleted with its attempts.

## Configuration

Put ASSEMBLYAI_API_KEY in padayon/.env, then recreate the API container:

    docker compose up -d --build api worker

ASSEMBLYAI_SPEECH_MODEL defaults to universal-3-5-pro. The permanent key
is available only to the API. An authenticated POST /speaking/token
requests a single-use, 60-second token and a 300-second maximum session
duration. Token issuance is limited to four requests per minute per user
per API process. This is not a distributed production quota.

Browser audio requires HTTPS or localhost and microphone permission.
An AudioWorklet emits mono 16-bit PCM at 16 kHz in 100 ms chunks. The browser
connects directly to AssemblyAI's v3 streaming endpoint using the temporary
token. Turn updates replace the previous version by turn_order, avoiding
duplicate partial/final transcripts. On Finish, the client flushes audio,
sends Terminate, and waits for final transcription before saving.
Navigation, cancellation and errors release microphone tracks and sockets.
Maximum recording length is three minutes.

## Three-part practice sets

The practice-set selector contains 16 authored sets using the structure
provided by the learner. These are not official, recalled or predicted exam
papers. The first preserves Morning Routines + Transport, Watching a Movie
and Causes of Stress in the Modern Workplace.

- Part 1: two topics, three questions each, three minutes speaking.
- Part 2: one situation and three options; one minute preparation, three minutes speaking.
- Part 3: topic, three suggested points and the learner's own idea; one minute
  preparation, four minutes speaking.

Part 3 overrides the general three-minute limit. Server validation enforces
the selected part's limit and streaming tokens now allow up to 300 seconds.
Preparation never starts the microphone automatically. The learner can finish
preparing early or start recording after the countdown.

Each part offers a concise model response before recording, full-model playback
and individual segment playback. Guided practice and independent answers are
stored separately in attempt metrics. Comparisons use the same part and mode.
Word-sequence similarity to the reference is labelled separately and is not a
pronunciation or proficiency score.

Live timing flags are recomputed from the latest AssemblyAI Turn snapshot,
so partial updates do not accumulate duplicate counts. Highlights show
recognised fillers, adjacent repeated words, completed pauses of at least
1.2 seconds and words lasting at least 1.2 seconds. These remain approximate
signals, not confirmed acoustic errors. A silent gap is reported when the
next recognised word supplies its endpoint.

    python -m pytest -q tests/integration/test_speaking_parts.py
    python -m scripts.smoke_speaking_parts

## Assessment and limitations

- Word timestamps, repetition, recognised fillers, pauses of at least 1.2
  seconds and long word durations are observable signals to review, not
  confirmed pronunciation errors. ASR can omit fillers and repetitions.
- Qwen reviews fluency evidence, grammar, vocabulary, coherence and relevance.
  Scores are provisional 0–5 practice estimates, not IELTS or CEFR results.
  With fewer than 20 words, scores are withheld.
- Pronunciation is explicitly **not scored**. AssemblyAI transcription
  confidence does not measure pronunciation. Phoneme/intonation assessment
  requires an additional acoustic assessment integration.
- Corrections must cite exact transcript substrings. The model example is
  English; explanations and practice steps have separate EN/TV fields.
- Sample playback uses browser speech synthesis, not an AssemblyAI TTS API.
  Voice availability depends on the browser and OS.
- PCM recordings remain in memory in the current tab; word timestamps,
  transcripts and coaching are stored on the server. Reloading preserves
  results but not audio playback. Audio is sent to AssemblyAI; the transcript
  is sent through the configured Qwen/local model route.
- The current client submits word timings received from AssemblyAI. These
  are suitable for self-study, not verified exam evidence or anti-cheating.

## Validation

    python -m pytest -q tests/integration/test_speaking.py
    python -m scripts.smoke_speaking
    python -m scripts.smoke_speaking --live

The browser check uses PCM capture, a simulated AssemblyAI WebSocket,
live Qwen coaching, two attempts, EN/TV and mobile. It does not establish
AssemblyAI recognition quality. The --live variant uses a synthetic English
WAV at data/benchmarks/speaking-test.wav and the real AssemblyAI service;
it never uses the physical microphone. Both variants delete their test sessions.

References:
- https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket
- https://www.assemblyai.com/docs/streaming/api-spec/generate-streaming-token
