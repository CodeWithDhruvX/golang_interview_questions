package main

import "fmt"

type Logger struct{}

func (l Logger) Log(message string) {
	fmt.Println("[LOG]:", message)
}

type App struct {
	Logger
	Name string
}

func main() {
	app := App{Name: "MyApp"}
	app.Log("Application started") // Promoted method
}
