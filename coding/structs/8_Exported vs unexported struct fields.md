# Exported vs unexported struct fields

8. Exported vs unexported struct fields

Opening Hook (0:00–0:10)
"Why is your JSON missing fields in Go? [pause] The answer might surprise you: it’s because of capitalization!"

Concept Explanation (0:10–0:40)
"In Go, identifiers that start with a capital letter are exported, meaning they’re visible outside the package. Identifiers with lowercase letters are unexported — they’re private. This rule also affects JSON marshaling, which is why lowercase struct fields won’t show up in the output."

Code Walkthrough (0:40–1:20)
"(show code on screen)
We have a struct Person with two fields: name string and Age int. Notice that name starts lowercase, while Age is uppercase.
In main, we create p := Person{\"Frank\", 40} and call json.Marshal(p).
When we print the JSON, the output is { \"Age\":40 }. The name field is missing! That’s because lowercase fields are unexported."

Why It’s Useful (1:20–2:10)
"This behavior is critical when building APIs. If you expect your JSON to include all fields, you need to make sure the struct fields are exported. On the flip side, sometimes you want fields to stay private — and this capitalization rule makes that easy. It’s also a fundamental concept of Go’s design: explicit simplicity over hidden magic."

Outro (2:10–2:30)
"So remember: capitalize your struct fields if you want them in JSON. [pause] Have you ever been stuck wondering why your JSON was empty? Share your story below! And if this cleared things up, hit like and subscribe for more Go basics."