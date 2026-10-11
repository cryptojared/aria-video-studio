# Aria Video Studio — Launch Checklist

## Pre-Launch

- [ ] Clone/fork base repo: `github.com/EverythingAI-Pro/ai-video-editor`
- [ ] Set up Python 3.12+ environment
- [ ] Install FFmpeg: `brew install ffmpeg`
- [ ] Configure OpenAI API key
- [ ] Set up Supabase project (Auth, DB, Storage)

## MVP Build

- [ ] Phase 1: Multi-clip upload + Whisper transcription
- [ ] Phase 2: GPT-4o Vision B-roll analysis
- [ ] Phase 3: LUTs + camera effects
- [ ] Phase 4: Conversational adjustments

## Launch Requirements

- [ ] Supabase storage buckets configured
- [ ] Payment integration (Stripe)
- [ ] User authentication flow
- [ ] Video processing queue (Celery/Redis or cloud workers)
- [ ] CDN for video delivery

## Post-Launch

- [ ] Monitor OpenAI API costs
- [ ] Optimize FFmpeg render times
- [ ] Add more LUT presets
- [ ] Implement vertical video (9:16) support

---

*Last updated: 2026-10-06*
