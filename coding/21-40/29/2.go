package main

import (
	"fmt"
)

func main() {
	shoppingList := map[string][]string{
		"Fruits":     {"Apple", "Banana"},
		"Vegetables": {"Carrot", "Spinach"},
	}

	// Add a new category
	shoppingList["Dairy"] = []string{"Milk", "Cheese"}

	// Append to existing category
	shoppingList["Fruits"] = append(shoppingList["Fruits"], "Mango")

	// Iterate and print
	for category, items := range shoppingList {
		fmt.Println(category + ":")
		for _, item := range items {
			fmt.Println("  -", item)
		}
	}
}
