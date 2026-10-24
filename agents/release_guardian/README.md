# CodeBrain Release Guardian

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)
![tag:domain/developer-tools](https://img.shields.io/badge/developer--tools-3D8BD3)

CodeBrain Release Guardian is the Fetch-a-thon 3 entry point for CodeBrain. In ASI:One it accepts a feature requirement, uses ASI:One-backed Actor–Critic reasoning to create a small QA plan, shows that plan for review, and only then offers an optional policy-gated test run in one configured release repository.

## What it does

Release Guardian helps engineering teams turn a feature requirement into reviewable, executable release evidence. It creates functional, boundary, and exception QA cases; critiques them with an independent reviewer pass; then asks for explicit approval before it runs the one allowed repository test command.

Use it in ASI:One for requests such as:

- "Create a release QA plan for password reset with an expiring email link."
- "Review boundary and failure coverage for guest checkout."
- "Generate a QA plan for this requirement, then run the configured repository check after I review it."

The agent accepts natural-language chat and ASI:One form/review-card selections. Its output is a QA plan with test steps and expected results, followed—only after confirmation—by a pass/fail summary of the configured pytest run.

**Scope and limits:** it is a QA planning and evidence agent, not a deployment agent. It never deploys code, accepts a repository path or command from chat, persists conversation data, or treats a quality score as release approval.

## Safety boundary

- The agent never deploys, writes data, handles credentials from chat, or accepts arbitrary paths or commands.
- The optional action runs only `python -m pytest` plus quiet-mode options in the absolute Git repository set by the operator in `RELEASE_GUARDIAN_REPO_PATH`.
- An explicit card approval is required before the test run. Skipping it leaves the whole workflow in ASI chat.
- The subprocess receives only basic OS execution variables, never the agent's API keys, seed, or Django secret. Configure only a repository whose tests you trust to execute.
- The agent is stateless across restarts. A user can resubmit the requirement to recover a review flow; no private conversation data is persisted by this package.

## Local run

From the repository root, use Python 3.10–3.13 and configure the environment variables shown in `.env.example`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-agent.txt
python -m agents.release_guardian.preflight
python -m agents.release_guardian.agent
```

The process prints its Agentverse address. For a public deployment, configure the public endpoint below before starting the process. The running uAgent will then receive ACP requests directly at that same endpoint rather than through a separate mailbox route.

Before a demo or deployment, run `python -m agents.release_guardian.preflight`. It checks only configuration and local package/repository readiness; it never calls ASI:One, registers an Agentverse profile, or exposes secret values. On the deployed host, add `--deployment --check-public-endpoint --check-agentverse-api` to verify the public health route and make a read-only Agentverse credential/profile lookup.

## Optional public deployment registration

For a deployed agent, set `AGENTVERSE_V2_REGISTRATION_ENABLED=true`, an
`AGENTVERSE_API_KEY`, and an `AGENTVERSE_PUBLIC_ENDPOINT` such as
`https://release-guardian.example.com/submit`. The endpoint must be a public HTTPS route that
forwards to the agent's `/submit` handler; the Agentverse Inspector URL is not an endpoint.
Without `AGENTVERSE_PUBLIC_ENDPOINT`, local development uses the Agentverse Mailbox. With a public endpoint configured, Agentverse registration and the running agent use that exact direct ACP route.

For an entirely local direct-ACP check, set `FETCH_AGENT_LOCAL_ENDPOINT=http://127.0.0.1:8000/submit` (using the same port as `FETCH_AGENT_PORT`) and leave `AGENTVERSE_PUBLIC_ENDPOINT` unset. Otherwise, local development defaults to Agentverse Mailbox transport.

For ASI:One discoverability, create the Agentverse entry as **Connect Agent → Chat Protocol**, set a specific handle such as `codebrain-release-guardian`, use discovery phrases such as `release QA`, `test planning`, `acceptance criteria`, `pytest verification`, and `quality engineering`, and then select **Evaluate Registration** while the public endpoint is live. Keep the agent online during the evaluation.
