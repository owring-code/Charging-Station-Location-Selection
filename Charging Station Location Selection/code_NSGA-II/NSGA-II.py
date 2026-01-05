import sys
import pandas as pd
import random
import numpy as np
from model import *

# 模型相关参数
A = 50000000  # 最大建设成本
B = 5000000  # 最大运营成本
p = 200000  # 基础建设成本
b = 12000  # 每个充电桩的建设成本
n = 0.1  # 运营成本系数

# 遗传算法相关参数
POP_SIZE = 250  # 种群大小
GENS = 300  # 迭代次数
CROSSOVER_RATE = 0.8  # 交叉率
MUTATION_RATE = 0.2  # 变异率



def init_population(pop_size, station_num, max_list, df_agg_grid):
    population = []
    demand_weights = df_agg_grid['CD_sum'].values / (df_agg_grid['CD_sum'].sum() + 1e-6)

    for _ in range(pop_size):
        if random.random() < 0.7:
            a_list = []
            x_list = []
            for i in range(station_num):
                prob = min(0.95, demand_weights[i] * 1.5 + 0.1)
                if random.random() < prob:
                    a = 1
                    base_num = int(max_list[i] * (demand_weights[i] + 0.2))
                    x = min(max_list[i], base_num + random.randint(0, 3))
                else:
                    a = 0
                    x = 0
                a_list.append(a)
                x_list.append(x)
        else:
            a_list = [random.choices([0, 1], weights=[0.3, 0.7])[0] for _ in range(station_num)]  # 偏向建站
            x_list = [random.randint(1, max(1, int(max_list[i] * 0.5))) if a == 1 else 0 for i, a in enumerate(a_list)]

        population.append([a_list, x_list])
    return population

# 多目标支配关系判断
def dominates(ind1, ind2):
    # 目标1：cost 越小越好，目标2：satisfaction 越大越好
    better_cost = ind1['cost'] <= ind2['cost']
    better_sat = ind1['satisfaction'] >= ind2['satisfaction']
    strictly_better = (ind1['cost'] < ind2['cost']) or (ind1['satisfaction'] > ind2['satisfaction'])
    return better_cost and better_sat and strictly_better


# 非支配排序
def non_dominated_sort(population):
    frontiers = []
    population = population.copy()
    while population:
        current_front = []
        to_remove = []
        for i, ind in enumerate(population):
            if not any(dominates(other, ind) for other in population):
                current_front.append(ind)
                to_remove.append(i)
        for index in reversed(to_remove):
            population.pop(index)
        frontiers.append(current_front)
    return frontiers


def crowding_distance(front):
    n = len(front)
    for ind in front:
        ind['crowding'] = 0
    for obj in ['cost', 'satisfaction']:
        sorted_front = sorted(front, key=lambda x: x[obj])
        min_obj = sorted_front[0][obj]
        max_obj = sorted_front[-1][obj]
        if max_obj - min_obj < 1e-6:
            continue
        sorted_front[0]['crowding'] = float('inf')
        sorted_front[-1]['crowding'] = float('inf')
        for i in range(1, n - 1):
            delta = (sorted_front[i + 1][obj] - sorted_front[i - 1][obj]) / (max_obj - min_obj + 1e-6)
            sorted_front[i]['crowding'] += delta
    return front


# NSGA-II选择机制
def selected(population, pop_size):
    frontiers = non_dominated_sort(population)
    selected = []
    for front in frontiers:
        if len(selected) + len(front) <= pop_size:
            selected += front
        else:
            sorted_front = sorted(front, key=lambda x: -x['crowding'])
            selected += sorted_front[:pop_size - len(selected)]
            break
    return selected


# def select(population, fitness_values, tournament_size):

#     selected_indices = np.random.choice(len(population), tournament_size, replace=False)
#     tournament_fitness = fitness_values[selected_indices]
#     winner = population[selected_indices[np.argmin(tournament_fitness)]]
#     return winner

