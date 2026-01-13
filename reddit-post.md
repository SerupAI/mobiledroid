# Reddit Title

**I built an AI agent that controls Android devices via natural language - would an n8n integration be useful?**

---

# Reddit Post

Hey r/n8n!

I've been working on something and wanted to get the community's feedback before going further.

**What I built:** An AI-powered Android automation platform. You describe what you want in plain English, and an AI agent (Claude) analyzes the screen and executes the actions - taps, swipes, typing, navigation, etc. Think of it like a browser automation tool, but for Android devices running in Docker containers.

**The demo video** shows me asking the AI to open Threads and create a post. The agent figures out the steps, executes them, and completes the task autonomously.

**Inspiration:** ByteBot was a big inspiration for this project. I wanted something similar but for mobile app automation specifically.

**What's coming:**
- REST API (almost done)
- MCP server integration (for Claude Desktop, etc.)
- Task queues for batch operations
- Multiple execution strategies (parallel devices, sequential tasks)
- Snapshot/restore for device states

**My question for you all:**

Would an n8n integration be useful for your workflows? I'm imagining it would work similar to how Browserless or Apify nodes work - essentially a wrapper around the API that lets you:

- Spin up Android device profiles
- Send natural language commands to control them
- Capture screenshots
- Chain mobile automation into larger workflows

Use cases I'm thinking about:
- Social media automation (posting, engagement)
- Mobile app testing
- Data extraction from mobile-only apps
- Automated mobile workflows that integrate with your existing n8n automations

**Not pitching anything** - genuinely curious if this solves a problem people have. The mobile automation space seems underserved compared to browser automation.

Would love to hear:
1. Is this something you'd actually use?
2. What mobile automation tasks do you wish you could automate?
3. Does an n8n node make sense, or is API + HTTP Request node enough?

Happy to answer any questions about how it works!

---

*[Video demo attached showing AI agent posting to Threads]*
