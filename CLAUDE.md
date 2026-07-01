# Looptimal — repo guidance for AI agents

Looptimal turns an objective into a delivered, **verified** outcome: a sealed acceptance suite, the
right loop, a war-game pass, domain-expert execution (**maker ≠ checker**), and a separate verifier.
Keep the core generic, dependency-light, and honest about its gates (see `CONTRIBUTING.md`,
`SECURITY.md`, `RELEASE.md`).

## Build Journal — capture the journey as you go

Whenever you (a) ship something that worked differently than expected, (b) hit a real
gotcha/limitation and had to work around or accept it, (c) make a judgment call with a
reason worth remembering, (d) reach a genuine milestone, or (e) discover something
counter-intuitive about the building process itself — append a short entry to
`.buildlog/journal.md` (create it, and add `.buildlog/` to `.gitignore`, if this is the
first entry).

Format per entry:

```
## <ISO timestamp> — <category> — <short title>
<commit: optional SHA if directly tied to a change>
2-6 sentences, first person, honest. What happened, why it mattered, what you'd tell
someone building the same thing. No marketing voice — write it the way you'd explain it
to a teammate, not the way you'd pitch it.
```

Category is one of: `breakthrough` | `learning` | `gotcha` | `decision` | `milestone` | `honest-limitation`

Rules:
- Small and frequent beats one giant retrospective — log as it happens, not at session end.
- Be honest about what didn't work. Limitations and honest misses make better build-in-public
  content than polished wins do — don't sand them off.
- Don't self-edit into marketing copy. This is raw material; a separate marketing process shapes it
  into public content later.
- Never put secrets, credentials, internal paths, or proprietary details in an entry — this file is
  read by that separate marketing process.
- `.buildlog/` is gitignored on purpose: raw internal narrative must never ship in the public OSS
  history.
