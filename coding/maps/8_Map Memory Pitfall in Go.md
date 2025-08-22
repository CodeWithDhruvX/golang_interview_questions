# Map Memory Pitfall in Go

8. Map Memory Pitfall in Go

Opening Hook (0:00–0:10)
"There’s a sneaky memory pitfall with Go maps—[pause] and if you don’t know about it, your program could bloat over time!"

Concept Explanation (0:10–0:40)
"Maps in Go hold onto keys and values until they’re deleted. Even if a value is no longer used elsewhere, it sticks around in memory as long as the map keeps the reference. That can surprise new Go developers."

Code Walkthrough (0:40–1:20)
"(show code on screen)
Here we create a map: m := map[int]*int{}.
We assign x := 42 and then m[1] = &x, storing a pointer inside the map.
Next, we call delete(m, 1). This removes the entry from the map.
Finally, printing m gives map[]. It looks empty.
But here’s the catch: until garbage collection runs, the memory for that value may still be held."

Why It’s Useful (1:20–2:10)
"This pitfall is important for long-running programs like servers. [pause] If you don’t clean up maps properly, or you rely on resizing, you might hold onto memory longer than expected. The good news is: calling delete lets Go know it can free things up. But be mindful if you store large objects—map references can keep them alive."

Outro (2:10–2:30)
"Have you ever battled memory leaks in Go? [pause] Drop your experience in the comments below. And don’t forget to like and subscribe for more Go gotchas and fixes!"