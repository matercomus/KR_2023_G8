import argparse
import glob
import json
import os
import time

import numpy as np
from no_java_lib import *
from owlready2 import *
from py4j.java_gateway import JavaGateway
from tqdm import tqdm


class Reasoner:
    def __init__(self, class_name, reasoner_EL, reasoner_ELK, elFactory, formatter, args):
        self.class_name = class_name
        self.reasoner_EL = reasoner_EL
        self.reasoner_ELK = reasoner_ELK
        self.elFactory = elFactory
        self.formatter = formatter
        self.args = args

    def calculate_stats(self, execution_times):
        total_time = sum(execution_times)
        avg_time = np.mean(execution_times)
        std_dev = np.std(execution_times)
        return total_time, avg_time, std_dev

    def process_class(self):
        result = {"class_name": self.class_name}

        # ELReasoner
        start_time_EL = time.time()
        subsumers_EL = self.reasoner_EL.compute_subsumers(self.class_name)
        end_time_EL = time.time()

        result["ELReasoner"] = {
            "subsumers": subsumers_EL,
            "count": len(subsumers_EL),
            "execution_time": end_time_EL - start_time_EL,
        }
        if self.args.verbose:
            print(f"ELReasoner computed {len(subsumers_EL)} subsumers for class {self.class_name} in {end_time_EL - start_time_EL:.5f} seconds")

        # ELK Reasoner
        start_time_ELK = time.time()
        class_name_ELK = self.elFactory.getConceptName(self.class_name)
        subsumers_ELK = self.reasoner_ELK.getSubsumers(class_name_ELK)
        end_time_ELK = time.time()

        result["ELK"] = {
            "subsumers": [self.formatter.format(concept) for concept in subsumers_ELK.toArray()],
            "count": len(subsumers_ELK),
            "execution_time": end_time_ELK - start_time_ELK,
        }
        if self.args.verbose:
            print(f"ELK computed {len(subsumers_ELK)} subsumers for class {self.class_name} in {end_time_ELK - start_time_ELK:.5f} seconds")

        # HermiT Reasoner
        start_time_HERMIT = time.time()
        class_object_HERMIT = ontology_HERMIT.search_one(iri="*" + self.class_name)
        subsumers_HERMIT = class_object_HERMIT.ancestors(include_self=True, include_constructs=False)
        end_time_HERMIT = time.time()

        result["HermiT"] = {
            "subsumers": [str(i) for i in subsumers_HERMIT],
            "count": len(subsumers_HERMIT),
            "execution_time": end_time_HERMIT - start_time_HERMIT,
        }
        if self.args.verbose:
            print(f"HermiT computed {len(subsumers_HERMIT)} subsumers for class {self.class_name} in {end_time_HERMIT - start_time_HERMIT:.5f} seconds")

        if self.args.verbose:
            print()

        return result, end_time_EL - start_time_EL, end_time_ELK - start_time_ELK, end_time_HERMIT - start_time_HERMIT


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="EL Reasoner")
    arg_parser.add_argument("ontology_file", type=str, help="Path to the ontology file or directory containing XML files")
    arg_parser.add_argument("-l", "--limit", type=int, help="Limit on the number of classes to process")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Print details while processing")
    arg_parser.add_argument("-p", "--progress", action="store_true", help="Show progress bar")
    arg_parser.add_argument("-o", "--output", type=str, default=".", help="Output directory")
    args = arg_parser.parse_args()

    # Connect to the Java Gateway ELK
    gateway = JavaGateway()
    parser = gateway.getOWLParser()
    formatter = gateway.getSimpleDLFormatter()

    if os.path.isdir(args.ontology_file):
        ontology_files = glob.glob(os.path.join(args.ontology_file, "*.xml"))
    else:
        ontology_files = [args.ontology_file]

    aggregate_results = {}

    for ontology_file in ontology_files:
        try:
            if args.verbose or args.progress:
                print(f"Processing {ontology_file}")

            # Load ontology for ELReasoner
            ontology_EL = load_ontology(ontology_file)
            reasoner_EL = ELReasoner(ontology_EL)

            # Get all classes in the ontology
            all_classes = reasoner_EL.compute_all_classes()

            # Limit the number of classes if limit flag specified
            if args.limit is not None:
                all_classes = all_classes[:args.limit]

            # Load ontology for ELK with py4j
            ontology_ELK = parser.parseFile(ontology_file)
            gateway.convertToBinaryConjunctions(ontology_ELK)
            elFactory = gateway.getELFactory()
            reasoner_ELK = gateway.getELKReasoner()
            reasoner_ELK.setOntology(ontology_ELK)

            # Load ontology for HermiT
            ontology_HERMIT = load_ontology(ontology_file)
            sync_reasoner()


            results = []
            execution_times_EL = []
            execution_times_ELK = []
            execution_times_HERMIT = []

            # Show progress bar if progress flag specified
            if args.progress:
                all_classes = tqdm(all_classes)

            # Process each class
            for class_name in all_classes:
                reasoner = Reasoner(class_name, reasoner_EL, reasoner_ELK, elFactory, formatter, args)
                result, time_elapsed_EL, time_elapsed_ELK, time_elapsed_HERMIT = reasoner.process_class()
                results.append(result)
                execution_times_EL.append(time_elapsed_EL)
                execution_times_ELK.append(time_elapsed_ELK)
                execution_times_HERMIT.append(time_elapsed_HERMIT)

            total_time_EL, avg_time_EL, std_dev_EL = reasoner.calculate_stats(execution_times_EL)
            total_time_ELK, avg_time_ELK, std_dev_ELK = reasoner.calculate_stats(execution_times_ELK)
            total_time_HERMIT, avg_time_HERMIT, std_dev_HERMIT = reasoner.calculate_stats(execution_times_HERMIT)

            if args.verbose:
                print(f"ELReasoner total time: {total_time_EL}, average time: {avg_time_EL}, standard deviation: {std_dev_EL}")
                print(f"ELK total time: {total_time_ELK}, average time: {avg_time_ELK}, standard deviation: {std_dev_ELK}")
                print(f"HermiT total time: {total_time_HERMIT}, average time: {avg_time_HERMIT}, standard deviation: {std_dev_HERMIT}")
                print()

            # Add the stats to the results
            stats = {
                "ELReasoner": {
                    "total_time": total_time_EL,
                    "average_time": avg_time_EL,
                    "std_dev": std_dev_EL
                },
                "ELK": {
                    "total_time": total_time_ELK,
                    "average_time": avg_time_ELK,
                    "std_dev": std_dev_ELK
                },
                "HermiT": {
                    "total_time": total_time_HERMIT,
                    "average_time": avg_time_HERMIT,
                    "std_dev": std_dev_HERMIT
                }
            }
            results.append({"statistics": stats})

            # Create output directory if it doesn't exist
            os.makedirs(args.output, exist_ok=True)

            # Save the results of each ontology
            with open(os.path.join(args.output, f"{os.path.basename(ontology_file)}.results.json"), "w") as f:
                json.dump(results, f, indent=2)

            # Add the stats to the aggregate results
            aggregate_results[os.path.basename(ontology_file)] = stats

            # Save the aggregate results after each ontology
            with open(os.path.join(args.output, "aggregate_results.json"), "w") as f:
                json.dump(aggregate_results, f, indent=2)

        except Exception as e:
            print(f"Error processing {ontology_file}: {e}")
