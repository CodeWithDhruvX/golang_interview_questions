package main

import (
	"encoding/json"
	"fmt"
)

type Product struct {
	Name    string  `json:"product_name"`
	Price   float64 `json:"product_price"`
	InStock bool    `json:"available"`
}

func main() {
	item := Product{Name: "Laptop", Price: 999.99, InStock: true}

	jsonOutput, err := json.MarshalIndent(item, "", "  ")
	if err != nil {
		fmt.Println("Error:", err)
		return
	}

	fmt.Println(string(jsonOutput))
}
