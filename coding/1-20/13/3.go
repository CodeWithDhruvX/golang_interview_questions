package main

import "fmt"

func getStatus(score int) (status string) {
	if score >= 40 {
		status = "Pass"
		// return status
		return
	}
	status = "Fail"
	// return status
	return
}

func main() {
	fmt.Println("Student Status:", getStatus(55))
}
