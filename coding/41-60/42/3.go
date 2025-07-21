package main

import "fmt"

type User struct {
	name string
	age  int
}

func (u *User) celebrateBirthday() {
	u.age += 1
}

func main() {
	user := User{name: "Alice", age: 29}
	fmt.Println("Before:", user)

	userPointer := &user
	userPointer.celebrateBirthday()

	fmt.Println("After:", user)
}
