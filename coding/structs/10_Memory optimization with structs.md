# Memory optimization with structs

10. Memory optimization with structs

Opening Hook (0:00–0:10)
"Want to make your Go programs faster and more memory efficient? [pause] The trick is how you order your struct fields."

Concept Explanation (0:10–0:40)
"In Go, struct fields are aligned in memory, and the compiler sometimes adds padding between them. If you don’t order fields carefully, you might waste memory. By grouping fields by size, you can shrink the struct’s footprint and make your program leaner."

Code Walkthrough (0:40–1:20)
"(show code on screen)
Here’s an example:
Bad has fields in the order A byte, B int64, C byte. Because of alignment, it ends up taking 24 bytes.
Now look at Good: we reorder the fields as B int64, then A byte, then C byte. The size drops to just 16 bytes.
We confirm this with unsafe.Sizeof, which prints 24 for the bad version and 16 for the good version."

Why It’s Useful (1:20–2:10)
"This kind of optimization can add up in high-performance systems where you’re storing thousands or millions of structs, like in databases, caches, or real-time simulations. While you shouldn’t obsess over it too early, it’s a great technique to keep in your toolbox when performance really matters."

Outro (2:10–2:30)
"So that’s how struct field ordering can save memory in Go. [pause] Have you ever optimized your structs for memory before, or is this new to you? Tell me in the comments, and don’t forget to like and subscribe for more Go performance tips."