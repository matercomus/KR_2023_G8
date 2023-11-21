#!/bin/bash

# Define your list
list=("Pizza" "PizzaBase" "Food" "Spiciness" "PizzaTopping" "American" "NamedPizza" "MozzarellaTopping" "PeperoniSausageTopping" "TomatoTopping")

# Loop over the list
for item in "${list[@]}"; do
	# Run your command and store its output
	output=$(python no_java_lib.py pizza.owl "$item")

	# Print the output
	echo "$output"
  echo ""
done

