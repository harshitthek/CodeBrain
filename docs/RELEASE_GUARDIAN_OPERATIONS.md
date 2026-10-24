# Release Guardian: Local, Deployment, and ASI:One Runbook

This runbook is the operating path for the Fetch-A-Thon submission agent. It covers three distinct proofs:

1. The repository can run the ACP agent locally.
2. A public deployment receives ACP traffic at a stable HTTPS `/submit` endpoint.
3. Agentverse and ASI:One can discover the agent and complete its primary user workflow in chat.

It deliberately separates code readiness from account-bound proof. A passing local test suite does not prove that an Agentverse registration, ASI:One conversation, or deployed tunnel is live.

## 0. Rotate exposed credentials first

If a seed phrase, ASI:One key, Agentverse key, or Django secret has been placed in a chat, shell history, issue, or commit, revoke it and create a replacement before deployment. Do not reuse the old agent seed: a seed identifies the agent address, so rotation creates a new `agent1...` identity that must be registered again.

Put values only in the deployment secret store or an ignored `.env` file. Never send secrets as an ASI:One message.

## 1. Local agent verification

Use Python 3.10-3.13. The Fetch runtime currently requires `uagents==0.25.5` and uses `AgentChatProtocol 0.3.0`.

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-agent.txt
cp .env.example .env
python -m agents.release_guardian.preflight
python -m pytest -q
python -m agents.release_guardian.agent
```

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-agent.txt
Copy-Item .env.example .env
python -m agents.release_guardian.preflight
python -m pytest -q
python -m agents.release_guardian.agent
```

Replace `-3.11` with an installed Python version in the supported range. Local development can leave `AGENTVERSE_V2_REGISTRATION_ENABLED=false`; in that case the agent uses the Agentverse Mailbox path and does not need a public endpoint.

For a fully local direct ACP listener instead of Mailbox transport, set both values below before starting the agent. The loopback endpoint is intentionally rejected if it points to any remote address.

```dotenv
FETCH_AGENT_PORT=8000
FETCH_AGENT_LOCAL_ENDPOINT=http://127.0.0.1:8000/submit
```

The preflight command validates package availability, the ACP protocol version, required secret *presence*, and the optional configured repository. It never prints secret values, calls ASI:One, runs pytest, or registers an agent.

For a local workflow test, speak to the agent through the Agentverse Inspector/Mailbox or a separate ACP client. Confirm this sequence:

1. Send `hello` and receive an acknowledgement plus an intake form.
2. Submit a requirement with `No test run — QA plan only`; receive actual QA cases, review text, and a review card.
3. Select `Finish QA review`; confirm no subprocess was run.
4. Repeat with the configured repository selected and approve the review card; confirm exactly one constrained pytest execution occurs.

## 2. Public deployment

Use a stable hostname for the demo when possible. Temporary ngrok URLs are acceptable for a live event demo but expire or change, making Agentverse evaluation and submitted links fragile.

Set these values in the server's secret manager or ignored environment file:

```dotenv
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=your-agent-domain.example
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_HSTS_SECONDS=31536000
FETCH_AGENT_PORT=8000
AGENTVERSE_PUBLIC_ENDPOINT=https://your-agent-domain.example/submit
AGENTVERSE_V2_REGISTRATION_ENABLED=true
AGENTVERSE_API_KEY=replace-in-secret-store
FETCH_AGENT_SEED=replace-in-secret-store
ASI1_API_KEY=replace-in-secret-store
RELEASE_GUARDIAN_REPO_PATH=/absolute/path/on/this/server/to/trusted-release-repository
RELEASE_GUARDIAN_REPO_TEST_COMMAND="python -m pytest -q"
RELEASE_GUARDIAN_REPO_TEST_TIMEOUT=120
CODEBRAIN_KNOWLEDGE_ENABLED=false
```

`AGENTVERSE_KEY` remains supported for backward compatibility, but `AGENTVERSE_API_KEY` is the documented name and should be used for new deployments. `RELEASE_GUARDIAN_REQUEST_TIMEOUT` is not an active setting; use `ASI1_REQUEST_TIMEOUT` for model latency and `RELEASE_GUARDIAN_REPO_TEST_TIMEOUT` for the bounded pytest action.

