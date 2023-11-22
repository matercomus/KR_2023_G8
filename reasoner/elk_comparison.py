#! /usr/bin/python

from py4j.java_gateway import JavaGateway
from no_java_lib import *
import argparse
import time
import timeit


def measure_reasoner_EL_execution(reasoner_EL, class_name):
    reasoner_EL.compute_subsumers(class_name)

def measure_reasoner_ELK_execution(reasoner_ELK, class_name):
    subsumers_ELK = reasoner_ELK.getSubsumers(class_name)
    return subsumers_ELK

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description="EL Reasoner")
    arg_parser.add_argument("ontology_file", type=str, help="Path to the ontology file")
    arg_parser.add_argument("class_name", type=str, help="Class name to find subsumers for")
    args = arg_parser.parse_args()

    # connect to the java gateway of dl4python
    gateway = JavaGateway()

    # get a parser from OWL files to DL ontologies
    parser = gateway.getOWLParser()

    # get a formatter to print in nice DL format
    formatter = gateway.getSimpleDLFormatter()

    # load ontologies
    ontology_ELK = parser.parseFile(args.ontology_file)
    ontology_EL = load_ontology(args.ontology_file)

    reasoner_EL = ELReasoner(ontology_EL)

    gateway.convertToBinaryConjunctions(ontology_ELK)
    elFactory = gateway.getELFactory()
    reasoner_ELK = gateway.getELKReasoner()
    class_name = elFactory.getConceptName(args.class_name)
    reasoner_ELK.setOntology(ontology_ELK)

     # Measure execution time of reasoner_EL.compute_subsumers
    execution_time = timeit.timeit(
        'measure_reasoner_EL_execution(reasoner_EL, args.class_name)',
        globals=globals(),
        number=100
    )
    print(f"Execution time for ELReasoner over 100 iterations: {execution_time} seconds")

    execution_time = timeit.timeit(
        'measure_reasoner_ELK_execution(reasoner_ELK, class_name)',
        globals=globals(),
        number=100
    )
    print(f"Execution time for ELK over 100 iterations: {execution_time} seconds")

    # run ELReasoner and compute subsumers
    # start_time_EL = time.time()  # Start time

    # reasoner_EL = ELReasoner(ontology_EL)
    # subsumers_EL = reasoner_EL.compute_subsumers(args.class_name)

    # end_time_EL = time.time()  # End time
    # time_elapsed_EL = end_time_EL - start_time_EL

    # run ELK rasoner and compute subsumers
    # start_time_ELK = time.time()  # Start time

    # gateway.convertToBinaryConjunctions(ontology_ELK)
    # elFactory = gateway.getELFactory()
    # reasoner_ELK = gateway.getELKReasoner()
    # class_name = elFactory.getConceptName(args.class_name)
    # reasoner_ELK.setOntology(ontology_ELK)
    # subsumers_ELK = reasoner_ELK.getSubsumers(class_name)

    # end_time_ELK = time.time()  # End time
    # time_elapsed_ELK = end_time_ELK - start_time_ELK

    # printing output
    # print(f"\nAccording to ELK, {args.class_name} has the following subsumers: ")
    # for concept in subsumers_ELK.toArray():
    #     print(" - ", formatter.format(concept))
    # print("(", len(subsumers_ELK), " in total)")
    # print("execution time:", time_elapsed_ELK)

    # print(f"According to our ELReasoner, {args.class_name} has the following subsumers: ")
    # for subsumer in subsumers_EL:
    #     print(" - ", subsumer)
    # print("(", len(subsumers_EL), " in total)")
    # print("execution time:", time_elapsed_EL)

