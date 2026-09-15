# SuperCool AI Cinematic Studio — Frontend User Manual

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Project Management](#project-management)
4. [Story Bible](#story-bible)
5. [Shot Timeline](#shot-timeline)
6. [Direction Chat](#direction-chat)
7. [4K Preview & Rendering](#4k-preview--rendering)
8. [QA Monitor](#qa-monitor)
9. [Analytics Dashboard](#analytics-dashboard)
10. [Local Video Analyzer](#local-video-analyzer)
11. [Keyboard Shortcuts](#keyboard-shortcuts)
12. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Access the Application

1. Open your browser and navigate to: **http://localhost:5173**
2. Ensure the backend API is running at http://localhost:8000
3. The interface loads with a dark cinematic theme

### First-Time Setup

1. **Create a Project** — Type a project name in the sidebar and press Enter
2. **Add Characters** — Define characters with traits for consistency
3. **Create Scenes** — Organize your film into scenes
4. **Add Shots** — Describe each shot within scenes
5. **Attach Clips** — Upload your video footage
6. **Render** — Generate the final cinematic edit

---

## Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚡ SUPERCOOL AI CINEMATIC STUDIO              4K | 24fps  🟢  │
├────────────┬────────────────────────┬───────────────────────────┤
│            │                        │                           │
│  STORY     │   DIRECTION CHAT       │   4K PREVIEW              │
│  BIBLE     │                        │                           │
│            │   [Chat messages]      │   [Video player]          │
│  - Project │                        │                           │
│  - Chars   │                        │   [Render controls]       │
│  - Scenes  │                        │                           │
│            │   [Input field]  ➤     │   [Render Final]          │
├────────────┴────────────────────────┴───────────────────────────┤
│  🎬 SHOT TIMELINE                                               │
│  [Upload Clips] [Shot prompt input] +                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ Shot #1 │ │ Shot #2 │ │ Shot #3 │ │ Shot #4 │  ← scroll →   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### Color Scheme

| Element | Color |
|---------|-------|
| Background | #0D0F12 (dark) |
| Panels | #1A1D24 |
| Borders | #2A2F3D |
| Primary accent | #3B82F6 (blue) |
| Success | #10B981 (green) |
| Warning | #F59E0B (amber) |
| Danger | #EF4444 (red) |
| Text primary | #F9FAFB (white) |
| Text secondary | #9CA3AF (gray) |

---

## Project Management

### Create a New Project

1. Locate the **"New project..."** input field at the top of the left sidebar
2. Type your project name (e.g., "My Short Film")
3. Press **Enter** or click the **+** button
4. The project is created and automatically selected

### Switch Projects

1. Click the **"Select project..."** dropdown
2. Select a project from the list
3. The sidebar updates to show that project's characters and scenes

### Project Settings

| Field | Default | Description |
|-------|---------|-------------|
| Title | (required) | Project name |
| Description | (optional) | Brief description |
| Resolution | 4K | Target output resolution |
| FPS | 24 | Frames per second |
| Aspect Ratio | 16:9 | Video aspect ratio |

---

## Story Bible

The Story Bible is the left panel where you manage characters and scenes.

### Tab Navigation

Click between three tabs:

| Tab | Purpose |
|-----|---------|
| **Story Bible** | Manage characters and scenes |
| **QA Monitor** | View shot quality status |
| **Analytics** | Project statistics |

### Characters

#### Create a Character

1. In the **Story Bible** tab, scroll to the **Characters** section
2. Enter a character name in the **"Name"** field
3. (Optional) Enter traits in **"Traits (comma separated)"** field
   - Example: `brave, tall, blue eyes, scar on cheek`
4. Click the **+** button (or the character will auto-create on Enter)

#### Character Traits

Traits ensure consistency across shots. Examples:

| Character | Traits |
|-----------|--------|
| Hero | brave, athletic, dark hair, leather jacket |
| Villain | mysterious, pale, red eyes, black cloak |
| Robot | metallic, glowing eyes, bulky, mechanical |

#### Anchor Faces

Anchor faces are reference images for character consistency.

**Upload a Reference Face:**

1. Click on a **character name** to expand it
2. Click **"+ Upload Reference"** button
3. Select an image file (JPG, PNG)
4. The image appears in the 3-column grid

**Manage Anchor Faces:**

- **View:** Faces appear as small thumbnails under the character
- **Primary:** The first face is marked "Primary" (blue badge)
- **Delete:** Hover over a face image, click the **red trash button** that appears

#### Character Card Layout

```
┌──────────────────────────────────┐
│ Hero                      ▼      │  ← Click to expand
│ [brave] [athletic] [dark hair]   │  ← Trait badges
├──────────────────────────────────┤
│ Anchor Faces                     │
│ ┌─────┐ ┌─────┐ ┌─────┐        │
│ │ 📷  │ │ 📷  │ │ 📷  │        │  ← Face thumbnails
│ │[Pri]│ │     │ │     │        │
│ └─────┘ └─────┘ └─────┘        │
│ [+ Upload Reference]             │  ← Upload button
└──────────────────────────────────┘
```

### Scenes

#### Create a Scene

1. Scroll to the **Scenes** section in the Story Bible
2. Enter a scene title in the **"Scene title"** field
3. Press **Enter** or click the **amber +** button
4. The scene appears with an auto-assigned number (#1, #2, etc.)

#### Select a Scene

1. Click on any **scene button** in the list
2. The scene highlights **blue** when selected
3. The Shot Timeline updates to show shots for this scene

#### Scene Button Layout

```
┌──────────────────────────────────┐
│ #1  Forest Chase - Deep Forest   │  ← Scene button
├──────────────────────────────────┤
│ #2  Final Battle - Ancient Ruins │  ← Scene button (selected = blue)
├──────────────────────────────────┤
│ #3  Escape Sequence - City       │  ← Scene button
└──────────────────────────────────┘
```

---

## Shot Timeline

The Shot Timeline is the bottom panel where you manage individual shots.

### Timeline Header

```
┌─────────────────────────────────────────────────────────────────┐
│ 🎬 Shot Timeline    [Upload Clips]  [Shot prompt...] +         │
└─────────────────────────────────────────────────────────────────┘
```

| Element | Action |
|---------|--------|
| **Upload Clips** | Bulk upload multiple video files to workspace |
| **Shot prompt input** | Type shot description |
| **+ button** | Create the shot |

### Upload Clips (Bulk)

1. Click **"Upload Clips"** button in the timeline header
2. Select one or more video files (MP4, MOV, etc.)
3. Files upload to the workspace
4. A confirmation message appears in the chat

### Create a Shot

1. **Select a scene first** (click a scene in the sidebar)
2. Type a shot description in the **"Shot prompt..."** input
   - Example: `Close-up of hero drawing sword, dramatic lighting`
3. Press **Enter** or click the **green +** button
4. The shot card appears in the timeline

### Shot Cards

Each shot appears as a card in the horizontal timeline:

```
┌────────────────────┐
│ Shot #1        ✓   │  ← Status indicator
│ [Clip]             │  ← Green badge if video attached
│                    │
│ Close-up of hero   │  ← Prompt text (2 lines max)
│ drawing sword...   │
│                    │
│ video_abc123.mp4   │  ← Filename (if attached)
│ [Attach Clip]      │  ← Button (if no video)
└────────────────────┘
```

### Status Indicators

| Icon | Status | Meaning |
|------|--------|---------|
| 🟢 ✓ | APPROVED | Shot passed QA |
| 🟡 ⏳ | PENDING | Awaiting review |
| 🔴 ✗ | REJECTED | Shot failed QA |
| (none) | No status | Not yet rendered |

### Attach a Video Clip to a Shot

1. Find the shot card in the timeline
2. Click **"Attach Clip"** button
3. Select a video file from your computer
4. The file uploads and the shot card updates

### Clip Badge

When a shot has an attached video, a green **[Clip]** badge appears:

```
┌────────────────────┐
│ Shot #1        ⏳  │
│ [Clip]  🎬        │  ← Green badge = has video
│                    │
│ Prompt text here   │
│                    │
│ my_video.mp4       │  ← Filename shown
└────────────────────┘
```

### Scroll the Timeline

- Use **horizontal scroll** (mouse wheel or trackpad) to navigate between shots
- Each card is 192px wide
- Timeline scrolls horizontally when there are many shots

---

## Direction Chat

The Direction Chat is the center-left panel for conversational film direction.

### Chat Interface

```
┌──────────────────────────────────┐
│ 👁 Direction Chat                │
├──────────────────────────────────┤
│                                  │
│ ┌──────────────────────────────┐ │
│ │ 🎬                           │ │  ← Empty state icon
│ │ Start directing your film    │ │
│ │ Type a prompt or upload      │ │
│ │ a script                     │ │
│ └──────────────────────────────┘ │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ Make the first shot more     │ │  ← User message (blue)
│ │ dramatic with rain effects   │ │
│ └──────────────────────────────┘ │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ Processing your request...   │ │  ← System response (gray)
│ └──────────────────────────────┘ │
│                                  │
├──────────────────────────────────┤
│ [Describe your scene...]     ➤  │  ← Input field
└──────────────────────────────────┘
```

### Send a Message

1. Type in the **"Describe your scene..."** input field
2. Press **Enter** or click the **blue send button** (➤)
3. Your message appears in blue
4. A system response appears in gray

### Example Prompts

| Prompt | Purpose |
|--------|---------|
| `Add rain effects to the forest scene` | Request visual effects |
| `Make the dialogue scene slower` | Adjust pacing |
| `Use cold color grading for night shots` | Set color mood |
| `Add tension music building to climax` | Audio direction |

> **Note:** The chat currently stores messages locally. AI-powered responses require backend integration.

---

## 4K Preview & Rendering

The 4K Preview is the center-right panel for viewing rendered output.

### Preview Area

**Before Rendering:**
```
┌──────────────────────────────────┐
│ 🎬 4K Preview                    │
├──────────────────────────────────┤
│                                  │
│         🎬                       │
│   No preview available           │
│   Render a video to preview      │
│                                  │
└──────────────────────────────────┘
```

**After Rendering:**
```
┌──────────────────────────────────┐
│ 🎬 4K Preview                    │
├──────────────────────────────────┤
│ ┌──────────────────────────────┐ │
│ │         ▶                    │ │  ← Video player
│ │    [video playback]          │ │
│ │         ⏸                    │ │
│ └──────────────────────────────┘ │
│                                  │
│ Engine: Auto-Route               │
│ Resolution: 4K                   │
│ FPS: 24                          │
│ IP-Adapter: 0.85                 │
│                                  │
│ [Render Final (5 clips)]         │  ← Render button
│                                  │
│ Mood: cinematic                  │  ← Render results
│ Duration: 45.2s                  │
│ Shots: 5                         │
│ [View Output]                    │
└──────────────────────────────────┘
```

### Render Controls

| Setting | Value | Description |
|---------|-------|-------------|
| Engine | Auto-Route | AI selects best engine |
| Resolution | 4K | Output resolution |
| FPS | 24 | Frames per second |
| IP-Adapter | 0.85 | Style consistency |

### Render Final Video

1. Ensure at least one shot has an **attached video clip**
2. Click the **"Render Final (N clips)"** button
   - N = number of shots with clips
3. Wait for rendering (button shows spinner)
4. The rendered video appears in the preview player
5. Click **▶** to play

### Render Button States

| State | Appearance | Action |
|-------|------------|--------|
| Ready | Indigo background, "Render Final (N clips)" | Click to render |
| Disabled | Gray, no clips attached | Attach clips first |
| Rendering | Dark gray, spinner, "Rendering..." | Wait for completion |

### View Output

After rendering completes:

1. Render metadata appears:
   - **Mood** — Detected scene mood
   - **Duration** — Total length in seconds
   - **Shots** — Number of shots merged
2. Click **"View Output"** to open the workspace folder in a new browser tab

### Video Player Controls

| Control | Function |
|---------|----------|
| ▶ / ⏸ | Play / Pause |
| ◀◀ / ▶▶ | Rewind / Forward |
| Volume | Adjust audio |
| Fullscreen | Expand to fill screen |
| Timeline | Scrub through video |

---

## QA Monitor

The QA Monitor shows the quality status of all shots.

### Access QA Monitor

1. Click the **"QA Monitor"** tab in the left sidebar

### View

```
┌──────────────────────────────────┐
│ QA Monitor                       │
├──────────────────────────────────┤
│                                  │
│ Shot #1  ✓  Close-up of hero... │  ← APPROVED (green)
│                                  │
│ Shot #2  ⏳ Forest chase...     │  ← PENDING (yellow)
│                                  │
│ Shot #3  ✗ Final battle...      │  ← REJECTED (red)
│                                  │
│ Shot #4  ⏳ Escape sequence...  │  ← PENDING (yellow)
│                                  │
└──────────────────────────────────┘
```

### Status Meanings

| Status | Icon | Meaning |
|--------|------|---------|
| APPROVED | ✓ Green | Shot meets quality standards |
| PENDING | ⏳ Yellow | Awaiting review or rendering |
| REJECTED | ✗ Red | Shot needs revision |

### Empty State

If no shots have been rendered yet:
```
No QA data yet
```

---

## Analytics Dashboard

The Analytics tab shows project-level statistics.

### Access Analytics

1. Click the **"Analytics"** tab in the left sidebar

### Dashboard

```
┌──────────────────────────────────┐
│ Analytics                        │
├──────────────────────────────────┤
│ ┌─────────────┬─────────────┐    │
│ │     3       │     12      │    │
│ │   Scenes    │    Shots    │    │
│ └─────────────┴─────────────┘    │
│ ┌─────────────┬─────────────┐    │
│ │     5       │     0       │    │
│ │ Characters  │  Rendered   │    │
│ └─────────────┴─────────────┘    │
└──────────────────────────────────┘
```

### Metrics

| Metric | Description |
|--------|-------------|
| **Scenes** | Total number of scenes in the project |
| **Shots** | Total number of shots across all scenes |
| **Characters** | Total number of defined characters |
| **Rendered** | Number of shots that have been rendered |

---

## Keyboard Shortcuts

| Location | Key | Action |
|----------|-----|--------|
| New project input | **Enter** | Create project |
| Scene title input | **Enter** | Create scene |
| Shot prompt input | **Enter** | Create shot |
| Chat input | **Enter** | Send message |
| Timeline | **Scroll** | Navigate shots horizontally |

---

## Complete Workflow Example

### Creating a Short Film

#### Step 1: Create Project
```
Input: "Rainforest Rescue"
→ Project created and selected
```

#### Step 2: Add Characters
```
Name: "Sasuke"
Traits: "brave, ninja, dark hair, sword master"
→ Character created

Name: "Boruto"
Traits: "young, determined, headband"
→ Character created
```

#### Step 3: Create Scene
```
Title: "The Rescue"
→ Scene #1 created
```

#### Step 4: Add Shots
```
Shot 1: "Vertical camera plunge through rainforest canopy"
Shot 2: "Sasuke draws sword with electrical arcs"  
Shot 3: "Over-shoulder MCU, Sasuke extends sword"
Shot 4: "Close-up profile, dialogue scene"
Shot 5: "Macro push toward headband"
→ 5 shots created in timeline
```

#### Step 5: Attach Video Clips
```
Click "Attach Clip" on Shot #1 → Select canopy_plunge.mp4
Click "Attach Clip" on Shot #2 → Select sword_draw.mp4
Click "Attach Clip" on Shot #3 → Select handoff.mp4
Click "Attach Clip" on Shot #4 → Select dialogue.mp4
Click "Attach Clip" on Shot #5 → Select headband.mp4
→ All shots now have [Clip] badges
```

#### Step 6: Render
```
Click "Render Final (5 clips)"
→ Wait for rendering...
→ Video appears in preview
→ Click ▶ to play
```

#### Step 7: Review
```
Click "QA Monitor" tab
→ Review shot statuses
→ Approve or reject shots
```

---

## Troubleshooting

### Common Issues

**1. "No preview available" after rendering**
- Ensure the backend API is running at localhost:8000
- Check that the render completed successfully
- Verify the output file exists in workspace/pipeline_output/

**2. Shots not appearing in timeline**
- Ensure a scene is selected (click a scene in the sidebar)
- Check that the API is running

**3. Upload fails silently**
- Check file size (videos should be under 200MB)
- Verify the backend API is running
- Check browser console for errors (F12)

**4. Render button is disabled**
- At least one shot must have an attached video clip
- Check that shots have video_path values

**5. Chat messages not getting AI responses**
- The chat is currently a local stub
- AI-powered responses require backend integration

### Error Handling

The frontend handles errors silently. If something fails:
- The UI simply does not update
- No error messages are displayed
- Try refreshing the page (F5)

### Browser Requirements

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |

### Performance Tips

- Keep videos under 100MB for faster uploads
- Use H.264 codec for best compatibility
- Close other browser tabs during rendering
- Use a wired connection for large file transfers

---

## Data Structures Reference

### Project
```typescript
{
  id: string;
  title: string;
  description: string | null;
  target_resolution: string;  // "4K"
  fps: number;                // 24
  aspect_ratio: string;       // "16:9"
  created_at: string;         // ISO timestamp
}
```

### Character
```typescript
{
  id: string;
  project_id: string;
  name: string;
  biography: string | null;
  locked_traits: string[];    // ["brave", "tall"]
  voice_profile_id: string | null;
}
```

### Scene
```typescript
{
  id: string;
  project_id: string;
  scene_number: number;
  title: string | null;
  location: string | null;
  time_of_day: string | null;
  summary: string | null;
}
```

### Shot
```typescript
{
  id: string;
  scene_id: string;
  shot_number: number;
  shot_type: string | null;
  motion_type: string | null;
  assigned_engine: string | null;
  prompt_text: string;
  injected_prompt: string | null;
  dialogue_text: string | null;
  video_path: string | null;   // Path to attached video
  status: string;              // "PENDING" | "APPROVED" | "REJECTED"
}
```

### Render Result
```typescript
{
  final_output: string;       // Path to final video
  video_only: string;         // Path to video without audio
  duration: number;           // Seconds
  shots: number;              // Number of shots
  mood: string;               // "cinematic" | "dramatic" | etc.
  music_crescendo: boolean;
}
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Shot** | A single continuous video clip |
| **Scene** | A group of related shots |
| **Project** | Top-level container for a film |
| **Character** | A person/role in the film |
| **Anchor Face** | Reference image for character consistency |
| **Locked Traits** | Consistent character attributes |
| **Creative Pipeline** | AI editing workflow |
| **Director AI** | AI that makes creative decisions |
| **Color Grade** | Visual color treatment applied to video |
| **Transition** | Effect between shots (cut, fade, etc.) |
| **Render** | Process of combining clips into final output |
| **Workspace** | Folder where clips and outputs are stored |
| **Local Analyzer** | Open-source AI models for local video analysis |
| **CLIP** | Model for shot-to-reference similarity scoring |
| **Florence** | Model for object detection and captioning |
| **Qwen2-VL** | Model for narrative/creative analysis |
| **Story Bible** | Reference images for storyboard comparison |

---

## Local Video Analyzer

### What Is It?

The Local Video Analyzer uses open-source AI models running on your machine (not the cloud) to analyze shots for quality and creative consistency. It runs **locally first** and falls back to cloud APIs only when needed.

### How It Works

1. **Keyframe Extraction:** Extracts 1 frame per second from your video
2. **Layer 1 (GPU):** CLIP compares shots against reference images; Florence detects objects
3. **Layer 2 (CPU):** Qwen2-VL analyzes lighting, costume, mood in natural language
4. **Decision:** Shot is APPROVED, RE-RENDER_REQUIRED, or ADJUST_COLOR
5. **Fallback:** If local analysis is weak, NEMOTRON (cloud) is used

### Setup

```bash
# Install dependencies
pip install torch torchvision transformers pillow opencv-python httpx

# Install Ollama for Qwen2-VL
ollama pull qwen2.5-vl:2b
```

### Using the CLI

```bash
# Analyze a single shot
python workspace/analizador_video_qwen2_vl.py workspace/shots/shot1.mp4

# With reference image (Story Bible)
python workspace/analizador_video_qwen2_vl.py workspace/shots/shot1.mp4 \
  --reference workspace/references/shot1.jpg

# Save results to JSON
python workspace/analizador_video_qwen2_vl.py workspace/shots/shot1.mp4 \
  --output analysis.json
```

### Adding Reference Images

Place reference images in `workspace/references/` named after your shot:

```
workspace/references/
├── shot1.jpg    # Reference for shot1.mp4
├── shot2.png    # Reference for shot2.mp4
└── ...
```

If no reference is provided, the system uses the first frame of the clip as reference.

### Configuration

In `.env`:

```env
SUPERCOOL_LOCAL_MODELS_ENABLED=true
SUPERCOOL_CLIP_THRESHOLD_DIALOGUE=0.78
SUPERCOOL_CLIP_THRESHOLD_ACTION=0.70
SUPERCOOL_QWEN_BACKEND=auto
```

### Output States

| State | Meaning |
|-------|---------|
| `APPROVED_FOR_EDIT` | Shot passes quality check |
| `RE-RENDER_REQUIRED` | Shot needs re-rendering (low similarity) |
| `ADJUST_COLOR` | Color grading adjustment needed |
| `NEEDS_ANALYSIS` | No video or models unavailable |

---

*SuperCool AI Cinematic Studio — Frontend User Manual v1.0*
