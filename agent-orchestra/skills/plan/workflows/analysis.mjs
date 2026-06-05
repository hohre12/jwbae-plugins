export const meta = {
  name: 'plan-analysis',
  description: 'Read-only brownfield analysis for /agent-orchestra:plan — one explorer per repo/area in parallel, a completeness pass, then a cross-repo seam synthesis. Returns structured findings; the planning lead writes plan.md.',
  phases: [
    { title: 'Explore', detail: 'one read-only explorer per repo/area, in parallel' },
    { title: 'Completeness', detail: 'check for missed repos/areas/unverified seams' },
    { title: 'Synthesize', detail: 'merge per-area findings into one cross-repo seam map' },
  ],
}

// ── inputs (passed via the Workflow `args` value) ───────────────────────────
// args = { goal, repos: string[], outputLanguage, today, knowledgePaths: string[] }
// args SHOULD arrive as a structured JSON object. If the caller passed it as a
// JSON-encoded string (a common Workflow-tool mistake), recover it by parsing —
// otherwise A.goal/A.repos would be undefined and the per-area fan-out silently
// falls back to a single explorer over '.'.
let A = args || {}
if (typeof A === 'string') {
  try { const parsed = JSON.parse(A); if (parsed && typeof parsed === 'object') A = parsed } catch (e) { A = {} }
}
const GOAL = A.goal || 'understand the codebase against the planning goal'
const OUTPUT_LANGUAGE = A.outputLanguage || "the user's language"
const TODAY = A.today || 'unknown'
const KNOWLEDGE = Array.isArray(A.knowledgePaths) ? A.knowledgePaths : []
const AREAS = Array.isArray(A.repos) && A.repos.length ? A.repos : ['.']

// ── schemas (validated at the tool layer; the agent must return these) ───────
const CITE = { type: 'string', description: 'file:line evidence' }
const CONFIDENCE = { type: 'string', enum: ['verified', 'inferred'] }

const FINDINGS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    area: { type: 'string', description: 'the repo/area this explorer mapped' },
    components: { type: 'array', items: { type: 'string' } },
    dataModels: { type: 'array', items: { type: 'string' } },
    apis: { type: 'array', items: { type: 'string' }, description: 'APIs / contracts / interfaces' },
    identifiers: { type: 'array', items: { type: 'string' }, description: 'keys, IDs, tenancy fields' },
    authTenancy: { type: 'string' },
    patterns: { type: 'array', items: { type: 'string' }, description: 'existing conventions to follow' },
    seams: {
      type: 'array',
      description: 'exact points where the new code attaches',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          location: CITE,
          attaches: { type: 'string', description: 'what new code connects here and how' },
          confidence: CONFIDENCE,
        },
        required: ['location', 'attaches', 'confidence'],
      },
    },
    risks: { type: 'array', items: { type: 'string' } },
  },
  required: ['area', 'seams'],
}

const GAPS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    coverageSolid: { type: 'boolean' },
    gaps: {
      type: 'array',
      items: { type: 'string', description: 'an unmapped area, an uncited seam, or an inferred claim that needs code verification' },
    },
  },
  required: ['coverageSolid', 'gaps'],
}

const SYNTH_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    seamMap: {
      type: 'array',
      description: 'the seams BETWEEN areas — how new code connects them',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          between: { type: 'string', description: 'which areas this seam joins' },
          connection: { type: 'string' },
          evidence: CITE,
          confidence: CONFIDENCE,
        },
        required: ['between', 'connection', 'confidence'],
      },
    },
    sharedContracts: { type: 'array', items: { type: 'string' }, description: 'identifiers/API shapes shared across areas' },
    integrationOrder: { type: 'array', items: { type: 'string' }, description: 'dependency-ordered build/integration sequence' },
    openRisks: { type: 'array', items: { type: 'string' } },
  },
  required: ['seamMap'],
}

const RULES = `RULES: read-only — never Write/Edit product code. Cite file:line for every concrete claim. Mark each finding "verified" (you read it in the code) or "inferred". Consult domain knowledge if present: ${KNOWLEDGE.join(', ') || 'none'}.`

// ── 1. Explore: one explorer per area, in parallel ───────────────────────────
phase('Explore')
const explored = (await parallel(AREAS.map((area) => () =>
  agent(
    `You are a read-only explorer for repo/area: ${area}.
Planning goal: ${GOAL}.
Map ONLY what the real code shows, against the goal: components, data models, APIs/contracts, identifiers, auth/tenancy, existing patterns, and the EXACT seams where the new code would attach.
${RULES}`,
    { label: `explore:${area}`, phase: 'Explore', agentType: 'Explore', schema: FINDINGS_SCHEMA },
  ),
))).filter(Boolean)

// ── 2. Completeness: one pass to catch what the fan-out missed ────────────────
phase('Completeness')
const gaps = await agent(
  `Review these exploration findings against the goal "${GOAL}". Identify ONLY genuine gaps: a repo/area/integration point that was never mapped, a seam asserted without a file:line citation, or a claim marked "inferred" that really should be verified in code. If coverage is solid, set coverageSolid=true with an empty gaps list. Do not invent work.
Findings: ${JSON.stringify(explored)}`,
  { label: 'completeness', phase: 'Completeness', schema: GAPS_SCHEMA },
)

// ── 3. Synthesize: merge into one cross-area seam map ─────────────────────────
phase('Synthesize')
const synthesis = await agent(
  `Synthesize a single cross-repo SEAM MAP from these per-area findings, for the planning goal "${GOAL}". Describe the exact seams BETWEEN areas (how new code connects them), the shared identifiers/contracts, and a dependency-ordered integration sequence. Preserve every file:line citation and verified/inferred marker. This is raw structured data for the planning lead, who will write plan.md in ${OUTPUT_LANGUAGE} — return the schema, not prose.
Per-area findings: ${JSON.stringify(explored)}`,
  { label: 'synthesize', phase: 'Synthesize', schema: SYNTH_SCHEMA },
)

return { goal: GOAL, today: TODAY, areas: AREAS, findings: explored, gaps, synthesis }
