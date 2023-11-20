from owlready2 import *

onto = get_ontology("http://example.org/onto.owl")

with onto:
    class Food(Thing):
        pass

    class Pizza(Food):
        pass

    class Vegetable(Food):
        pass

    class Cheese(Thing):
        pass

    class hasIngredient(ObjectProperty):
        pass

    class isToppingOf(hasIngredient):
        inverse_property = hasIngredient

    class Margherita(Pizza):
        equivalent_to = [Pizza & hasIngredient.some(Cheese)]

    margheritaInstance = Margherita()

onto.save(file="small_ontology.owl")
