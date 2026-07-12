/**
 * How It Works page
 *
 * A plain-language explainer aimed at a non-technical business owner: what the
 * assistant does, how it fits into day-to-day work, and why its answers can be
 * trusted. Deliberately avoids jargon (embeddings, vectors, prompts, etc.).
 */

function Flow({ steps }) {
    return (
        <div className="hiw-flow">
            {steps.map((s, i) => (
                <div className="hiw-flow-item" key={i}>
                    <div className={`hiw-step ${s.accent ? 'hiw-step-accent' : ''}`}>
                        <span className="hiw-step-num">{s.n}</span>
                        <span className="hiw-step-title">{s.title}</span>
                        <span className="hiw-step-sub">{s.sub}</span>
                    </div>
                    {i < steps.length - 1 && <span className="hiw-arrow">→</span>}
                </div>
            ))}
        </div>
    )
}

function HowItWorks({ onTryIt }) {
    const setupSteps = [
        { n: '1', title: 'Your know-how', sub: 'guides, pricing, FAQs, policies' },
        { n: '2', title: 'Organized for you', sub: 'like a smart filing cabinet', accent: true },
    ]

    const everydaySteps = [
        { n: '1', title: 'A question', sub: 'asked in plain English' },
        { n: '2', title: 'Finds the answer', sub: 'in your own documents', accent: true },
        { n: '3', title: 'Clear reply', sub: 'with the source shown', accent: true },
    ]

    const fits = [
        {
            title: 'On the phone & front desk',
            body: 'Answer customer questions on the spot — pricing, scheduling, what a service includes — without putting them on hold.',
        },
        {
            title: 'New team members',
            body: 'New hires get up to speed fast and find answers themselves instead of interrupting a manager.',
        },
        {
            title: 'Everyone says the same thing',
            body: 'Consistent, correct answers across the whole team, so customers hear one clear story.',
        },
        {
            title: 'Always on call',
            body: "Your business's know-how is available any time — even when your most experienced people are out in the field.",
        },
    ]

    const trust = [
        {
            title: 'Only your information',
            body: "It answers from your company's own documents — not random guesses from the internet.",
        },
        {
            title: 'Shows its sources',
            body: 'Every answer points to the exact document it came from, so anyone can double-check it.',
        },
        {
            title: "Won't make things up",
            body: "If the answer isn't in your documents, it says so instead of guessing.",
        },
    ]

    return (
        <div className="hiw">
            <section className="hiw-intro">
                <h2>How it works</h2>
                <p>
                    Think of it as a super-organized binder of everything about your business —
                    with a helper who can instantly find the right page and read the answer back.
                    Your team asks a question in plain English and gets a clear, trustworthy answer
                    pulled straight from your own guides and policies.
                </p>
            </section>

            <section className="hiw-lane">
                <div className="hiw-lane-head">
                    <span className="hiw-lane-badge">Setup · once</span>
                    <h3>We load your business knowledge</h3>
                </div>
                <p className="hiw-lane-desc">
                    You hand over what you already have — service guides, pricing, FAQs, policies —
                    and it gets organized so any topic can be found in a second.
                </p>
                <Flow steps={setupSteps} />
            </section>

            <section className="hiw-lane">
                <div className="hiw-lane-head">
                    <span className="hiw-lane-badge">Every day</span>
                    <h3>Your team asks, it answers</h3>
                </div>
                <p className="hiw-lane-desc">
                    Anyone on the team types a question the way they'd say it out loud. The assistant
                    looks it up in your documents and replies in plain language.
                </p>
                <Flow steps={everydaySteps} />
            </section>

            <section className="hiw-accuracy">
                <h3>Where it helps in your business</h3>
                <div className="hiw-cards">
                    {fits.map((a, i) => (
                        <div className="hiw-card" key={i}>
                            <h4>{a.title}</h4>
                            <p>{a.body}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section className="hiw-accuracy">
                <h3>Why you can trust the answers</h3>
                <div className="hiw-cards">
                    {trust.map((a, i) => (
                        <div className="hiw-card" key={i}>
                            <h4>{a.title}</h4>
                            <p>{a.body}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section className="hiw-stack">
                <button className="hiw-cta" onClick={onTryIt}>Try it — ask a question →</button>
            </section>
        </div>
    )
}

export default HowItWorks
