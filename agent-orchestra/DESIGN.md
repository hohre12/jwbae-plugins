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

monorepo `hohre12/jwbae-plugins` 안의 `agent-orchestra/` 디렉토리(§2.5).

```
agent-orchestra/                    # jwbae-plugins 안의 플러그인 디렉토리
├── .claude-plugin/
│   └── plugin.json                 # 매니페스트 (§2.4)  ← .claude-plugin엔 이것만
├── skills/                         # 네임스페이스: /agent-orchestra:<name>
│   ├── init/SKILL.md               # /agent-orchestra:init     ← triage + 스캐폴딩
│   ├── run/SKILL.md                # /agent-orchestra:run      ← 오케스트레이터 두뇌
│   └── briefing/SKILL.md           # /agent-orchestra:briefing ← Redmine 브리핑
├── agents/                         # 자동 발견되는 실제 플러그인 에이전트
│   ├── orchestrator.md             #   메인 스레드 페르소나 (init이 프로젝트 default agent로 지정)
│   ├── reviewer.md                 #   memory: project (color: blue)
│   └── critic.md                   #   memory: project (color: red)
├── hooks/
│   └── hooks.json                  # 리뷰 게이트·팀 강제 등 결정성 레이어
├── scripts/                        # 훅이 호출하는 스크립트 (${CLAUDE_PLUGIN_ROOT}/scripts/...)
├── templates/                      # 비자동발견 보조. init이 ${CLAUDE_PLUGIN_ROOT}/templates/로 읽음
│   ├── CLAUDE.md.tmpl  rules/*.tmpl  mcp.json.tmpl
│   └── archetypes/                 #   워커 원형 (§2.3) — 템플릿이라 agents/ 아닌 여기 둠
│       ├── backend.md  frontend.md  test.md
│       └── explorer.md  architect.md  devops.md
└── .mcp.json                       # 루트 (자동 발견)
```

> ⚠️ 워커 archetype은 `{{placeholder}}`가 든 *템플릿*이다. `agents/`에 두면 런타임에 깨진
> 에이전트로 로드되므로 자동 발견되지 않는 `templates/archetypes/`에 둔다. `init`이 프로젝트
> 값으로 채워 그 프로젝트의 `.claude/agents/`에 *실제* 워커로 인스턴스화한다.

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

- 플러그인이 `templates/archetypes/`에 6개 원형 보유: **backend / frontend / test / explorer / architect / devops**.
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
| `templates/archetypes`, `agents/{reviewer,critic}`, `hooks/`, `scripts/`, `templates/` | **플러그인 (고정)** | ❌ | 범용 로직 |
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

## 3. 연속성 — 수동 관리 agent-memory (bare path 정본)

- 메모리 정본 = `.claude/agent-memory/{orchestrator,reviewer,critic}/`(레포 커밋·공유). **bare path가 정본.**
- reviewer/critic 정의엔 **`memory:` frontmatter 없음** — 네이티브가 `agent-orchestra-*` 네임스페이스 빈 폴더를
  만드는 것을 막기 위함(v1.4 Q4 수정). 메모리는 전적으로 **수동 관리**.
- `MEMORY.md`는 간결 인덱스(첫 200줄/25KB만 로드), 상세는 토픽 파일 on-demand.

### 3.1 팀원 메모리 주입·기록 — **[확정: 수동, bare path]**

1. 리드(`/run`)가 reviewer/critic 스폰 *직전*, `agent-memory/{name}/MEMORY.md`(+토픽)를 읽어 **스폰 프롬프트에 주입**.
2. reviewer/critic은 **Write 도구가 없으므로 `Bash`(`>>`)로** bare path에 write-back(인덱스 유지).
3. orchestrator 메모리도 `/run`이 bare path에서 직접 read/write.
→ 네이티브 네임스페이스 폴더 미사용(단일 진실). 산출물·메모리는 **사용자 언어**로 기록(지침은 영어).

#### Q4/Q5 수정 (v1.4)
- **Q4**: reviewer/critic `memory:` 제거 → `agent-orchestra-*` 빈 폴더 제거, bare path 단일화.
- **Q5**: 산출물(PRD/design/review/report)·메모리는 사용자 언어, 지침(.md·CLAUDE.md·skills)은 영어.

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

