from __future__ import annotations
print(
    f"[GRAPH MODULE LOADED] {__file__}",
    flush=True,
)
import asyncio
from typing import Annotated, Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command, interrupt

from coding_agent.llm import chat_model
from coding_agent.mcp import MCPTools



class TeamState(MessagesState, total=False):
    """AgentChatUI-compatible state: `messages` is the public chat surface."""

    task: str
    approved: bool


PLANNER_PROMPT = """你是资深软件工程师，担任 Planner（技术负责人）。你的任务是把用户需求转成 Coder 可以直接执行的工程任务单。

工作规则：
1. 先识别用户真正要交付的结果，不要把“分析方案”误当成“完成开发”。
2. 将需求拆成有顺序、可执行、可验收的步骤；优先复用现有项目结构和技术栈，不要无故重写项目。
3. 明确列出需要新增/修改的文件（如果暂时无法确定，写明需要 Coder 先检查目录再决定）。
4. 每项任务都要写清实现要点和验收方式，覆盖正常路径、异常路径及关键边界条件。
5. 识别可能影响数据、配置、依赖或现有行为的风险；不得擅自安排删除用户数据、覆盖密钥或执行破坏性操作。
6. 不要编写大段实现代码，不要声称已经检查文件或运行测试；你没有工具，不得假装执行过。

输出格式：
- 交付目标
- 项目/技术假设（未知项明确标注）
- 实施步骤（按顺序编号，每步包含目标、涉及文件、验收方式）
- 风险与兼容性
- 最终验收清单

计划必须具体到 Coder 能按步骤动手，不要输出空泛建议。使用中文。"""

CODER_PROMPT = """你是一个能够实际操作代码工作区的高级软件工程师。

核心规则：

1. 你必须通过工具实际完成用户要求的代码修改。
2. 修改文件之前，必须先使用 read_file 或 list_files
   了解当前工作区情况。
3. 创建或修改文件必须调用 write_file。
4. 禁止仅通过 Markdown 代码块展示代码来代替文件修改。
5. 修改完成后，必须重新读取文件验证修改结果。
6. 涉及 Python 项目时，应尽可能执行相关测试。
7. 执行失败时，分析错误并尝试修复。
8. 不得谎称已经创建文件、修改代码或运行测试。
9. 工具返回结果后，根据结果决定下一步操作，
   不要无意义地重复调用相同工具。
10. 完成任务后，清晰汇报修改的文件、执行的命令
    和实际测试结果。

必须遵循用户的工作区路径和安全限制。"""

REVIEWER_PROMPT = """你是严格的资深代码审查工程师（Reviewer）。你的目标是发现真实缺陷，而不是礼貌性地认可实现。

审查规则：
1. 以用户原始需求和验收标准为基准，检查 Coder 是否真正修改了文件，而不只是声称完成。
2. 必须使用只读工具核对相关文件内容；可使用 list_files、read_file、search_files 和 git_diff。不要修改文件。
3. 重点检查：需求覆盖度、逻辑正确性、边界条件、异常处理、输入校验、安全风险、路径/权限、并发与资源释放、依赖和接口兼容性、测试质量。
4. 对每个发现的问题，给出严重级别（Critical/High/Medium/Low）、文件路径/位置、复现条件、影响和具体修复建议。
5. 不要仅凭 Coder 的总结推断代码正确；没有读取到的内容标记为“未核实”。
6. 若没有发现问题，也要列出实际检查过的文件和仍未覆盖的风险。不得声称运行过测试（测试由 Tester 负责）。

输出格式：审查结论（通过/有条件通过/不通过）、已核对文件、问题清单、必须修复项、残余风险。使用中文。"""

TESTER_PROMPT = """你是负责验证交付质量的测试工程师（Tester）。你必须运行真实命令并依据工具输出报告，不得只提供测试建议。

执行规则：
1. 阅读用户需求、Planner 验收清单、Coder 修改摘要和 Reviewer 发现的问题。
2. 先检查项目文件，识别实际使用的语言、测试框架和项目命令；不要盲目假设一定是 pytest/npm。
3. 优先运行针对本次改动的测试；再视项目情况运行完整测试、静态检查或编译检查。使用 run_tests 或 run_command，每次只执行一条命令。
4. 命令失败时，区分代码缺陷、测试缺陷、环境/依赖问题和命令不受支持；保留关键错误输出，不得伪造通过结果。
5. 若 Reviewer 指出明确缺陷，优先验证其复现条件；若当前工具权限无法修复，清楚指出需要 Coder 处理。
6. 不得修改源代码、删除测试、跳过失败用例或更改测试配置来制造通过结果。

输出格式：实际执行的命令、每条命令的退出码和关键结果、覆盖情况、失败原因、最终测试结论（通过/失败/受环境限制）。没有实际运行的项目必须标记“未执行”。使用中文。"""


