import json
import copy
import os
import argparse
import datasets
from tqdm import tqdm

from utils import (
    pred_extractor,
    pred_cut,
    verify_description_answer,
    verify_number_set_answer,
    verify_variable_answer,
    append_try_list,
)


def verify_result(pred_extract, ori_info):
    info = copy.deepcopy(ori_info)
    assert 'prompt' in info
    assert 'question_id' in info
    assert 'answer' in info
    assert 'answer_type' in info

    if info["answer_type"] == "description":
        result = verify_description_answer(pred_extract, info)
        
    elif info["answer_type"] in ["number", "set"]:
        result = verify_number_set_answer(pred_extract, info)

    else:
        assert info["answer_type"] == "variable"
        result = verify_variable_answer(pred_extract, info)
    
    return result

def grading(pred, info):
    answer_type = info["answer_type"]
    pred_extract = pred_extractor(pred, answer_type)

    try:
        result = verify_result(pred_extract, info)
    except Exception as e:
        print("Error in grading")
        print(e)
        result = False

    result_cut = False
    pred_extract_cut = None
    if answer_type not in ['description']:
        pred_extract_cut = pred_cut(pred_extract)
        try:
            result_cut = verify_result(pred_extract_cut, info)
        except Exception as e:
            print("Error in grading")
            print(e)
            result_cut = False

    if result is True or result_cut is True:
        acc = 1.0
    else:
        acc = 0.0
    
    return acc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--response_file", type=str, required=True, help="Input file name.")
    parser.add_argument("--only_parser", type=bool, default=False, help="Only evaluate on problems with parser-based grading.")
    args = parser.parse_args()

    if not os.path.exists("model_responses"):
        os.makedirs("model_responses")

    dataset = datasets.load_dataset("meituan-longcat/AMO-Bench")
    question_id_to_info = {}
    for item in dataset["test"]:
        question_id_to_info[item["question_id"]] = append_try_list(item)
    
    with open(os.path.join("model_responses", args.response_file), "r", encoding="utf-8") as f_read:
        model_responses = [json.loads(line) for line in f_read.readlines()]
    
    question_id2acc = {}
    for model_response in tqdm(model_responses):
        question_id = model_response["question_id"]
        pred = model_response["model_response"]
        gold_info = question_id_to_info[question_id]

        if args.only_parser and gold_info["answer_type"] == "description":
            continue

        acc = grading(pred, gold_info)
        question_id2acc[question_id] = acc
    
    avg_acc = sum(question_id2acc[qid] for qid in question_id2acc) / len(question_id2acc)
    print(f"Average Accuracy: {avg_acc}")
    grading_result = {
        "average_accuracy": avg_acc,
        "per_question_accuracy": question_id2acc,
    }

    if not os.path.exists("grading_results"):
        os.makedirs("grading_results")

    if args.only_parser:
        write_file = os.path.join("grading_results", f"result_p_subset_{args.response_file}.log")
    else:
        write_file = os.path.join("grading_results", f"result_{args.response_file}.log")

    with open(write_file, "w", encoding="utf-8") as f_write:
        json.dump(grading_result, f_write, indent=4, ensure_ascii=False)

    
