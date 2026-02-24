# ⚡ 电动汽车充电站布局多目标优化系统
*(Charging Station Location Selection)*

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Algorithm](https://img.shields.io/badge/Algorithm-GA%20%7C%20NSGA--II-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎯 项目概述

随着新能源汽车的普及，如何科学地选址充电站并合理配置充电桩数量成为了关键挑战。

本项目致力于**电动汽车充电站的智能布局优化**。系统引入了**遗传算法 (GA)** 与**非支配排序遗传算法 (NSGA-II)**，综合权衡 **“经济建设成本”** 与 **“用户充电满意度”** 两大核心目标，为城市充电网络的规划和选址提供强大的科学决策与量化支持。

---

## ✨ 主要功能模块

### 1. 🧹 空间数据预处理
* 自动读取并解析充电需求点及候选充电站的地理分布数据。
* 采用**网格化聚合处理**方法，降低计算复杂度，提高大规模城市数据的处理效率。

### 2. 🧠 多目标智能优化
本项目提供两种优化策略以适应不同决策场景：
* **多目标寻优 (NSGA-II)**：在经济成本与用户满意度之间寻找平衡，生成 **Pareto 前沿解集**（即不存在绝对优劣的多种妥协方案集合），供决策者灵活挑选。
* **单目标寻优 (GA)**：通过加权或其他方式将多目标转化为单一适应度，寻找全局唯一的**综合最优解**。

### 3. 📊 结果可视化与输出
* 自动绘制并输出 **Pareto 前沿分布散点图**，直观展示不同方案在双目标维度下的表现。
* 将详细的优化结果（如站址坐标、定容数量、各项成本指标）结构化并保存至文本文件中，方便后续数据复用或接入 GIS 系统。

---

## 📂 项目文件结构

项目代码结构模块化，职责清晰，便于二次开发：

```text
project/
├── main.py              # 🚀 主程序入口：统筹数据读取、优化模型执行与最终结果输出
├── NSGA-II.py           # 🧬 多目标优化算法：NSGA-II (Non-dominated Sorting Genetic Algorithm II) 的核心逻辑实现
├── GA.py                # 🧬 单目标优化算法：标准遗传算法 (Genetic Algorithm) 的核心逻辑实现
├── model.py             # 📐 数学模型库：包含充电站选址数学模型搭建及适应度(成本/满意度)评估函数定义
├── README.md            # 📖 项目说明文档 (您正在阅读的文件)
└── data/                # 📁 数据集目录：存放充电需求与候选站点数据 (运行时需自行准备并放入此目录)
```

> **📌 附加说明**：关于单目标遗传算法 (GA) 版本的更详细代码说明，请参阅随附的其他 GA 版本代码说明文件。

---

## 🚀 快速开始

```bash
# 1. 克隆项目仓库
git clone https://github.com/owring-code/Charging-Station-Location-Selection.git

# 2. 进入项目目录
cd Charging-Station-Location-Selection

# 3. 运行主程序开始优化求解 (请确保 data 目录下已有正确格式的数据集)
python main.py
```
