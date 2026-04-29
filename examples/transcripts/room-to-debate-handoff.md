This is an illustrative transcript, not host-live or provider-live validation evidence.

# Transcript: `/room -> /debate` Handoff

This example shows the shape of a `/room` discussion being packaged into a
`handoff_packet` and consumed by `/debate`. It is hand-written to demonstrate
the protocol and should not be read as output from a live host, provider, or
release validation run.

Topic: 面向大学生的 AI 学习产品

## Room Context Before Upgrade

The room has already completed three turns:

```text
/room 我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进
/focus 先只盯考试前 48 小时复习路径
/summary
```

Current room summary:

```json
{
  "room_id": "room-example-handoff",
  "title": "大学生 AI 学习产品方向探索",
  "primary_type": "startup",
  "secondary_type": "product",
  "stage": "decision",
  "consensus_points": [
    "方向需要缩窄到高压考试场景",
    "先用手工服务验证，不应先开发 App",
    "验证重点是付费或复用意愿，不是口头喜欢"
  ],
  "open_questions": [
    "哪一门课或考试场景最适合做首轮验证？",
    "什么信号足以支持继续做软件化 MVP？"
  ],
  "tension_points": [
    "机会侧认为可以小步验证，风险侧担心考试周尖峰需求会制造伪信号"
  ],
  "recommended_next_step": "选择一门高压考试课，招募 10 个学生，用手工方式交付 48 小时复习路径并记录付费、复用和结果反馈。"
}
```

## User Requests Upgrade

```text
/upgrade-to-debate
```

Orchestrator upgrade signal:

```json
{
  "triggered_at_turn": 3,
  "reason": "user_explicit_request",
  "tension_unresolved": true,
  "confidence": 0.74
}
```

## Handoff Packet

`/room` does not pass the raw conversation log into `/debate`. It packages the
discussion into a controlled handoff packet:

```json
{
  "handoff_packet": {
    "schema_version": "v0.1",
    "generated_at_turn": 3,
    "source_room_id": "room-example-handoff",
    "field_01_original_topic": "我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进",
    "field_02_room_title": "大学生 AI 学习产品方向探索",
    "field_03_type": {
      "primary": "startup",
      "secondary": "product"
    },
    "field_04_sub_problems": [
      {
        "text": "考试前 48 小时复习路径是否是足够窄的首轮切口",
        "tags": ["value_proposition", "product_focus", "execution_path"],
        "discussed_in_turns": [1, 2, 3],
        "status": "converged"
      },
      {
        "text": "考试周尖峰需求是否会误导长期产品判断",
        "tags": ["downside_analysis", "long_term_strategy"],
        "discussed_in_turns": [2, 3],
        "status": "open"
      }
    ],
    "field_05_consensus_points": [
      "方向需要缩窄到高压考试场景",
      "先用手工服务验证，不应先开发 App",
      "验证重点是付费或复用意愿，不是口头喜欢"
    ],
    "field_06_tension_points": [
      "机会侧认为可以小步验证，风险侧担心考试周尖峰需求会制造伪信号"
    ],
    "field_07_open_questions": [
      "哪一门课或考试场景最适合做首轮验证？",
      "什么信号足以支持继续做软件化 MVP？"
    ],
    "field_08_candidate_solutions": [
      {
        "solution_text": "只选一门高压考试课，招募 10 个学生，用手工方式交付 48 小时复习路径。",
        "proposed_by": ["steve-jobs", "paul-graham", "munger"],
        "support_level": "high",
        "unresolved_concerns": [
          "Taleb 仍担心考试周尖峰需求无法代表长期留存"
        ]
      }
    ],
    "field_09_factual_claims": [
      {
        "claim_text": "当前房间尚未产生真实学生访谈、付费或留存数据。",
        "cited_by": ["munger", "taleb"],
        "source_hint": "Turn 2 和 Turn 3 的风险侧发言均要求把真实用户信号作为前置条件。",
        "reliability": "asserted"
      }
    ],
    "field_10_uncertainty_points": [
      "Munger 的不确定性：感谢、试用和付费不是同一个信号。",
      "Taleb 的不确定性：考试周需求是否具备可重复性。",
      "Jobs 的不确定性：不同课程对复习路径的交付要求可能差异很大。"
    ],
    "field_11_suggested_agents": [
      "paul-graham",
      "steve-jobs",
      "munger",
      "taleb"
    ],
    "field_12_suggested_agent_roles": {
      "paul-graham": "判断这是否是足够真实、足够窄的早期创业机会，并审查首轮验证是否能产生有效学习。",
      "steve-jobs": "审查用户价值主张是否足够直接，防止 MVP 被功能清单和技术展示拖散。",
      "munger": "检查创始人投射、机会成本和停止条件，防止把兴趣误判成市场。",
      "taleb": "识别小样本伪信号、尖峰需求和重投入带来的脆弱性。"
    },
    "field_13_upgrade_reason": {
      "reason_code": "user_explicit_request",
      "reason_text": "用户要求把已形成的低成本验证方案与仍未解决的伪信号风险交给 /debate 正式审议。",
      "triggered_by": "user_explicit",
      "confidence": 0.74,
      "warning_flags": []
    }
  }
}
```

## Debate Consumes The Packet

```text
/debate --from-handoff room-example-handoff
```

Debate launch summary:

```json
{
  "workflow": "debate",
  "input_source": "handoff_packet",
  "decision_question": "是否值得基于 /room 的方案进入极轻 MVP 验证？",
  "selected_panel": ["paul-graham", "steve-jobs", "munger", "taleb"],
  "reviewer_required": true,
  "raw_room_log_in_review_scope": false
}
```

## Debate Result

Moderator summary:

```text
共识：可以验证，但只能以极轻方式验证。
分歧：机会侧认为手工验证足够小，风险侧担心考试周场景制造一次性伪信号。
初步建议：进入 concierge MVP，不进入软件化 MVP。
审查重点：验证指标和停止条件是否足够明确。
```

Reviewer result:

```text
评分：8/10。
允许进入最终决议：允许。
缺证据点：没有真实学生样本，必须把下一步定义成验证，而不是发布。
被忽略问题：首批课程选择标准需要明确。
```

Final decision:

```text
单一建议：进入极轻 concierge MVP，不开发完整产品。

下一步：只选一门高压考试课，招募 10 个学生，人工交付 48 小时复习路径。

停止条件：少于 3 人愿意付费或复用则暂停；超过 5 人愿意付费或主动推荐，再讨论软件化。
```

## What This Transcript Demonstrates

- `/room -> /debate` is a compression and handoff flow, not a raw log dump.
- `/debate` consumes a controlled `handoff_packet` and reselects or confirms a
  panel through its own rules.
- The final decision stays claim-safe and does not imply provider-live or
  host-live execution.
