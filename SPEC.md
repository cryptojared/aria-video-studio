# Aria Video Studio — Technical Specification

## Overview

**Project Name:** Aria Video Studio  
**Type:** AI-Powered Video Editing SaaS  
**Core Functionality:** Zero-click video editor that automatically edits user-provided talking head and B-roll clips into polished, publish-ready videos  
**Target Users:** UGC creators, founders, marketers who want professional edits without manual editing skills

---

## 1. Data Models

### 1.1 Project

```python
class VideoProject:
    id: str              # UUID
    user_id: str         # Owner
    name: str            # "Q3 Product Launch"
    status: str          # draft/processing/completed/error
    
    # Input clips
    talking_heads: list[Clip]      # Required
    broll_clips: list[Clip]       # Optional
    
    # Settings
    style_preset: str             # cinematic/warm/corporate/custom
    custom_lut: str | None       # .cube file path
    instructions: str | None      # "Fast-paced, upbeat music"
    
    # Output
    rendered_video_url: str | None
    shorts: list[str]             # URLs for vertical clips
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
```

### 1.2 Clip

```python
class Clip:
    id: str
    project_id: str
    type: str            # talking_head | broll
    
    file_url: str        # Supabase Storage URL
    duration: float      # seconds
    thumbnail_url: str
    
    # For B-roll only
    analysis: dict | None  # GPT-4o vision results
    embeddings: list[float] | None
    
    created_at: datetime
```

### 1.3 RenderJob

```python
class RenderJob:
    id: str
    project_id: str
    type: str            # full_video | short | adjustment
    
    # Adjustment details (for re-renders)
    adjustment_type: str | None   # pace/broll/lut/effect
    adjustment_params: dict | None
    
    status: str          # queued/processing/completed/failed
    progress: float     # 0.0 - 1.0
    
    output_url: str | None
    error_message: str | None
    
    started_at: datetime
    completed_at: datetime | None
```

---

## 2. API Endpoints

### 2.1 Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/projects | Create new project |
| GET | /api/projects | List user's projects |
| GET | /api/projects/{id} | Get project details |
| PUT | /api/projects/{id} | Update project settings |
| DELETE | /api/projects/{id} | Delete project |

### 2.2 Clips

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/projects/{id}/clips | Upload clip |
| DELETE | /api/clips/{id} | Remove clip |
| POST | /api/clips/{id}/analyze | Run GPT-4o vision analysis |

### 2.3 Rendering

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/projects/{id}/render | Start render |
| GET | /api/render/{id} | Check render status |
| POST | /api/render/{id}/adjust | Request adjustment |

### 2.4 Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/projects/{id}/chat | Send adjustment request |

---

## 3. AI Pipeline

### 3.1 Transcription (Stage 1)

**Model:** Whisper (local)  
**Input:** Talking head video files  
**Output:**
```json
{
  "words": [
    {"text": "hello", "start": 0.5, "end": 0.8, "speaker": "speaker_0"},
    {"text": "everyone", "start": 0.9, "end": 1.2, "speaker": "speaker_0"}
  ],
  "events": [
    {"type": "laugh", "start": 5.2, "end": 5.8}
  ],
  "duration": 180.5
}
```

### 3.2 B-Roll Analysis (Stage 2)

**Model:** GPT-4o Vision  
**Input:** B-roll video clip  
**Process:**
1. Extract keyframes every 2 seconds
2. Send frames to GPT-4o with prompt: "Describe what you see in this clip"
3. Store text description + embeddings

**Output:**
```json
{
  "clip_id": "xxx",
  "description": "urban city skyline at night with lit buildings",
  "tags": ["city", "business", "downtown", "night", "buildings"],
  "mood": "professional",
  "best_for": ["business success", "growth", "city life"]
}
```

### 3.3 Smart Editing (Stage 3)

**Model:** GPT-4 (text)  
**Input:** Transcript + B-roll analysis  
**Process:**
1. Identify dead space segments
2. Determine clip ordering
3. Match B-roll to transcript segments
4. Select camera effects
5. Choose LUT

**Output:**
```json
{
  "segments": [
    {
      "type": "talking_head",
      "source_clip_id": "th_1",
      "start": 0,
      "end": 15.2,
      "adjustments": {"remove_filler": true}
    },
    {
      "type": "broll",
      "source_clip_id": "broll_1",
      "start": 3.5,
      "end": 6.0,
      "trigger_word": "business",
      "effect": "zoom_in"
    }
  ],
  "lut": "cinematic",
  "transitions": ["fade", "cut", "fade"]
}
```

