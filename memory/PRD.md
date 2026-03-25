# AgentZZ - Product Requirements Document

## Original Problem Statement
Comprehensive, mobile-first, no-code SaaS platform "AgentZZ" for deploying AI agents on social media. Features Directed Studio Mode for AI video production with Pipeline v5 and Continuity Engine v2 (Keyframe-First).

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB
- **AI Stack**: Claude Sonnet (text/vision), Sora 2 (video), Gemini (images/keyframes), ElevenLabs (multilingual voice)

## Continuity Engine v2 — Keyframe-First Pipeline (CURRENT)

### Problem
Sora 2 has a strong visual bias: desert/tent scenes → camels, regardless of text prompts. Even with explicit "LION" instructions and Style DNA blocks, Sora 2 generates camels in ~40% of scenes.

### Solution: Keyframe-First
1. Before each scene, generate a **reference keyframe image** using Gemini (`gemini-3.1-flash-image-preview` via Emergent LLM Key)
2. The keyframe contains the CORRECT characters (species, clothing, age) in the correct art style
3. This keyframe is passed as `image_path` to Sora 2, which animates from it
4. If keyframe fails, retry 3 times before falling back to avatar composite

### Architecture
```
PRE-PRODUCTION:
  1. Avatar Analysis (Claude Vision) → character descriptions
  2. Production Design Bible (Claude) → style anchors, color palette
  3. Scene Directors (Claude, parallel) → Sora prompts

PRODUCTION (Continuity Mode):
  For each scene (SEQUENTIAL):
    1. Generate Keyframe Image (Gemini) ← NEW
    2. Render Video (Sora 2, using keyframe as reference)
    3. Upload to Supabase Storage

POST-PRODUCTION:
  1. Narration scripts (Claude)
  2. Voice synthesis (ElevenLabs, ISO 639-1 codes)
  3. Music segmentation
  4. Color grading + extended crossfades (1.5s, FFmpeg)
  5. Final mix + upload
```

### Test Results Comparison

**Scene 1 (Night/Stars):**
| Version | Species | Style | Quality |
|---------|---------|-------|---------|
| v1 (no keyframe) | Lion ✅ | 3D ✅ | 9/10 |
| v3 (keyframe) | Lion ✅ | 3D ✅ | 9/10 |

**Scene 2 (Tent/Birth):**
| Version | Species | Style | Quality |
|---------|---------|-------|---------|
| v1 (no keyframe) | Camels ❌ | 2D ❌ | 4/10 |
| v3 (keyframe failed) | Camels ❌ | 2D ❌ | 4/10 |

**Scene 3 (Field/Teaching):**
| Version | Species | Style | Quality |
|---------|---------|-------|---------|
| v1 (no keyframe) | Lion+Camel ⚠️ | 3D ✅ | 7/10 |
| v3 (keyframe) | Lions ✅ | 3D ✅ | 9/10 |

### Known Limitation
Scene 2 keyframe failed silently during v3 test. Fix: 3-retry logic now implemented. The Sora 2 tent/desert bias remains the hardest to overcome — may require generating keyframes with explicit visual anchoring.

## Bug Fixes
- **ElevenLabs Language Codes**: Fixed `pt-BR` → `pt` (ISO 639-1) for `eleven_multilingual_v2`
- **Python Lint**: All 27 errors in studio.py fixed
- **RegenSceneRequest**: Removed redundant `scene_number` from body

## Key Files
- `/app/backend/routers/studio.py` — Pipeline + continuity engine + keyframe gen + post-prod
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI + continuity toggle
- `/app/frontend/src/components/PostProduction.jsx` — Audio + localization + subtitles UI

## Upcoming Tasks
- **P0**: Fix Scene 2 consistency — ensure keyframe generates reliably for all scenes
- **P1**: Refactor `studio.py` (3600+ lines) → `core/media.py`
- **P1**: Refactor `DirectedStudio.jsx` (1750+ lines) → smaller components
- **P2**: Phase 8 Omnichannel Integrations
- **P3**: Admin Dashboard & Stripe

## Credentials
- Test: test@agentflow.com / password123
