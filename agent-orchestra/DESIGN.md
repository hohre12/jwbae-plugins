# orchestra — 멀티에이전트 오케스트레이션 플러그인 설계 문서

> 작성일: 2026-05-20 · 갱신: 2026-05-20 (TBD 6개 확정)
> 상태: 설계 동결(freeze). 구현 착수 전 합의안.
> 이름 `orchestra`는 작업명(working name) — 변경 가능.

Claude Code 기반 멀티에이전트 개발 환경을 **개인 플러그인 하나**로 패키징한다.
사용자는 오직 **오케스트레이터**하고만 대화하고, 오케스트레이터가 요구사항을
분석해 동적으로 팀을 구성하며, **상주 리뷰어 + 상주 감시자**가 모든 산출물을
검증한 뒤 최종 보고한다.

---

## 설계 목적 (Why) — 사용자 명시 목표

1. **표준 `.claude` 세팅 자동화·누락 방지 (최우선 가치).** 공식 `.claude` 표준
   (CLAUDE.md, settings.json, rules, skills, agents, agent-memory, output-styles 등)을
   프로젝트마다 수동 구성하면 항목을 빼먹는다. **이 세팅 과정을 한 번에 완벽히, 누락 없이**
   해주는 것이 이 도구의 1번 가치다. (멀티에이전트 오케스트레이션은 이 단단한 기반 위의 고급 레이어.)
2. **가독성 좋은 관전 (cmux).** tmux의 자잘한 버그/가독성 한계 때문에 cmux 채택.
   화면 가독성 + 브라우저 즉시 띄우기가 핵심 동기. (worktree 격리는 부수 효과, 채택 이유 아님.)
3. **동료 공유 가능.** 본인이 써보고 괜찮으면 동료에게 추천. → 플러그인 패키징 + **개인 비밀정보를
   플러그인에 박지 않기**(secrets는 `userConfig` 프롬프트/전역 설정으로) + 좋은 기본값·낮은 설정 부담.
4. **자기 확증 편향(self-confirmation bias) 교정 — 정확한 작업.** 단일 에이전트 Claude는 처음
   내놓은 해답에 anchoring하여 *스스로를 확증*하는 경향이 있다(공식 Agent Teams 문서도 단일
   에이전트의 anchoring 문제와 debate 구조의 교정 효과를 명시). **매 작업을 멀티에이전트로 진행하고,
   리뷰어 + (적대적) 감시자가 산출물을 challenge**하게 하여 편향을 깨고 정확도를 높이는 것이 목적이다.
   → 이 때문에 리뷰어/감시자 게이트는 *선택적 고급 기능이 아니라 핵심 목적*이다.

---

## 포지셔닝 — 기존 플러그인과의 구분 (중복 방지)

저자(hohre12)는 이미 관련 플러그인을 배포 중이며, orchestra는 이들과 **역할이 다르다.**

| 플러그인 | 초점 | orchestra와의 관계 |
|---|---|---|
| `agent-harmony` | **하네스 엔지니어링** — 요구사항→PRD→팀→build/test/audit/fix 파이프라인, 서버 검증, 강제 게이트 | cmux·Agent Teams 없음. orchestra가 그 빈자리 |
| `immunity` | **검증 스킬** — critic(편향 교정)/contracts/ripple/prodlens | orchestra가 *선택적으로 호출*해 깊은 분석 위임 가능(재구현 X) |

**orchestra의 고유 정체성 = "관전 가능한(observable) 멀티에이전트 오케스트레이션":**
네이티브 **Agent Teams**(팀원 mailbox 통신)를 **cmux 패널**로 실시간 관전하며, 오케스트레이터가
리드로서 조율한다. 여기에 표준 `.claude` 스캐폴딩 + Redmine 브리핑 + Remote Control을 더한다.
즉 *파이프라인 강제(agent-harmony)*나 *검증 스킬(immunity)*이 아니라, **시각적·대화형 팀 조율**이
orchestra의 차별점이다. (필요 시 immunity 스킬을 도구로 호출해 검증을 위임할 수 있다.)

