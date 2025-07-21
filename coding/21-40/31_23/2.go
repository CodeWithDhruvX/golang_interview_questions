package main

import (
	"fmt"
	"reflect"
)

func main() {
	map1 := map[string]int{"foo": 10, "bar": 20}
	map2 := map[string]int{"bar": 20, "foo": 10}

	isEqual := reflect.DeepEqual(map1, map2)
	fmt.Println("Are maps equal?", isEqual)
}
