# Convert a struct to JSON

6. Convert a struct to JSON

Opening Hook (0:00–0:10)
"Want to turn a Go struct into JSON in just one line? [pause] It’s easier than you think — let me show you."

Concept Explanation (0:10–0:40)
"Go has a built-in package called encoding/json that makes converting structs into JSON super straightforward. JSON is the standard format for APIs, config files, and data exchange, so knowing how to do this is a must-have skill for any Go developer."

Code Walkthrough (0:40–1:20)
"(show code on screen)
We define a struct called User with one field: Username string. Notice we added a tag json:\"username\" so the JSON key is lowercase.
In main, we create u := User{\"Dave\"}.
Then we call json.Marshal(u) which turns the struct into JSON bytes.
Finally, fmt.Println(string(b)) prints it as text. The result? {\"username\":\"Dave\"}."

Why It’s Useful (1:20–2:10)
"This is used constantly when building REST APIs. Imagine your backend written in Go sending data to a frontend in React or Vue — that communication almost always happens through JSON. Struct tags give you control over the format, so you can match whatever the client expects. It’s also great for reading or writing JSON config files directly into Go structs."

Outro (2:10–2:30)
"And that’s how easy it is to convert a struct to JSON in Go. [pause] What’s the first API or project you’d use this in? Drop your ideas below! And don’t forget to like and subscribe for more practical Go tutorials."