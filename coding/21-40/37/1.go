package main

import "fmt"

type Person struct {
	Name string
	Age  int
}

type Employee struct {
	Person
	EmployeeID string
}

func main() {
	e := Employee{
		Person:     Person{Name: "Alice", Age: 30},
		EmployeeID: "EMP001",
	}

	fmt.Println("Name:", e.Name) // Accessing embedded field
	fmt.Println("Age:", e.Age)   // Accessing embedded field
	fmt.Println("Employee ID:", e.EmployeeID)
}
