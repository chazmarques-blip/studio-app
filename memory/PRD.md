# Agents - PRD (Product Requirements Document)

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying AI agents on social channels. Key feature: AI Marketing Studio with avatar generation, campaign creation, and multi-format video with AI avatars.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- AI Pipeline: 8 specialized agents for campaign creation
- Video: Sora 2 + FFmpeg cinematic audio
- Storage: Supabase Storage

## Completed - March 20, 2026

### Critical Audio Pipeline Fix
- **Sidechain inverted**: `[narr][music]sidechaincompress` → `[music][narr_sc]sidechaincompress` with `asplit`
- **-shortest flag**: Replaced with `-t {duration}` for exact video length (24.2s)
- **apad=pad_dur**: Fixed to `apad=whole_dur` for correct padding
- **Loudness normalization**: Added `loudnorm=I=-14:TP=-1:LRA=7` for broadcast-quality audio
- **Stereo output**: Added `-ac 2` for stereo (was mono)
- **Result**: Volume +6.5dB (from -24.8dB to -18.3dB mean), stereo 256kb/s, 96kHz

### Avatar URL Fix
- Corrected broken avatar URL (404) in campaigns and pipelines
- Superhero avatar now loads correctly in gallery and campaign detail

### Avatar in Campaign Assets (from earlier)
- Avatar displayed in CampaignCard, CampaignDetail, GlobalArtGallery
- Lightbox modal with Copy/Download buttons
- Testing: 12/12 passed

## Backlog
### P1
- [ ] Audio Preview in Dylan step
- [ ] Refactor PipelineView.jsx
### P2
- [ ] HeyGen avatars, CRM Kanban, Login Social
### P3
- [ ] Omnichannel, Admin, Payment, Legal

## Credentials
- Email: test@agentflow.com / Password: password123
