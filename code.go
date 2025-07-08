package main

import (
	"fmt"
	"net/http"
	"time"
)

// fetch makes a simple GET request and sends the result to the channel
func fetch(url string, ch chan string) {
	start := time.Now()
	resp, err := http.Get(url)
	if err != nil {
		ch <- fmt.Sprintf("Error fetching %s", url)
		return
	}
	defer resp.Body.Close()
	duration := time.Since(start)
	ch <- fmt.Sprintf("Fetched %s in %v", url, duration)
}

func main() {
	urls := []string{"https://golang.org", "https://google.com", "https://github.com"}
	ch := make(chan string)

	// Start a goroutine for each URL
	for _, url := range urls {
		go fetch(url, ch)
	}

	// Receive results from the channel
	for range urls {
		fmt.Println(<-ch)
	}
}
