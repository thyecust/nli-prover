# 确保已安装 transformers 和 PyTorch
# pip install transformers torch
# readline (通常内置于Python标准库在Unix-like系统) 或 pyreadline3 (Windows) 用于命令历史
try:
    import readline
except ImportError:
    try:
        import pyreadline3 # For Windows
        # Note: pyreadline3 might need to be explicitly installed: pip install pyreadline3
    except ImportError:
        print("警告: 未找到 readline 或 pyreadline3 模块。命令行历史和高级编辑功能可能不可用。")

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# --- 1. 加载预训练的NLI模型和分词器 ---
NLI_MODEL_NAME = "facebook/bart-large-mnli"
ENTAILMENT_THRESHOLD = 0.7 # 定义蕴含关系的阈值

nli_tokenizer = None
nli_model = None
is_nli_model_loaded = False

try:
    print(f"正在加载 NLI 分词器: {NLI_MODEL_NAME}...")
    nli_tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
    print(f"NLI 分词器 '{NLI_MODEL_NAME}' 加载成功。")
    
    print(f"正在加载 NLI 模型: {NLI_MODEL_NAME}...")
    nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
    print(f"NLI 模型 '{NLI_MODEL_NAME}' 加载成功。")
    
    # 将模型设置为评估模式
    nli_model.eval()
    is_nli_model_loaded = True
    
except Exception as e:
    print(f"加载 NLI 模型或分词器 '{NLI_MODEL_NAME}' 失败: {e}")
    print("NLI 功能将不可用。")

# --- 2. 定义NLI预测函数 ---
def get_nli_relations(premise: str, hypothesis: str):
    """
    使用加载的NLI模型预测前提和假设之间的关系分数。

    Args:
        premise (str): 前提句子。
        hypothesis (str): 假设句子。

    Returns:
        dict: 包含所有类别标签及其对应概率的字典，或者在模型未加载时返回错误信息。
    """
    if not is_nli_model_loaded:
        return {"error": "NLI 模型或分词器未加载。"}

    try:
        if not premise.strip() or not hypothesis.strip():
            # print("警告: 前提或假设为空字符串，NLI预测可能不准确。")
            pass # Let transformers handle it, it might error out or give low confidence

        inputs = nli_tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, padding=True, max_length=512)

        with torch.no_grad():
            outputs = nli_model(**inputs)
            logits = outputs.logits

        probabilities = torch.softmax(logits, dim=-1)
        
        scores = {}
        for i in range(probabilities.shape[1]):
            label = nli_model.config.id2label[i] 
            score = probabilities[0, i].item()
            scores[label] = score
            
        return scores

    except Exception as e:
        print(f"NLI 预测过程中发生错误: {e}")
        return {"error": f"NLI 预测失败: {str(e)}"}

# --- 3. 定义检查目标与基本事实矛盾的函数 (保留原有功能) ---
def check_target_contradiction_with_ground_truths(target_statement: str, ground_truth_statements: list):
    """
    计算目标陈述与每个基本事实陈述相矛盾的概率。
    """
    if not is_nli_model_loaded:
        return [{"error": "NLI 模型未加载，无法执行检查。"}]
    if not ground_truth_statements:
        print("提示: 当前没有任何基本事实(公理)被定义。请先使用 'axiom <陈述>' 命令添加。")
        return []

    results = []
    print(f"\n--- 正在检查目标 \"{target_statement}\" 与基本事实的矛盾性 ---")
    for gt_statement in ground_truth_statements:
        nli_scores = get_nli_relations(premise=gt_statement, hypothesis=target_statement)
        
        contradiction_probability = None
        if "error" not in nli_scores:
            contradiction_probability = nli_scores.get('contradiction', 0.0)
        
        results.append({
            "ground_truth": gt_statement,
            "target": target_statement,
            "contradiction_probability": contradiction_probability,
            "all_nli_scores": nli_scores
        })
        
        print(f"  基本事实: \"{gt_statement}\"")
        print(f"  与目标 \"{target_statement}\" 矛盾的概率: {contradiction_probability if contradiction_probability is not None else '错误'}")
        print("-" * 30)
        
    return results

