import asyncio
from coding_agent.graph import CodingTeam

async def main_async():
    team = CodingTeam()
    await team.build()
    print("Local Coding Agent ready. Type /exit to quit.")
    while True:
        try:
            prompt = input("\nYou> ").strip()
            if prompt.lower() in {"/exit", "exit", "quit"}:
                break
            if not prompt:
                continue
            result = await team.ainvoke(prompt)
            while result.get("approval_required"):
                print("\n[需要人工审批]")
                print(result["interrupt"])
                choice = input("输入 approve 批准，其他内容拒绝：").strip().lower()
                result = await team.resume("approve" if choice == "approve" else "reject")
            print("\n" + result.get("response", ""))
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print(f"\n[ERROR] {type(exc).__name__}: {exc}")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