---

## 4. FFmpeg Pipeline

### 4.1 Dead Space Removal

```bash
# Detect silence
ffmpeg -i input.mp4 -af "silencedetect=noise=-40dB:d=1.2" -f null -

# Cut segments
ffmpeg -i input.mp4 -af "atrim=start:end,asetpts=PTS-STARTPTS" ...
```

### 4.2 LUT Application

```bash
# Apply .cube LUT
ffmpeg -i input.mp4 -vf "lut3d=file=cinematic.cube" output.mp4
```

### 4.3 Camera Effects

```bash
# Zoom in
ffmpeg -i input.mp4 -vf "zoompan=z='min(1.25,1+0.25*(t/3))':d=3:s=1920x1080" output.mp4

# Ken Burns (still image)
python zoom_still.py in.png out.mp4 5 --rate 0.015
```

### 4.4 Final Render

```bash
# Concatenate with transitions
ffmpeg -f concat -safe 0 -i segments.txt -c copy output.mp4

# Normalize audio
ffmpeg -i output.mp4 -af "loudnorm=I=-14:TP=-1.5:LRA=11" final.mp4
```

---

## 5. Style Presets

### 5.1 Cinematic
- LUT: Film look (orange-teal)
- Zoom: subtle (1.0 → 1.1)
- Transitions: smooth fade (500ms)
- Captions: auto, highlight pain/money words

### 5.2 Warm VLOG
- LUT: Warm golden hour
- Zoom: minimal
- Transitions: quick cut (200ms)
- Captions: on by default

### 5.3 Corporate
- LUT: Clean, neutral
- Pan: subtle
- Transitions: direct cut
- Captions: on by default

### 5.4 Custom
- User uploads .cube file
- Adjustable intensity (0-100%)
- Custom effect parameters

---

## 6. Conversational Interface

### 6.1 Adjustment Types

| Command | AI Action |
|---------|-----------|
| "Make it faster" | Reduce pauses by 30%, add quick cuts |
| "Add more B-roll" | Find additional matching segments |
| "Change the B-roll at 0:45" | Remove, find alternative, re-insert |
| "Add zoom at [timestamp]" | Add push-in effect |
| "Use warm LUT" | Switch LUT, re-render |
| "Remove music" | Strip audio track |

### 6.2 Selective Re-render

Instead of full re-render, identify affected segments:
1. Parse adjustment request
2. Identify changed timestamps
3. Re-render only affected segments
4. Concatenate with unchanged segments

---

## 7. Storage Architecture

### 7.1 Supabase Storage Buckets

| Bucket | Purpose | Access |
|--------|---------|--------|
| projects | Source clips | Private (owner only) |
| renders | Output videos | Private (owner only) |
| thumbnails | Preview images | Public |
| luts | Custom .cube files | Private |

### 7.2 Database Tables

- `projects` — Project metadata
- `clips` — Clip records + analysis
- `render_jobs` — Render queue + status
- `style_presets` — User-created presets

---

## 8. Security

### 8.1 Authentication
- Supabase Auth (Google OAuth)
- JWT tokens for API access

### 8.2 Authorization
- RLS on all tables (owner only)
- Storage policies per bucket

### 8.3 API Keys
- OpenAI: User-provided or platform-provided
- No keys in client-side code

---

## 9. Pricing Model

### 9.1 Subscription Tiers

| Feature | Free | Pro ($19/mo) | Enterprise ($49/mo) |
|---------|------|--------------|-------------------|
| Videos/month | 2 | Unlimited | Unlimited |
| Max duration | 5 min | 30 min | 60 min |
| B-roll library | 10 clips | 100 clips | Unlimited |
| Custom LUTs | ❌ | ✅ | ✅ |
| Priority render | ❌ | ❌ | ✅ |
| API access | ❌ | ❌ | ✅ |

---

## 10. Dependencies

### 10.1 Python Packages
```txt
ffmpeg-python==0.2.0
moviepy==1.0.3
openai==1.12.0
whisper==20231117
numpy==1.26.0
pillow==10.2.0
supabase==2.3.4
python-dotenv==1.0.0
```

### 10.2 External Services
- OpenAI API (GPT-4o Vision)
- Supabase (Auth, DB, Storage)
- FFmpeg (system install)

---

*Last updated: 2026-10-06*