---

## 0. 설계 원칙 (1급 규칙)

1. **엔진과 DNA를 분리한다.** 재사용되는 *로직*은 플러그인(전역, 1회 설치),
   프로젝트마다 달라지는 *내용*은 레포(커밋).
2. **연속성은 프로세스가 아니라 기억(글)이다.** 리뷰어/감시자는 일회용으로
   스폰돼도, 레포에 커밋된 `MEMORY.md`에서 어제의 자신을 복원한다.
   → 물리적 상주 프로세스 불필요.
3. **부탁이 아니라 강제.** CLAUDE.md/프롬프트에 "~해라"는 모델이 무시할 수 있는
   *부탁*이다. 반드시 지킬 것은 **hooks·shim·스킬 스크립트**로 하네스가 강제한다.
4. **임시 처리·누락·미루기 금지.** 한 번에 완벽하게. (덮어쓰기 대신 통합, 우회 대신 해결.)
5. **변경은 항상 제안 → 사용자 승인(approval gate).** 멋대로 바꾸지 않는다.
6. **공유 가능하게.** 플러그인에 개인 비밀정보·머신 고유값을 박지 않는다. 비밀은
   `userConfig` 프롬프트 또는 전역 설정으로. 좋은 기본값으로 동료가 낮은 설정 부담으로 시작.

---

## 1. 시스템 아키텍처

```
                    ┌─────────────── 사용자 ───────────────┐
              로컬 터미널(cmux)          Remote Control(폰/웹)
                    └──────────────┬──────────────────────┘
                                   ▼
                      ╔════════════════════════╗
                      ║   오케스트레이터        ║  ← 유일한 대화 창구 = 팀 리드
                      ║   (Claude Code, 리드)   ║     /orchestrate
                      ╚════════════╤═══════════╝
            triage·재조정 │ 요구분석 │ 팀 구성
         ┌────────────────┼─────────────────────────┐
         ▼                ▼                          ▼
   [동적 워커들]      [상주 리뷰어]              [상주 감시자]
   (병렬 작업)        memory:project             memory:project
   cmux 패널          MEMORY.md 누적             MEMORY.md 누적
         │                ▲  팀원끼리 메일박스로 직접 대화 ▲
         └─ 작업 완료 ─────┴──── 리뷰 게이트(훅 강제) ─────┘
                  통과해야 → 오케스트레이터 최종 보고

   외부 연동(MCP):  Redmine(이슈 브리핑)  ·  Supabase/GitHub(진단)
```

- **오케스트레이터 = 팀 리드.** 사용자와 대화하는 유일한 창구.
- **워커 = 팀원.** 작업 성격에 맞게 동적 스폰. 각자 독립 컨텍스트.
- **리뷰어 / 감시자 = 상주 팀원.** 패널에서 워커 산출물을 실시간 challenge.
  사용자가 cmux 패널로 토론을 지켜보고, 필요하면 패널 클릭으로 직접 개입.
- 실행 모델 = 네이티브 **Agent Teams** (팀원끼리 mailbox 통신 + 공유 task list).

---

## 2. 무엇이 어디에 사는가

### 2.1 플러그인 (전역, 1회 설치, 모든 프로젝트 재사용) — **[확정: 플러그인 패키징]**

설치 스코프는 `user`(전역, `~/.claude/settings.json`, 기본값)로 설치 → 모든 프로젝트에서 사용.

