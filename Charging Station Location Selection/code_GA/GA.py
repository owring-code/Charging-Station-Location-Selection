import sys
import pandas as pd
import random
import numpy as np
from model import *

# 模型相关参数
A = 50000000  # 最大建设成本
B = 5000000   # 最大运营成本
a_1 = 0.5     # 成本的权重系数
a_2 = 0.5     # 用户满意度权重系数
p = 300000    # 基础建设成本
b = 12000     # 每个充电桩的建设成本
n = 0.1       # 运营成本系数

# 遗传算法相关参数
POP_SIZE = 250          # 种群大小
GENS = 2               # 迭代次数
CROSSOVER_RATE = 0.6    # 交叉率
MUTATION_RATE = 0.1     # 变异率

def init_population(pop_size, station_num, max_list):
    population = []
    for _ in range(pop_size):
        a_list = [random.randint(0, 1)for _ in range(station_num)]
        x_list = [1 if a == 1 else 0 for a in a_list]
        for i in range(station_num):
            x_list[i] = random.randint(1, max_list[i]) if a_list[i] == 1 else 0
        population.append([a_list, x_list])
    return population

def select(population, fitness_values, tournament_size):

    selected_indices = np.random.choice(len(population), tournament_size, replace=False)
    tournament_fitness = fitness_values[selected_indices]
    winner = population[selected_indices[np.argmin(tournament_fitness)]]
    return winner

