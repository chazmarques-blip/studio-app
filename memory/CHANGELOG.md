# StudioX Changelog

## 2026-04-18 (Session 4)

### Sora 2 Character Voice Lock (NEW)
- **Problem**: Sora 2 generates a different voice for each scene even for the same character (stochastic sampling).
- **Solution**: Integrated OpenAI's official Sora 2 Characters API (`POST /v1/sora/characters`) that creates a reusable `character_id` from an anchor scene. Reusing the ID in subsequent generations locks **voice + appearance** natively.
- New module: `/app/backend/routers/studio/sora_characters.py`
- Auto-detects first rendered scene per character to use as voice anchor.
- Supports Sora 2 2-character-per-generation limit (March 2026).
- Endpoints:
  - `POST /api/studio/projects/{id}/auto-register-sora-characters` (auto, idempotent)
  - `POST /api/studio/projects/{id}/register-sora-character` (manual with specific scene)
  - `GET  /api/studio/projects/{id}/sora-characters`
  - `DELETE /api/studio/projects/{id}/sora-characters/{character_name}`
- `production.py`: `_generate_video_with_openai_direct` and `_generate_video_unified` accept optional `sora_character_ids`. Character lookup is per-scene from `project.characters[].sora_character_id`.
- **Backward compatible**: zero impact on existing/in-flight projects (fallback is empty list → payload identical to before).
- UI: "🎤 Travar Vozes" button on the Vídeos tab of `DirectedStudio.jsx` + badge showing locked characters count.


## 2026-04-17 (Session 3)

### ElevenLabs Music - Children's Song Generator
- Integrated ElevenLabs Music API (`client.music.compose()`) for generating original children's songs
- LLM (Claude) generates lyrics based on story briefing + scenes + characters
- Music style adapts to age range: 0-3 (lullaby), 3-5 (Galinha Pintadinha), 5-8 (Disney Junior), 8-12 (Disney/Pixar)
- Lyrics in project language (Portuguese by default)
- Endpoint: `POST /api/studio/projects/{id}/generate-music`
- UI card "Música Cantada" added to RESULTADO tab with lyrics display
- Song saved to project as `generated_song` field

### Film Rebuild for Large Projects
- Fixed: Previous rebuild of 26 scenes crashed silently (FFmpeg crossfade memory exhaustion)
- Reduced crossfade scene limit: 30 → 15 scenes
- V2A sonoplastia now non-blocking in rebuild
- Successfully rebuilt "Jonas e o Peixe Grande" (32 scenes, 276MB → 17MB)

### Folder System Improvements
- Fixed: Delete folder button not working (replaced `window.confirm` with inline two-click)
- Fixed: Stale avatar IDs auto-cleanup was deleting valid avatars (REMOVED auto-cleanup)
- Hierarchical folders: parent_id support with expand/collapse (no modal reload)
- Compact sidebar: smaller fonts, narrower width
- Chevron arrow moved after folder name for alignment
- `useTransition` for smooth folder switching (no flash)
- New endpoint: `PUT /api/folders/bulk-update` for atomic folder operations
- New endpoint: `PUT /api/folders/update-avatars` for replacing folder avatar IDs

### Audio Pipeline Upgraded (Sora 2)
- Primary: ElevenLabs Music generates original soundtrack matching story
- Fallback: Kling V2A for BGM + SFX if ElevenLabs fails
- Mix: native Sora 2 audio (100%) + music (15% volume)

## 2026-04-15 (Session 2)
[... previous entries unchanged ...]
