# Sort Map by Key in Go

6. Sort Map by Key in Go

Opening Hook (0:00–0:10)
"Go maps are unordered—so how do you sort them? [pause] Let’s unlock this Go coding secret."

Concept Explanation (0:10–0:40)
"Maps in Go are designed for fast lookups, not ordered storage. That’s why you can’t just say, ‘give me the items in sorted order’. But when you do need sorting—for example, printing leaderboard scores—you can sort the keys separately, then access the values in order."

Code Walkthrough (0:40–1:20)
"(show code)
We start with m := map[string]int{\"b\": 2, \"a\": 1}.
First, we collect all keys into a slice:
go\nkeys := []string{}\nfor k := range m {\n keys = append(keys, k)\n}\n
Next, we call slices.Sort(keys)—this sorts the keys alphabetically.
Finally, we loop through keys and print each key with its value.
The output is nicely ordered: a 1 followed by b 2."

Why It’s Useful (1:20–2:10)
"This technique is essential when you want consistent output. [pause] Think about config files, JSON generation, or reporting where order matters. By sorting the keys, you control exactly how the data is presented—even though Go maps themselves stay unordered under the hood."

Outro (2:10–2:30)
"Have you ever needed sorted maps in Go, maybe for JSON or reporting? [pause] Drop your experience in the comments. And if you’re enjoying these quick Go tips, hit like and subscribe so you don’t miss the next one!"