```
orchestra/                          # 개인 git 레포 = 마켓플레이스
├── .claude-plugin/
│   ├── plugin.json                 # 매니페스트 (§2.4)
│   └── marketplace.json            # 마켓플레이스 등록 (§2.5)
├── skills/
│   ├── orchestrate/SKILL.md        # /orchestrate         ← 오케스트레이터 두뇌
│   ├── orchestrate-init/SKILL.md   # /orchestrate init    ← triage + 스캐폴딩
│   └── briefing/SKILL.md           # /orchestrate briefing ← Redmine 브리핑
├── agents/                         # 베이스 정의 (원형)
│   ├── reviewer.md                 #   memory: project
│   ├── critic.md                   #   memory: project
│   └── archetypes/                 #   워커 원형 (§2.3)
│       ├── backend.md   ├── frontend.md  ├── test.md
│       ├── explorer.md  ├── architect.md └── devops.md
├── hooks/
│   └── hooks.json                  # 리뷰 게이트·팀 강제 등 결정성 레이어
├── scripts/                        # 훅이 호출하는 스크립트 (${CLAUDE_PLUGIN_ROOT}/scripts/...)
└── templates/                      # init이 레포에 찍어내는 골격
    ├── CLAUDE.md.tmpl  ├── rules/*.tmpl  └── mcp.json.tmpl
```

### 2.2 프로젝트 레포 (init이 생성·커밋, 프로젝트별 튜닝)

```
your-project/
├── CLAUDE.md                       # 오케스트레이터 SSOT (성숙도 단계/스택/팀 로스터/컨벤션 요약, <200줄)
├── .mcp.json                       # 이 프로젝트의 Redmine·Supabase 등
└── .claude/
    ├── settings.json               # env teams=1, teammateMode "tmux"  (커밋)
    ├── rules/                      # path-scoped 컨벤션 (해당 경로 만질 때만 로드)
    ├── agents/                     # archetype을 상속·오버라이드한 프로젝트 인스턴스
    └── agent-memory/               # 네이티브 영속 기억 (자동 read/write, 커밋)
        ├── reviewer/MEMORY.md
        └── critic/MEMORY.md
```

> `bypassPermissions`는 레포가 아니라 **전역** 설정에 둔다(§7).

### 2.3 워커 archetype 모델 — **[확정: 상속 + 오버라이드]**

- 플러그인이 6개 원형을 보유: **backend / frontend / test / explorer / architect / devops**.
- 각 원형은 역할 골격 + 플레이스홀더(`{{STACK}}`, `{{TEST_CMD}}`, `{{CONVENTIONS}}` 등).
- `init`이 triage로 읽은 프로젝트 값으로 빈칸을 채워 **레포 `.claude/agents/`에 인스턴스 생성**.
- 프로젝트가 원형에 없는 역할이 필요하면 그 프로젝트 레포에만 추가(오버라이드/확장).
- 효과: DRY·일관성(원형은 하나) + 프로젝트별 자유(인스턴스는 튜닝).

### 2.4 `plugin.json` 매니페스트 (확정 스키마)

```json
{
  "name": "agent-orchestra",
  "displayName": "Agent Orchestra",
  "version": "0.1.0",
  "description": "Observable multi-agent orchestration: lead + dynamic workers + standing reviewer/critic, watched live in cmux panes",
  "author": { "name": "jwbae", "email": "hohre12@gmail.com" },
  "homepage": "https://github.com/hohre12/jwbae-plugins/tree/main/agent-orchestra",
  "repository": "https://github.com/hohre12/jwbae-plugins",
  "license": "MIT",
  "keywords": ["agent-teams", "orchestrator", "multi-agent", "cmux", "code-review", "agent-memory"]
}
```

- 컴포넌트(skills/agents/hooks/.mcp.json)는 **표준 위치에 두면 자동 발견**된다. 비표준 경로만
  `"skills": "./custom/skills/"`, `"agents": ["./custom/agents/x.md"]` 식으로 매니페스트에서 오버라이드.
- `hooks`는 `hooks/hooks.json` 또는 `plugin.json` 인라인. MCP는 `.mcp.json` 또는 인라인.
- 스크립트 경로는 항상 **`${CLAUDE_PLUGIN_ROOT}`** 변수로 참조(설치 위치 무관).
- `claude plugin validate`는 미인식 필드를 *경고*로만 처리(로드는 됨). 타입 오류만 실패.
- ⚠️ **`.claude-plugin/` 안에는 `plugin.json`만.** `skills/`·`agents/`·`hooks/`·`.mcp.json`은 모두
  플러그인 **루트**에 둔다(공식 문서가 지적하는 흔한 실수). `templates/`·`scripts/`는 비표준 보조
  디렉토리로 루트에 두고 `${CLAUDE_PLUGIN_ROOT}`로 참조(자동 발견 대상 아님).
