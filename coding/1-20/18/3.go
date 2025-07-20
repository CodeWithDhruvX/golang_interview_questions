package main

import "fmt"

type Writer interface {
	Write([]byte) (int, error)
}

type Dummy struct{}

// We’re required to implement Writer but don’t actually use the return values
func (d Dummy) Write(p []byte) (int, error) {
	_, _ = fmt.Println("Pretend writing:",
		string(p))
	return 0, nil
}

func main() {
	var w Writer = Dummy{}
	w.Write([]byte("Hello Golang"))
}
