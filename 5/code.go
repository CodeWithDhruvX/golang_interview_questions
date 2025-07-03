package main

import (
	"fmt"
)

type DemoStruct struct {
	IntField       int
	FloatField     float64
	BoolField      bool
	StringField    string
	PointerField   *int
	SliceField     []string
	MapField       map[string]int
	ChannelField   chan int
	InterfaceField interface{}
	FuncField      func()
}

func main() {
	var d DemoStruct // declared but not initialized

	fmt.Println("Zero Value Table for DemoStruct fields:")
	fmt.Printf("IntField:       %v\n", d.IntField)
	fmt.Printf("FloatField:     %v\n", d.FloatField)
	fmt.Printf("BoolField:      %v\n", d.BoolField)
	fmt.Printf("StringField:    %q\n", d.StringField)
	fmt.Printf("PointerField:   %v\n", d.PointerField)
	fmt.Printf("SliceField:     %v\n", d.SliceField)
	fmt.Printf("MapField:       %v\n", d.MapField)
	fmt.Printf("ChannelField:   %v\n", d.ChannelField)
	fmt.Printf("InterfaceField: %v\n", d.InterfaceField)
	fmt.Printf("FuncField:      %v\n", d.FuncField)
}
