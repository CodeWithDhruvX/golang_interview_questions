# Iterate Over a Map in Go

5. Iterate Over a Map in Go

Opening Hook (0:00–0:10)
"Want to loop through a Go map? [pause] Here’s the right way—and the one thing most beginners get wrong!"

Concept Explanation (0:10–0:40)
"In Go, you use a for range loop to go over maps. But here’s the catch: map iteration order is random. That means every run might give you a different sequence of keys. If you expect a sorted order, you’ll be surprised."

Code Walkthrough (0:40–1:20)
"(show code)
We define a map: m := map[string]int{\"a\": 1, \"b\": 2}.
Then we loop with for k, v := range m.
This gives us each key and its value. Inside the loop, we print them with fmt.Println(k, v).
The output shows all pairs, but the order is unpredictable. Sometimes 'a' comes first, sometimes 'b'. Go deliberately randomizes it for safety."

Why It’s Useful (1:20–2:10)
"Random iteration order prevents developers from accidentally depending on key order—which could lead to flaky bugs. [pause] But if you really need order, you can collect the keys in a slice, sort them, and then iterate in the order you want. That’s the Go way: explicit and predictable."

Outro (2:10–2:30)
"So, have you ever been confused by Go’s map order randomness? [pause] Tell me your story in the comments below. And if this tip helped, smash that like button and subscribe for more Go deep-dives!"