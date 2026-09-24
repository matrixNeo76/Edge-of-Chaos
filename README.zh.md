# Edge-of-Chaos

*阅读其他语言版本：[English](README.md) | [Italiano](README.it.md) | **中文***

> **计算与硬件在环（Hardware-in-the-Loop）计量平台**，用于对连续物质基底
> （*可朽计算*，Mortal Computation）中的原初感受性、热力学效价 $\Psi(t)$
> 以及运行性划界条件进行实验验证，作为拉卡托斯研究纲领
> （*P0_Distilled v0.1*）的一部分开发。

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22895263.svg)](https://doi.org/10.5281/zenodo.22895263)

---

## 📌 目录
1. [科学框架](#-科学框架)
2. [仓库架构](#-仓库架构)
3. [核心数学公式](#-核心数学公式)
4. [环境要求与快速安装](#-环境要求与快速安装)
5. [脚本使用指南](#-脚本使用指南)
   - [计量与数字孪生（`thermodynamic_valence.py` / `.rs`）](#1-计量与数字孪生)
   - [真实硬件接口（`hardware_driver_v2.py`）](#2-真实硬件接口)
   - [划界与必要条件（`demarcation.py`、`necessary_conditions.py`）](#3-划界与必要条件)
   - [可视化与仪表盘（`valence_dashboard.py`）](#4-可视化与仪表盘)
6. [独立可执行文件（无需 Docker）](#-独立可执行文件无需-docker用于实验室电脑)
7. [容器化与可复现性（Docker）](#-容器化与可复现性docker)
8. [相关出版物](#-相关出版物)
9. [参考文献](#-参考文献)

---

## 🔬 科学框架

**Paper 0（P0_Distilled_v0.1）** 提出了一种物理与热力学划界模型，用于评估连续物理基底
（扩散型离子忆阻器阵列 $SiO_x{:}Ag$、Mott 型忆阻器 $VO_2$、以及银纳米线渗流网络）
是否具备支持原初内感受性（interoceptive sentience）的候选资格。

与基于冯·诺依曼/GPU 架构的数字人工智能（*不朽计算*，Immortal Computation，受
Kleiner & Ludwig（2024）提出的"芯片意识不可能定理"（No-Go Theorem for Consciousness
on a Chip）约束）不同，本平台直接在**物质层面**评估基底，验证以下三点：
* 材料物理与计算之间的**因果不可分离性**（causal non-separability）。
* 与离子及随机动力学相关的**内禀非马尔可夫记忆**。
* 在预防性允稳态调节（$\Psi(t)$）下的**状态依赖有效动力学**。

---

## 📂 仓库架构

```
Edge-of-Chaos/
├── thermodynamic_valence.py       # Python 计量引擎（耗散代理量、k-NN KL 散度、Psi(t)）
├── thermodynamic_valence.rs       # 高性能原生 Rust 计量引擎（零拷贝）
├── lib.rs                        # PyO3 FFI 模块，将 Rust 编译为原生 Python 扩展
├── Cargo.toml                    # Rust 基础设施的 Cargo / PyO3 配置
├── demo_pyo3_integration.py      # Rust/Python FFI 集成与性能基准演示脚本
│
├── hardware_driver_v2.py         # 用于 Keithley DMM 与 PicoScope 的 PyVISA/SCPI 驱动，带自动合规保护
├── test_hardware_session.py      # 硬件安全限制验证的扩展测试套件
├── demarcation.py                # 三个运行性划界条件（因果不可分性、非马尔可夫记忆、状态依赖动力学）
├── necessary_conditions.py       # 三个必要条件的判据（混沌边缘、因果简并度、指数稳定性）
├── synthetic_systems.py          # 答案已知的合成系统（用于测试与演示）
├── demarcation_tests.py          # 兼容模块（重新导出上述两个模块）
├── valence_dashboard.py          # 四象限图形仪表盘生成器（Seaborn/Matplotlib）
├── valence_dashboard.png         # 示例仿真运行的高分辨率可视化结果
│
├── test_thermodynamic_valence.py  # 验证 SDE 数学与 Psi(t) 的单元测试
├── test_demarcation.py           # 在答案已知的系统上测试划界条件
├── test_necessary_conditions.py  # 必要条件判据的测试
├── paper0_cli.py                 # 统一的多子命令 CLI 入口
├── notebooks/demo.ipynb          # 演示笔记本（可在 Binder 上运行）
├── references.bib                # 完整的 BibTeX 参考文献数据库（49 条引用，涵盖 IIT、FEP、Chua、Lakatos）
│
├── install.sh                    # Linux / macOS 安装脚本
├── install.ps1                   # Windows PowerShell 安装脚本
├── build_exe.ps1                 # 独立可执行文件构建脚本（PyInstaller，无需 Docker）
├── Dockerfile                    # 多阶段 Docker 容器（Python 3.11 + Rust）
└── docker-compose.yml            # 用于实验室可复现性的 Docker 编排
```

完整且带注释的文件树请见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
（包括本公开仓库之外、仍在期刊审稿流程中的科学手稿等部分）。

---

## 🧮 核心数学公式

### 1. 热力学效价泛函 $\Psi(t)$
$$\Psi_{allo}(t) = \alpha \cdot \ln\left(1 + \frac{\sigma_{ex}(t)}{\sigma_{hk}(t) + \epsilon}\right) - \beta \cdot \mathcal{D}_{KL}\big(P(x) \,||\, P_{target}\big) + \gamma \cdot G_{pred}(t)$$

* **$\sigma_{ex}$ / $\sigma_{hk}$**：在论文中，指 Hatano-Sasa 非平衡稳态分解中的过量熵产生与管家
  熵产生（housekeeping entropy production）。**在当前代码中，它们只是启发式代理量，并非
  Hatano-Sasa 量**：$\sigma_{hk}$ 按 $\sigma_{noise}^2/dt$ 缩放，因而依赖于积分步长；而数字孪生
  单变量模型的真实管家熵产生恒为零。只应在相同 $dt$ 下比较 $\Psi(t)$ 的数值。正确的估计方法
  （例如 Sekizawa, Ito & Oizumi, *Phys. Rev. X* 14, 041003, 2024）尚未实现。
* **$\mathcal{D}_{KL}$**：相对于目标允稳态稳定性生态位的非参数化（$k$-NN）概率散度。
* **$G_{pred}$**：由 $A_2$ 层生成、作用于 $A_1$ 层的传出副本（efference copy）
  预测增益。

### 2. 局部活动条件（混沌边缘，Edge of Chaos）
$$\text{Re}\big(Y(j\omega)\big) < 0 \quad \text{对于 } \omega \in [\omega_1, \omega_2] \quad \land \quad \text{Tr}\big(J(E_k)\big) < 0, \quad \det\big(J(E_k)\big) > 0$$

### 3. 谱因果简并度
$$\rho_{deg} = \frac{\dim\left(\ker(J - \lambda_0 I)\right)}{\|\Delta W_{therm}\|}$$

---

## ⚡ 环境要求与快速安装

### 系统要求
* **Python 3.9+**，需安装 `numpy`、`scipy`、`matplotlib`、`seaborn`
* **Rust / Cargo**（可选，建议安装以启用高性能原生模块）

### 自动化安装

* **Linux / macOS：**
  ```bash
  chmod +x install.sh
  ./install.sh
  ```

* **Windows（PowerShell）：**
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\install.ps1
  ```

---

## 💻 脚本使用指南

### 1. 计量与数字孪生
运行 $A_1/A_2$ 基底仿真并计算效价 $\Psi(t)$：
```bash
python3 thermodynamic_valence.py
```

运行数学验证单元测试：
```bash
python3 test_thermodynamic_valence.py
```

### 2. 真实硬件接口
在启用安全合规保护（$V_{comp}=1.5\text{V}, I_{comp}=1.0\text{mA}$）以及校准过的
$1/f$ 噪声（$\sigma_{noise}=0.10$）的情况下启动硬件会话：
```bash
python3 hardware_driver_v2.py
```
默认情况下，驱动运行于**模拟（mock）模式**——无需任何物理仪器。真实仪器访问
（通过 PyVISA）也可用，但为可选项。

通过硬件测试套件验证安全性与合规限制：
```bash
python3 test_hardware_session.py
```

### 3. 划界与必要条件
`demarcation.py` 实现 P0（第 3 节）的三个**运行性划界条件**：因果不可分性（响应矩阵相对于线性叠加模型的数值秩）、非马尔可夫记忆（超出马尔可夫阶 k 的条件互信息，与 IAAFT 替代数据比较）以及状态依赖的有效动力学（相空间三个区域中的雅可比矩阵）。`necessary_conditions.py` 实现五个**必要条件**中三个的判据（P1 第 3 节、附录 B 与 D）：混沌边缘、带鲁棒半径 rho_deg 的因果简并度，以及指数稳定性。两者都作用于测量或估计的数据；下面的演示在答案已知的合成系统上运行它们：
```bash
python3 paper0_cli.py demarcation   # 替代数据设置已缩减；协议：--surrogates 100 --percentile 99
python3 paper0_cli.py conditions
```
论文将最高马尔可夫阶设为 k_max = 500，k 近邻估计器无法处理；因此 k_max 是一个参数（见 `demarcation.py` 的文档字符串）。

### 4. 可视化与仪表盘
生成图形仪表盘 `valence_dashboard.png`：
```bash
python3 valence_dashboard.py
```

### 一体化 CLI
`notebooks/demo.ipynb` 在模拟数据上运行效价代理量与传出副本消融、G_pred 的已知局限、划界条件以及混沌边缘判据，并附有说明。无需安装，可通过 [Binder](https://mybinder.org/v2/gh/matrixNeo76/Edge-of-Chaos/HEAD?labpath=notebooks%2Fdemo.ipynb) 在浏览器中打开。

以上所有命令也可通过统一入口调用，该入口同样是下方 `build_exe.ps1` 打包的对象：
```bash
python3 paper0_cli.py metrology|dashboard|demarcation|conditions|hardware|test
```

---

## 📦 独立可执行文件（无需 Docker，用于实验室电脑）

用于生成 Windows 独立可执行文件（目标机器无需安装 Python/Rust），适用于使用真实
仪器采集数据、而 Docker 不便使用的场景（USB/GPIB 访问、管理员权限限制等）：

```powershell
.\build_exe.ps1
.\dist\paper0\paper0.exe metrology   # 或：dashboard | demarcation | conditions | hardware | test
```

---

## 🐳 容器化与可复现性（Docker）

在一个透明且无依赖问题的容器中隔离并运行计量环境：

```bash
# 构建并运行容器
docker-compose up --build
```

---

## 📚 相关出版物

本软件是 **P0_Distilled** 研究纲领语料库的配套数字孪生计量平台，已发布于 Zenodo。
建议从蒸馏版论文开始阅读；其余为配套/扩展论文。

| 论文 | DOI |
|---|---|
| **P0_Distilled_v0.1**（主要入口） | [10.5281/zenodo.22895484](https://doi.org/10.5281/zenodo.22895484) |
| P1_Main（扩展/权威版本） | [10.5281/zenodo.22896026](https://doi.org/10.5281/zenodo.22896026) |
| P2_SelfAgency（自我能动性扩展） | [10.5281/zenodo.22896870](https://doi.org/10.5281/zenodo.22896870) |
| P3_Critique（外部批判性评估） | [10.5281/zenodo.22896988](https://doi.org/10.5281/zenodo.22896988) |
| C1_Philosophy（公设2的论证） | [10.5281/zenodo.22897359](https://doi.org/10.5281/zenodo.22897359) |
| C2_PowerAnalysis（蒙特卡洛功效分析） | [10.5281/zenodo.22897562](https://doi.org/10.5281/zenodo.22897562) |
| ES_Summary（执行摘要） | [10.5281/zenodo.22897732](https://doi.org/10.5281/zenodo.22897732) |
| Medium 风格科普文章（英文） | [10.5281/zenodo.22898609](https://doi.org/10.5281/zenodo.22898609) |

---

## 📜 参考文献

论文与脚本中引用的所有理论、认识论及硬件相关参考文献，均收录于随附的 BibTeX 文件中：
* **`references.bib`**：包含 49 条格式化引用（Chua、Hatano-Sasa、Tononi、Friston、
  Lakatos、Kleiner & Ludwig、Iavarone 2026）。

---
*拉卡托斯神经形态意识研究纲领（2026）*
