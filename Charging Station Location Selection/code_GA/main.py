from GA import *
import matplotlib.pyplot as plt

# 文件路径
FILE_NAME = 'charging_demand_with_center_lat_lon_50%_all.csv'
STATION_FILE = './station5.csv'

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


best_chromosome, best_fitness, fitness_history = genetic_algorithm(POP_SIZE, GENS, df_agg_grid, df_station, CROSSOVER_RATE, MUTATION_RATE)

# 绘制收敛曲线
plt.figure(figsize=(10, 6))
plt.plot(range(1, len(fitness_history) + 1), fitness_history, marker='o', color='b', linestyle='-')
plt.title('Genetic Algorithm Iteration')
plt.xlabel('Generation')
plt.ylabel('Best Fitness Value')
plt.grid(True)
plt.show()

# 打印最优结果
print(f"Best Chromosome: {best_chromosome}")
print(f"Best Fitness: {best_fitness}")