def crossover(parent1, parent2):
    num_genes = len(parent1[0])

    a1_np = np.array(parent1[0])
    x1_np = np.array(parent1[1])
    a2_np = np.array(parent2[0])
    x2_np = np.array(parent2[1])

    num_crossover_points = random.randint(1, num_genes // 2)  # 随机确定交叉点的数量，至少1个，最多为基因数量的一半

    crossover_points = sorted(random.sample(range(1, num_genes), num_crossover_points))  # 随机选择交叉点位置并排序

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


# def mutate(chromosome, max_list):
#     if random.random() < MUTATION_RATE:
#         point = random.randint(0, len(chromosome) - 1)
#         chromosome[0][point] = 1 - chromosome[0][point]
#         chromosome[1][point] = random.randint(1, max_list[point]) if chromosome[0][point] == 1 else 0
#
#     return chromosome

def mutate(chromosome, max_list):
    mutated = [chromosome[0].copy(), chromosome[1].copy()]
    for i in range(len(chromosome[0])):
        if random.random() < MUTATION_RATE:
            mutated[0][i] = 1 - mutated[0][i]
            mutated[1][i] = random.randint(1, max_list[i]) if mutated[0][i] else 0
        # 小幅调整已建站的充电桩数量
        elif mutated[0][i] == 1 and random.random() < 0.1:
            mutated[1][i] = max(1, mutated[1][i] + random.choice([-1, 0, 1]))
    return mutated


def Fitness(chromosome, df_agg_grid, df_station, gen=0):
    punish = 0

    new_stations = []
    for i, a in enumerate(chromosome[0]):
        if a == 1:
            new_station = {'station_id': i, 'lat': df_station.loc[i, 'lat'], 'lon': df_station.loc[i, 'lon'],
                           'num': chromosome[1][i]}
            new_stations.append(new_station)

    if len(new_stations) == 0:
        return {
            'cost': sys.maxsize,
            'satisfaction': 0.0,
            'chromosome': chromosome
        }

    new_stations = pd.DataFrame(new_stations)

    # 使用numpy向量化操作来更新df_agg_grid中每个网格到最近充电站的距离
    grid_lats = df_agg_grid['lat'].values
    grid_lons = df_agg_grid['lon'].values
    station_lats = new_stations['lat'].values
    station_lons = new_stations['lon'].values

    # 计算距离
    distances = np.zeros((len(df_agg_grid), len(new_stations)))
    for i, (lat1, lon1) in enumerate(zip(grid_lats, grid_lons)):
        for j, (lat2, lon2) in enumerate(zip(station_lats, station_lons)):
            lat_distance_km = abs(lat1 - lat2) * 111
            average_lat = (lat1 + lat2) / 2
            lon_distance_km = abs(lon1 - lon2) * 111 * math.cos(math.radians(average_lat))
            distances[i, j] = lat_distance_km + lon_distance_km

    nearest_station_indices = np.argmin(distances, axis=1)
    df_agg_grid['service_distance'] = distances[np.arange(len(df_agg_grid)), nearest_station_indices]
    df_agg_grid['service_station'] = new_stations['station_id'].values[nearest_station_indices]

    # 最大距离约束
    exceed_distance = df_agg_grid['service_distance'] - D_MAX
    exceed = exceed_distance * (df_agg_grid['CD_sum'] / 30)
    exceed = exceed[exceed_distance > 0]
    n2 = exceed.sum()
    punish += n2 * 1000

    # 距离满意度
    df_agg_grid['score_sat'] = df_agg_grid['service_distance'].apply(score_of_satisfaction)
    total_fitness_user_sat = sum(df_agg_grid['score_sat'] * (df_agg_grid['CD_sum'] / 30))

    # 对选择同一充电站的需求点的需求进行求和，得到每个充电站一天要服务的需求总和
    ssd_sum = df_agg_grid.groupby('service_station')['CD_sum'].sum().reset_index()

    # 将选取同一个充电站的需求点的相同时间的最大需求相加
    ssd_hour_max = df_agg_grid.groupby(['service_station', 'CD_max_hour']).sum()
    # 一天内，每个充电站对应的单位小时的最大服务需求
    series = ssd_hour_max.groupby('service_station')['CD_max'].max()

    ssd_sum = ssd_sum.merge(series.rename('CD_hour_max'), left_on='service_station', right_index=True)
    df_agg_station = ssd_sum.merge(new_stations, left_on='service_station', right_on='station_id', how='left')
    df_agg_station = df_agg_station.drop(['lat', 'lon', 'service_station'], axis=1)

    df_agg_station['lambda_j'] = (df_agg_station['CD_hour_max'] / 30).apply(arrival_rate)
    df_agg_station['mu_j'] = 1 / t_j  # 单个充电机的服务能力
    df_agg_station['rho'] = df_agg_station.apply(lambda x: rho(x['lambda_j'], x['mu_j']), axis=1)
    df_agg_station['rho_j'] = df_agg_station.apply(lambda x: service_intensity(x['lambda_j'], x['num'], x['mu_j']),
                                                   axis=1)

    # 充电站服务能力约束
    exceed_rho_j = df_agg_station['rho_j'] - 1
    exceed_rho_j = exceed_rho_j[exceed_rho_j > 0]
    n1 = exceed_rho_j.sum()
    punish += n1 * 300000

    df_agg_station['P_j'] = df_agg_station.apply(lambda x: p_j(x['rho'], x['num'], x['rho_j']), axis=1)
    df_agg_station['tlj'] = df_agg_station.apply(
        lambda x: expected_queue_time(x['lambda_j'], x['rho'], x['num'], x['P_j'], x['rho_j']), axis=1)
    df_agg_station['queueing_sat'] = df_agg_station['tlj'].apply(score_of_queueing)

    # 计算等待时间满意度总和
    total_fitness_queueing = sum(df_agg_station['queueing_sat'] * (df_agg_station['CD_sum'] / 30))

    # 计算建设、运营和维修成本
    C_build_base = p * sum(chromosome[0]) + b * sum(chromosome[1])
    C_build = C_build_base * depreciation_rate(r_0, z)
    C_run = n * C_build_base

    # 最大建设成本（和维护成本）约束条件
    if C_build_base > A:
        return {
            'cost': sys.maxsize,
            'satisfaction': 0.0,
            'chromosome': chromosome
        }

    # 最小化经济成本，最大化用户满意度
    # fitness = ( - a_2 * 365 * (total_fitness_user_sat +  total_fitness_queueing)
    #             + a_1 * (C_build + C_run)
    #             + punish)

    economic_cost = (C_build + C_run) + punish
    user_satisfaction = 365 * (total_fitness_user_sat + total_fitness_queueing)

    return {
        'cost': round(economic_cost, 2),
        'satisfaction': round(user_satisfaction, 2),
        'chromosome': chromosome
    }


def genetic_algorithm(pop_size, gens, df_agg_grid, df_station):
    df_station['max'] = df_station['max'].apply(lambda x: 20 if x > 20 else x)
    population = init_population(pop_size, len(df_station), df_station['max'], df_agg_grid)
    # 评估初始种群
    evaluated_pop = []
    for chromo in population:
        fitness = Fitness(chromo, df_agg_grid, df_station, gen=0)
        evaluated_pop.append(fitness)

    for gen in range(gens):
        # 记录当前前沿
        current_front = non_dominated_sort(evaluated_pop)[0]

        # 生成子代
        offspring = []
        elite_size = int(pop_size*0.15)
        elites = random.sample(current_front, min(elite_size, len(current_front)))

        while len(offspring) < pop_size - elite_size:
            parent1 = random.choice(evaluated_pop)
            parent2 = random.choice(evaluated_pop)
            child_chromo = crossover(parent1['chromosome'], parent2['chromosome'])
            child_chromo = mutate(child_chromo, df_station['max'])
            child_fitness = Fitness(child_chromo, df_agg_grid, df_station, gen=gen)
            offspring.append(child_fitness)

        offspring +=[e.copy() for e in elites]
        # 合并父代和子代
        combined_pop = evaluated_pop + offspring

        # 去重
        unique_pop = []
        seen = set()
        for ind in combined_pop:
            key = (tuple(ind['chromosome'][0]), tuple(ind['chromosome'][1]))
            if key not in seen:
                seen.add(key)
                unique_pop.append(ind)
        combined_pop = unique_pop
        # 非支配排序和拥挤度计算
        for ind in combined_pop:
            if 'crowding' not in ind:
                ind['crowding'] = 0
        # 非支配排序和拥挤度计算
        frontiers = non_dominated_sort(combined_pop)
        for front in frontiers:
            crowding_distance(front)
        # 选择新一代种群
        evaluated_pop = selected(combined_pop, pop_size)

    # 返回Pareto前沿
    pareto_front = non_dominated_sort(evaluated_pop)[0]
    pareto_front2 = non_dominated_sort(evaluated_pop)[2]
    return pareto_front, pareto_front2
