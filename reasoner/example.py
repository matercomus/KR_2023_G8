#! /usr/bin/python

from py4j.java_gateway import JavaGateway

# connect to the java gateway of dl4python
gateway = JavaGateway()

# get a parser from OWL files to DL ontologies
parser = gateway.getOWLParser()

# get a formatter to print in nice DL format
formatter = gateway.getSimpleDLFormatter()

print("Loading the ontology...")

# load an ontology from a file
ontology = parser.parseFile("amino-acid.amino-acid-ontology.2.owl.xml")

print("Loaded the ontology!")

# IMPORTANT: the algorithm from the lecture assumes conjunctions to always be over two concepts
# Ontologies in OWL can however have conjunctions over an arbitrary number of concpets.
# The following command changes all conjunctions so that they have at most two conjuncts
print("Converting to binary conjunctions")
gateway.convertToBinaryConjunctions(ontology)



# get the TBox axioms
tbox = ontology.tbox()
axioms = tbox.getAxioms()


print("These are the axioms in the TBox:")
for axiom in axioms:
    print(formatter.format(axiom))


# get all concepts occurring in the ontology
allConcepts = ontology.getSubConcepts()

print()
print("There are ",len(allConcepts), " concepts occurring in the ontology")
print("These are the concepts occurring in the ontology:")
print([formatter.format(x) for x in allConcepts])

conceptNames = ontology.getConceptNames()

print()
print("There are ", len(conceptNames), " concept names occurring in the ontology")
print("These are the concept names: ")
print([formatter.format(x) for x in conceptNames])


# access the type of axioms:
foundGCI = False
foundEquivalenceAxiom = False
print()
print("Looking for axiom types in EL")
for axiom in axioms:
    axiomType = axiom.getClass().getSimpleName() 
    #print(axiomType)
    if(not(foundGCI)
       and axiomType == "GeneralConceptInclusion"):
        print("I found a general concept inclusion:")
        print(formatter.format(axiom))
        print("The left hand side of the axiom is: ", formatter.format(axiom.lhs()))
        print("The right hand side of the axiom is: ", formatter.format(axiom.rhs()))
        print()
        foundGCI = True

    elif(not(foundEquivalenceAxiom)
         and axiomType == "EquivalenceAxiom"):
        print("I found an equivalence axiom:")
        print(formatter.format(axiom))
        print("The concepts made equivalent are: ")
        for concept in axiom.getConcepts():
            print(" - "+formatter.format(concept))
        print()
        foundEquivalenceAxiom = True

# accessing the relevant types of concepts:
foundConceptName=False
foundTop=False
foundExistential=False
foundConjunction=False
foundConceptTypes = set()

print()
print("Looking for concept types in EL")
for concept in allConcepts:
    conceptType = concept.getClass().getSimpleName()
    if(not(conceptType in foundConceptTypes)): 
        print(conceptType)
        foundConceptTypes.add(conceptType)
    if(not(foundConceptName) and conceptType == "ConceptName"):
        print("I found a concept name: "+formatter.format(concept))
        print()
        foundConceptName = True
    elif(not(foundTop) and conceptType == "TopConcept$"):
        print("I found the top concept: "+formatter.format(concept))
        print()
        foundTop = True
    elif(not(foundExistential) and conceptType == "ExistentialRoleRestriction"):
        print("I found an existential role restriction: "+formatter.format(concept))
        print("The role is: "+formatter.format(concept.role()))
        print("The filler is: "+formatter.format(concept.filler()))
        print()
        foundExistential = True
    elif(not(foundConjunction) and conceptType == "ConceptConjunction"):
        print("I found a conjunction: "+formatter.format(concept))
        print("The conjuncts are: ")
        for conjunct in concept.getConjuncts():
            print(" - "+formatter.format(conjunct))
        print()
        foundConjunction=True


# Creating EL concepts and axioms

elFactory = gateway.getELFactory()

conceptA = elFactory.getConceptName("A")
conceptB = elFactory.getConceptName("B")
conjunctionAB = elFactory.getConjunction(conceptA, conceptB)
role = elFactory.getRole("r")
existential = elFactory.getExistentialRoleRestriction(role,conjunctionAB)
top = elFactory.getTop()
conjunction2 = elFactory.getConjunction(top,existential)

gci = elFactory.getGCI(conjunctionAB,conjunction2)

