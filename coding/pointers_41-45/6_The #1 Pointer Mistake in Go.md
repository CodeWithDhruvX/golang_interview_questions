# The #1 Pointer Mistake in Go

6. The #1 Pointer Mistake in Go

Opening Hook (0:00–0:10)
“Are you passing big structs by value in Go? [pause] If so… RIP your performance. Let me show you the #1 pointer mistake beginners make.”

Concept Explanation (0:10–0:40)
“In Go, when you pass a struct by value, the entire thing gets copied. [pause] If that struct is small, no big deal. But if it’s huge — like thousands of elements — that copy wastes memory and slows everything down. [pause] Instead, you should usually pass a pointer.”

Code Walkthrough (0:40–1:20)
(show code on screen)
“Here’s a struct called Big with an array of 1000 integers.
We have two functions: changeValue(b Big) takes the struct by value, and changePointer(b *Big) takes a pointer.
Inside changeValue, we try to set the first element to 1. But because it’s a copy, the original never changes.
In main, we create b and call changeValue(b). When we print, it’s still 0.
Then we call changePointer(&b). This time it modifies the actual struct, and we see 1. [pause] Big difference!”

Why It’s Useful (1:20–2:10)
“This matters whenever you’re working with large data — structs, slices, or even maps wrapped inside structs. Passing by value can silently kill performance and give unexpected behavior. [pause] Passing a pointer means less memory overhead and actual modifications. [pause] But here’s the tip: benchmark before deciding. Sometimes a copy is okay if it makes your code clearer.”

Outro (2:10–2:30)
“So — have you ever accidentally passed a big struct by value? [pause] Tell me in the comments if you’ve hit this bug. And if this saved you some debugging pain, smash that like button and subscribe for more Go coding insights!”