# report reference — structure & path

## Path (protocol)
`docs/agent-orchestra/<feature-slug>/<YYYY-MM-DD>/report.md`
(One report per run-completion / feature-day. Same convention `run` already uses for its run report —
`/agent-orchestra:report` formalizes and guarantees it.) Also append a pointer row to
`docs/agent-orchestra/INDEX.md` (the onboarding timeline).

## Structure (write in `OUTPUT_LANGUAGE`, e.g. 한국어)

```
# <기능> — 작업 리포트
> 날짜: <YYYY-MM-DD> · feature: <slug> · plan: <plan.md 링크(있으면)>

## 무엇을 했나
- 구현/변경의 요약 (산문 X, 결과 중심)

## 왜 / 핵심 결정
- 이번 작업에서 내린 결정과 근거 (plan의 locked 결정 + 작업 중 새로 정한 것)

## 변경 파일 / 레포
- 레포·경로별로 무엇이 바뀌었는지 (멀티레포면 레포별)

## 검증 결과 (사실)
- test / lint / build / e2e 결과(객관 게이트), reviewer APPROVE + critic NO BLOCKING 여부
- 실패·생략·미완이 있으면 숨기지 말고 그대로 명시

## 남은 일 / 다음 단계
- 후속 작업, 미해결, 다음 phase
```

## Rules
- **Outcome-faithful**: 실패/생략/미완은 그대로. verify-gate 사실이 정본.
- **Output language only** (literal `OUTPUT_LANGUAGE` from CLAUDE.md).
- Existing report for the same feature+date → **update/extend**, don't duplicate.
- This is the run-completion artifact; the session-level history lives in `INDEX.md` (one line per report).