# --- 4. REPL (Read-Eval-Print Loop) 实现 ---
def repl():
    """
    启动一个交互式循环来处理用户输入。
    """
    if not is_nli_model_loaded:
        print("NLI 模型未能成功加载。REPL 功能受限或不可用。")
        return

    print(f"\n欢迎来到 NLI 证明助手 (REPL)！蕴含阈值: {ENTAILMENT_THRESHOLD}")
    print("输入 'help' 获取可用命令列表。")
    
    current_axioms = []
    current_lemmas = {} # {lemma_name: lemma_statement}

    while True:
        try:
            user_input_raw = input("nli-prover> ").strip()
            if not user_input_raw:
                continue

            command_parts = user_input_raw.split(" ", 1)
            command = command_parts[0].lower()
            argument = command_parts[1].strip() if len(command_parts) > 1 else ""

            if command == "axiom":
                if argument:
                    if argument not in current_axioms:
                        current_axioms.append(argument)
                        print(f"已添加公理 (A{len(current_axioms)}): \"{argument}\"")
                    else:
                        print(f"公理 \"{argument}\" 已存在。")
                else:
                    print("用法: axiom <公理陈述>")
            
            elif command == "lemma":
                if argument:
                    lemma_parts = argument.split(" ", 1)
                    if len(lemma_parts) == 2:
                        lemma_name = lemma_parts[0]
                        if lemma_name.lower() in ["axioms", "lemmas", "using", "with"]: 
                            print(f"错误: 引理名称 '{lemma_name}' 与系统关键字冲突，请选择其他名称。")
                            continue
                        lemma_statement = lemma_parts[1]
                        current_lemmas[lemma_name] = lemma_statement
                        l_num = list(current_lemmas.keys()).index(lemma_name) + 1
                        print(f"已添加引理 L{l_num} ('{lemma_name}'): \"{lemma_statement}\"")
                    else:
                        print("用法: lemma <引理名称> <引理陈述> (名称应为单个词，不能包含空格)")
                else:
                    print("用法: lemma <引理名称> <引理陈述>")

            elif command == "target": 
                if argument:
                    if not current_axioms:
                        print("错误: 请先至少添加一个公理(axiom)才能设定目标进行矛盾检查。")
                    else:
                        check_target_contradiction_with_ground_truths(argument, current_axioms)
                else:
                    print("用法: target <目标陈述> (用于矛盾检查)")
            
            elif command == "prove":
                if not argument:
                    print("用法: prove <目标> [using axioms <公理编号列表> [lemmas <引理名称列表>]]")
                    continue
                
                parts_using_split = argument.split(" using ", 1)
                target_to_prove = parts_using_split[0].strip()
                is_proven_this_call = False # Flag for the current prove command's success

                if len(parts_using_split) > 1: # 'using' 子句存在
                    using_clause = parts_using_split[1].strip()
                    combined_premise_parts = []
                    tokens = using_clause.split()
                    current_mode = None 
                    valid_combination_build = True

                    for token_val in tokens:
                        token_lower = token_val.lower()
                        if token_lower == "axioms":
                            current_mode = "axiom"; continue
                        elif token_lower == "lemmas":
                            current_mode = "lemma"; continue
                        
                        if current_mode == "axiom":
                            try:
                                axiom_num = int(token_val)
                                if 1 <= axiom_num <= len(current_axioms):
                                    combined_premise_parts.append(current_axioms[axiom_num - 1])
                                else:
                                    print(f"错误: 公理编号 {axiom_num} 无效 (可用范围 1-{len(current_axioms)})。"); valid_combination_build = False; break
                            except ValueError:
                                print(f"错误: 无效的公理编号 '{token_val}'。"); valid_combination_build = False; break
                        elif current_mode == "lemma":
                            if token_val in current_lemmas:
                                combined_premise_parts.append(current_lemmas[token_val])
                            else:
                                print(f"错误: 未找到引理名称 '{token_val}'."); valid_combination_build = False; break
                        else:
                            print(f"错误: 'using' 子句格式不正确。应以 'axioms' 或 'lemmas' 开始。遇到了 '{token_val}'"); valid_combination_build = False; break
                    
                    if not valid_combination_build: continue
                    if not combined_premise_parts:
                        print("错误: 未指定有效的公理或引理进行合并，或者指定的公理/引理列表为空。"); continue
                    
                    combined_premise_str = ". ".join(combined_premise_parts) + "." 
                    print(f"\n--- 尝试使用合并前提证明目标: \"{target_to_prove}\" ---")
                    print(f"  合并的前提: \"{combined_premise_str}\"")
                    
                    nli_scores = get_nli_relations(premise=combined_premise_str, hypothesis=target_to_prove)
                    if "error" not in nli_scores:
                        entailment_score = nli_scores.get('entailment', 0.0)
                        if entailment_score >= ENTAILMENT_THRESHOLD:
                            print(f"  [合并前提证明成功] 合并前提 \n    --蕴含({entailment_score:.4f})--> 目标 \"{target_to_prove}\"")
                            is_proven_this_call = True
                        else:
                            print(f"  [合并前提证明失败] 合并前提未能充分蕴含目标 (蕴含概率: {entailment_score:.4f}, 阈值: {ENTAILMENT_THRESHOLD})")
                    else:
                        print(f"  NLI预测错误: {nli_scores.get('error')}")
                
                else: # 'using' 子句不存在, 执行原有的证明逻辑
                    print(f"\n--- 尝试证明目标: \"{target_to_prove}\" (未使用合并前提) ---")
                    if not current_axioms:
                        print("  错误: 没有任何公理，无法进行直接或基于引理的证明。")
                    else:
                        # 尝试1: 直接由公理蕴含目标
                        for i, axiom in enumerate(current_axioms):
                            nli_scores = get_nli_relations(premise=axiom, hypothesis=target_to_prove)
                            if "error" not in nli_scores:
                                entailment_score = nli_scores.get('entailment', 0.0)
                                if entailment_score >= ENTAILMENT_THRESHOLD:
                                    print(f"  [直接证明成功] 公理 A{i+1}: \"{axiom}\" \n    --蕴含({entailment_score:.4f})--> 目标 \"{target_to_prove}\"")
                                    is_proven_this_call = True; break 
                        
                        if is_proven_this_call:
                            print("--- 目标已通过直接证明达成 ---")
                        else: 
                            print("  未找到直接证明路径，尝试通过引理证明...")
                            if not current_lemmas:
                                print("  当前没有定义引理可供尝试。")
                            else:
                                lemma_items = list(current_lemmas.items())
                                for l_idx, (lemma_name, lemma_statement) in enumerate(lemma_items):
                                    if is_proven_this_call: break 
                                    axiom_that_proves_lemma = None; axiom_to_lemma_entailment_score = 0.0; axiom_idx_for_lemma_proof = -1
                                    for ax_idx, axiom in enumerate(current_axioms):
                                        nli_scores_axiom_lemma = get_nli_relations(premise=axiom, hypothesis=lemma_statement)
                                        if "error" not in nli_scores_axiom_lemma:
                                            current_entail_score = nli_scores_axiom_lemma.get('entailment', 0.0)
                                            if current_entail_score >= ENTAILMENT_THRESHOLD:
                                                axiom_that_proves_lemma = axiom; axiom_to_lemma_entailment_score = current_entail_score
                                                axiom_idx_for_lemma_proof = ax_idx
                                                print(f"    - 找到路径: 公理 A{ax_idx+1}: \"{axiom}\" \n      --蕴含({current_entail_score:.4f})--> 引理 L{l_idx+1} ('{lemma_name}'): \"{lemma_statement}\"")
                                                break 
                                    if axiom_that_proves_lemma:
                                        nli_scores_lemma_target = get_nli_relations(premise=lemma_statement, hypothesis=target_to_prove)
                                        if "error" not in nli_scores_lemma_target:
                                            lemma_to_target_entailment_score = nli_scores_lemma_target.get('entailment', 0.0)
                                            if lemma_to_target_entailment_score >= ENTAILMENT_THRESHOLD:
                                                print(f"    - 且 引理 L{l_idx+1} ('{lemma_name}'): \"{lemma_statement}\" \n      --蕴含({lemma_to_target_entailment_score:.4f})--> 目标 \"{target_to_prove}\"")
                                                print(f"  [通过引理证明成功] 路径: \n    公理 A{axiom_idx_for_lemma_proof+1}: \"{axiom_that_proves_lemma}\" \n    --蕴含({axiom_to_lemma_entailment_score:.4f})--> 引理 L{l_idx+1} ('{lemma_name}') \n    --蕴含({lemma_to_target_entailment_score:.4f})--> 目标 \"{target_to_prove}\"")
                                                is_proven_this_call = True; break
                                            else:
                                                print(f"    - 但 引理 L{l_idx+1} ('{lemma_name}') 不能充分蕴含目标 (蕴含概率: {lemma_to_target_entailment_score:.4f}, 阈值: {ENTAILMENT_THRESHOLD})。")
                        
                        if not is_proven_this_call: # After all attempts (direct, and lemma if applicable)
                             print("--- 未能通过当前公理和引理证明目标 (未使用合并前提) ---")

                # Add to axioms if proven in this call by any method
                if is_proven_this_call:
                    if target_to_prove not in current_axioms:
                        current_axioms.append(target_to_prove)
                        print(f"  [已证实] 目标 \"{target_to_prove}\" 已添加为新公理 (A{len(current_axioms)})。")
                    else:
                        print(f"  [已证实] 目标 \"{target_to_prove}\" 已存在于公理中 (A{current_axioms.index(target_to_prove)+1})。")


            elif command == "axioms":
                if not current_axioms:
                    print("当前没有已定义的基本事实(公理)。")
                else:
                    print("\n当前公理列表:")
                    for i, ax in enumerate(current_axioms):
                        print(f"  A{i+1}: \"{ax}\"")
                    print("")
            
            elif command == "lemmas":
                if not current_lemmas:
                    print("当前没有已定义的引理。")
                else:
                    print("\n当前引理列表:")
                    lemma_items_list = list(current_lemmas.items())
                    for i, (name, stmt) in enumerate(lemma_items_list):
                        print(f"  L{i+1} ({name}): \"{stmt}\"")
                    print("")

            elif command == "clear":
                current_axioms = []
                current_lemmas = {}
                print("所有公理和引理已被清除。")

            elif command == "help":
                print("\n可用命令:")
                print("  axiom <陈述>                    - 添加一个新的公理。")
                print("  lemma <名称> <陈述>             - 添加一个新的命名引理 (名称应为单个词)。")
                print("  target <陈述>                   - (原功能)检查目标与所有公理的矛盾概率。")
                print("  prove <目标> [using axioms <A_nums> [lemmas <L_names>]]")
                print("                                  - 尝试证明目标。可选择使用 'using' 合并指定公理(通过A编号)")
                print("                                    和/或引理(通过名称)作为前提。证明成功的目标会自动成为新公理。")
                print("                                    例如: prove C using axioms 1 2 lemmas my_L")
                print("  axioms                          - 列出所有当前的公理 (带编号 A1, A2...)。")
                print("  lemmas                          - 列出所有当前的引理 (带编号 L1, L2... 及名称)。")
                print("  clear                           - 清除所有公理和引理。")
                print("  help                            - 显示此帮助信息。")
                print("  exit / quit                     - 退出程序。")
                print(f"(当前蕴含阈值: {ENTAILMENT_THRESHOLD})")
                print("")

            elif command in ["exit", "quit"]:
                print("正在退出 NLI 证明助手。再见！")
                break
            
            else:
                print(f"未知命令: \"{command}\". 输入 'help' 查看可用命令。")

        except EOFError:
            print("\n正在退出 NLI 证明助手。再见！")
            break
        except KeyboardInterrupt:
            print("\n操作已中断。输入 'exit' 或 'quit' 退出。")
        except Exception as e:
            print(f"发生了一个错误: {e}")
            import traceback
            traceback.print_exc() 


# --- 5. 主程序入口 ---
if __name__ == "__main__":
    if is_nli_model_loaded:
        repl()
    else:
        print("由于NLI模型未能加载，REPL无法启动。请检查错误信息并确保 transformers 和 torch 已正确安装。")