### 5.4 호출 모델 — **[확정: b+c 호출형 / v1.4, v1.1의 always-on 철회]**

> v1.1에선 `agent: orchestrator`로 *강제 always-on*이었으나, **AI-DLC(체크포인트/bolt 기반)와 플러그인
> 관례(호출형)와 충돌**하고 opt-out이 불가해 **철회**했다(§14 근거). 대신 **b+c 호출형**:

- **(b) 명시 호출**: `/agent-orchestra:run <요구>`로 사용자가 오케스트레이션을 시작(= bolt를 사람이 연다).
- **(c) 모델 자동호출**: `run` 스킬에 `disable-model-invocation` 없음 + "substantive coding work" 트리거
  description → Claude가 실질 작업이라 판단하면 자동 호출. 단순 질문/한 줄 수정은 plain Claude.
- **always-on 아님**: `init`은 `agent` 키를 쓰지 않는다. 평소엔 plain Claude → **언제든 opt-out**.
- 오케스트레이터는 별도 메인스레드 에이전트가 아니라 **`run` 스킬 자체**(메인 세션이 그 절차로 리드가 됨).
  오케스트레이터 메모리는 `run` 스킬이 `.claude/agent-memory/orchestrator/MEMORY.md`를 직접 read/write.
- 리뷰어/감시자는 여전히 *반응형 팀원* — `run` 시 소환 + 게이트로 강제.
- ✅ 인터랙티브 실측 완료(v1.2~v1.3): 팀 스폰·패널 분할·게이트·메모리 주입 동작 확인.

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
| `--dangerously-skip-permissions` (= bypassPermissions) | **`cgo` alias (셸)** | **[확정]** `cmux claude-teams`가 인자를 claude로 전달하므로 `alias cgo="cmux claude-teams --dangerously-skip-permissions"`로 묶음(§7.1). settings.json에 둘 필요 없음 |

→ env 적용 특성상 **Phase 1(init·셋업)과 Phase 2(실사용)는 세션이 갈리는 게 정상**.

### 7.1 일상 진입 = `cgo` 한 번 — **[확정]**

`cmux claude-teams`는 **런처**다(검증됨): `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 설정 +
`--teammate-mode auto` + tmux 유사 env(TMUX/TMUX_PANE/TERM) 주입 + private tmux shim을 PATH 앞에
prepend + **이후 인자를 claude로 전달하며 claude를 직접 실행**한다.

- 따라서 올바른 alias는 인자를 전달하는 형태다(런처가 claude를 실행하므로 별도 `&& claude` 불필요):
  ```sh
  alias cgo="cmux claude-teams --dangerously-skip-permissions"
  ```
  → 일상 진입은 `cgo` 한 번. bypass는 전달된 플래그가, 팀 활성/패널은 런처가 처리.
- shim은 **세션 단위**(런처가 매 실행마다 설정) → 영구 PATH 등록 불필요. 항상 `cgo`(런처)로 진입하면 됨.
- `teammateMode`: 런처가 `auto` + TMUX env 주입으로 이미 cmux split panes를 띄우므로 `.claude/settings.json`의
  `teammateMode: "tmux"`는 **불필요**(비-cmux 실행 대비 belt-and-suspenders로 둘 수는 있음).
- 자세한 셋업·실측 체크리스트: `docs/cmux-setup.md`.

---

## 8. Agent Teams 제약 (설계가 지키는 한계)

- **한 번에 한 팀** / **중첩 팀 불가**(팀원이 또 팀 못 만듦) / **리드 고정**(오케스트레이터가 평생 리드).
- in-process 팀원은 `/resume`·`/rewind` 복구 안 됨. task 상태 누락·종료 지연 가능(실험적).
- 권한은 스폰 시점에 리드 것 상속(`bypassPermissions`면 팀원도 전부).

---

## 9. 사용자 흐름 (전체 생애주기)

```
[평생 1회]   cmux 설치 → claude plugin marketplace add <repo> → claude plugin install orchestra
              → cgo alias 결합: alias cgo="cmux claude-teams --dangerously-skip-permissions"
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

