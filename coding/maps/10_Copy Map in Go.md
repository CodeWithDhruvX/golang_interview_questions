# Copy Map in Go

10. Copy Map in Go

Opening Hook (0:00–0:10)
"Think assigning one map to another in Go makes a copy? [pause] Wrong—it actually creates a trap that catches many beginners!"

Concept Explanation (0:10–0:40)
"In Go, maps are reference types. That means if you do map2 := map1, both variables point to the same underlying data. Change one, and the other changes too. If you want a true copy, you need to loop through the map and copy each key-value pair."

Code Walkthrough (0:40–1:20)
"(show code on screen)
We start with m1 := map[string]int{\"a\": 1}.
Next, we create m2 := map[string]int{} — an empty map.
Then we loop: for k, v := range m1 { m2[k] = v }. This copies every key and value into the new map.
Finally, printing m1 and m2 shows map[a:1] map[a:1]. Two separate maps—modifying one won’t affect the other."

Why It’s Useful (1:20–2:10)
"This is super useful when you need to duplicate data safely. [pause] For example, maybe you’re caching results and don’t want later changes to affect your backup. Or you’re writing a function that shouldn’t mutate the caller’s data. Knowing that maps are references—and how to copy them properly—helps avoid sneaky bugs in production."

Outro (2:10–2:30)
"So, did you think map2 := map1 was making a copy before today? [pause] Tell me honestly in the comments. And if you want more Go pitfalls explained in plain English, hit like and subscribe so you never miss a tip!"