# NLI-Prover

A natural language proof assistant demo, using NLI model.

```python
% python3 prover/main.py
正在加载 NLI 分词器: facebook/bart-large-mnli...
NLI 分词器 'facebook/bart-large-mnli' 加载成功。
正在加载 NLI 模型: facebook/bart-large-mnli...
NLI 模型 'facebook/bart-large-mnli' 加载成功。

欢迎来到 NLI 证明助手 (REPL)！蕴含阈值: 0.7
输入 'help' 获取可用命令列表。
nli-prover> help

可用命令:
  axiom <陈述>                    - 添加一个新的公理。
  lemma <名称> <陈述>             - 添加一个新的命名引理 (名称应为单个词)。
  target <陈述>                   - (原功能)检查目标与所有公理的矛盾概率。
  prove <目标> [using axioms <A_nums> [lemmas <L_names>]]
                                  - 尝试证明目标。可选择使用 'using' 合并指定公理(通过A编号)
                                    和/或引理(通过名称)作为前提。证明成功的目标会自动成为新公理。
                                    例如: prove C using axioms 1 2 lemmas my_L
  axioms                          - 列出所有当前的公理 (带编号 A1, A2...)。
  lemmas                          - 列出所有当前的引理 (带编号 L1, L2... 及名称)。
  clear                           - 清除所有公理和引理。
  help                            - 显示此帮助信息。
  exit / quit                     - 退出程序。
(当前蕴含阈值: 0.7)

nli-prover> axiom jina has one dog
已添加公理 (A1): "jina has one dog"
nli-prover> axiom alice has two cats
已添加公理 (A2): "alice has two cats"
nli-prover> target alice has more than one dog

--- 正在检查目标 "alice has more than one dog" 与基本事实的矛盾性 ---
  基本事实: "jina has one dog"
  与目标 "alice has more than one dog" 矛盾的概率: 0.6705502271652222
------------------------------
  基本事实: "alice has two cats"
  与目标 "alice has more than one dog" 矛盾的概率: 0.5456193089485168
------------------------------
nli-prover> target alice has more than one cats

--- 正在检查目标 "alice has more than one cats" 与基本事实的矛盾性 ---
  基本事实: "jina has one dog"
  与目标 "alice has more than one cats" 矛盾的概率: 0.8870380520820618
------------------------------
  基本事实: "alice has two cats"
  与目标 "alice has more than one cats" 矛盾的概率: 0.000234932143939659
------------------------------
nli-prover> axioms

当前公理列表:
  A1: "jina has one dog"
  A2: "alice has two cats"

nli-prover> prove "alice has more than one cats" using axioms 2

--- 尝试使用合并前提证明目标: ""alice has more than one cats"" ---
  合并的前提: "alice has two cats."
  [合并前提证明成功] 合并前提 
    --蕴含(0.9955)--> 目标 ""alice has more than one cats""
  [已证实] 目标 ""alice has more than one cats"" 已添加为新公理 (A3)。
nli-prover> prove "alice has more pets than jina"

--- 尝试证明目标: ""alice has more pets than jina"" (未使用合并前提) ---
  未找到直接证明路径，尝试通过引理证明...
  当前没有定义引理可供尝试。
--- 未能通过当前公理和引理证明目标 (未使用合并前提) ---
nli-prover> prove "alice has more pets than jina" using axioms 1 2

--- 尝试使用合并前提证明目标: ""alice has more pets than jina"" ---
  合并的前提: "jina has one dog. alice has two cats."
  [合并前提证明成功] 合并前提 
    --蕴含(0.7391)--> 目标 ""alice has more pets than jina""
  [已证实] 目标 ""alice has more pets than jina"" 已添加为新公理 (A4)。
nli-prover> axioms

当前公理列表:
  A1: "jina has one dog"
  A2: "alice has two cats"
  A3: ""alice has more than one cats""
  A4: ""alice has more pets than jina""
```