- ✅ `cmux claude-teams` = 런처(env+auto+shim+claude 실행, 인자 전달), shim은 세션 단위 →
  alias `cgo="cmux claude-teams --dangerously-skip-permissions"` 확정 (§7.1, `docs/cmux-setup.md`)
- ⏳ 인터랙티브 실측(`docs/cmux-setup.md` 체크리스트): 팀원이 실제 cmux 패널로 뜨는지, reviewer(파랑)/
  critic(빨강) 색 구분, 패널 클릭 개입, cmux 버전의 `claude-teams` 지원
- ✅ `claude plugin validate` 통과 확인 (전 태스크에서 통과)
- ⏳ E2E: 빈 프로젝트에서 init→run→gate→report (Task #13, 인터랙티브)

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
- **v1.1 (always-on, 프로젝트 스코프):** `orchestrator` 메인 스레드 페르소나 + init이 프로젝트
  `agent: orchestrator` 설정 → `/run` 없이도 모든 실질 작업이 팀+게이트를 거침 (§5.4)
- **v1.2 (최종 목표 2·4·5 + native 게이트):** §13
  - 목표2: init/재조정 propose→approve→apply HITL 게이트(전 단계)
  - 목표4: `{{OUTPUT_DIR}}`(기본 `docs/agent-orchestra/{prd,design,review,reports}/`)에 산출물 저장
  - 목표5: `.claude/knowledge/` + CLAUDE.md `@import`(native 로드) + rules/
  - native 게이트: `TaskCompleted`/`TeammateIdle` 훅 + Stop 백스톱
- **v1.3 (흐름·TDD·오케스트레이터 메모리):** §14
  - 오케스트레이터 흐름: 이해·구체화(HITL) → 분해·승인(HITL) → task 루프(계약→TDD→게이트→**task별 보고**)
  - TDD: 독립 `test` 워커가 실패 테스트 먼저, 구현은 green (task 의존성으로 test-first 강제)
  - 오케스트레이터 `memory: project` (커밋·공유)
- **v1.4 (호출모델·경로·정리·메모리):** §15
  - **always-on 철회 → b+c 호출형**(명시 `/run` + substantive work 자동호출), opt-out 가능
  - 산출물: 프로젝트 PRD=`docs/PRD.md`(분리), 도구산출물=`agent-orchestra/<기능>/<날짜>/`, 무게 비례
  - 팀 정리 지침 강화(패널 수동닫기는 upstream 한계), 메모리 인덱스 패턴 + 컨텍스트 가드
- **v2 (차후 추가, seam에 꽂기만):**
  - GPT 이종 감시자 (seam 뒤 구현만 교체)
  - 서버 상주 진단 에이전트, Discord 창구
- **원칙:** v1은 "한 번에 완벽하게"(원칙 4). 임시 처리·누락·미루기 없이 v1.5 범위까지 한 번에 출시.

---

## 13. 최종 목표 5개 — 구현 매핑 (v1.2)

사용자가 명시한 최종 목표 5개의 구현 상태:

| # | 목표 | 상태 | 메커니즘 |
|---|---|---|---|
| 1 | 프로젝트 스코프별 최적 세팅 | ✅ | init triage→스캐폴딩(헤드리스 검증), archetype 인스턴스화, 재조정 루프 |
| 2 | HITL로 하나씩 승인하며 진행 | ✅(구조) | init/재조정 **propose→approve(AskUserQuestion)→apply**, 전 단계. 승인 일시정지는 인터랙티브 |
| 3 | 단순질문 제외 전부 오케스트레이터→전문 에이전트 협업→매번 최적 | ✅(구조)/⏳(팀스폰 실측) | always-on orchestrator(§5.4) + Agent Teams + reviewer/critic 게이트 + agent-memory |
| 4 | 산출물이 정해진 경로에 저장 | ✅ | `{{OUTPUT_DIR}}` 기본 `docs/agent-orchestra/{prd,design,review,reports}/`, 에이전트가 거기 저장 (헤드리스 검증) |
| 5 | 외부 지식 폴더 참조 | ✅ | `.claude/knowledge/index.md`를 CLAUDE.md `@import`(상시 로드) + `.claude/rules/`. native 로드 (헤드리스 검증) |

게이트 강제(목표 3의 "매번 최적"): **native 팀 훅** `TaskCompleted`(비-리뷰 작업 완료 차단)·
`TeammateIdle`(리뷰어/감시자 idle 차단) + `Stop` 백스톱 + `PreToolUse` 위험명령 가드. 전부 단위 테스트 통과.

⏳ 유일한 인터랙티브 미검증: 메인 스레드 오케스트레이터가 실제로 Agent Team을 리드로 스폰하는지(§5.4),
HITL 승인 일시정지 UX. cmux 실측으로 확정.

## 14. v1.3 — HITL 흐름 · TDD · 오케스트레이터 메모리

**오케스트레이터 흐름 (HITL 리듬):**
1. **이해·구체화** — 요구 재진술 + 애매하면 `AskUserQuestion`으로 질문해 구체화(명확하면 건너뜀). *구현 전.*
2. **분해·승인** — task로 쪼개 계획 제시 → 짧은 승인("그냥 진행" escape). 소규모는 단일 task.
3. **task 루프(한 팀, 공유 task list)** — 각 task: 계약 합의 → TDD → 게이트 → **task 완료 시 사용자 보고 → 다음**.
4. **마무리** — 최종 보고를 `docs/agent-orchestra/reports/`에 저장.
→ HITL = 구체화 + 분해승인 + task별 보고. (매 tool마다 X, 끝까지 자율 X.)

**TDD (test-first, 독립 작성):**
- 독립 `test` 워커가 **계약 기준 실패 테스트(red)를 먼저** 작성(구현자는 테스트 안 씀 — 편향 교정의 테스트판).
- 구현 워커는 green으로 만들고 리팩터. **네이티브 task 의존성**(impl task가 test task에 의존)으로 test-first를 구조적으로 강제.
- reviewer가 "테스트가 실패할 수 있는지" 검증.

**오케스트레이터 메모리:**
- `memory: project` → `.claude/agent-memory/orchestrator/MEMORY.md`(커밋·공유, reviewer/critic과 일관).
- auto-memory(홈·머신-로컬)와 달리 레포 커밋·공유. 본문이 직접 read/write도 지시(메인 스레드 auto-fire 무관하게 동작).
- 헤드리스 검증: init이 `agent-memory/{orchestrator,reviewer,critic}/` 생성 확인 ✅.

## 15. v1.4 — 호출 모델 · 경로 · 정리 · 메모리

**#3 호출 모델 (always-on 철회 → b+c):** 근거 — AWS AI-DLC는 "조용한 always-on"이 아니라 *3단계 +
bolt당 10~26 사람 검증 포인트*의 체크포인트 모델이고, 플러그인 관례(및 저자의 immunity/agent-harmony)도
전부 *호출형*. 강제 always-on은 공격적·관례 이탈·opt-out 불가. → `agent` 키 제거, `/run` 명시+자동호출,
평소 plain Claude. (§5.4)

**#2 산출물 경로 (분리·기능폴더·무게비례):**
- 프로젝트 PRD/아키텍처(제품 1급) → **`docs/PRD.md`**(도구 중립, 분리). greenfield 인터뷰 산출, 살아있는 문서.
- 도구 산출물 → `docs/agent-orchestra/<기능-slug>/[prd|design].md` + `<YYYY-MM-DD>/{review,report}.md`.
- **무게 비례**: 작은 변경은 인라인 리뷰(파일 X). init은 카테고리 폴더 미리 안 만듦.

**#1 팀 정리:** 종료→정지확인→cleanup 순서 명시. 빈 cmux 패널 자동 닫힘은 **rules/hook으로 불가**(적절한
이벤트 없음, Agent Teams 느린 종료 + cmux 미닫힘 = upstream 한계) → 수동 닫기 안내.

