# Compare Maps in Go

2. Compare Maps in Go

Opening Hook (0:00–0:10)
"Think you can just compare two maps in Go with ==? Nope! [pause] This is one of the most common interview traps."

Concept Explanation (0:10–0:40)
"In Go, maps are not directly comparable. That means if you try map1 == map2, the compiler will throw an error. The only direct check you can do is whether a map is nil. So how do we compare them? Well, that’s where Go’s newer features come in."

Code Walkthrough (0:40–1:20)
"(show code)
We import maps from the Go standard library.
Then, we create two maps: m1 := map[string]int{\"a\": 1} and m2 := map[string]int{\"a\": 1}.
At first glance, they look identical—but Go doesn’t let us compare them with ==.
Instead, we use maps.Equal(m1, m2), which checks if both maps contain exactly the same keys and values.
The output here is true, because both maps are equal in content."

Why It’s Useful (1:20–2:10)
"[pause] So the next time you want to know if two maps are the same—you’ve got the right tool."

Outro (2:10–2:30)
"Quick question: have you ever used reflect.DeepEqual in your Go projects? [pause] Drop a comment and tell me. And if you want more Go tips like this, hit subscribe and join our community of learners!"