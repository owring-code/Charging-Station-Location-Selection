import math

D_MAX = 20
D_MIN = 3
r_0 = 0.08  # 折旧率
z = 15  # 使用年限
t_j = 0.75  # 平均充电时间，例如小时
T_MAX = 0.5  # 排队等待时间最大值(45 分钟)
T_MIN = 0.15  # 排队等待时间最小值(15 分钟)
t_c = 1  # 充电站最高充电需求的小时的服务时长（1 小时）

def score_of_satisfaction(d):
    if d > D_MAX:
        return 0
    elif d < D_MIN:
        return 1
    else:
        return 0.5 + 0.5 * math.cos(math.pi * 0.5 + math.pi / (D_MAX - D_MIN) * (d - 0.5 * (D_MAX - D_MIN)))

def arrival_rate(demand):
    return demand / t_c if t_c != 0 else 0.0  # 避免除以零

def rho(lambda_j, mu_j):
    if mu_j <= 0:
        return 0.0
    return lambda_j / mu_j

def service_intensity(lambda_j, N_j, mu_j):
    if N_j <= 0 or mu_j <= 0:
        return 0.0
    rho_j = lambda_j / (N_j * mu_j)
    return min(rho_j, 0.99)  # 限制 rho_j <= 0.99

def p_j(rho, N_j, rho_j):
    if rho_j >= 1 or rho_j < 0:
        return 0.0
    sum_term = sum((rho ** k) / math.factorial(k) for k in range(int(N_j)))
    denominator = math.factorial(int(N_j)) * (1 - rho_j)
    if denominator <= 0:
        return 0.0
    p_j_value = (sum_term + (rho ** N_j) / denominator) ** -1
    return p_j_value

def expected_queue_time(lambda_j, rho, N_j, p_j, rho_j):
    if 1 > rho_j > 0 and lambda_j > 0:
        return ((rho ** int(N_j)) * p_j * rho_j) / (lambda_j * math.factorial(int(N_j)) * ((1 - rho_j) ** 2))
    else:
        return float('inf')

def score_of_queueing(t_lj):
    if t_lj > T_MAX:
        return 0
    elif t_lj < T_MIN:
        return 1
    else:
        return (T_MAX - t_lj) / (T_MAX - T_MIN)

def depreciation_rate(r_0, z):
    return (r_0 * (r_0 + 1) ** z) / ((r_0 + 1) ** z - 1)