**#4 컨텍스트/메모리:** `MEMORY.md`=간결 인덱스(200줄/25KB 캡), 상세는 토픽 파일 on-demand(사용자 제안 =
네이티브 패턴). knowledge `index.md`는 `@import`로 전체 로드되니 짧게 유지(깊은 docs는 링크만). CLAUDE.md
200줄 가드(초과 시 rules로). → 컨텍스트 압박 대비됨.

✅ 헤드리스 검증(ao-v14): settings에 `agent` 키 없음, 카테고리 폴더 미생성, agent-memory{orchestrator,reviewer,critic} 생성.

## 16. v0.7 — 객관 게이트 · FE 디자인/E2E · 온보딩 인덱스 · 하이브리드 에이전트 생성

**객관 게이트 (사실 > 의견):** Stop 훅 `verify-gate.py`가 게이트 시점에 `.agent-orchestra/verify.json`의
`test`/`lint`/`build`(+FE `e2e`)를 **직접 재실행** → 리뷰어 APPROVE가 실패 위에서 통과 불가(센티넬 위조 차단).
verify.json 없으면 fail-open. init이 트리아지에서 명령을 채워 생성.

**FE 품질:** frontend 아키타입에 `frontend-design` 스킬 + `figma`/`stitch` MCP로 high-end UI(“AI-generic은
결함”), 그리고 **Playwright 라이브 브라우저 E2E + 스크린샷 필수**(코드 리뷰만으로 FE 게이트 통과 불가, e2e는
verify.json에 넣어 객관 게이트가 재실행). 리뷰어는 렌더 결과를 판정.