- ⚠️ **스킬은 네임스페이스됨.** 플러그인 `agent-orchestra`의 스킬은 `/agent-orchestra:init`,
  `/agent-orchestra:run`, `/agent-orchestra:briefing` 형태로 호출된다(설계 본문의 `/orchestrate`는
  `/agent-orchestra:run`으로 매핑).
- 개발/테스트는 `claude --plugin-dir ./agent-orchestra` + `/reload-plugins`로 (설치 없이 즉시 반영).

### 2.5 배포 전략 — **[확정: monorepo (jwbae-plugins 안)]**

`agent-orchestra`는 별도 레포가 아니라 **기존 마켓플레이스 레포 `hohre12/jwbae-plugins` 안**에
`agent-orchestra/` 디렉토리로 산다(monorepo). marketplace.json은 상대경로로 가리킨다:

```json
{ "name": "agent-orchestra", "source": "./agent-orchestra", "...": "..." }
```

- **이유:** 업데이트 = `jwbae-plugins`에 **한 번 푸시**. catalog/코드 분리·이중 푸시 없음.
- **버전 단일 출처:** marketplace 엔트리에 `version`을 넣지 않고 **플러그인의 `plugin.json` version**으로만
  관리(해석 우선순위상 plugin.json이 이김). 업데이트 시 `plugin.json` version만 bump.
- 기존 `immunity`·`agent-harmony`·`feed`는 외부 `github` 엔트리 그대로 둔다(상대경로 + github 혼용 허용).
- 설치:
  ```bash
  /plugin marketplace add hohre12/jwbae-plugins
  /plugin install agent-orchestra@jwbae-plugins   # 기본 user 스코프(전역)
  ```
- 스코프: `user`(전역, 기본) / `project` / `local` / `managed`.

> `source` 타입: 상대경로(`"./x"`, monorepo) · `github`(외부 repo) · `git`(repo 하위경로) · `npm`.
> 업데이트 시 이중 푸시는 marketplace 엔트리에 `sha`를 핀할 때만 발생 — 본 설계는 핀하지 않는다.

### 2.6 항목별 소재 정리

| 항목 | 소재 | init이 프로젝트 튜닝? | 비고 |
|---|---|---|---|
| `skills/` (엔진 진입점) | **플러그인 (고정)** | ❌ | 1회 배포·전 프로젝트 재사용 |
| `agents/archetypes`, `agents/{reviewer,critic}` 베이스, `hooks/`, `scripts/` | **플러그인 (고정)** | ❌ | 범용 로직 |
| `rules/` | 레포 | ✅ | 프로젝트 컨벤션 |
| `agents/` (인스턴스) | 레포 | ✅ | archetype → 스택 맞춰 빈칸 채움 |
| `agent-memory/` | 레포 | ✅ 자동 | init은 빈 그릇만, 이후 에이전트가 누적 |
| `CLAUDE.md`, `.mcp.json` | 레포 | ✅ | SSOT·연동 |
| `output-styles/` | (선택) | ➖ | 보통 사용자 전역 취향. 프로젝트 고유 보고 톤 필요 시만 |
| `bypassPermissions` | **전역 `~/.claude`** | ❌ | §7 |

### 2.7 표준 `.claude` 스캐폴딩 보장 — **[설계 목적 1번: 누락 방지]**

`/orchestrate init`은 공식 `.claude` 표준의 모든 슬롯을 **체크리스트로 순회**하여, 각 항목을
*생성하거나 의식적으로 N/A 처리*한다. "조용히 빼먹기"가 구조적으로 불가능하게 만든다.

