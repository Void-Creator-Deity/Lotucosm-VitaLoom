"""狼羊草生态系统模拟入口"""

from ai_organism.ecosystem import Ecosystem


def run_simulation(load_from_save: bool = False):
    """运行模拟（支持从保存的状态继续）"""
    # 从保存的状态加载或新建生态系统
    if load_from_save:
        try:
            ecosystem = Ecosystem.load_state()
        except (FileNotFoundError, EOFError):
            print("未找到有效保存文件，将创建新生态系统")
            ecosystem = Ecosystem(50, 50)
    else:
        ecosystem = Ecosystem(50, 50)
    
    print("开始生态模拟... (按下Ctrl+C中断并保存)")
    print("时间步 | 狼数量 | 羊数量 | 草数量 | 平均记忆数")
    print("-" * 50)
    
    try:
        while True:
            ecosystem.simulate_step()  # 执行一步模拟
            current_step = ecosystem.time_step
            
            # 每50步打印基础统计
            if current_step % 50 == 0:
                stats = ecosystem.get_statistics()
                print(f"{stats['time_step']:6} | {stats['wolf_count']:6} | "
                      f"{stats['sheep_count']:6} | {stats['grass_count']:6} | "
                      f"{stats['avg_wolf_memories']:.1f}/{stats['avg_sheep_memories']:.1f}")
            
            # 每1000步输出记忆信息（新增）
            if current_step % 1000 == 0:
                print(f"\n===== 第 {current_step} 步记忆快照 =====")
                # 输出狼的记忆
                if ecosystem.wolves:
                    wolf = ecosystem.wolves[0]
                    print(f"随机狼的记忆库({len(wolf.memory_bank)}个):")
                    for memory in wolf.memory_bank[:3]:  # 显示前3个
                        print(f"  {memory.situation} -> {memory.action.value} "
                              f"(成功:{memory.success}, 强度:{memory.strength:.2f})")
                # 输出羊的记忆
                if ecosystem.sheep:
                    sheep = ecosystem.sheep[0]
                    print(f"随机羊的记忆库({len(sheep.memory_bank)}个):")
                    for memory in sheep.memory_bank[:3]:  # 显示前3个
                        print(f"  {memory.situation} -> {memory.action.value} "
                              f"(成功:{memory.success}, 强度:{memory.strength:.2f})")
                print("===================================
")
            
            # 种群失衡时重新初始化
            if len(ecosystem.wolves) == 0 or len(ecosystem.sheep) == 0:
                print("种群失衡，重新初始化...")
                ecosystem.initialize_ecosystem()
                
    except KeyboardInterrupt:
        # 中断时保存状态（修改：新增保存逻辑）
        ecosystem.save_state()
        print("\n模拟已中断并保存状态")
        final_stats = ecosystem.get_statistics()
        print(f"\n当前统计 (时间步: {final_stats['time_step']}):")
        print(f"狼数量: {final_stats['wolf_count']}, 羊数量: {final_stats['sheep_count']}, 草数量: {final_stats['grass_count']}")
        print(f"平均记忆数: 狼 {final_stats['avg_wolf_memories']:.1f}, 羊 {final_stats['avg_sheep_memories']:.1f}")
    
    return ecosystem


if __name__ == "__main__":
    import sys
    # 支持命令行参数：python 狼羊草杀.py continue （继续上次模拟）
    load_prev = len(sys.argv) > 1 and sys.argv[1] == "continue"
    final_ecosystem = run_simulation(load_from_save=load_prev)
    
    # 最终输出记忆分析
    if final_ecosystem.wolves:
        wolf = final_ecosystem.wolves[0]
        print(f"\n最终狼的记忆库({len(wolf.memory_bank)}个记忆):")
        for i, memory in enumerate(wolf.memory_bank[:5]):
            print(f"  {memory.situation} -> {memory.action.value} (成功:{memory.success}, 强度:{memory.strength:.2f})")
