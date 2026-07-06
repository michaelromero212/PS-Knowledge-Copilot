/**
 * How It Works page
 *
 * A demo-oriented explainer of the RAG pipeline: how documents become a
 * searchable knowledge base, how a question turns into a grounded answer, and
 * the layers that keep answers accurate.
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
    const ingestSteps = [
        { n: '1', title: 'Knowledge docs', sub: '8 ITSM markdown files' },
        { n: '2', title: 'Chunk', sub: '~800 chars, 150 overlap' },
        { n: '3', title: 'Embed', sub: 'MiniLM · 384-dim' },
        { n: '4', title: 'ChromaDB', sub: 'vector store', accent: true },
    ]

    const querySteps = [
        { n: '1', title: 'Question', sub: 'user asks' },
        { n: '2', title: 'Guardrails', sub: 'injection · PII', accent: true },
        { n: '3', title: 'Vector search', sub: 'top-3 chunks' },
        { n: '4', title: 'Grounded prompt', sub: 'context + rules', accent: true },
        { n: '5', title: 'Gemini', sub: 'generates answer' },
        { n: '6', title: 'Cited answer', sub: 'with citations', accent: true },
    ]

    const accuracy = [
        {
            title: 'Grounded generation',
            body: 'The model is instructed to answer only from the retrieved context — and to say when the context is insufficient rather than guess.',
        },
        {
            title: 'Source citations',
            body: 'Every answer links back to the document chunks it used, shown alongside the answer so a human can verify it in one glance.',
        },
        {
            title: 'Safety guardrails',
            body: 'User input is screened for prompt injection and PII, and retrieved text is fenced as untrusted data to block indirect injection.',
        },
        {
            title: 'Measured, not assumed',
            body: 'An offline eval harness scores prompt variants on citation, grounding, and correct refusal — so changes are validated with data.',
        },
    ]

    const stack = ['React + Vite', 'FastAPI', 'ChromaDB', 'Sentence-Transformers', 'Google Gemini']

    return (
        <div className="hiw">
            <section className="hiw-intro">
                <h2>How it works</h2>
                <p>
                    This is a Retrieval-Augmented Generation (RAG) assistant. Instead of asking a
                    language model to answer from memory — where it can confidently invent facts —
                    it retrieves the most relevant passages from a curated knowledge base first,
                    then answers <em>only</em> from those passages and cites them.
                </p>
            </section>

            <section className="hiw-lane">
                <div className="hiw-lane-head">
                    <span className="hiw-lane-badge">Stage 1</span>
                    <h3>Ingestion — building the knowledge base (offline)</h3>
                </div>
                <p className="hiw-lane-desc">
                    Documents are split into overlapping chunks, converted into embedding vectors,
                    and stored in a local vector database. This runs once, up front.
                </p>
                <Flow steps={ingestSteps} />
            </section>

            <section className="hiw-lane">
                <div className="hiw-lane-head">
                    <span className="hiw-lane-badge">Stage 2</span>
                    <h3>Query — answering a question (live)</h3>
                </div>
                <p className="hiw-lane-desc">
                    A question is screened, embedded, and matched against the store. The top matches
                    become context for a grounded prompt that the LLM answers with citations.
                </p>
                <Flow steps={querySteps} />
            </section>

            <section className="hiw-accuracy">
                <h3>How answers stay accurate</h3>
                <div className="hiw-cards">
                    {accuracy.map((a, i) => (
                        <div className="hiw-card" key={i}>
                            <h4>{a.title}</h4>
                            <p>{a.body}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section className="hiw-stack">
                <h3>Built with</h3>
                <div className="hiw-chips">
                    {stack.map((s) => (
                        <span className="hiw-chip" key={s}>{s}</span>
                    ))}
                </div>
                <button className="hiw-cta" onClick={onTryIt}>Try it — ask a question →</button>
            </section>
        </div>
    )
}

export default HowItWorks
