package main

import (
	"fmt"
	"reflect"
)

func printWithTypes(values ...interface{}) {
	for _, val := range values {
		fmt.Printf("Value: %v, Type: %s\n", val, reflect.TypeOf(val))
	}
}

func main() {
	printWithTypes("hello", 42, 3.14, true)
}
