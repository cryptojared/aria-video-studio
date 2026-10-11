# Aria Video Studio — MVP Roadmap

## Overview

**Goal:** Build the FIRST AI video editor that fully automates editing USER'S footage (not AI-generated like Pexo)  
**Timeline:** 8 weeks  
**Status:** Planning phase

---

## 📋 Phase Checklist

### Phase 1: CORE (Week 1-2)
- [ ] Multi-clip upload functionality
- [ ] Whisper transcription integration
- [ ] Dead space removal (FFmpeg silence detection)
- [ ] Basic clip concatenation
- [ ] Simple fade transitions

### Phase 2: SMART (Week 3-4)
- [ ] GPT-4o Vision B-roll analysis
- [ ] Semantic matching (transcript → B-roll)
- [ ] Auto-placement at logical points
- [ ] First "generate" pass

### Phase 3: CINEMATIC (Week 5-6)
- [ ] LUT support (.cube files)
- [ ] Camera effects (zoom/pan via FFmpeg)
- [ ] Style presets
- [ ] Preview player

### Phase 4: CONVERSATIONAL (Week 7-8)
- [ ] Chat interface for adjustments
- [ ] Selective re-render (timestamp-accurate)
- [ ] Undo/redo operations
- [ ] Final polish

---

## 🎯 Phase 1: CORE (Week 1-2)

### Week 1: Foundation

#### Day 1-2: Project Setup
- [ ] Initialize project repository
- [ ] Set up Python virtual environment
- [ ] Install FFmpeg
- [ ] Configure Supabase project
- [ ] Create storage buckets

#### Day 3-4: Multi-Clip Upload
- [ ] Build drag-drop upload UI
- [ ] Implement chunked file upload to Supabase
- [ ] Create clip metadata database
- [ ] Add video duration extraction
- [ ] Generate thumbnails

#### Day 5-7: Transcription Pipeline
- [ ] Integrate Whisper for local transcription
- [ ] Implement word-level timestamp extraction
- [ ] Speaker diarization (if multiple speakers)
- [ ] Audio event detection (laughs, pauses)
- [ ] Store transcript in normalized JSON format

### Week 2: Basic Editing

#### Day 8-10: Dead Space Removal
- [ ] FFmpeg silence detection
- [ ] Filler word identification (um, uh, like, you know)
- [ ] Natural pause detection
- [ ] Clip trimming logic

#### Day 11-14: Concatenation
- [ ] Order clips by user preference or energy
- [ ] Implement fade transitions
- [ ] Basic FFmpeg concat pipeline
- [ ] Output MP4 export

---

## 🧠 Phase 2: SMART (Week 3-4)

### Week 3: AI B-Roll Analysis

#### Day 15-17: GPT-4o Vision Integration
- [ ] Set up OpenAI API connection
- [ ] Extract keyframes from B-roll (every 2 seconds)
- [ ] Send frames to GPT-4o for analysis
- [ ] Parse and store descriptions
- [ ] Generate embeddings for semantic matching

#### Day 18-21: Semantic Matching
- [ ] Build matching algorithm
- [ ] Match transcript segments to B-roll
- [ ] Handle "no match" fallback
- [ ] Confidence scoring

### Week 4: Auto-Placement

#### Day 22-25: Smart Placement
- [ ] Determine placement timestamps
- [ ] Handle transitions intelligently
- [ ] Preserve speaking segments
- [ ] Add cutaway logic

#### Day 26-28: First Generate Pass
- [ ] End-to-end pipeline test
- [ ] Error handling
- [ ] Progress reporting
- [ ] Output validation

---

## 🎬 Phase 3: CINEMATIC (Week 5-6)

### Week 5: LUTs & Color

#### Day 29-31: LUT Support
- [ ] .cube file parser
- [ ] FFmpeg lut3d integration
- [ ] Built-in preset LUTs:
  - [ ] Cinematic (orange-teal)
  - [ ] Warm (golden hour)
  - [ ] Corporate (clean)
  - [ ] Cool (blue-tinted)
- [ ] Custom LUT upload

#### Day 32-35: Color Grading
- [ ] Auto color matching across clips
- [ ] White balance correction
- [ ] Contrast/saturation adjustments
- [ ] Preview before/after

### Week 6: Camera Effects

#### Day 36-39: Zoom/Pan Effects
- [ ] Zoom in (emphasis)
- [ ] Zoom out (reveal)
- [ ] Pan left/right
- [ ] Push in / pull out
- [ ] Ken Burns for still images

#### Day 40-42: Preview Player
- [ ] Video player component
- [ ] Frame-accurate seeking
- [ ] Effect preview
- [ ] Export quality selection

---

## 💬 Phase 4: CONVERSATIONAL (Week 7-8)

### Week 7: Chat Interface

#### Day 43-46: Adjustment Commands
- [ ] Parse natural language requests
- [ ] Pace adjustments ("faster", "slower")
- [ ] B-roll changes ("change at 0:45")
- [ ] Effect additions ("add zoom")

#### Day 47-49: Selective Re-render
- [ ] Identify affected segments
- [ ] Partial re-render logic
- [ ] Concatenation with unchanged
- [ ] Progress tracking

### Week 8: Polish

#### Day 50-53: Undo/Redo
- [ ] Action history
- [ ] State restoration
- [ ] Multiple undo levels

#### Day 54-56: Final Testing
- [ ] End-to-end user flows
- [ ] Error handling
- [ ] Performance optimization
- [ ] Beta testing

#### Day 57-58: Launch Prep
- [ ] Documentation
- [ ] Marketing materials
- [ ] Pricing page
- [ ] Onboarding flow

---

## 📊 Milestones

| Milestone | Target | Deliverable |
|-----------|--------|-------------|
| M1: Basic Upload | Week 1 | Can upload multiple clips |
| M2: First Edit | Week 2 | Dead space removed, clips concatenated |
| M3: Smart B-Roll | Week 4 | AI matches B-roll to transcript |
| M4: Cinematic | Week 6 | LUTs + effects working |
| M5: Conversational | Week 7 | Chat adjustments work |
| M6: Beta Launch | Week 8 | Functional beta |

---

## 🔄 Dependencies

```
Week 1 ─────► Week 2 ─────► Week 3 ─────► Week 4 ─────► Week 5 ─────► Week 6 ─────► Week 7 ─────► Week 8
   │              │              │              │              │              │              │              │
   ▼              ▼              ▼              ▼              ▼              ▼              ▼              ▼
Setup         Upload         Transcribe    B-Roll AI     LUTs &       Effects       Chat          Launch
             + Thumbs       + Dead Space   Analysis       Color        + Preview     Adjustments   Prep
```

---

## 🛠️ Technical Prerequisites

Before starting, ensure:
- [ ] Python 3.12+ installed
- [ ] FFmpeg installed (`brew install ffmpeg`)
- [ ] Supabase project created
- [ ] OpenAI API key available
- [ ] GitHub repository initialized

---

## 📝 Notes

- MVP focuses on horizontal video (16:9) first
- Vertical (9:16) support in later phase
- Start with local processing, add cloud workers later
- Prioritize reliability over features

---

*Last updated: 2026-10-06*
