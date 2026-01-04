from GA_ import *
import os
import glob
import re
import matplotlib.pyplot as plt

# 文件路径
FILE_NAME = r'D:\模型代码以及数据\模型代码以及数据\【12-07】code\code\charging_demand_with_center_lat_lon_50%_all.csv'
STATION_FILE = r'D:\模型代码以及数据\模型代码以及数据\【12-07】code\code\station5.csv'

# 读取数据
df = pd.read_csv(FILE_NAME, sep=',')
df_station = pd.read_csv(STATION_FILE, sep=',')

# 按照网格聚合需求数据
df_agg_grid = (df.groupby(['lat', 'lon'])
               .agg(CD_sum=('CD', 'sum'),
                    CD_max=('CD', 'max'),
                    CD_max_hour=('CD', lambda x: df.loc[x.idxmax(), 'Hour']))
               .query('CD_sum!= 0')
               .reset_index())

# 初始化网格数据中的服务充电站信息
df_agg_grid['service_station'] = -1.0 * np.ones(len(df_agg_grid))
df_agg_grid['service_distance'] = -1.0 * np.ones(len(df_agg_grid))

def plot_pareto_front(pareto_front, pareto_front2, save_dir=None, prefix="pareto", dpi=300):
    if not pareto_front:
        print("警告: Pareto前沿为空, 无法绘制图表")
        return

    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['mathtext.fontset'] = 'custom'  # 如果需要数学字体也匹配

    # 提取所有解的原始成本和满意度
    all_costs = [sol['cost'] for sol in pareto_front + pareto_front2]
    all_satisfactions = [-sol['satisfaction'] for sol in pareto_front + pareto_front2]

    # 归一化到[0,1]
    cost_min, cost_max = min(all_costs), max(all_costs)
    sat_min, sat_max = min(all_satisfactions), max(all_satisfactions)

    # 防止分母为零
    cost_range = cost_max - cost_min + 1e-6
    sat_range = sat_max - sat_min + 1e-6

    plt.figure(figsize=(10, 6))

    # 绘制第一前沿（归一化后）
    if pareto_front:
        costs_1 = [(sol['cost'] - cost_min) / cost_range for sol in pareto_front]
        sats_1 = [(-sol['satisfaction'] - sat_min) / sat_range for sol in pareto_front]

        # 过滤 (0,0) 和 (1,1) 点（正确方式）
        filtered_pairs = [
            (c, s) for c, s in zip(costs_1, sats_1)
            if not ((abs(c) < 1e-6 and abs(s) < 1e-6) or (abs(c - 1) < 1e-6 and abs(s - 1) < 1e-6))
        ]
        costs_1_filtered = [c for c, s in filtered_pairs]
        sats_1_filtered = [s for c, s in filtered_pairs]

        plt.scatter(
            costs_1_filtered, sats_1_filtered,
            s=100,
            c='#d7191c',
            edgecolors='k',
            alpha=0.8,
            zorder=3,
            label='Pareto Front (1st)'
        )

    # 绘制第二前沿（归一化后）
    if pareto_front2:
        costs_2 = [(sol['cost'] - cost_min) / cost_range for sol in pareto_front2]
        sats_2 = [(-sol['satisfaction'] - sat_min) / sat_range for sol in pareto_front2]

        # 同上过滤逻辑
        filtered_pairs_2 = [
            (c, s) for c, s in zip(costs_2, sats_2)
            if not ((abs(c) < 1e-6 and abs(s) < 1e-6) or (abs(c - 1) < 1e-6 and abs(s - 1) < 1e-6))
        ]
        costs_2_filtered = [c for c, s in filtered_pairs_2]
        sats_2_filtered = [s for c, s in filtered_pairs_2]

        plt.scatter(
            costs_2_filtered, sats_2_filtered,
            s=100,
            facecolors='none',
            edgecolors='#2c7bb6',
            linewidths=1.5,
            alpha=0.8,
            zorder=3,
            label='Pareto Front (2nd)'
        )

    # 坐标轴标签和标题
    plt.xlabel('Economic Cost', fontsize=12)
    plt.ylabel('User Satisfaction', fontsize=12)
    plt.title('NSGA-II Pareto Front', fontsize=14)

    # 显式设置坐标轴
    plt.xlim(-0.05, 1.05)  # 扩展5%边距
    plt.ylim(-0.05, 1.05)

    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.legend()

    # 保存和显示逻辑
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        pattern = os.path.join(save_dir, f"{prefix} _*.png")
        existing_files = glob.glob(pattern)
        max_num = 0
        for f in existing_files:
            match = re.search(rf"{prefix}_(\d{{3}})\.png$", f)
            if match:
                current_num = int(match.group(1))
                max_num = max(max_num, current_num)
        new_num = max_num + 1 if existing_files else 1
        filename = f"{prefix}_{new_num:03d}.png"
        save_path = os.path.join(save_dir, filename)
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
        print(f"图表已保存至：{os.path.abspath(save_path)}")
    plt.show()
    plt.close()

def save_pareto_solutions(pareto_solutions, save_dir=None, prefix='output'):
    """
    将Pareto解集保存到按序号递增的文本文件

    :param pareto_solutions: Pareto解集列表
    :param save_dir: 保存目录（默认'./results'）
    :param prefix: 文件名前缀（默认'output'）
    :return: 生成的完整文件路径
    """
    # 确保目录存在
    os.makedirs(save_dir, exist_ok=True)

    # 查找现有文件的最大序号
    pattern = os.path.join(save_dir, f"{prefix}_*.txt")
    existing_files = glob.glob(pattern)

    # 提取最大序号（使用正则表达式精确匹配）
    max_num = 0
    for f in existing_files:
        match = re.search(rf"{prefix}_(\d{{3}})\.txt$", f)
        if match:
            current_num = int(match.group(1))
            max_num = max(max_num, current_num)

    # 生成新序号（3位数字）
    new_num = max_num + 1 if existing_files else 1
    filename = f"{prefix}_{new_num:03d}.txt"
    file_path = os.path.join(save_dir, filename)

    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"Pareto Solutions (Total: {len(pareto_solutions)})\n")
        f.write("=" * 50 + "\n")

        for i, solution in enumerate(pareto_solutions, 1):

            f.write(
                f"Solution {i}:\n"
                f"  Cost: {solution['cost']:.2f}\n"
                f"  Satisfaction: {solution['satisfaction']:.4f}\n"
                f"  Chromosome: \n"
                f"  sum_chosen: {sum(solution['chromosome'][0])}\n"
                f"  Location: {solution['chromosome'][0]}\n"
                f"  Number: {solution['chromosome'][1]}\n"
            )
            f.write("-" * 50 + "\n")

    print(f"解集已保存至：{os.path.abspath(file_path)}")
    return file_path

pareto_solutions, pareto_2 = genetic_algorithm(POP_SIZE, GENS, df_agg_grid, df_station)
# 绘制前沿
plot_pareto_front(pareto_solutions, pareto_2, save_dir='./picture')
# 保存解集
save_pareto_solutions(pareto_solutions, save_dir='./results', prefix='pareto')
save_pareto_solutions(pareto_2, save_dir='./results', prefix='pareto_2')
# print("Pareto最优解集:")
# for solution in pareto_solutions:
#     print(f"Cost: {solution['cost']}, Satisfaction: {solution['satisfaction']}, Chromosome: {solution['chromosome']}")
