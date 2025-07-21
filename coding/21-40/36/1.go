package main

import (
	"encoding/json"
	"fmt"
)

type User struct {
	Name  string `json:"name"`
	Email string `json:"email"`
	Age   int    `json:"age"`
}

func main() {
	data := `{"name": "Alice", "email": "alice@example.com", "age": 30}`
	var user User

	if err := json.Unmarshal([]byte(data), &user); err != nil {
		panic(err)
	}

	fmt.Printf("Decoded User: %+v\n", user)

	encoded, _ := json.Marshal(user)
	fmt.Println("Re-encoded JSON:", string(encoded))
}