| 표준 슬롯 | init 처리 | 로딩 시점 |
|---|---|---|
| `CLAUDE.md` | 생성(SSOT) | 매 세션 |
| `.claude/settings.json` | 생성(env, teammateMode) | 세션 시작 |
| `.claude/rules/` | 컨벤션 추출해 생성 | path-scoped |
| `.claude/agents/` | archetype 인스턴스화 | 스폰 시 |
| `.claude/agent-memory/` | 빈 그릇 생성(이후 자동 누적) | 서브에이전트 시작 |
| `.claude/output-styles/` | 기본 N/A(필요 시 보고 톤 생성) | 선택 |
| `.mcp.json` | Redmine/Supabase 등 생성 | — |
| `skills/` | 플러그인 제공(프로젝트 고유만 예외) | 호출 시 |

- init은 매 실행마다 이 체크리스트를 재점검(재조정 루프) → 누락분을 *제안*(승인 게이트).
- 비밀정보(예: Redmine API 키)는 파일에 평문 저장하지 않고 `userConfig` 프롬프트/전역으로(원칙 6).

---

## 3. 연속성 — 네이티브 agent-memory

- 리뷰어/감시자 정의에 **`memory: project`** → `.claude/agent-memory/<name>/MEMORY.md` 자동 생성.
  - `memory: project` → 레포 커밋, 팀 공유 (**기본값, 메모리는 항상 프로젝트 스코프 고정**)
  - (`local`/`user` 옵션 존재하나 본 설계에서는 미사용)
- 서브에이전트는 매 작업 시작 시 MEMORY.md를 읽고, 끝에 배운 걸 써넣음(자동, 첫 200줄/25KB 주입).

### 3.1 팀원 메모리 주입 — **[확정: 항상 수동 주입(belt-and-suspenders)]**

서브에이전트 정의를 *팀원*으로 쓸 때 `memory:` 자동 주입 여부는 문서가 침묵한다(서브에이전트
기준으로만 보장). **검증 결과에 의존하지 않고**, 리드가 항상 명시적으로 처리한다:

1. 리뷰어/감시자 팀원 스폰 *직전*, 리드가 `agent-memory/<name>/MEMORY.md`를 읽어 **스폰 프롬프트에 주입**.
2. 리뷰/비평 종료 시 교훈을 그 파일에 **써넣도록 지시**.

→ 네이티브 `memory:`가 팀원에도 동작하면 *중복 안전망*이 될 뿐, 설계는 거기 의존하지 않는다.

---

## 4. 결정성(determinism) 강제 레이어

| 강제 대상 | 강도 | 수단 |
|---|---|---|
| **리뷰 게이트** | 하드 | `TaskCompleted`/`TeammateIdle`/`Stop` 훅 exit 2 — 리뷰/비평 task 미완이면 종료 불가 |
| **cmux/tmux 혼동 제거** | 하드 | `cmux claude-teams`의 tmux shim이 명령을 cmux API로 번역 → 모델이 구분 불필요 |
| **매번 팀 사용** | 준-하드 | ⓐ `/orchestrate` 스킬이 1단계로 팀 생성 스크립트 + ⓑ `Stop` 훅이 `~/.claude/teams/`에 활성 팀 없으면 exit 2 차단 |
| **위험 명령 차단** | 하드 | `PreToolUse` 훅 (예: 파괴적 명령, `.env` 읽기 등) |
| **재조정 변경** | 승인 게이트 | 항상 제안 → 사용자 승인(B) |

> 직접적인 "pre-team" 훅 이벤트는 없으므로 "매번 팀"은 스킬 스크립트 + Stop 훅 조합으로 사실상 강제.

---

## 5. 재조정 루프 (reconcile loop)

고정된 `init` 한 번이 아니라, 진입 시마다 **현재 레포 상태 ↔ 기록된 DNA를 diff**하여 팀 구성을
재조정(Terraform desired-state 패턴).

### 5.1 Triage — 성숙도 분류 (Phase 0)

신호: 코드/테스트/CI/의존성 매니페스트/PRD·아키텍처 문서/git 히스토리/기존 `.claude` 유무.

