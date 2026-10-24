# CodeBrain Release Guardian

CodeBrain Release Guardian is the Fetch-a-thon 3 entry point for CodeBrain. In ASI:One it accepts a feature requirement, uses ASI:One-backed Actor–Critic reasoning to create a small QA plan, shows that plan for review, and only then offers an optional policy-gated test run in one configured release repository.

## Safety boundary

- The agent never deploys, writes data, handles credentials from chat, or accepts arbitrary paths or commands.
- The optional action runs only `python -m pytest` plus quiet-mode options in the absolute Git repository set by the operator in `RELEASE_GUARDIAN_REPO_PATH`.
- An explicit card approval is required before the test run. Skipping it leaves the whole workflow in ASI chat.
- The subprocess receives only basic OS execution variables, never the agent's API keys, seed, or Django secret. Configure only a repository whose tests you trust to execute.
- The agent is stateless across restarts. A user can resubmit the requirement to recover a review flow; no private conversation data is persisted by this package.

## Local run

From the repository root, use Python 3.12 or 3.13 and configure the environment variables shown in `.env.example`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-agent.txt
python -m agents.release_guardian.agent
```

The process prints its Agentverse address. For a public deployment, configure the public endpoint below before starting the process. The running uAgent will then receive ACP requests directly at that same endpoint rather than through a separate mailbox route.

## Optional public deployment registration

For a deployed agent, set `AGENTVERSE_V2_REGISTRATION_ENABLED=true`, an
`AGENTVERSE_API_KEY`, and an `AGENTVERSE_PUBLIC_ENDPOINT` such as
`https://release-guardian.example.com/submit`. The endpoint must be a public HTTPS route that
forwards to the agent's `/submit` handler; the Agentverse Inspector URL is not an endpoint.
Without `AGENTVERSE_PUBLIC_ENDPOINT`, local development uses the Agentverse Mailbox. With a public endpoint configured, Agentverse registration and the running agent use that exact direct ACP route.
