package main

import (
	"errors"
	"fmt"
)

func getValue(m map[string]int, key string) (int, error) {
	if val, ok := m[key]; ok {
		return val, nil
	}
	return 0, errors.New("key not found")
}

func main() {
	animals := map[string]int{"lion": 3, "tiger": 5}

	value, err := getValue(animals, "tiger")
	if err != nil {
		fmt.Println(err)
	} else {
		fmt.Printf("'tiger' has value: %d\n", value)
	}
}