| 시작 상태 | 첫 행동 | 팀 무게중심 |
|---|---|---|
| 그린필드(빈 레포+아이디어) | 요구사항 추출 모드 — plan mode 인터뷰(§5.2) → PRD·스택·스켈레톤 | architect/explorer |
| 스펙만(문서 O, 코드 X) | 문서에서 의도 추출 → 계획 스택 기준 팀 | architect + 초기 워커 |
| 개발 중(부분 코드) | 실제 관용구 분석 → 현실 컨벤션에 맞춤 | worker 다수 + reviewer |
| 완성/유지보수 | git 히스토리·테스트로 루브릭 시딩 | reviewer/critic 중심 |
| 레거시(물려받음) | 고고학 패스(이해 지도 먼저) | explorer + reviewer |

기존 하네스(이미 있는 agents/skills/loop)를 감지하면 **덮어쓰지 않고 재사용·통합을 제안**(원칙 4).

### 5.2 그린필드 인터뷰 깊이 — **[확정: 표준]**

- plan mode로 진행. **사용자가 명시적으로 승인할 때까지** plan/PRD md를 함께 채운다.
- **표준 깊이 = ① PRD 핵심(목표·범위·핵심 유저스토리) + ② 스택 결정 + ③ 핵심 아키텍처 결정**
  까지 합의되면 코드로 진입. (데이터모델·API 전체 윤곽은 진입 후 워커가 채움.)
- 승인 대상 = *대화*가 아니라 *문서(plan/PRD md)*. 그 문서가 단계 전환 트리거.
- 무한 인터뷰 방지: "그냥 진행(승인)" 탈출구 상시 제공, 승인된 결정 재논의 금지.

### 5.3 자동성 수위 — **[확정: B = 승인 게이트]**

재조정이 팀 변경을 감지하면 **제안만 하고 사용자 승인 후 적용**. 자동 적용 안 함.

---

## 6. cmux 통합 (시각화·격리)

- **채택 이유(설계 목적 2번):** 화면 **가독성** + tmux 자잘한 버그 회피 + **브라우저 즉시 띄우기**
  (localhost 프론트·문서 확인). 즉 *관전 UX*가 cmux 채택의 동기. worktree 격리는 부수 효과.
- **`cmux claude-teams`**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 세팅 + PATH에 tmux shim 설치
  → Claude Code의 tmux 호출(`split-window`/`send-keys`/`capture-pane`)을 cmux 네이티브 split/workspace
  API로 번역 → cmux 패널에서 팀원 토론 시각화.
- `teammateMode: "tmux"`와 함께 동작(shim이 가로챔).
- worktree-per-worker: **git 저장소일 때만** cmux가 각 워커를 독립 worktree로 격리(브랜치 충돌 방지).
  git이 아니면 in-process + 리드가 파일 분담.
- ⚠️ **cmux 재시작 = 라이브 프로세스 소실**(MEMORY.md 기억은 레포에 생존). 작업 중 cmux를 끄지 않는다.

---

## 7. 설정(settings)

| 키 | 파일 | 비고 |
|---|---|---|
| `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS = "1"` | 프로젝트 `.claude/settings.json` (커밋) | ⚠️ **다음 세션부터 적용**. init 후 재실행 안내 |
| `teammateMode = "tmux"` | 프로젝트 `.claude/settings.json` (커밋) | cmux shim이 가로챔 |
| `--dangerously-skip-permissions` (= bypassPermissions) | **`cgo` alias (셸)** | **[확정]** 사용자가 이미 `alias cgo="claude --dangerously-skip-permissions"` 사용. settings.json에 둘 필요 없음 |

→ env 적용 특성상 **Phase 1(init·셋업)과 Phase 2(실사용)는 세션이 갈리는 게 정상**.

### 7.1 일상 진입 = `cgo` 한 번 — **[확정]**

- **bypass** = `cgo` 플래그가 처리. **AGENT_TEAMS env** = 프로젝트 `.claude/settings.json`이 처리.
  → 이 둘 때문에 `cmux claude-teams`를 매일 칠 필요는 없다.
