---
name: upwork-proposal
description: Write Upwork job application proposals/cover letters. Use when the user shares an Upwork job posting, mentions applying to Upwork jobs, provides a Loom video transcript, or needs help writing a proposal for freelance work.
---

# Upwork Proposal Writer

## When to Use
- User shares an Upwork job posting
- User provides a Loom video transcript
- User asks for help with a job application or proposal

## Workflow

1. **You record a Loom video FIRST** showing how you'd solve the project
2. **You provide:** Job posting + video transcript
3. **Claude writes:** Proposal that references and summarizes what's shown in the video

This is a genuinely proven workflow, keep it as-is: recording yourself solving the actual problem
gives the proposal real technical specifics to draw on, and that's exactly what keeps it from
reading as generic. A proposal written without the video tends to fall back on vague claims — the
video is what earns the specificity.

## Required Inputs

1. **Job Posting** - The Upwork job description
2. **Loom Video Link** - URL to the personalized demo video
3. **Loom Video Transcript** - Transcript of the video showing:
   - How you'd approach/solve the specific project
   - Demo of similar past work or live walkthrough
   - Relevant skills and tools

---

## Your Background

Read the user's own background from `context/experience.md` before writing — that's where their
core skills, experience highlights, tools/platforms, portfolio links, tone, and unique selling
points are recorded. Pull the relevant pieces from there into the proposal rather than inventing
or assuming anything about the user's background.

---

## Instructions

### Step 1: Analyze the Job Posting
Extract:
- What the client actually needs (not just what they say)
- Pain points or problems they're trying to solve
- Required skills vs nice-to-haves
- Budget/timeline expectations
- Red flags or clarifying questions needed

### Step 2: Process the Video Transcript
Identify from the transcript:
- What you demonstrated in the video
- Your proposed solution/approach
- Specific examples or past work you showed
- Key talking points to weave into the written proposal
- Any questions you asked or offered to answer

### Step 3: Write the Proposal

**Structure:**

1. **Hook (1-2 sentences)**
   - Show you understand their specific problem
   - Reference something specific from their posting
   - NO generic "I read your job posting and..."

2. **Video Reference (2-3 sentences)**
   - Introduce the Loom video with context
   - Briefly summarize what's shown: "Here's how I would do it :)"
   - Format: 📽️: [insert the actual Loom link provided]

3. **Relevance (2-3 sentences)**
   - Connect experience directly to their needs
   - Mention similar projects or results with specific metrics
   - Reference what was demonstrated in the video

4. **Portfolio Proof**
   - Include portfolio link with context
   - Format: ❗ [Portfolio link]

5. **Call to Action (1-2 sentences)**
   - Friendly, action-oriented close
   - "Looking forward to hearing from you!"
   - Sign off with the user's own name, as recorded in `context/config.yaml` (key: `name`)

**Tone Guidelines:**
- Professional but friendly
- Confident, not arrogant
- Action-focused: "Here's how I would do it"
- Use emojis sparingly (📽️, ❗)
- Specific metrics when possible (real numbers beat vague claims)

**Length:** 150-250 words ideal (Upwork clients skim)

### Step 4: Output Format

Provide:
1. The proposal ready to copy/paste (with the actual Loom link inserted)
2. Note any key points from the transcript that were emphasized

---

## What NOT to Do

- Don't start with "Dear Hiring Manager" or "I am writing to apply..."
- Don't list every skill - only relevant ones
- Don't be vague ("I have experience in automation")
- Don't copy the job posting back at them
- Don't make it about you - make it about solving their problem
- Don't use filler phrases ("I believe", "I think I would be a great fit")
- Don't forget to reference the video!

---

## Example Proposal Style

This is one illustrative example of the shape a strong proposal takes, not a fixed voice to copy.
Replace it with your own accepted proposals as you collect them — the real value comes from
examples in your own tone, referencing your own real numbers and links.

**Job:** "Need a CRM expert to set up appointment booking and follow-up automation"

**Example shape:**

```
Hey, I'm a full time [your specialty] expert and can definitely help you set up your appointment booking system.

Here's how I would do it :)
📽️: [Loom link]

In terms of relevant experience, I have worked with [X+] clients now building out a variety of complex systems for appointment setting, sales, marketing, and reputation management, for businesses with up to [N] employees. I believe that actions speak louder than words so I would recommend you quickly check out the video I recorded as well as my portfolio projects and feedback I have received from past clients :).

Websites, funnels etc:
❗[Your portfolio link]

Looking forward to hearing from you!
[Your name]
```
