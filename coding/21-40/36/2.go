package main

import (
	"encoding/xml"
	"fmt"
)

type Product struct {
	XMLName xml.Name `xml:"product"`
	ID      int      `xml:"id"`
	Name    string   `xml:"name"`
	Price   float64  `xml:"price"`
}

func main() {
	item := Product{ID: 101, Name: "Gadget", Price: 19.99}

	output, err := xml.MarshalIndent(item, "", "  ")
	if err != nil {
		panic(err)
	}

	fmt.Println(string(output))
}
