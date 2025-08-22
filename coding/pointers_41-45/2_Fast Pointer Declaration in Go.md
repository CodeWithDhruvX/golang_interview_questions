# Fast Pointer Declaration in Go

2. Fast Pointer Declaration in Go

Opening Hook (0:00–0:10)
“Stop wasting time declaring pointers the long way! [pause] In Go, there’s a faster way to create pointers, and I’ll show you how in just 60 seconds.”

Concept Explanation (0:10–0:40)
“In Go, you can declare pointers in multiple ways. The traditional method involves declaring a variable, assigning it, and then pointing to it. But there’s a shortcut: the built-in new function. [pause] It allocates memory for a type and returns a pointer to it — simple and clean.”

Code Walkthrough (0:40–1:20)
(show code on screen)
“Here’s how it works:
We write p := new(int). This tells Go to create memory for an integer and give us back a pointer to it.
Then we assign *p = 99. Notice the star again — dereferencing. We’re not setting the pointer itself, but the value at that memory address.
Finally, we print *p, and the result is 99. [pause] That’s it! One line to declare and allocate.”

Why It’s Useful (1:20–2:10)
“Why bother with new? [pause] It’s a quick, clean way to grab a pointer when you don’t care about the variable name beforehand. This is handy in scenarios like initializing counters, flags, or when you’re passing data structures into functions that expect pointers. [pause] It keeps your code concise and readable.”

Outro (2:10–2:30)
“So — do you prefer the new approach or the manual declaration? Let me know in the comments. [pause] And don’t forget to subscribe for more quick Go coding tips and tricks!”