Configure the reverse proxy or tunnel so it forwards the exact HTTPS `/submit` route, its POST body, and relevant headers to `FETCH_AGENT_PORT`. Do not point Agentverse at an Inspector URL, a localhost URL, a health-only URL, or a proxy route other than `/submit`.

Before starting the service, run:

```bash
python -m agents.release_guardian.preflight --deployment
```

Then start the agent. It validates registration configuration before starting, opens the uAgent listener, and only then performs the opt-in Agentverse registration attempt. This ordering avoids advertising an endpoint before the listener is online.

With the service live, run this from the deployment host:

```bash
python -m agents.release_guardian.preflight --deployment --check-public-endpoint --check-agentverse-api
```

Expected outcome: every required check reports `PASS`, the public endpoint returns a 2xx status, and the command prints `READY`.

## 3. Agentverse and ASI:One activation

Registration is not complete merely because the process logs an attempt. In Agentverse:

1. Open **Agents → Launch an Agent → Connect Agent**.
2. Choose **Chat Protocol**, set the exact public `https://.../submit` endpoint, and keep the agent online.
3. Add precise discovery language: `release QA`, `test planning`, `acceptance criteria`, `boundary testing`, `pytest verification`, and `quality engineering`.
4. Set a memorable handle, for example `codebrain-release-guardian`.
5. Select **Evaluate Registration** and confirm the agent is active and its ACP protocol is shown.
6. Check the Agentverse profile has the Innovation Lab and hackathon badges, the public GitHub link, a clear description, example prompts, and this agent README.

In ASI:One, first test direct routing with the handle, then natural-language discovery:

```text
@codebrain-release-guardian Create a release QA plan for password reset with a one-hour email link. Do not run tests.
```

Verify the response acknowledges the message, renders the intake or review card, displays test steps and expected results, and completes with no tool action when rejected. Then run a second conversation with a safe configured repository and choose the explicit approval button. Record that one pytest evidence action ran and that a second approval cannot run it again.

Finally, create the ASI:One shared-chat URL after this full flow, and record the Agentverse profile URL and a 3-5 minute video. These are account-bound submission artifacts; they cannot be generated by local code alone.

## 4. Submission evidence ledger

| Evidence | How to obtain | Completion criterion |
|---|---|---|
| Public repository | GitHub repository URL | README contains agent run and test instructions |
| Agentverse profile | Agentverse profile after evaluation | Active agent, `/submit` endpoint, ACP manifest, handle, correct README |
| ASI:One shared chat | Share the completed ASI:One conversation | Intake, QA plan, review, explicit action/no-action outcome all visible |
| Demo video | Record a 3-5 minute walk-through | Shows intent, cards, Actor-Critic QA evidence, and one approved tool action |
| Deployment health | `preflight --deployment --check-public-endpoint --check-agentverse-api` | `READY`, public HTTP 2xx, and accepted Agentverse credentials |

## 5. Incident guide

| Symptom | First check |
|---|---|
| Agentverse says endpoint unreachable | Confirm the process, tunnel, TLS certificate, and exact `/submit` forwarding route are live. |
| Registration identity mismatch | The Agentverse registration must use the same `FETCH_AGENT_SEED` as the running agent. |
| ASI:One cannot find the agent | Confirm active profile status, handle, ACP manifest, descriptive README, and specific discovery keywords. |
| ASI:One returns a plain message instead of a card | Confirm `card_protocol_version="1"`, string metadata values, and a valid card payload smaller than 64 KB. |
| Model call fails | Confirm `ASI1_API_KEY`, `ASI1_MODEL`, outbound HTTPS, and `ASI1_REQUEST_TIMEOUT`; do not expose the provider error to chat users. |
| No repository target appears | Verify that `RELEASE_GUARDIAN_REPO_PATH` is an absolute Git repository path on the host actually running the agent. |
| Approved test run fails | Check the trusted repository's dependencies and test command locally; only approved quiet pytest flags are permitted. |