- `cmux claude-teams`의 *유일한 잔여 역할* = tmux→cmux 패널 shim. 이를 `cgo`에 결합:
  ```sh
  alias cgo="cmux claude-teams && claude --dangerously-skip-permissions"
  ```
  → 일상 진입은 `cgo` 한 번으로 끝.
- ⚠️ shim이 세션 단위인지 영구 등록 가능한지는 **구현 후 실측**(§11.1). 결과에 따라 alias 결합 방식 확정.

---

## 8. Agent Teams 제약 (설계가 지키는 한계)

- **한 번에 한 팀** / **중첩 팀 불가**(팀원이 또 팀 못 만듦) / **리드 고정**(오케스트레이터가 평생 리드).
- in-process 팀원은 `/resume`·`/rewind` 복구 안 됨. task 상태 누락·종료 지연 가능(실험적).
- 권한은 스폰 시점에 리드 것 상속(`bypassPermissions`면 팀원도 전부).

---

## 9. 사용자 흐름 (전체 생애주기)

```
[평생 1회]   cmux 설치 → claude plugin marketplace add <repo> → claude plugin install orchestra
              → cgo alias 결합: alias cgo="cmux claude-teams && claude --dangerously-skip-permissions"
[프로젝트 1회] cd 프로젝트 → cgo → /orchestrate init
              → triage(그린필드=표준 인터뷰·승인 / 코드 있음=분석) → .claude/ 생성·커밋(env teams=1, teammateMode tmux)
              → (세션 재시작: env 적용)
[매일]        cmux → cd 프로젝트 → cgo → /orchestrate
              → 재조정 루프 변경점 제안→승인(B)
              → 자연어 요구사항 투척
              → 리드가 팀 구성: 워커(archetype 인스턴스) + 상주 리뷰어 + 상주 감시자 (MEMORY.md 주입)
              → cmux 패널에서 팀원 메일박스 토론 (사용자 관전/개입)
              → 리뷰/비평 task 완료 강제(훅) → 통과해야 마무리
              → 리뷰어/감시자 MEMORY.md 기록 → 오케스트레이터 최종 보고
[출근]        /orchestrate briefing → Redmine 할당 이슈 브리핑 → 선택/자연어 지시
[외부]        claude remote-control → 폰/웹에서 오케스트레이터와 대화 + 모바일 푸시
```

---

## 10. 요구사항 매핑

| # | 요구사항 | 구현 | 상태 |
|---|---|---|---|
| 1 | 오케스트레이터-only 대화 + 동적 팀 + 상주 리뷰어/감시자 검증 | Agent Teams(리드+팀원) + 상주 리뷰어/감시자 + 게이트 훅 | **v1 핵심** |
| 2 | 서버 상주 에이전트와 통신해 배포 서비스 진단 | 원격 헤드리스 Claude Code를 MCP 서버로 노출 → 오케스트레이터가 도구 호출 | **v2** (인터페이스 seam 고정) |
| 3 | 출근 시 Redmine 할당 이슈 브리핑 | Redmine MCP + `/orchestrate briefing` (또는 SessionStart 훅) | **v1** |
| 4 | Remote Control / Discord 창구 | 네이티브 Remote Control(v1) / Discord 브리지(v2) | RC=v1 |
| - | 이종(GPT) 감시자 | 무상태 2차 의견 | **v2** (인터페이스 seam 고정) |

### 10.1 v2 인터페이스 seam (지금 고정, 구현은 나중) — **[확정]**

v2 항목들이 나중에 깔끔히 붙도록, v1에서 **호출 인터페이스만 MCP 도구로 고정**해 둔다:

- **이종 감시자**: 감시자 호출을 `critic.review(target, context) -> findings` 형태의 MCP 도구로
  추상화. v1은 이 도구 뒤에 Claude 감시자를 두고, v2에서 GPT 등으로 *구현만 교체*. 오케스트레이터 불변.
- **서버 진단**: `investigate_incident(service, symptom) -> diagnosis` MCP 도구 시그니처를 예약.
  v1은 미구현(stub), v2에서 원격 헤드리스 에이전트로 backing.

