# The Silent Bug in Go Methods

9. The Silent Bug in Go Methods

Opening Hook (0:00–0:10)
“This one line of code in Go looks fine… [pause] but it creates a silent bug that’ll drive you crazy. Let’s catch it before it bites.”

Concept Explanation (0:10–0:40)
“In Go, when you use a value receiver, the method gets a copy of the struct. [pause] If you try to change something, the original doesn’t update. [pause] That’s fine if you just want to read data — but deadly if you think you’re actually modifying it.”

Code Walkthrough (0:40–1:20)
(show code on screen)
“Here’s a Counter struct with one field, n.
The method IncValue has a value receiver. Inside, it does c.n++, but remember — that’s a copy.
Then there’s IncPointer, which uses a pointer receiver.
In main, we create a counter starting at 0. We call c.IncValue(), and when we print, it’s still 0. [pause] Bug!
Then we call c.IncPointer(), and now it prints 1. [pause] That’s the correct behavior.”

Why It’s Useful (1:20–2:10)
“This distinction matters every time you’re designing methods. [pause] If you expect a method to modify state, always use a pointer receiver. Otherwise, your program may look like it works but silently fail to update data. [pause] Think of counters, balances, configurations — anything that needs persistent change must use pointer receivers.”

Outro (2:10–2:30)
“Have you ever spent hours debugging, only to realize your method used a value receiver? [pause] If yes, share your story in the comments — we’ve all been there. And if this tip saves you time, make sure to like, share, and subscribe for more Go pitfalls explained.”