# eta-skills

Agent skills for research planning, software design, and writing. Each skill follows the [Agent Skills specification](https://agentskills.io/specification), and the repo doubles as a Claude Code plugin marketplace, so one copy of each skill installs in Claude Code, other skills-compatible clients, and claude.ai.

## Skills

<!-- catalog:start -->
| Skill | Bundle | Description |
| --- | --- | --- |
| _none yet_ | | |
<!-- catalog:end -->

## Install

**Claude Code**

```
/plugin marketplace add tjmustard/eta-skills
/plugin install <bundle>@eta-skills
```

Update later with `/plugin marketplace update eta-skills`.

**Other skills-compatible clients**

```
npx skills add tjmustard/eta-skills
```

**claude.ai**

Run `make package name=<skill-name>` and upload `dist/<skill-name>.zip` under Settings > Capabilities > Skills.

## Contributing

See [AGENTS.md](AGENTS.md). License: MIT.
