package main

import (
	"encoding/json"
	"fmt"
)

type User struct {
	Name  string
	Age   int
	Email string
}

func main() {
	user := User{Name: "Alice", Age: 30, Email: "alice@example.com"}

	jsonData, err := json.Marshal(user)
	if err != nil {
		fmt.Println("Error marshaling JSON:", err)
		return
	}

	fmt.Println(string(jsonData))
}
