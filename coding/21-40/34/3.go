package main

import (
	"fmt"
	"sort"
)

type kv struct {
	Key   string
	Value int
}

func main() {
	m := map[string]int{"banana": 3, "apple": 2, "cherry": 5}
	var list []kv

	for k, v := range m {
		list = append(list, kv{k, v})
	}

	sort.SliceStable(list, func(i, j int) bool {
		return list[i].Value > list[j].Value
	})

	for _, item := range list {
		fmt.Printf("%s: %d\n", item.Key, item.Value)
	}
}
