# Kare — Demo Video Script

**Portal limit: max 5 minutes. Public or Unlisted YouTube (Private can't be
embedded for judges).** The portal explicitly requires the video to *show*
code-switching, not just claim it in narration — the cold open below exists
specifically for that; don't cut it. Screen recording of the live PWA
(`kare-health.vercel.app`, not localhost — judges should see it's actually
deployed) with voice audible. Keep talking-head to zero; narrate over the
screen. Script below runs ~4:15, leaving under a minute of buffer against the
5:00 cap — keep narration tight.

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

Two genuinely fresh accounts — registered live via the real API, zero seeded
history, nothing pre-loaded:

| Account | Email | Password | Used for |
|---|---|---|---|
| **Bisi Adewale** | `demo.a@karedemo.app` | `KareDemo2026!` | consult, meds, memory, escalation |
| **Funke Bello** | `demo.b@karedemo.app` | `KareDemo2026!` | pregnancy onboarding |

Both exist only on the live deployment (`kare-health.up.railway.app` /
`kare-health.vercel.app`) — record against that, not localhost.

**Have a real medication box or blister pack next to you** — the scan-photo
shot needs an actual label to read. Any pack with printed English text works.

Have a headset mic (avoids echo when Kare talks back — see recording
mechanics above). Rehearse the spoken lines once so the code-switching sounds
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

### 0:20–0:35 — Log in as a brand new patient

> **Narration:** "This is Bisi — an account I created minutes ago. Nothing
> seeded, nothing pre-loaded."

Log in as **Bisi** (`demo.a@karedemo.app`). Land on an empty Dashboard —
that emptiness is the point, briefly let it show.

---

### 0:35–1:00 — Scan a medication (new feature)

Open **Medications → Add**. Tap **Scan the box or pack**, photograph the real
pack you have next to you. Show Kare reading it — drug name and strength
land in the form on their own. Confirm, **Save**.

> **Narration:** "Kare can read the medication straight off the pack — no
> typing."

---

### 1:00–2:10 — Voice consultation: code-switching + the agent

Open **Voice Doctor**. Accept the consent gate on screen (pause half a
second — judges want to see consent). Tap the mic. Say, code-switched,
naming a **different** drug than the one just scanned:

> *"Kare, I get headache since morning and I dey feel small dizzy. I don just add [the scanned drug] to my list, and I wan take Panadol Extra too — e safe make I take both?"*

Let Kare respond in voice. On screen, point out:

- the **live transcript** showing the code-switched text transcribed correctly;
- the **"Checked drug interactions"** chip that appears — *the model decided
  on its own* to check the two drugs against each other;
- the reply comes back **in the same Pidgin/English register**, spoken aloud,
  referencing the specific medication just added.

> **Narration:** "It transcribed the mixed speech, and without being asked it
> checked the interaction against a medication that was added thirty seconds
> ago — before answering. That's the agent, not a script."

---

### 2:10–2:40 — Memory, and replaying a reply

Send a second message in the same conversation:

> *"Remind me wetin you talk about my headache."*

Kare answers referencing what was just discussed, without being re-told.
Tap **Doctor's notes** to show the structured record Kare kept from this one
conversation. Then tap the **play icon** on one of Kare's earlier replies —
it re-synthesizes and plays that exact reply again on demand.

> **Narration:** "Every reply is replayable, and every consultation updates a
> real record — next time Bisi comes back, Kare already knows this."

---

### 2:40–3:35 — Pregnancy companion (fresh onboarding)

Log out, log in as **Funke** (`demo.b@karedemo.app`) — another brand new
account. The nav doesn't show Pregnancy yet; open it and go through
onboarding live — gestational age or LMP, due date shown immediately.

Land on the companion home: week number, EDD countdown, the trimester
danger-sign list always visible. Tap mic:

> *"Kare, I dey feel the baby move plenty today, that one normal?"*

Kare answers warmly, refers to "our little one," confirms what's normal at
this stage. Then a red-flag line:

> *"But since morning I never really feel am move."*

Kare's tone shifts: reduced fetal movement → **contact your midwife or go to
the clinic today**, clearly and calmly.

> **Narration:** "A dedicated mode that tracks the pregnancy week by week and
> knows the danger signs cold — set up in under a minute, from nothing."

---

### 3:35–4:00 — Emergency escalation

Back to Bisi's account. Voice Doctor. Say:

> *"Kare, chest dey pain me and e hard for me to breathe."*

Kare **immediately** — no back-and-forth — responds: *get to a hospital now,
call 112, or 767 / 122 in Lagos.*

> **Narration:** "Emergencies don't wait on the language model. A separate
> detector runs alongside every turn and cuts straight to the action and the
> local emergency number."

---

### 4:00–4:15 — Close

Cut to the benchmark chart (`benchmark/report/charts/wer_by_language.png`).

> **Narration:** "We didn't pick the speech model on faith. We benchmarked five
> of them on code-switched clinical audio — the report's in the repo. Sahara
> won on the language our users actually speak. Kare — health that listens,
> and remembers."

---

## Capture checklist

- [ ] Both accounts are freshly logged into on camera (not pre-loaded state)
- [ ] Medication scan: photo → auto-filled drug name/strength shown clearly
- [ ] Consent gate visible for ~1 s
- [ ] Live transcript shows correct code-switched text
- [ ] "Checked drug interactions" tool chip visible, referencing the just-added drug
- [ ] Doctor's notes drawer shown
- [ ] Memory recall works with nothing re-stated
- [ ] Replay button clicked on a past reply — audio plays again
- [ ] Pregnancy onboarding shown live (LMP/weeks → EDD), not a pre-set week
- [ ] Pregnancy: week number + danger-sign list on screen
- [ ] Red-flag line → immediate escalation with "112 / 767 / 122"
- [ ] Benchmark chart at the end
- [ ] Total under 5:00 (script runs ~4:15)

## Note: proactive follow-up push

Not in the live shot list above — it needs a delivered notification, which
depends on timing (quiet hours, the worker's schedule) that's genuinely hard
to guarantee live on a fresh account with minutes to spare. If there's time
left after everything else and you want it in: enable check-ins in Settings
on Bisi's account, have Claude trigger the follow-up worker once off-camera
so a "Kare checked in on you" card is already sitting on the Dashboard when
you start that take, then just tap it on camera — the notification itself
was real, only its *timing* was arranged for the recording.