def crossover(parent1, parent2):
    num_genes = len(parent1[0])

    a1_np = np.array(parent1[0])
    x1_np = np.array(parent1[1])
    a2_np = np.array(parent2[0])
    x2_np = np.array(parent2[1])

    num_crossover_points = random.randint(1, num_genes // 2)

    crossover_points = sorted(random.sample(range(1, num_genes), num_crossover_points))

    new_a_list = []
    new_x_list = []

    current_source = 0

    for i in range(num_genes):
        if i in crossover_points:
            current_source = 1 - current_source

        if current_source == 0:
            new_a_list.append(a1_np[i])
            new_x_list.append(x1_np[i])
        else:
            new_a_list.append(a2_np[i])
            new_x_list.append(x2_np[i])

    return [list(new_a_list), list(new_x_list)]

def mutate(chromosome, max_list):
    if random.random() < MUTATION_RATE:
        point = random.randint(0, len(chromosome) - 1)
        chromosome[0][point] = 1 - chromosome[0][point]
        chromosome[1][point] = random.randint(1, max_list[point]) if chromosome[0][point] == 1 else 0

    return chromosome

def Fitness(chromosome, df_agg_grid, df_station):

    # 约束条件惩罚值
    punish = 0
    # 收集新站点数据的列表
    new_stations = []
    for i, a in enumerate(chromosome[0]):
        if a == 1:  # 如果该区域建设了充电站
            new_station = {'station_id': i, 'lat': df_station.loc[i, 'lat'], 'lon': df_station.loc[i, 'lon'], 'num': chromosome[1][i]}
            new_stations.append(new_station)

    if len(new_stations) == 0:  # 代表没有建充电站
        return sys.maxsize

    new_stations = pd.DataFrame(new_stations)

    # 使用numpy向量化操作来更新df_agg_grid中每个网格到最近充电站的距离
    grid_lats = df_agg_grid['lat'].values
    grid_lons = df_agg_grid['lon'].values
    station_lats = new_stations['lat'].values
    station_lons = new_stations['lon'].values

    # 计算曼哈顿距离
    distances = np.zeros((len(df_agg_grid), len(new_stations)))
    for i, (lat1, lon1) in enumerate(zip(grid_lats, grid_lons)):
        for j, (lat2, lon2) in enumerate(zip(station_lats, station_lons)):
            # 计算纬度差值对应的实际距离（近似为1度纬度约等于111千米）
            lat_distance_km = abs(lat1 - lat2) * 111
            # 计算经度差值对应的实际距离（1度经度约等于111 * cos(平均纬度)千米）
            average_lat = (lat1 + lat2) / 2
            lon_distance_km = abs(lon1 - lon2) * 111 * math.cos(math.radians(average_lat))
            # 曼哈顿距离（以千米为单位）计算公式
            distances[i, j] = lat_distance_km + lon_distance_km

    nearest_station_indices = np.argmin(distances, axis=1)
    df_agg_grid['service_distance'] = distances[np.arange(len(df_agg_grid)), nearest_station_indices]
    df_agg_grid['service_station'] = new_stations['station_id'].values[nearest_station_indices]

    # 最大距离约束
    exceed_distance = df_agg_grid['service_distance'] - D_MAX
    exceed = exceed_distance * (df_agg_grid['CD_sum']/30)
    exceed = exceed[exceed_distance > 0]
    n2 = exceed.sum()
    punish += n2 * 1000

    # 距离满意度
    df_agg_grid['score_sat'] = df_agg_grid['service_distance'].apply(score_of_satisfaction)
    total_fitness_user_sat = sum(df_agg_grid['score_sat'] * (df_agg_grid['CD_sum']/30))

    # 对选择同一充电站的需求点的需求进行求和，得到每个充电站一天要服务的需求总和
    ssd_sum = df_agg_grid.groupby('service_station')['CD_sum'].sum().reset_index()

    # 将选取同一个充电站的需求点的相同时间的最大需求相加
    ssd_hour_max = df_agg_grid.groupby(['service_station', 'CD_max_hour']).sum()
    # 一天内，每个充电站对应的单位小时的最大服务需求
    series = ssd_hour_max.groupby('service_station')['CD_max'].max()

    ssd_sum = ssd_sum.merge(series.rename('CD_hour_max'), left_on='service_station', right_index=True)
    df_agg_station = ssd_sum.merge(new_stations, left_on='service_station', right_on='station_id', how='left')
    df_agg_station = df_agg_station.drop(['lat', 'lon','service_station'], axis=1)

    df_agg_station['lambda_j'] = (df_agg_station['CD_hour_max']/30).apply(arrival_rate)
    df_agg_station['mu_j'] = 1 / t_j  # 单个充电机的服务能力
    df_agg_station['rho'] = df_agg_station.apply(lambda x: rho(x['lambda_j'], x['mu_j']), axis=1)
    df_agg_station['rho_j'] = df_agg_station.apply(lambda x: service_intensity(x['lambda_j'], x['num'], x['mu_j']), axis=1)

    # 充电站服务能力约束
    exceed_rho_j = df_agg_station['rho_j'] - 1
    exceed_rho_j = exceed_rho_j[exceed_rho_j > 0]
    n1 = exceed_rho_j.sum()
    punish += n1 * 300000

    df_agg_station['P_j'] = df_agg_station.apply(lambda x: p_j(x['rho'], x['num'], x['rho_j']), axis=1)
    df_agg_station['tlj'] = df_agg_station.apply(lambda x: expected_queue_time(x['lambda_j'], x['rho'], x['num'], x['P_j'], x['rho_j']), axis=1)
    df_agg_station['queueing_sat'] = df_agg_station['tlj'].apply(score_of_queueing)

    # 计算等待时间满意度总和
    total_fitness_queueing = sum(df_agg_station['queueing_sat'] * (df_agg_station['CD_sum']/30))

    # 计算建设、运营和维修成本
    C_build_base = p * sum(chromosome[0]) + b * sum(chromosome[1])
    C_build = C_build_base * depreciation_rate(r_0, z)
    C_run = n * C_build_base

    # 最大建设成本（和维护成本）约束条件
    if C_build_base > A:
        return sys.maxsize

    # 最小化经济成本，最大化用户满意度
    fitness = ( - a_2 * 365 * (total_fitness_user_sat +  total_fitness_queueing)
                + a_1 * (C_build + C_run)
                + punish)

    return fitness

def genetic_algorithm(pop_size, gens, df_agg_grid, df_station, CROSSOVER_RATE, MUTATION_RATE):

    # 对充电桩个数再限制（避免单个站点的规模过大）
    df_station['max'] = df_station['max'].apply(lambda x: 15 if x > 15 else x)

    population = init_population(pop_size, len(df_station), df_station['max'])  # 种群
    best_chromosome = None
    best_fitness = float('inf')
    fitness_history = []

    for gen in range(gens):

        fitness_values_array = np.zeros(pop_size)
        for i, chromosome in enumerate(population):
            fitness_values_array[i] = Fitness(chromosome, df_agg_grid, df_station)

        new_population = []
        for i in range(pop_size):
            parent1 = select(population, fitness_values_array, tournament_size=4)
            parent2 = select(population, fitness_values_array, tournament_size=4)
            child = crossover(parent1, parent2)
            child = mutate(child, df_station['max'])
            new_population.append(child)

        population = new_population

        # 更新最优解
        current_best_fitness = np.min(fitness_values_array)
        fitness_history.append(-current_best_fitness)

        if current_best_fitness < best_fitness:
            best_fitness = current_best_fitness
            best_chromosome = population[np.argmin(fitness_values_array)]

        # 自适应调整交叉率和变异率
        if current_best_fitness == best_fitness:
            CROSSOVER_RATE = min(0.9, CROSSOVER_RATE + 0.05)
            MUTATION_RATE = min(0.5, MUTATION_RATE + 0.02)
        else:
            CROSSOVER_RATE = max(0.4, CROSSOVER_RATE - 0.05)
            MUTATION_RATE = max(0.1, MUTATION_RATE - 0.02)


    return best_chromosome, best_fitness, fitness_history