**온보딩 인덱스:** `docs/agent-orchestra/INDEX.md`(`templates/INDEX.md.tmpl`) — init이 시드, `/run`이
substantial run마다 한 줄(날짜·기능·what/why·산출물 링크) 추가. 신규 합류자가 프로젝트 히스토리를 읽음.

**하이브리드 에이전트 생성 (rigid 템플릿 ↔ free-write 메타 에이전트의 중간):** 근거 — 고정 6 아키타입만
인스턴스화하면 프로젝트 고유 도메인(payments/recsys/realtime)을 놓치고, 반대로 메타 에이전트가 매번
**통째로 생성**하면 LLM 드리프트로 게이트 필수 절(TDD 순서·리뷰어 생존·파일 소유권·임시처리 금지)이 누락될 수
있음. → 표준 에이전트 **`agent-architect`**(opus)가 PRD/코드베이스로 도메인 분석·right-size(3개 미만 병합/8개
초과 분리)·고유 specialist 추가를 하되, **반드시 아키타입에서 조립하고 NON-NEGOTIABLE 블록을 verbatim 보존**.
아키타입에 보존 마커 주석 추가. init/run은 로스터 작성을 agent-architect에 위임(불가 시 동일 규칙 폴백).

**누락 방지 (강제, not 부탁):** init에 **post-apply 존재 검증** 단계 추가 — apply가 슬롯을 만들었다고 믿지 말고
디스크에서 필수 슬롯(CLAUDE.md/settings/agents/agent-memory 4종/verify.json/INDEX.md/knowledge)을 실제로
확인하고, 누락분은 hand-off 전에 생성. N/A는 승인된 계획에 명시된 것만 허용.

⚠️ 검증 노트: 마켓플레이스 소스가 `./agent-orchestra`(상대경로 = 마켓플레이스 **클론** 기준)이라, 로컬 커밋은
`git push` + 클론 갱신 전까지 새 프로젝트 설치에 반영되지 않음. v0.7 init의 전체 슬롯 생성 검증은 push 후
마켓플레이스 클론을 최신화한 뒤 수행해야 유효(이전 ao-v07 누락은 LLM 스킵이 아니라 v0.6.0 클론 설치였음).

## 부록 A. 핵심 참고 문서

- Agent Teams: https://code.claude.com/docs/en/agent-teams
- .claude 디렉토리 표준: https://code.claude.com/docs/en/claude-directory
- 서브에이전트/영속 메모리: https://code.claude.com/docs/en/sub-agents#enable-persistent-memory
- Hooks: https://code.claude.com/docs/en/hooks
- 플러그인 레퍼런스: https://code.claude.com/docs/en/plugins-reference
- Remote Control: https://code.claude.com/docs/en/remote-control
- cmux: https://cmux.com · cmux + Claude teams: https://cmux.com/blog/cmux-claude-teams
