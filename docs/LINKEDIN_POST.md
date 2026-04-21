# LinkedIn / portfolio template

Copy, trim, and fill the brackets. The goal is to lead with the
business problem, not the tech stack — hiring managers for
BI/Analyst roles skim for outcomes.

---

### Version A — Business-first

> I spent the last [N] days building a real-time e-commerce
> monitoring system that catches revenue spikes and low-stock events
> the moment they happen — not 24 hours later.
>
> The problem: most "sales dashboards" refresh nightly. By the time
> an analyst sees a flash-sale spike or a SKU hitting zero stock, the
> window to respond is gone.
>
> What I built:
>
> • Simulated order stream feeding Apache Kafka
> • Spark Structured Streaming aggregating revenue by the minute
> • Anomaly detection (Isolation Forest + z-score fallback) flagging
>   spikes in under 60 seconds
> • A threshold-driven KPI engine so business users tune SLOs in SQL
>   — no code changes
> • Power BI (DirectQuery, 1-min auto-refresh) as the operator view
>
> Demo video below shows a burst hitting the stream and the alert
> firing in the dashboard live. Full code + architecture write-up:
> [GitHub link]
>
> #DataEngineering #PowerBI #ApacheSpark #ApacheKafka #RealTime

### Version B — Short-form

> Built a real-time sales + inventory monitor: Kafka → Spark
> Structured Streaming → MySQL → Power BI. Anomaly detection flags
> revenue spikes inside a minute; a thresholds table lets analysts
> tune KPI alerts without a deploy. 30-sec demo ↓ [video link]
> • Repo: [GitHub link]

## Repo README polish before sharing

- Architecture image at the top (export the mermaid diagram from
  `docs/ARCHITECTURE.md` as PNG via mermaid.live).
- Screenshots of all four Power BI pages under a collapsed section.
- "Tech stack" badges strip.
- A "What I learned" block that pulls 3-4 bullets from
  `docs/LEARNINGS.md`.
- Demo video as a GitHub release asset or YouTube embed.

## Where to post

- LinkedIn (primary).
- Hacker News `Show HN` (if the demo video is strong).
- r/dataengineering for technical feedback.
- Personal portfolio site — frame it around the decision log in
  `docs/LEARNINGS.md`, not the Python.
