# Slices as Map Keys in Go

4. Slices as Map Keys in Go

Opening Hook (0:00–0:10)
"Can you use slices as map keys in Go? [pause] This is one of the most common interview traps—and it might just crash your program!"

Concept Explanation (0:10–0:40)
"In Go, not every type can be used as a map key. Keys must be comparable. That means Go needs to know how to check if two keys are equal. Basic types like strings, integers, and even arrays are fine. But slices? Nope. Slices are not comparable, and if you try, you’ll hit a runtime panic."

Code Walkthrough (0:40–1:20)
"(show code on screen)
Here’s an example: m := map[[]int]string{} won’t even compile—it’s invalid.
But arrays are allowed because they’re comparable.
So in this code, we define an array arrKey := [2]int{1, 2}.
Then we create a map using that array as a key: m := map[[2]int]string{arrKey: \"ok\"}.
Finally, printing the map gives map[[1 2]:ok].
This works because arrays have fixed size and are fully comparable—unlike slices."

Why It’s Useful (1:20–2:10)
"This matters when you need to represent complex keys. [pause] For example, you might want to group data by a pair of integers, or by a small fixed-size array. Arrays work perfectly here. But if you really need to use slices, the workaround is converting the slice to a string—like string(slice)—before using it as a key. Just remember: slices themselves can’t be keys."

Outro (2:10–2:30)
"So tell me—did you already know slices can’t be keys in Go? [pause] Drop your answer in the comments. And if you want more Go interview tips, don’t forget to hit like and subscribe!"