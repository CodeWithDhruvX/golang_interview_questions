package main

import (
	"fmt"
	"sync"
)

type singleton struct {
	value string
}

var instance *singleton
var once sync.Once

func GetInstance() *singleton {
	once.Do(func() {
		fmt.Println("Creating singleton instance...")
		instance = &singleton{value: "Go Singleton"}
	})
	return instance
}

func main() {
	s1 := GetInstance()
	s2 := GetInstance()
	fmt.Println("Are both instances same?", s1 == s2)
}
