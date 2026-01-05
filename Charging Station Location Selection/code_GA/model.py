import math

D_MAX = 20     # 最大距离
D_MIN = 3      # 最小距离
r_0 = 0.08     # 年折旧率
z = 15         # 使用年限
t_j = 0.75     # 平均充电时间(45分钟)
T_MAX = 0.5    # 最大排队等待时间(30分钟)
T_MIN = 0.15   # 最小排队等待时间(9分钟)
t_c = 1

def score_of_satisfaction(d):
    if d > D_MAX:
        return 0
    elif d < D_MIN:
        return 1
    else:
        return 0.5 + 0.5 * math.cos(math.pi * 0.5 + math.pi
                                    / (D_MAX - D_MIN) * (d - 0.5 * (D_MAX - D_MIN)))

# 用户到达频率
def arrival_rate(demand):
    return demand / t_c   # lambda_j

# 充电站服务强度
def rho(lambda_j, mu_j):
    return lambda_j / mu_j  # rho

# 充电站利用率
def service_intensity(lambda_j, N_j, mu_j):
    rho_j = lambda_j / (N_j * mu_j)
    return rho_j if rho_j != 1 else 0.99

# 充电站空闲概率
def p_j(rho, N_j,rho_j):
    sum_term = sum((rho ** k) / math.factorial(k) for k in range(int(N_j)))
    p_j = (sum_term + (rho ** N_j) / (math.factorial(int(N_j)) * (1 - rho_j))) ** -1
    return p_j

# 排队等待时间期望
def expected_queue_time(lambda_j, rho, N_j, p_j, rho_j):
    if rho_j < 1:
        return (((rho ** int(N_j)) * p_j * rho_j)
                / (lambda_j * math.factorial(int(N_j)) * ((1 - rho_j) ** 2)))
    else:
        return float('inf')

# 排队等待时间满意度
def score_of_queueing(t_lj):
    if t_lj > T_MAX:
        return 0
    elif t_lj < T_MIN:
        return 1
    else:
        return (T_MAX - t_lj) / (T_MAX - T_MIN)

def depreciation_rate(r_0, z):
    return (r_0 * (r_0 + 1) ** z) / ((r_0 + 1) ** z - 1)