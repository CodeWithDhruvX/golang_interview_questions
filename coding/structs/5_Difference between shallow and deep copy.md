# Difference between shallow and deep copy?

5. Difference between shallow and deep copy?

Opening Hook (0:00–0:10)
"Copying structs in Go might not work the way you think… [pause] because sometimes it only makes a shallow copy, not a deep one."

Concept Explanation (0:10–0:40)
"In Go, when you assign one struct to another, the values of its fields are copied. That’s fine for simple data like strings and numbers. But if the struct contains a reference type like a slice or map, only the reference gets copied. This means both structs point to the same underlying data — which can lead to surprising bugs."

Code Walkthrough (0:40–1:20)
"(show code on screen)
We define a struct Data with a field Values, which is a slice of ints.
In main, we create d1 := Data{[]int{1, 2}}.
Then we assign d2 := d1. Looks like we made a copy, right? But here’s the pitfall: when we change d2.Values[0] = 99, it actually changes d1.Values too.
The output is [99 2], not the [1 2] you might expect. That’s a shallow copy in action!"

Why It’s Useful (1:20–2:10)
"Understanding shallow versus deep copy is crucial when working with structs that hold slices, maps, or pointers. If you really need a separate copy, you have to create a new slice and copy the values manually, or use helper functions. This comes up a lot in data processing, where you don’t want different parts of your program accidentally sharing the same data."

Outro (2:10–2:30)
"So now you know the hidden trap of shallow copies in Go. [pause] Have you ever been bitten by this bug? Tell me your story in the comments! And don’t forget to hit like and subscribe so you don’t miss future Go tips."