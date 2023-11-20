from owlready2 import SOME, And, Restriction, Thing, ThingClass, get_ontology


class ELReasoner:
    def __init__(self, ontology):
        self.ontology = ontology
        self.elements = {}  # Map element to a set of concepts
        self.role_successors = {}  # New structure to track role successors

    def add_element(self, element, concept):
        if element not in self.elements:
            self.elements[element] = set()
        self.elements[element].add(concept)

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

    def apply_existential_restriction_rule(self, element, concepts):
        changed = False
        for concept in concepts.copy():
            if isinstance(concept, Restriction) and concept.type == SOME:
                relation, filler = concept.property, concept.filler
                # Check for an existing r-successor
                if element in self.role_successors and relation in self.role_successors[element]:
                    for succ_element in self.role_successors[element][relation]:
                        if filler not in self.elements[succ_element]:
                            self.elements[succ_element].add(filler)
                            changed = True
                else:
                    # Create a new r-successor
                    new_element = f'{element}_{relation.name}'
                    self.add_element(new_element, filler)
                    # Track the new r-successor
                    if element not in self.role_successors:
                        self.role_successors[element] = {}
                    if relation not in self.role_successors[element]:
                        self.role_successors[element][relation] = set()
                    self.role_successors[element][relation].add(new_element)
                    changed = True
        return changed

    def apply_subclass_rule(self, concepts):
        changed = False
        # Check for each concept if it is a subclass of another concept
        for concept in concepts.copy():
            if not isinstance(concept, ThingClass):
                continue
            for super_concept in concept.is_a:
                if isinstance(super_concept, ThingClass) and super_concept not in concepts:
                    concepts.add(super_concept)
                    changed = True
        return changed
    
    def apply_role_successor_rule(self, element, concepts):
        changed = False
        # For each role successor, if the role is not already assigned to the element, assign it
        for role, successors in self.role_successors.get(element, {}).items():
            for successor in successors:
                # Check if 'successor' has a concept 'C' assigned
                for concept in self.elements[successor]:
                    # Check if there is an existential restriction ∃r.C in the ontology
                    existential_restriction = role.some(concept)
                    if existential_restriction not in concepts:
                        # Assign ∃r.C to the current element 'd'
                        concepts.add(existential_restriction)
                        changed = True
        return changed

    def apply_rules(self):
        changed = True
        while changed:
            changed = False
            for element in list(self.elements.keys()):
                concepts = self.elements[element]

                # Apply all rules
                changed |= self.apply_T_rule(concepts)
                changed |= self.apply_conjunction_rule(concepts)
                changed |= self.apply_existential_restriction_rule(element, concepts)
                changed |= self.apply_subclass_rule(concepts)
                changed |= self.apply_role_successor_rule(element, concepts)

        return self.elements

    def compute_subsumers(self, class_name):
        # Find the class in the ontology
        target_class = self.ontology.search_one(iri="*" + class_name)
        if not target_class:
            print(f"Class {class_name} not found in the ontology.")
            return []

        self.add_element('d0', target_class)  # Start with initial element d0, assign to C0

        # Apply the rules iteratively
        self.apply_rules()

        # Compute subsumers
        subsumers = set()
        for concepts in self.elements.values():
            subsumers.update(concepts)

        # Filter out the target class and Thing
        return ['T' if cls == Thing else 'DomainThing' if cls.name == 'DomainConcept' else cls.name for cls in subsumers]

def load_ontology(file_path):
    ontology = get_ontology(file_path).load()
    return ontology

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
