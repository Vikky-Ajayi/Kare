# Kare — Demo Video Script

**Portal limit: max 5 minutes. Public or Unlisted YouTube (Private can't be
embedded for judges).** The portal explicitly requires the video to *show*
code-switching, not just claim it in narration — the cold open below exists
specifically for that; don't cut it. Screen recording of the live PWA
(`kare-health.vercel.app`, not localhost — judges should see it's actually
deployed) with voice audible. Keep talking-head to zero; narrate over the
screen. Script below runs ~4:00, leaving a minute of buffer.

Record on a phone-sized viewport (Chrome devtools device mode, or an actual
phone) so it reads as the mobile product it is.

---

## How to actually record it (Mac)

1. **Redeploy first.** Confirm Railway has the latest commit (tool-call
   crash fix, vision model fix) *before* filming — rehearsing the takes
   against code that's about to change wastes a re-record.
2. **Screen + mic:** `Cmd+Shift+5` → "Record Selected Portion" → drag it to
   the browser window sized to a phone viewport → click the **Options**
   menu → pick your microphone as the audio source → Record.
   (QuickTime Player → File → New Screen Recording works the same way.)
3. **Avoid feedback:** Kare talks back through your speakers, and an open
   mic will pick that up as an echo in the recording. Wear headphones/earbuds
   while filming — audio input stays clean, and viewers still hear Kare's
   reply because it's playing on your machine, just not re-captured.
4. **Do one continuous take per section**, not the whole 4 minutes at once —
   stop the recording between shot-list sections below, and stitch clips
   together after (QuickTime trim, iMovie, or just `ffmpeg -f concat`).
   Much less painful than restarting from 0:00 over a stumble at 2:30.
5. **Rehearse the code-switched lines out loud once** before recording them —
   they should sound like natural speech, not a read-aloud script.
6. **Upload to YouTube as Unlisted**, then open the link in a private/
   incognito window before pasting it into the portal — confirms it's
   actually viewable without your account signed in.

---

## Before you record

```bash
# backend running (Railway prod, or local):
make run
# seed the demo patients:
make seed
# frontend:
cd frontend_kare && npm run dev
```

Demo accounts (`scripts/seed_demo.py`, password `demo-kare-2026`):

| Persona | Email | State |
|---|---|---|
| **Amina** (pregnant, 24 wks) | `amina@demo.kare.health` | pregnancy profile, prior consults |
| **Tayo** (malaria follow-up) | `tayo@demo.kare.health` | history: recurrent malaria |
| **Chidi** (hypertension) | `chidi@demo.kare.health` | on amlodipine, for the interaction demo |
| **Ngozi** (new user) | `ngozi@demo.kare.health` | clean slate |

Have a headset mic. Rehearse the spoken lines once so the code-switching sounds
natural, not read.

---

## Shot list

### 0:00–0:20 — The problem (cold open) — this is the shot that satisfies "must show code-switching"

> **Narration:** "This is how a Nigerian patient actually describes a symptom."

Play a single audio line on screen (text on a black slide, then speak it):

> *"Doctor, the malaria don come back. My body dey hot since morning, and the sharp pain for my side never stop."*

> **Narration:** "Three languages in one sentence. Pidgin, English clinical
> terms, all mixed. Type that into a health app and you're locked out. Kare
> listens instead — and it remembers you."

---

### 0:20–1:15 — Voice consultation + code-switching + the agent

Log in as **Chidi**. Open **Voice Doctor**. Accept the consent gate on screen
(pause half a second on it — judges want to see consent).

Tap the mic. Say, code-switched:

> *"Kare, I get headache since morning and I dey feel small dizzy. I still dey take my blood pressure medicine, amlodipine. I wan take Panadol Extra, e safe?"*

Let Kare respond in voice. On screen, point out:

- the **live transcript** showing the code-switched text transcribed correctly;
- the **"Checked drug interactions"** chip that appears — *the model decided on
  its own* to call the interaction tool against his recorded amlodipine;
