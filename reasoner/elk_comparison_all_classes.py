#! /usr/bin/python

import argparse
import json
import time

from no_java_lib import *
from py4j.java_gateway import JavaGateway

if __name__ == "__main__":
    # Argument parsing for command line inputs
    arg_parser = argparse.ArgumentParser(description="EL Reasoner")
    arg_parser.add_argument("ontology_file", type=str, help="Path to the ontology file")
    arg_parser.add_argument("-l", "--limit", type=int, help="Limit on the number of classes to process")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Print details while processing")
    args = arg_parser.parse_args()

    # Connect to the Java gateway of dl4python
    gateway = JavaGateway()

    # Get a parser from OWL files to DL ontologies
    parser = gateway.getOWLParser()

    # Get a formatter to print in nice DL format
    formatter = gateway.getSimpleDLFormatter()

    # Load ontologies
    ontology_ELK = parser.parseFile(args.ontology_file)
    ontology_EL = load_ontology(args.ontology_file)

    # Get all classes in the ontology
    reasoner_EL = ELReasoner(ontology_EL)
    all_classes = reasoner_EL.compute_all_classes()

    # If a limit is set, truncate the list of classes
    if args.limit is not None:
        all_classes = all_classes[:args.limit]
    if args.verbose:
        print(all_classes)

    gateway.convertToBinaryConjunctions(ontology_ELK)
    elFactory = gateway.getELFactory()
    reasoner_ELK = gateway.getELKReasoner()
    reasoner_ELK.setOntology(ontology_ELK)

    results = []

    # Loop over all classes in the ontology
    for class_name in all_classes:
        if args.verbose:
            print(f"Processing class: {class_name}")  # Print current class name

        result = {"class_name": class_name}

        # Run ELReasoner and compute subsumers
        start_time_EL = time.time()
        subsumers_EL = reasoner_EL.compute_subsumers(class_name)
        end_time_EL = time.time()
        time_elapsed_EL = end_time_EL - start_time_EL

        # Print ELReasoner results
        if args.verbose:
            print(f"ELReasoner computed {len(subsumers_EL)} subsumers in {time_elapsed_EL:.5f} seconds")

        result["ELReasoner"] = {
            "subsumers": subsumers_EL,
            "count": len(subsumers_EL),
            "execution_time": time_elapsed_EL,
        }

        # Run ELK reasoner and compute subsumers
        start_time_ELK = time.time()
        class_name_ELK = elFactory.getConceptName(class_name)
        subsumers_ELK = reasoner_ELK.getSubsumers(class_name_ELK)
        end_time_ELK = time.time()
        time_elapsed_ELK = end_time_ELK - start_time_ELK

        # Print ELK results
        if args.verbose:
            print(f"ELK computed {len(subsumers_ELK)} subsumers in {time_elapsed_ELK:.5f} seconds")

        result["ELK"] = {
            "subsumers": [formatter.format(concept) for concept in subsumers_ELK.toArray()],
            "count": len(subsumers_ELK),
            "execution_time": time_elapsed_ELK,
        }

        if args.verbose:
            print()
        results.append(result)

    # Save results to a JSON file
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
