import pstats

# 读取性能分析文件
p = pstats.Stats('profile.stats')

# 按累计时间排序，显示前50个函数
p.sort_stats('cumulative').print_stats(50)

# 按自身时间排序，显示前50个函数
p.sort_stats('time').print_stats(50)

# 找出调用次数最多的函数
p.sort_stats('calls').print_stats(50)
