"""性能分析比较脚本

该脚本用于比较AI生命体项目优化前后的性能差异，通过读取两个性能分析文件（原始和优化后），
分析关键函数的调用次数和执行时间，输出性能对比结果。

使用方法：
1. 先运行原始代码生成profile.stats文件
2. 运行优化后的代码生成profile_optimized.stats文件
3. 执行该脚本进行性能分析比较
"""

import pstats


def get_function_stats(profiler_stats, func_name):
    """获取指定函数的性能统计信息
    
    参数:
        profiler_stats: pstats.Stats - 性能分析器统计对象
        func_name: str - 要查找的函数名
    
    返回:
        tuple或None - 函数的统计信息，包含调用次数、执行时间等，
                      如果找不到该函数则返回None
    """
    for func, stats in profiler_stats.stats.items():
        if func_name in func[0]:
            return stats
    return None


def compare_function_performance(original_stats, optimized_stats, func_name, display_name):
    """比较两个性能分析器中指定函数的性能差异
    
    参数:
        original_stats: pstats.Stats - 原始代码的性能分析器统计对象
        optimized_stats: pstats.Stats - 优化后代码的性能分析器统计对象
        func_name: str - 要比较的函数名
        display_name: str - 显示在输出中的函数名称
    """
    print(f"\n{display_name}：")
    original_func_stats = get_function_stats(original_stats, func_name)
    optimized_func_stats = get_function_stats(optimized_stats, func_name)
    
    if original_func_stats and optimized_func_stats:
        original_calls = original_func_stats[0]  # 调用次数
        original_time = original_func_stats[1]  # 执行时间（秒）
        optimized_calls = optimized_func_stats[0]
        optimized_time = optimized_func_stats[1]
        
        print(f"  原始调用次数: {original_calls}, 时间: {original_time:.4f}秒")
        print(f"  优化后调用次数: {optimized_calls}, 时间: {optimized_time:.4f}秒")
        
        # 计算性能提升百分比
        if original_time > 0:
            time_reduction = ((original_time - optimized_time) / original_time) * 100
            print(f"  时间减少: {time_reduction:.2f}%")
        
        if original_calls > 0:
            calls_reduction = ((original_calls - optimized_calls) / original_calls) * 100
            print(f"  调用次数减少: {calls_reduction:.2f}%")
    else:
        print(f"  未找到{func_name}函数的性能数据")


# 主执行部分
if __name__ == "__main__":
    try:
        # 读取原始性能分析文件
        original_profiler = pstats.Stats('profile.stats')
        
        # 读取优化后性能分析文件
        optimized_profiler = pstats.Stats('profile_optimized.stats')
        
        # 打印完整的性能分析报告（前20个函数）
        print("===== 原始性能分析 ====")
        original_profiler.sort_stats('cumulative').print_stats(20)
        
        print("\n===== 优化后性能分析 ====")
        optimized_profiler.sort_stats('cumulative').print_stats(20)
        
        # 比较关键函数的性能差异
        print("\n===== 关键函数性能对比 ====")
        
        # 比较paintEvent函数
        compare_function_performance(original_profiler, optimized_profiler, 'paintEvent', 'paintEvent函数')
        
        # 比较draw函数
        compare_function_performance(original_profiler, optimized_profiler, 'draw', 'Node.draw函数')
        
        # 比较drawLine调用次数
        print("\ndrawLine调用：")
        original_draw_line = original_profiler.stats.get(('{built-in method drawLine}',), None)
        optimized_draw_line = optimized_profiler.stats.get(('{built-in method drawLine}',), None)
        
        if original_draw_line and optimized_draw_line:
            original_calls = original_draw_line[0]
            optimized_calls = optimized_draw_line[0]
            
            print(f"  原始调用次数: {original_calls}")
            print(f"  优化后调用次数: {optimized_calls}")
            
            if original_calls > 0:
                calls_reduction = ((original_calls - optimized_calls) / original_calls) * 100
                print(f"  调用次数减少: {calls_reduction:.2f}%")
        else:
            print("  未找到drawLine调用的性能数据")
            
    except FileNotFoundError as e:
        print(f"错误：找不到性能分析文件 - {e}")
        print("请先运行代码生成性能分析文件，例如：")
        print("python -m cProfile -o profile.stats your_script.py")
        print("python -m cProfile -o profile_optimized.stats your_optimized_script.py")
    except Exception as e:
        print(f"发生错误：{e}")
