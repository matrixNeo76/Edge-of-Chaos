# Edge-of-Chaos

*阅读其他语言版本：[English](README.md) | [Italiano](README.it.md) | **中文***

> **计算与硬件在环（Hardware-in-the-Loop）计量平台**，用于对连续物质基底
> （*可朽计算*，Mortal Computation）中的原初感受性、热力学效价 $\Psi(t)$
> 以及运行性划界条件进行实验验证，作为拉卡托斯研究纲领
> （*P0_Distilled v0.1*）的一部分开发。

---

## 📌 目录
1. [科学框架](#-科学框架)
2. [仓库架构](#-仓库架构)
3. [核心数学公式](#-核心数学公式)
4. [环境要求与快速安装](#-环境要求与快速安装)
5. [脚本使用指南](#-脚本使用指南)
   - [计量与数字孪生（`valenza_metrologia.py` / `.rs`）](#1-计量与数字孪生)
   - [真实硬件接口（`hardware_driver_v2.py`）](#2-真实硬件接口)
   - [运行性划界测试（`demarcation_tests.py`）](#3-运行性划界测试)
   - [可视化与仪表盘（`dashboard_valenza.py`）](#4-可视化与仪表盘)
6. [独立可执行文件（无需 Docker）](#-独立可执行文件无需-docker用于实验室电脑)
7. [容器化与可复现性（Docker）](#-容器化与可复现性docker)
8. [参考文献](#-参考文献)

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
├── valenza_metrologia.py         # Python 计量引擎（Hatano-Sasa 分解、k-NN KL 散度、Psi(t)）
├── valenza_metrologia.rs         # 高性能原生 Rust 计量引擎（零拷贝）
├── lib.rs                        # PyO3 FFI 模块，将 Rust 编译为原生 Python 扩展
├── Cargo.toml                    # Rust 基础设施的 Cargo / PyO3 配置
├── demo_pyo3_integration.py      # Rust/Python FFI 集成与性能基准演示脚本
│
├── hardware_driver_v2.py         # 用于 Keithley DMM 与 PicoScope 的 PyVISA/SCPI 驱动，带自动合规保护
├── test_hardware_session.py      # 硬件安全限制验证的扩展测试套件
├── demarcation_tests.py          # 运行性划界测试（Edge of Chaos、简并度、有限尺寸标度）
├── dashboard_valenza.py          # 四象限图形仪表盘生成器（Seaborn/Matplotlib）
├── dashboard_valenza.png         # 示例仿真运行的高分辨率可视化结果
│
├── test_valenza_metrologia.py    # 验证 SDE 数学与 Psi(t) 的单元测试
├── paper0_cli.py                 # 统一的多子命令 CLI 入口
├── references.bib                # 完整的 BibTeX 参考文献数据库（45 条引用，涵盖 IIT、FEP、Chua、Lakatos）
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

* **$\sigma_{ex}$ / $\sigma_{hk}$**：相对于稳态管家熵产生（housekeeping entropy
  production）的过量耗散（Hatano-Sasa 非平衡稳态分解）。
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
python3 valenza_metrologia.py
```

运行数学验证单元测试：
```bash
python3 test_valenza_metrologia.py
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

### 3. 运行性划界测试
验证 P0 的三个运行性条件（混沌边缘、谱简并度、有限尺寸标度）：
```bash
python3 demarcation_tests.py
```

### 4. 可视化与仪表盘
生成图形仪表盘 `dashboard_valenza.png`：
```bash
python3 dashboard_valenza.py
```

### 一体化 CLI
以上四个命令也可通过统一入口调用，该入口同样是下方 `build_exe.ps1` 打包的对象：
```bash
python3 paper0_cli.py metrologia|dashboard|demarcazione|hardware|test
```

---

## 📦 独立可执行文件（无需 Docker，用于实验室电脑）

用于生成 Windows 独立可执行文件（目标机器无需安装 Python/Rust），适用于使用真实
仪器采集数据、而 Docker 不便使用的场景（USB/GPIB 访问、管理员权限限制等）：

```powershell
.\build_exe.ps1
.\dist\paper0\paper0.exe metrologia   # 或：dashboard | demarcazione | hardware | test
```

---

## 🐳 容器化与可复现性（Docker）

在一个透明且无依赖问题的容器中隔离并运行计量环境：

```bash
# 构建并运行容器
docker-compose up --build
```

---

## 📜 参考文献

论文与脚本中引用的所有理论、认识论及硬件相关参考文献，均收录于随附的 BibTeX 文件中：
* **`references.bib`**：包含 45 条格式化引用（Chua、Hatano-Sasa、Tononi、Friston、
  Lakatos、Kleiner & Ludwig、Iavarone 2026）。

---
*拉卡托斯神经形态意识研究纲领（2026）*
