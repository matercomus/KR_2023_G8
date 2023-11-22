import argparse
import json
import time

import numpy as np
from no_java_lib import *
from py4j.java_gateway import JavaGateway


def calculate_stats(execution_times):
    total_time = sum(execution_times)
    avg_time = np.mean(execution_times)
    std_dev = np.std(execution_times)
    return total_time, avg_time, std_dev

def process_class(class_name, reasoner_EL, reasoner_ELK, elFactory, formatter, args):
    result = {"class_name": class_name}

    start_time_EL = time.time()
    subsumers_EL = reasoner_EL.compute_subsumers(class_name)
    end_time_EL = time.time()

    result["ELReasoner"] = {
        "subsumers": subsumers_EL,
        "count": len(subsumers_EL),
        "execution_time": end_time_EL - start_time_EL,
    }

    if args.verbose:
        print(f"ELReasoner computed {len(subsumers_EL)} subsumers for class {class_name} in {end_time_EL - start_time_EL:.5f} seconds")

    start_time_ELK = time.time()
    class_name_ELK = elFactory.getConceptName(class_name)
    subsumers_ELK = reasoner_ELK.getSubsumers(class_name_ELK)
    end_time_ELK = time.time()

    result["ELK"] = {
        "subsumers": [formatter.format(concept) for concept in subsumers_ELK.toArray()],
        "count": len(subsumers_ELK),
        "execution_time": end_time_ELK - start_time_ELK,
    }

    if args.verbose:
        print(f"ELK computed {len(subsumers_ELK)} subsumers for class {class_name} in {end_time_ELK - start_time_ELK:.5f} seconds")

    if args.verbose:
        print()

    return result, end_time_EL - start_time_EL, end_time_ELK - start_time_ELK

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="EL Reasoner")
    arg_parser.add_argument("ontology_file", type=str, help="Path to the ontology file")
    arg_parser.add_argument("-l", "--limit", type=int, help="Limit on the number of classes to process")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Print details while processing")
    args = arg_parser.parse_args()

    gateway = JavaGateway()
    parser = gateway.getOWLParser()
    formatter = gateway.getSimpleDLFormatter()
    ontology_ELK = parser.parseFile(args.ontology_file)
    ontology_EL = load_ontology(args.ontology_file)

    reasoner_EL = ELReasoner(ontology_EL)
    all_classes = reasoner_EL.compute_all_classes()
    if args.limit is not None:
        all_classes = all_classes[:args.limit]

    gateway.convertToBinaryConjunctions(ontology_ELK)
    elFactory = gateway.getELFactory()
    reasoner_ELK = gateway.getELKReasoner()
    reasoner_ELK.setOntology(ontology_ELK)

    results = []
    execution_times_EL = []
    execution_times_ELK = []

    for class_name in all_classes:
        result, time_elapsed_EL, time_elapsed_ELK = process_class(class_name, reasoner_EL, reasoner_ELK, elFactory, formatter, args)
        results.append(result)
        execution_times_EL.append(time_elapsed_EL)
        execution_times_ELK.append(time_elapsed_ELK)

    total_time_EL, avg_time_EL, std_dev_EL = calculate_stats(execution_times_EL)
    total_time_ELK, avg_time_ELK, std_dev_ELK = calculate_stats(execution_times_ELK)

    if args.verbose:
        print(f"ELReasoner total time: {total_time_EL}, average time: {avg_time_EL}, standard deviation: {std_dev_EL}")
        print(f"ELK total time: {total_time_ELK}, average time: {avg_time_ELK}, standard deviation: {std_dev_ELK}")

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
