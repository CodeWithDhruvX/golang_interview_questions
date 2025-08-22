# How do you define and use struct tags?

2. How do you define and use struct tags?

Opening Hook (0:00–0:10)
"Ever tried converting a struct to JSON in Go… and got an empty result? [pause] The secret is struct tags, and once you see them, you’ll never forget."

Concept Explanation (0:10–0:40)
"Struct tags are special annotations you attach to fields in a struct. They tell Go’s libraries, like the JSON encoder, how to interpret and use your fields. Without tags, Go might not output the data the way you expect — which leads to frustration and bugs."

Code Walkthrough (0:40–1:20)
"(show code on screen)
Here, we define type Person struct { Name string \json:"name"`; Age int `json:"age"` }. Notice those backticks with json:"name"andjson:"age". These are the struct tags. They tell Go: when converting to JSON, map Nameto"name"andAgeto"age". In main, we create a Person{"Bob", 25}, then use json.Marshal(p)to convert it to JSON. The result is{"name":"Bob","age":25}` — exactly what we wanted!"

Why It’s Useful (1:20–2:10)
"Struct tags are super common when working with APIs, configuration files, or databases. Imagine you’re building a REST API — your Go struct might use capitalized field names, but the JSON your frontend expects is lowercase. Tags solve this problem instantly. They’re also used for XML, database ORM mappings, and even validation libraries."

Outro (2:10–2:30)
"So that’s struct tags in Go. [pause] Have you ever run into the missing-JSON-field bug before? Drop a 'yes' or 'no' in the comments! And if this helped, hit that like button and subscribe for more Go coding lessons."