- the reply comes back **in the same Pidgin/English register**, spoken aloud,
  2–3 sentences, and it references that he's on amlodipine.

> **Narration:** "It transcribed the mixed speech, and without being asked it
> pulled his medication record and checked the interaction before answering.
> That's the agent — seven tools, it picks what the situation needs."

---

### 1:15–1:55 — Memory

Still as Chidi, tap **Doctor's notes** (the drawer). Show the structured notes
Kare has kept — conditions, medications, the concern just discussed.

End the consultation. Re-open Voice Doctor. Tap mic:

> *"Remind me wetin you talk about my headache."*

Kare answers referencing the earlier conversation and his hypertension —
without being re-told any of it.

> **Narration:** "Every consultation updates a longitudinal record. Next time,
> Kare already knows him. Two patients with the same symptom get different
> questions, because Kare remembers different histories."

---

### 1:55–2:40 — Proactive follow-up

> **Narration:** "When a consultation ends, Kare decides whether to check back
> in — and when."

Switch to **Tayo**. (If you can, show `scheduled_followups` briefly, or just
narrate.) Trigger the follow-up worker so a push fires now:

```bash
python -m app.worker.followup_tick        # processes the due queue
```

Show the **push notification** arriving on the phone:

> *"Hi Tayo 😊 How's the body today? Has the fever come down since we spoke, and did you finish the malaria drugs?"*

> **Narration:** "That message was written just now, from Tayo's actual
> context — not a template. A different patient gets a different message."

**Tap the notification.** It opens Voice Doctor **on the same conversation** —
the previous messages are right there. Reply by voice:

> *"The fever don reduce but I never finish the drugs."*

Kare picks up exactly where it left off.

> **Narration:** "The notification is the doorway back into the conversation.
> Quiet hours, a frequency cap, and it stops after two unanswered check-ins."

---

### 2:40–3:25 — Pregnancy companion

Log in as **Amina**. The nav now shows **Pregnancy**. Open it.

Show the companion home: **Week 24**, EDD countdown, "this week" note, the
trimester danger-sign list always visible.

Tap mic:

> *"Kare, I dey feel the baby move plenty today, that one normal?"*

Kare answers warmly, refers to "our little one", confirms what's normal at
24 weeks, and reminds her of the movement pattern to watch for — and to keep
her next antenatal appointment.

Then say a red-flag line:

> *"But since morning I never really feel am move."*

Kare's tone shifts: reduced fetal movement at this stage → **contact your
midwife or go to the clinic today**, clearly and calmly.

> **Narration:** "A dedicated mode that tracks the pregnancy week by week, in
> her language, and knows the danger signs cold — it doesn't leave those to
> chance."

---

### 3:25–3:50 — Emergency escalation

Back to any account. Voice Doctor. Say:

> *"Kare, chest dey pain me and e hard for me to breathe."*

Kare **immediately** — no back-and-forth — responds: *get to a hospital now,
call 112, or 767 / 122 in Lagos.*

> **Narration:** "Emergencies don't wait on the language model. A separate
> detector runs alongside every turn and cuts straight to the action and the
> local emergency number."

---

### 3:50–4:00 — Close

Cut to the benchmark chart (`benchmark/report/charts/wer_by_language.png`).

> **Narration:** "We didn't pick the speech model on faith. We benchmarked five
> of them on code-switched clinical audio — the report's in the repo. Sahara
> won on the language our users actually speak. Kare — health that listens,
> and remembers."

---

## Capture checklist

- [ ] Consent gate visible for ~1 s
- [ ] Live transcript shows correct code-switched text
- [ ] "Checked drug interactions" tool chip visible
- [ ] Doctor's notes drawer shown
- [ ] Memory recall works with nothing re-stated
- [ ] Real push notification on a real device (or convincing emulation)
- [ ] Notification tap → same conversation, history intact
- [ ] Pregnancy: week number + danger-sign list on screen
- [ ] Red-flag line → immediate escalation with "112 / 767 / 122"
- [ ] Benchmark chart at the end
- [ ] Total under 4:00