print()
print()
print("I made the following GCI:")
print(formatter.format(gci))

# Define the ELReasoner class
class ELReasoner:
    def __init__(self, ontology):
        self.ontology = ontology
        self.subsumers = {}

    def apply_top_rule(self, concept):
        # Implement the ⊤-rule here
        if concept.getClass().getSimpleName() == "TopConcept$":
            self.subsumers[concept].add(concept)

    def apply_conjunction_rules(self, concept):
        # Implement the ⊓-rules here
        if concept.getClass().getSimpleName() == "ConceptConjunction":
            for conjunct in concept.getConjuncts():
                self.subsumers[concept].update(self.getSubsumers(conjunct))
            print(f"Applied conjunction rules to {formatter.format(concept)}: {self.format_concepts(self.subsumers[concept])}")

    def apply_existential_rules(self, concept):
        # Implement the ∃-rules here
        if concept.getClass().getSimpleName() == "ExistentialRoleRestriction":
            filler = concept.filler()
            for other_concept in self.ontology.getSubConcepts():
                if other_concept.getClass().getSimpleName() == "ConceptName" and other_concept == filler:
                    self.subsumers[concept].add(other_concept)
            print(f"Applied existential rules to {formatter.format(concept)}: {self.format_concepts(self.subsumers[concept])}")

    def apply_subsumption_rule(self, concept):
        # Implement the ⊑-rule here
        for axiom in self.ontology.tbox().getAxioms():
            if axiom.getClass().getSimpleName() == "GeneralConceptInclusion":
                lhs = axiom.lhs()
                rhs = axiom.rhs()
                if lhs in self.getSubsumers(concept):
                    self.subsumers[concept].add(rhs)
        print(f"Applied subsumption rule to {formatter.format(concept)}: {self.format_concepts(self.subsumers[concept])}")

    def reason(self):
        changed = True
        while changed:
            changed = False
            for concept in self.ontology.getSubConcepts():
                old_subsumers = self.getSubsumers(concept)
                self.apply_top_rule(concept)
                self.apply_conjunction_rules(concept)
                self.apply_existential_rules(concept)
                self.apply_subsumption_rule(concept)
                new_subsumers = self.getSubsumers(concept)
                if old_subsumers != new_subsumers:
                    changed = True
            print(f"After reasoning, subsumers for {formatter.format(concept)}: {self.format_concepts(self.subsumers[concept])}")

    def getSubsumers(self, concept):
        if concept not in self.subsumers:
            self.subsumers[concept] = set([concept])
        return self.subsumers[concept]

    def format_concepts(self, concepts):
        return [formatter.format(concept) for concept in concepts]

# Create an instance of ELReasoner
el_reasoner = ELReasoner(ontology)

# Example usage similar to ELK and HermiT
margherita = elFactory.getConceptName('A')
print("\nI am now testing the ELReasoner.")
el_reasoner.reason()
print("\nAccording to the ELReasoner, A has the following subsumers: ")
subsumers = el_reasoner.getSubsumers(margherita)
for concept in subsumers:
    print(" - ", formatter.format(concept))
print("(", len(subsumers), " in total)")

# Using the reasoners

elk = gateway.getELKReasoner()
hermit = gateway.getHermiTReasoner() # might the upper case T!

margherita = elFactory.getConceptName('A')

print()
print("I am first testing ELK.")
elk.setOntology(ontology)
print()
print("According to ELK, Margherita has the following subsumers: ")
subsumers = elk.getSubsumers(margherita)
for concept in subsumers:
    print(" - ",formatter.format(concept))
print("(",len(subsumers)," in total)")
print()
print("I can also classify the ontology with ELK.")
classificationResult = elk.classify()
print("But I am not printing the result, because that would be too much stuff (it is a dictionary)")
print()

# print()
# print("I am now testing HermiT.")
# hermit.setOntology(ontology)
# print()
# print("According to HermiT, Margherita has the following subsumers: ")
# subsumers = hermit.getSubsumers(margherita)
# for concept in subsumers:
#     print(" - ",formatter.format(concept))
# print("(",len(subsumers)," in total)")
# print()
# print("I can also classify the ontology with HermiT")
# classificationResult = hermit.classify()
# print("But I am not printing the result, because that would be too much stuff (it is a dictionary)")
# print()