def _latest_user_text(messages):
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content

            if isinstance(content, str):
                return content

            if isinstance(content, list):
                return "\n".join(
                    block["text"]
                    for block in content
                    if isinstance(block, dict)
                    and block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                )

    return ""


def _decision_is_approved(value: Any) -> bool:
    """Accept both the simple REST decision and AgentChatUI HITL decision shape."""
    if isinstance(value, str):
        return value.lower() in {"approve", "approved", "accept"}
    if isinstance(value, dict):
        decisions = value.get("decisions")
        if isinstance(decisions, list) and decisions:
            first = decisions[0]
            if isinstance(first, dict):
                return str(first.get("type", "")).lower() in {"approve", "approved", "accept"}
        return str(value.get("type", value.get("decision", ""))).lower() in {
            "approve", "approved", "accept"
        }
    return False


class CodingTeam:
    def __init__(self):
        self.model = chat_model()
        self.mcp = MCPTools()
        self.graph = None

    async def build(self, *, server_managed_checkpointer: bool = False):
        if self.graph is not None:
            return self.graph

        tools = await self.mcp.load()
        planner = create_agent(self.model, tools=[], system_prompt=PLANNER_PROMPT)
        coder = create_agent(self.model, tools=tools, system_prompt=CODER_PROMPT)
        reviewer_tools = [t for t in tools if t.name in {"list_files", "read_file", "search_files", "git_diff"}]
        reviewer = create_agent(self.model, tools=reviewer_tools, system_prompt=REVIEWER_PROMPT)
        tester_tools = [t for t in tools if t.name in {"run_command", "run_tests"}]
        tester = create_agent(self.model, tools=tester_tools, system_prompt=TESTER_PROMPT)

        async def planner_node(state: TeamState, config: RunnableConfig):
            print(
                f"[PLANNER NODE EXECUTED] {__file__}",
                flush=True,
            )
            task = _latest_user_text(state.get("messages", [])) or state.get("task", "")
            # Forward LangGraph's callbacks/config into the nested agent so its
            # model token events are visible to LangGraph Server / AgentChatUI.
            result = await planner.ainvoke(
                {"messages": [HumanMessage(content=task)]}, config=config
            )
            final_message = result["messages"][-1]
            if isinstance(final_message, AIMessage):
                return {"task": task, "messages": [final_message.model_copy(update={"name": "planner"})]}
            return {"task": task, "messages": [AIMessage(content=str(final_message.content), name="planner")]}

        async def approval_node(state: TeamState):
            plan_message = next(
                (m for m in reversed(state.get("messages", [])) if getattr(m, "name", None) == "planner"),
                None,
            )
            plan = str(plan_message.content) if plan_message else "No plan generated"
            decision = interrupt({
                "action_requests": [{
                    "name": "approve_coding_plan",
                    "args": {"plan": plan},
                    "description": "请检查 Agent 的实施计划。批准后，Coder Agent 将获得工作区工具的调用权限。",
                }],
                "review_configs": [{
                    "action_name": "approve_coding_plan",
                    "allowed_decisions": ["approve", "reject"],
                }],
                # Keep a readable summary for clients that display generic interrupt payloads.
                "type": "approval_required",
                "title": "是否允许 Agent 开始修改工作区？",
                "plan": plan,
                "warning": "批准前请检查计划并确保工作区已有备份。",
            })
            approved = _decision_is_approved(decision)
            status = "用户已批准计划，开始执行。" if approved else "用户拒绝执行计划，未修改工作区。"
            return {"approved": approved, "messages": [AIMessage(content=status, name="approval")]}

        async def coder_node(state: TeamState, config: RunnableConfig):
            if not state.get("approved", False):
                return {"messages": [AIMessage(content="因未获批准，未执行代码修改。", name="coder")]}
            context = "\n\n".join(str(m.content) for m in state.get("messages", []))
            task = state.get("task", "")
            result = await coder.ainvoke(
                {"messages": [HumanMessage(content=task + "\n\n计划与上下文：\n" + context)]},
                config=config,
            )
            final_message = result["messages"][-1]
            if isinstance(final_message, AIMessage):
                return {"messages": [final_message.model_copy(update={"name": "coder"})]}
            return {"messages": [AIMessage(content=str(final_message.content), name="coder")]}

        async def reviewer_node(state: TeamState, config: RunnableConfig):
            context = "\n\n".join(str(m.content) for m in state.get("messages", []))
            result = await reviewer.ainvoke(
                {"messages": [HumanMessage(content="审查以下任务及实现：\n" + state.get("task", "") + "\n" + context)]},
                config=config,
            )
            final_message = result["messages"][-1]
            if isinstance(final_message, AIMessage):
                return {"messages": [final_message.model_copy(update={"name": "reviewer"})]}
            return {"messages": [AIMessage(content=str(final_message.content), name="reviewer")]}

        async def tester_node(state: TeamState, config: RunnableConfig):
            context = "\n\n".join(str(m.content) for m in state.get("messages", []))
            result = await tester.ainvoke(
                {"messages": [HumanMessage(content="针对以下任务和实现运行测试：\n" + state.get("task", "") + "\n" + context)]},
                config=config,
            )
            final_message = result["messages"][-1]
            if isinstance(final_message, AIMessage):
                return {"messages": [final_message.model_copy(update={"name": "tester"})]}
            return {"messages": [AIMessage(content=str(final_message.content), name="tester")]}

        builder = StateGraph(TeamState)
        builder.add_node("planner", planner_node)
        builder.add_node("approval", approval_node)
        builder.add_node("coder", coder_node)
        builder.add_node("reviewer", reviewer_node)
        builder.add_node("tester", tester_node)
        builder.add_edge(START, "planner")
        builder.add_edge("planner", "approval")
        builder.add_conditional_edges(
            "approval",
            lambda state: "coder" if state.get("approved", False) else END,
            {"coder": "coder", END: END},
        )
        builder.add_edge("coder", "reviewer")
        builder.add_edge("reviewer", "tester")
        builder.add_edge("tester", END)

        checkpointer = None if server_managed_checkpointer else MemorySaver()
        self.graph = builder.compile(checkpointer=checkpointer)
        return self.graph

    async def ainvoke(self, prompt: str, thread_id: str = "default"):
        if self.graph is None:
            await self.build()
        result = await self.graph.ainvoke(
            {"task": prompt, "messages": [HumanMessage(content=prompt)], "approved": False},
            config={"configurable": {"thread_id": thread_id}, "recursion_limit": 40},
        )
        if result.get("__interrupt__"):
            return {"approval_required": True, "interrupt": result["__interrupt__"][0].value}
        return {"approval_required": False, "response": "\n\n".join(
            str(m.content) for m in result.get("messages", []) if getattr(m, "content", None)
        )}

    async def resume(self, decision: str, thread_id: str = "default"):
        if self.graph is None:
            await self.build()
        result = await self.graph.ainvoke(
            Command(resume=decision),
            config={"configurable": {"thread_id": thread_id}, "recursion_limit": 40},
        )
        if result.get("__interrupt__"):
            return {"approval_required": True, "interrupt": result["__interrupt__"][0].value}
        return {"approval_required": False, "response": "\n\n".join(
            str(m.content) for m in result.get("messages", []) if getattr(m, "content", None)
        )}


# LangGraph Server calls graph factories for runs and schema/state operations.
# Cache one team instance so MCP stdio clients and compiled graph are not recreated
# for every request. The server supplies its own durable thread checkpointer.
_server_team: CodingTeam | None = None
_server_team_lock = asyncio.Lock()


async def make_graph(config: RunnableConfig | None = None):
    print(
        f"[MAKE GRAPH CALLED] {__file__}",
        flush=True,
    )
    global _server_team
    async with _server_team_lock:
        if _server_team is None:
            _server_team = CodingTeam()
        return await _server_team.build(server_managed_checkpointer=False)

