import pstats

# 读取原始性能分析文件
p_original = pstats.Stats('profile.stats')

# 读取优化后性能分析文件
p_optimized = pstats.Stats('profile_optimized.stats')

print("===== 原始性能分析 ====")
p_original.sort_stats('cumulative').print_stats(20)

print("\n===== 优化后性能分析 ====")
p_optimized.sort_stats('cumulative').print_stats(20)

# 比较关键函数的调用次数和时间
print("\n===== 关键函数性能对比 ====")

# 获取关键函数信息
def get_function_stats(p, func_name):
    for func, stats in p.stats.items():
        if func_name in func[0]:
            return stats
    return None

# 比较paintEvent函数
print("\npaintEvent函数：")
original_paint = get_function_stats(p_original, 'paintEvent')
optimized_paint = get_function_stats(p_optimized, 'paintEvent')
if original_paint and optimized_paint:
    print(f"  原始调用次数: {original_paint[0]}, 时间: {original_paint[1]:.4f}秒")
    print(f"  优化后调用次数: {optimized_paint[0]}, 时间: {optimized_paint[1]:.4f}秒")
    print(f"  时间减少: {((original_paint[1] - optimized_paint[1]) / original_paint[1] * 100):.2f}%")

# 比较draw函数
print("\nNode.draw函数：")
original_draw = get_function_stats(p_original, 'draw')
optimized_draw = get_function_stats(p_optimized, 'draw')
if original_draw and optimized_draw:
    print(f"  原始调用次数: {original_draw[0]}, 时间: {original_draw[1]:.4f}秒")
    print(f"  优化后调用次数: {optimized_draw[0]}, 时间: {optimized_draw[1]:.4f}秒")
    print(f"  时间减少: {((original_draw[1] - optimized_draw[1]) / original_draw[1] * 100):.2f}%")

# 比较drawLine调用次数
print("\ndrawLine调用：")
original_drawLine = p_original.stats.get(('{built-in method drawLine}',), None)
optimized_drawLine = p_optimized.stats.get(('{built-in method drawLine}',), None)
if original_drawLine and optimized_drawLine:
    print(f"  原始调用次数: {original_drawLine[0]}")
    print(f"  优化后调用次数: {optimized_drawLine[0]}")
    print(f"  调用次数减少: {((original_drawLine[0] - optimized_drawLine[0]) / original_drawLine[0] * 100):.2f}%")
