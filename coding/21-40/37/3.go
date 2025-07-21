package main

import "fmt"

type Address struct {
	City  string
	State string
}

type Contact struct {
	Phone string
	Email string
}

type Customer struct {
	Name    string
	Address // Embedded struct
	Contact // Embedded struct
}

func main() {
	c := Customer{
		Name:    "John Doe",
		Address: Address{City: "New York", State: "NY"},
		Contact: Contact{Phone: "1234567890", Email: "john@example.com"},
	}

	fmt.Printf("Customer: %s\n", c.Name)
	fmt.Printf("Location: %s, %s\n", c.City, c.State)
	fmt.Printf("Contact: %s / %s\n", c.Phone, c.Email)
}
