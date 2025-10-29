import copy

from math_verify import parse, verify
from sympy import solve

from timeout_function_decorator import timeout

from openai import OpenAI


API_KEY = "API_KEY_HERE"
BASE_URL = "BASE_URL_HERE"

SCORE_PROMPT = """
For the following math problem, we have the reference answer and the student's answer.
Determine whether the student's answer is equivalent to the reference answer.
If equivalent, output "Correct".
If not equivalent, output "Incorrect".

### Problem
QUESTION

### Reference Answer
GOLD

### Student Answer
PRED

Now, please provide your judgment.
Please strictly follow the format below to summarize your conclusion at the end of your judgment:
### Conclusion: Correct/Incorrect
If the answer involves a decimal approximation, it must be accurate to at least four decimal places.
""".strip()

answer_prefix_list = [
    "### the final answer is:", "### the final answer:", "### final answer is:", "### final answer:",
    "### the final answer is", "### the final answer", "### final answer is", "### final answer",
]
answer_prefix_list_wo_hashtag = [p[4:] for p in answer_prefix_list]

think_postfix_list = [
    "</think>",
    "</longcat_think>",
]

cut_list = [
    "\\medskip", "\n---"
]

remove_list = [
    "\\bigl", "\\bigr", 
    "\\Bigl", "\\Bigr",
    "\\biggl", "\\biggr",
    "\\Biggl", "\\Biggr",
    "\\bigg", "\\Bigg", "\\big", "\\Big",
    "\\left", "\\right",
]
replace_list = [
    ["‘", "'"],
    ["’", "'"],
    ["“", '"'],
    ["”", '"'],
    ["（", "("],
    ["）", ")"],
    ["，", ", "],
    ["：", ": "],
    ["；", "; "],
    ["。", ". "],
    ["！", "! "],
    ["？", "? "],
    ["…", "..."],
    ["–", "-"],
    ["−", "-"],
]


@timeout(30)
def solve_with_timeout(exp):
    return solve(exp)

def pred_cut(pred_extract):
    for pat in cut_list:
        pred_extract = pred_extract.split(pat)[0].strip()
    return pred_extract

def pred_extractor(pred, answer_type):

    pred_extract = pred.replace('：', ': ')

    for think_postfix in think_postfix_list:
        pred_extract = pred_extract.split(think_postfix)[-1].strip()

    for prefix in answer_prefix_list + answer_prefix_list_wo_hashtag:
        if prefix in pred_extract.lower():
            pred_extract_lower = pred_extract.lower().split(prefix)[-1]
            pred_extract = pred_extract[-len(pred_extract_lower):]
            pred_extract = pred_extract.strip()
            break
    
    if answer_type != "description":
        for pat in remove_list:
            pred_extract = pred_extract.replace(pat, "")
    
    for pat, new_pat in replace_list:
        pred_extract = pred_extract.replace(pat, new_pat)

    while " }" in pred_extract:
        pred_extract = pred_extract.replace(" }", "}")
    while ".}" in pred_extract:
        pred_extract = pred_extract.replace(".}", "}")
    
    if answer_type in ["number", "variable", "set"]:
        pred_extract = pred_extract.replace("\\,", "")
        pred_extract = pred_extract.replace("\\;", "")
        pred_extract = pred_extract.replace("\,", "")
        pred_extract = pred_extract.replace("\;", "")
        pred_extract = pred_extract.replace("\n", " ")
    
    if answer_type in ["number", "variable"]:
        pred_extract = pred_extract.replace(",", "")
        pred_extract = pred_extract.replace("\\{", "(").replace("\\}", ")").replace("\\[", "(").replace("\\]", ")")

    return pred_extract.strip()

def call_api(prompt):
    client = OpenAI(
        api_key = API_KEY,
        base_url = BASE_URL
    )
    try:
        response = client.chat.completions.create(
            model="o4-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=False,
            max_tokens=8192,
            temperature=1.0,
            reasoning_effort="low",
        )
    except Exception as e:
        print("Error in response")
        e_str = str(e)
        print(e_str)
        response = {}

    return response

def verify_description_answer(pred_extract, info):
    llm_score_prompt = SCORE_PROMPT

    assert "GOLD" in llm_score_prompt
    llm_score_prompt = llm_score_prompt.replace("GOLD", info["answer"])

    assert "PRED" in llm_score_prompt
    llm_score_prompt = llm_score_prompt.replace("PRED", pred_extract)

    assert "QUESTION" in llm_score_prompt
    llm_score_prompt = llm_score_prompt.replace("QUESTION", info["prompt"])

    if len(llm_score_prompt) >= 20000:
        print("Prompt is too long, truncate it.")
        llm_score_prompt = llm_score_prompt[:10000] + "\n\n...\n\n" + llm_score_prompt[-10000:]

    llm_judge_vote_num = 5
    llm_judge_vote_list = []
    for vote_round in range(llm_judge_vote_num):
        response = call_api(llm_score_prompt)
        response_content = response.choices[0].message.content

        conclusion = response_content.lower().split("conclusion:")[-1]
        if "correct" in conclusion.split() and "not correct" not in conclusion and "n't correct" not in conclusion:
            llm_judge_vote = True
        else:
            llm_judge_vote = False

        llm_judge_vote_list.append(llm_judge_vote)

    assert len(llm_judge_vote_list) == llm_judge_vote_num
    llm_judge = True if llm_judge_vote_list.count(True) > llm_judge_vote_list.count(False) else False

    return llm_judge

