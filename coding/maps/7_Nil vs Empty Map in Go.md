# Nil vs Empty Map in Go

7. Nil vs Empty Map in Go

Opening Hook (0:00–0:10)
"This Go map question trips up 70% of interviewees: [pause] What’s the difference between a nil map and an empty map? Let’s clear it up!"

Concept Explanation (0:10–0:40)
"In Go, maps can either be uninitialized, meaning they’re nil, or they can be created as empty maps with no elements. Both look similar, but they behave differently when you try to use them."

Code Walkthrough (0:40–1:20)
"(show code)
Here we declare var nilMap map[string]int. That’s a nil map—it hasn’t been allocated any memory.
Next, emptyMap := make(map[string]int) creates a proper empty map, ready to use.
When we print nilMap == nil, the result is true.
When we print emptyMap == nil, it’s false—because it exists, just with no keys yet."

Why It’s Useful (1:20–2:10)
"This distinction matters in real-world Go. [pause] If you try to insert into a nil map, you’ll get a runtime panic. But inserting into an empty map works just fine. That’s why many developers use make when initializing maps. It guarantees the map is usable right away. This becomes crucial in APIs, JSON decoding, or any scenario where a nil map might slip through."

Outro (2:10–2:30)
"So, quick question: have you ever hit a nil map panic in your Go code? [pause] Share your story in the comments! And if you’re learning something new today, hit like and subscribe for more Go insights."