---

## 11. 결정 로그 (TBD → 확정)

| # | 항목 | 확정 |
|---|---|---|
| 1 | 워커 archetype 모델 | **상속 + 오버라이드.** 원형 6종(backend/frontend/test/explorer/architect/devops), init이 인스턴스화 (§2.3) |
| 2 | 그린필드 인터뷰 깊이 | **표준.** PRD 핵심 + 스택 + 핵심 아키텍처 결정까지 합의 후 진입 (§5.2) |
| 3 | plugin/marketplace 매니페스트 | **확정.** 공식 스키마 반영 (§2.4–2.5) |
| 4 | `memory:` 팀원 적용 | **항상 수동 주입.** 검증에 의존 안 함 (§3.1) |
| 5 | `bypassPermissions` 위치 | **전역 `~/.claude`.** 프로젝트 파일에 두지 않음 (§7) |
| 6 | 요구사항2 / 이종 감시자 | **v2로 분리 + 인터페이스 seam 고정** (§10.1) |
| - | 패키징 | **플러그인** (user 스코프 설치) (§2) |
| - | 자동성 수위 | **B = 승인 게이트** (§5.3) |
| - | 구현 단계 | **v1에 스캐폴더+오케스트레이션+cmux+게이트 전부 포함**, GPT 감시자/서버진단은 v2 (§12) |
| - | 설계 목적 | 4가지: 표준세팅 누락방지 · cmux 가독성 · 동료공유 · 자기확증편향 교정 (§설계 목적) |

### 11.1 구현 시 실측 확인(설계 변경 아님)

- `cmux claude-teams` 정확한 명령/플래그 + **shim이 세션 단위인지 영구 등록 가능한지** (cgo alias 결합 방식 확정)
- `teammateMode: "tmux"`가 cmux shim 위에서 패널을 실제로 띄우는지
- `Stop` 훅에서 `~/.claude/teams/` 활성 팀 탐지 방식
- `claude plugin validate` 통과 확인

---

## 12. 구현 단계 (Phasing) — **[확정]**

- **v1 (최초 빌드, 완벽하게 — 목적 1·2·3·4 전부 충족):**
  - 표준 `.claude` 스캐폴더 (`/orchestrate init`, 누락 방지 체크리스트) — 목적 1
  - 멀티에이전트 오케스트레이션: 병렬 워커 + 상주 리뷰어 + 상주 감시자, 팀원 mailbox 토론 — 목적 4
  - cmux 패널 관전(`cmux claude-teams` shim) + 동적 팀 스케일링 — 목적 2
  - 리뷰/비평 게이트(훅 강제, 자기 확증 편향 교정) — 목적 4
  - Redmine 브리핑 + 네이티브 Remote Control — 요구사항 3·4
  - 플러그인 패키징(공유 가능, 비밀정보 미포함) — 목적 3
  - **v2 인터페이스 seam(`critic.review`, `investigate_incident`)은 v1에 미리 고정** (§10.1)
- **v2 (차후 추가, seam에 꽂기만):**
  - GPT 이종 감시자 (seam 뒤 구현만 교체)
  - 서버 상주 진단 에이전트, Discord 창구
- **원칙:** v1은 "한 번에 완벽하게"(원칙 4). 임시 처리·누락·미루기 없이 v1.5 범위까지 한 번에 출시.

---

## 부록 A. 핵심 참고 문서

- Agent Teams: https://code.claude.com/docs/en/agent-teams
- .claude 디렉토리 표준: https://code.claude.com/docs/en/claude-directory
- 서브에이전트/영속 메모리: https://code.claude.com/docs/en/sub-agents#enable-persistent-memory
- Hooks: https://code.claude.com/docs/en/hooks
- 플러그인 레퍼런스: https://code.claude.com/docs/en/plugins-reference
- Remote Control: https://code.claude.com/docs/en/remote-control
- cmux: https://cmux.com · cmux + Claude teams: https://cmux.com/blog/cmux-claude-teams