def verify_number_set_answer(pred_extract, info):
    pred_parse = parse(pred_extract)
    gold_parse = parse(info["answer"])
    verify_result = verify(gold_parse, pred_parse, float_rounding=4) or verify(pred_parse, gold_parse, float_rounding=4)

    if pred_parse and '=' in pred_parse[-1]:
        pred_last_str = pred_parse[-1].split('=')[-1]
        pred_last_str_parse = parse("\\boxed{" + pred_last_str + "}")
        verify_last_result = verify(gold_parse, pred_last_str_parse, float_rounding=4) or verify(pred_last_str_parse, gold_parse, float_rounding=4)
        verify_result = verify_result or verify_last_result

    return verify_result

def verify_variable_answer(pred_extract, info):
    assert "try_list" in info
            
    pred_parse_ori = parse(pred_extract)
    if not pred_parse_ori:
        print("Cannot parse the prediction: {}".format(pred_extract))
        info['verify_result'] = False
        return False
    
    pred_parse_str = pred_parse_ori[-1]
    pred_parse_str = pred_parse_str.split("\\qquad")[-2].strip() if "\\qquad" in pred_parse_str else pred_parse_str
    pred_parse_str = pred_parse_str.split("\\quad")[-2].strip() if "\\quad" in pred_parse_str else pred_parse_str
    pred_parse_str = pred_parse_str.split("=")[-1]

    gold_parse_ori = parse(info["answer"])
    gold_parse_str = gold_parse_ori[-1]
    gold_parse_str = gold_parse_str.split("=")[-1]

    assert len(info["try_list"]) >= 1
    verify_result = True
    for try_str in info["try_list"]:
        pred_parse_equ = parse("\\boxed{" + try_str + ", y=" + pred_parse_str + "}")
        gold_parse_equ = parse("\\boxed{" + try_str + ", y=" + gold_parse_str + "}")

        try:
            pred_parse_solve = solve_with_timeout(pred_parse_equ[0])
        except Exception as e:
            print("Error in solving the prediction: {}".format(pred_parse_equ[0]))
            print(e)
            verify_result = False
            break
        gold_parse_solve = solve(gold_parse_equ[0])

        assert gold_parse_solve != [] and gold_parse_solve != {}

        if not pred_parse_solve:
            verify_result = False
            break

        if isinstance(pred_parse_solve, list):
            pred_parse_solve = pred_parse_solve[0]
        if isinstance(gold_parse_solve, list):
            gold_parse_solve = gold_parse_solve[0]

        pred_parse_solve_y = None
        gold_parse_solve_y = None

        try:
            for s in pred_parse_solve:
                if str(s) == 'y':
                    pred_parse_solve_y = pred_parse_solve[s]
        except Exception as e:
            print("Error in parsing the prediction solution: {}".format(pred_extract))
            print(e)
            verify_result = False
            break
            
        for s in gold_parse_solve:
            if str(s) == 'y':
                gold_parse_solve_y = gold_parse_solve[s]

        assert gold_parse_solve_y is not None

        pred_parse_solve_y = pred_parse_solve_y.evalf()
        gold_parse_solve_y = gold_parse_solve_y.evalf()

        verify_result = verify(gold_parse_solve_y, pred_parse_solve_y, float_rounding=8) or verify(pred_parse_solve_y, gold_parse_solve_y, float_rounding=8)

        if not verify_result:
            break

    return verify_result

def append_try_list(ori_info):
    info = copy.deepcopy(ori_info)
    assert "question_id" in info
    question_id = info["question_id"]
    if question_id == 5:
        assert info["answer_type"] == "variable"
        try_list = ["n=1", "n=2", "n=3", "n=4", "n=5", "n=6", "n=7", "n=8", "n=9", "n=10",
                    "n=11", "n=12", "n=13", "n=14", "n=15", "n=16", "n=17", "n=18", "n=19", "n=20"]
        info["try_list"] = try_list
    elif question_id == 37:
        assert info["answer_type"] == "variable"
        try_list = ["a=2,b=3,c=4", "a=3,b=4,c=5", "a=4,b=5,c=6", "a=5,b=6,c=7", "a=6,b=7,c=8",
                    "a=7,b=8,c=9", "a=8,b=9,c=10", "a=9,b=10,c=11", "a=10,b=11,c=12",
                    "a=11,b=12,c=13", "a=12,b=13,c=14", "a=13,b=14,c=15", "a=14,b=15,c=16",
                    "a=15,b=16,c=17", "a=16,b=17,c=18", "a=17,b=18,c=19", "a=18,b=19,c=20"]
        info["try_list"] = try_list
    
    return info
