#!/usr/bin/python3

from owlready2 import SOME, And, Restriction, Thing, ThingClass, get_ontology


def load_ontology(file_path):
    ontology = get_ontology(file_path).load()
    return ontology


class ELReasoner:
    def __init__(self, ontology):
        self.ontology = ontology

    def add_element(self, element, concept, elements):
        if element not in elements:
            elements[element] = set()
        elements[element].add(concept)

    def apply_T_rule(self, concepts):
        if Thing not in concepts:
            concepts.add(Thing)
            return True
        return False

    def apply_conjunction_rule(self, concepts):
        changed = False
        for concept in concepts.copy():
            if isinstance(concept, And):
                for part in concept.Classes:
                    if part not in concepts:
                        concepts.add(part)
                        changed = True
        return changed

    def apply_existential_restriction_rule(self, element, concepts, elements, role_successors):
        changed = False
        for concept in concepts.copy():
            if isinstance(concept, Restriction) and concept.type == SOME:
                relation = concept.property
                filler = concept.value  # Use value instead of filler

                # Check for an existing r-successor
                if element in role_successors and relation in role_successors[element]:
                    for succ_element in role_successors[element][relation]:
                        if filler not in elements[succ_element]:
                            elements[succ_element].add(filler)
                            changed = True
                else:
                    # Create a new r-successor
                    new_element = f'{element}_{relation.name}'
                    self.add_element(new_element, filler, elements)
                    # Track the new r-successor
                    if element not in role_successors:
                        role_successors[element] = {}
                    if relation not in role_successors[element]:
                        role_successors[element][relation] = set()
                    role_successors[element][relation].add(new_element)
                    changed = True
        return changed

    def apply_subclass_rule(self, concepts):
        changed = False
        for concept in concepts.copy():
            if not isinstance(concept, ThingClass):
                continue
            # Retrieve all ancestors (superclasses) of the concept
            for super_concept in concept.ancestors(include_self=False):
                if super_concept not in concepts:
                    concepts.add(super_concept)
                    changed = True
        return changed

    def apply_role_successor_rule(self, element, concepts, elements, role_successors):
        changed = False
        # For each role successor, if the role is not already assigned to the element, assign it
        for role, successors in role_successors.get(element, {}).items():
            for successor in successors:
                # Check if 'successor' has a concept 'C' assigned
                for concept in elements[successor]:
                    # Check if there is an existential restriction ∃r.C in the ontology
                    existential_restriction = role.some(concept)
                    if existential_restriction not in concepts:
                        # Assign ∃r.C to the current element 'd'
                        concepts.add(existential_restriction)
                        changed = True
        return changed

    def apply_rules(self, elements, role_successors):
        changed = True
        while changed:
            changed = False
            for element in list(elements.keys()):
                concepts = elements[element]

                # Apply all rules
                changed |= self.apply_T_rule(concepts)
                changed |= self.apply_conjunction_rule(concepts)
                changed |= self.apply_existential_restriction_rule(element, concepts, elements, role_successors)
                changed |= self.apply_subclass_rule(concepts)
                changed |= self.apply_role_successor_rule(element, concepts, elements, role_successors)

        return elements

    def initialize_elements_with_class_and_equivalents(self, element, target_class, elements):
        self.add_element(element, target_class, elements)
        if hasattr(target_class, 'equivalent_to'):
            for eq_class in target_class.equivalent_to:
                if isinstance(eq_class, (And, Restriction)):
                    self.add_element(element, eq_class, elements)


    def filter_and_format_subsumers(self, subsumers, target_class):
        filtered_subsumers = []
        # List of concepts to be filtered out
        filter_out = ['ValuePartition', 'Thing', 'DomainConcept']
        for cls in subsumers:
            if cls is Thing:
                continue
            if isinstance(cls, ThingClass) and not isinstance(cls, Restriction) and not isinstance(cls, And):
                cls_name = cls.name if hasattr(cls, 'name') else str(cls)
                # Check if the concept is in the filter_out list
                if cls_name not in filter_out:
                    filtered_subsumers.append(cls_name)
        if target_class.name not in filtered_subsumers:
            filtered_subsumers.append(target_class.name)
        return filtered_subsumers

    def compute_subsumers(self, class_name):
        # Initialize elements and role_successors dictionaries
        elements = {}
        role_successors = {}

        target_class = self.ontology.search_one(iri="*" + class_name)
        if not target_class:
            return []

        self.initialize_elements_with_class_and_equivalents('d0', target_class, elements)
        self.apply_rules(elements, role_successors)
        subsumers = set()
        for concepts in elements.values():
            subsumers.update(concepts)

        return self.filter_and_format_subsumers(subsumers, target_class)

    # Compute all classes in the ontology
    def compute_all_classes(self):
        return [cls.name for cls in self.ontology.classes()]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EL Reasoner")
    parser.add_argument("ontology_file", type=str, help="Path to the ontology file")
    parser.add_argument("class_name", type=str, help="Class name to find subsumers for")
    args = parser.parse_args()

    ontology = load_ontology(args.ontology_file)
    reasoner = ELReasoner(ontology)
    subsumers = reasoner.compute_subsumers(args.class_name)

    for subsumer in subsumers:
        print(subsumer)
